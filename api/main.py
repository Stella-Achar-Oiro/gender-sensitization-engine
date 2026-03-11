"""JuaKazi Correction API — HTTP routing only."""

import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .audit import log as log_audit
from .ml_rewriter import ml_rewrite
from .rules_engine import apply_rules_on_spans, build_reason
from .schemas import BatchRewriteRequest, RewriteRequest, RewriteResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval.correction_evaluator import SemanticPreservationMetrics

logger = logging.getLogger(__name__)
SEMANTIC_THRESHOLD = 0.70

app = FastAPI(title="JuaKazi Correction Engine (hybrid)", version="0.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
semantic_metrics = SemanticPreservationMetrics()


@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    t0 = time.time()
    try:
        rewritten, edits, matched_rules, skipped = apply_rules_on_spans(
            req.text, req.lang, flags=req.flags or None
        )
        source = "rules"
        ml_info = None
        semantic_score = None

        if rewritten != req.text:
            score = semantic_metrics.calculate_composite_preservation_score(req.text, rewritten)
            semantic_score = score["composite_score"]
            if semantic_score < SEMANTIC_THRESHOLD:
                rewritten, edits, source, semantic_score = req.text, [], "preserved", 1.0

        if matched_rules == 0 and source != "preserved":
            ml_out = ml_rewrite(req.text, lang=req.lang, num_return_sequences=3)
            ml_score = semantic_metrics.calculate_composite_preservation_score(req.text, ml_out["best"])
            if ml_score["composite_score"] < SEMANTIC_THRESHOLD:
                rewritten, source, semantic_score = req.text, "preserved", 1.0
            else:
                rewritten = ml_out["best"]
                source = "ml"
                semantic_score = ml_score["composite_score"]
                ml_info = ml_out
                edits.append({"from": req.text, "to": rewritten, "severity": "ml_fallback", "tags": "", "reason": "ML rewrite"})

        latency_ms = int((time.time() - t0) * 1000)
        confidence = {"rules": 0.85, "ml": 0.60, "preserved": 0.95}.get(source, 0.85)
        needs_review = source == "ml" or len(edits) == 0
        reason = build_reason(source, edits, skipped)
        has_bias_detected = any(e.get("severity") == "replace" for e in edits)

        response = RewriteResponse(
            id=req.id,
            original_text=req.text,
            rewrite=rewritten,
            edits=edits,
            confidence=confidence,
            needs_review=needs_review,
            source=source,
            reason=reason,
            semantic_score=semantic_score,
            skipped_context=skipped or None,
            has_bias_detected=has_bias_detected,
        )
        log_audit({
            "request": req.model_dump(),
            "response": response.model_dump(),
            "model_info": ml_info or {"model": "rulepack-v0.3"},
            "latency_ms": latency_ms,
            "region_dialect": req.region_dialect or "unknown",
        })
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("rewrite failed id=%s lang=%s", req.id, req.lang)
        raise HTTPException(status_code=500, detail="Rewrite failed; try again or contact support.") from e


@app.post("/rewrite/batch", response_model=list[RewriteResponse])
def rewrite_batch(body: BatchRewriteRequest):
    return [rewrite(item) for item in body.items]
