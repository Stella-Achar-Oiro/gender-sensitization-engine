"""JuaKazi rewrite service — core correction logic (no HTTP)."""

import time
from typing import Optional

from config import (
    AIBRIDGE_ENABLED,
    DEFAULT_REWRITE_CONFIDENCE,
    REWRITE_CONFIDENCE_BY_SOURCE,
    get_semantic_threshold,
)
from core.semantic_preservation import SemanticPreservationMetrics

from .bias_detection_client import LANG_CODE_MAP, AibridgeResult, detect_bias
from .disambiguator import disambiguate
from .ml_rewriter import ml_rewrite
from .rules_engine import apply_rules_on_spans, build_reason
from .schemas import RewriteResponse

semantic_metrics = SemanticPreservationMetrics()

# Callers that already ran bias detection upstream — skip Stage 0 external /detect gate.
# StudyLabs (and similar) detect; we only correct when they hit POST /rewrite with this set.
_SKIP_EXTERNAL_BIAS_GATE_CALLERS = frozenset({"aibridge", "studylabs"})


def rewrite_text(
    id: str,
    text: str,
    lang: str,
    flags: Optional[list] = None,
    region_dialect: Optional[str] = None,
    caller: Optional[str] = None,
) -> tuple[RewriteResponse, dict]:
    """
    Run bias detection + correction. Returns (response, audit_info).
    audit_info has model_info, latency_ms for logging.

    caller 'studylabs' or 'aibridge': skip Stage 0 external /detect — partner already
    detected bias; we only run lexicon (and later stages) to correct.
    """
    t0 = time.time()

    # Stage 0: optional external bias detection gate (haus | swahili | zulu when enabled).
    # Skipped when the integration partner already flagged bias (StudyLabs, AIBRIDGE pipeline).
    # If the external model says no bias, skip correction entirely and return immediately.
    # On any network/auth error, aibridge_result.error is set and we fall through silently.
    aibridge_result: Optional[AibridgeResult] = None
    caller_norm = (caller or "").strip().lower()
    skip_gate = caller_norm in _SKIP_EXTERNAL_BIAS_GATE_CALLERS
    ext_lang = LANG_CODE_MAP.get(lang) if (AIBRIDGE_ENABLED and not skip_gate) else None
    if ext_lang:
        aibridge_result = detect_bias(text, ext_lang)
        # Do NOT return early — always run our lexicon rules regardless of AIBRIDGE result.
        # AIBRIDGE has low recall and misses real bias; our lexicon rules have higher precision.
        # AIBRIDGE result is used as an additional signal in the final response only.

    rewritten, edits, matched_rules, skipped = apply_rules_on_spans(
        text, lang, flags=flags
    )
    source = "rules"
    ml_info = None
    semantic_score = None

    threshold = get_semantic_threshold()
    if rewritten != text:
        # Lexicon replace-severity rules are high precision — use a lower threshold (0.40)
        # so paraphrase-style corrections (hawafai→wanaweza) are not suppressed.
        # Only apply strict threshold to ML-generated corrections.
        has_replace_edits = any(e.get("severity") == "replace" for e in edits)
        effective_threshold = 0.40 if has_replace_edits else threshold
        score = semantic_metrics.calculate_composite_preservation_score(text, rewritten)
        semantic_score = score["composite_score"]
        if semantic_score < effective_threshold:
            rewritten, edits, source, semantic_score = text, [], "preserved", 1.0

    # Stage 2.5: LLM disambiguation for borderline warn-only matches (SW).
    # Only fires when rules found warn-severity terms but no replace-severity terms.
    warn_only = matched_rules > 0 and not any(
        e.get("severity") == "replace" for e in edits
    )
    if warn_only and lang == "sw":
        llm_result = disambiguate(text)
        if llm_result is True:
            # LLM confirmed bias — promote the warn edits to replace
            for e in edits:
                if e.get("severity") == "warn":
                    e["severity"] = "replace"
                    e["reason"] = (e.get("reason") or "") + " [LLM confirmed]"
            source = "disambiguated"
        elif llm_result is False:
            # LLM says not bias — suppress the warn edits
            edits = []
            rewritten = text
            source = "preserved"

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
    aibridge_ok = aibridge_result is not None and aibridge_result.error is None
    aibridge_detected = aibridge_result.has_bias if aibridge_ok else None
    reason = build_reason(source, edits, skipped, aibridge_detected=bool(aibridge_detected))
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
        aibridge_confidence=aibridge_result.confidence if aibridge_ok else None,
        aibridge_detected=aibridge_detected,
    )
    audit_info = {
        "model_info": ml_info or {"model": "rulepack-v0.3"},
        "latency_ms": latency_ms,
        "region_dialect": region_dialect or "unknown",
        "aibridge_error": aibridge_result.error if aibridge_result else None,
    }
    return response, audit_info
