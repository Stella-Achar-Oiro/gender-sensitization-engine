"""JuaKazi rewrite service — core correction logic (no HTTP)."""

import time
from typing import Optional

from config import get_semantic_threshold, REWRITE_CONFIDENCE_BY_SOURCE, DEFAULT_REWRITE_CONFIDENCE
from core.semantic_preservation import SemanticPreservationMetrics

from .ml_rewriter import ml_rewrite
from .rules_engine import apply_rules_on_spans, build_reason
from .schemas import RewriteResponse

semantic_metrics = SemanticPreservationMetrics()


def rewrite_text(
    id: str,
    text: str,
    lang: str,
    flags: Optional[list] = None,
    region_dialect: Optional[str] = None,
) -> tuple[RewriteResponse, dict]:
    """
    Run bias detection + correction. Returns (response, audit_info).
    audit_info has model_info, latency_ms for logging.
    """
    t0 = time.time()
    rewritten, edits, matched_rules, skipped = apply_rules_on_spans(
        text, lang, flags=flags
    )
    source = "rules"
    ml_info = None
    semantic_score = None

    threshold = get_semantic_threshold()
    if rewritten != text:
        score = semantic_metrics.calculate_composite_preservation_score(text, rewritten)
        semantic_score = score["composite_score"]
        if semantic_score < threshold:
            rewritten, edits, source, semantic_score = text, [], "preserved", 1.0

    if matched_rules == 0 and source != "preserved":
        ml_out = ml_rewrite(text, lang=lang, num_return_sequences=3)
        ml_score = semantic_metrics.calculate_composite_preservation_score(
            text, ml_out["best"]
        )
        if ml_score["composite_score"] < threshold:
            rewritten, source, semantic_score = text, "preserved", 1.0
        else:
            rewritten = ml_out["best"]
            source = "ml"
            semantic_score = ml_score["composite_score"]
            ml_info = ml_out
            edits.append({
                "from": text,
                "to": rewritten,
                "severity": "ml_fallback",
                "tags": "",
                "reason": "ML rewrite",
            })

    latency_ms = int((time.time() - t0) * 1000)
    confidence = REWRITE_CONFIDENCE_BY_SOURCE.get(source, DEFAULT_REWRITE_CONFIDENCE)
    needs_review = source == "ml" or len(edits) == 0
    reason = build_reason(source, edits, skipped)
    has_bias_detected = any(e.get("severity") == "replace" for e in edits)

    response = RewriteResponse(
        id=id,
        original_text=text,
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
    audit_info = {
        "model_info": ml_info or {"model": "rulepack-v0.3"},
        "latency_ms": latency_ms,
        "region_dialect": region_dialect or "unknown",
    }
    return response, audit_info
