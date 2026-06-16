"""JuaKazi rewrite service — core correction logic (no HTTP)."""

import os
import time
from typing import Optional

from config import (
    DEFAULT_REWRITE_CONFIDENCE,
    REWRITE_CONFIDENCE_BY_SOURCE,
    get_semantic_threshold,
)
from core.semantic_preservation import SemanticPreservationMetrics

from .bias_detection_client import LANG_CODE_MAP, AibridgeResult
from .ml_rewriter import ml_rewrite
from .rules_engine import apply_rules_on_spans, build_reason
from .schemas import RewriteResponse

_ML_DETECTOR_THRESHOLD = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.56"))
_ML_DETECTOR_ENABLED   = bool(os.environ.get("JUAKAZI_ML_MODEL", ""))

semantic_metrics = SemanticPreservationMetrics()

# Callers that already ran bias detection upstream — skip Stage 0 external /detect gate.
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
    AIBRIDGE external call is NOT made here — caller fires it as a background task.
    """
    t0 = time.time()

    # Stage 0 AIBRIDGE gate removed from this path.
    # AIBRIDGE is called asynchronously in main.py after the response is returned,
    # so it never blocks the user. aibridge_* fields in the response are always None
    # on the initial return; the background task appends to the audit log separately.
    aibridge_result: Optional[AibridgeResult] = None

    rewritten, edits, matched_rules, skipped = apply_rules_on_spans(
        text, lang, flags=flags
    )
    source = "rules"
    ml_info = None
    semantic_score = None

    threshold = get_semantic_threshold()
    if rewritten != text:
        # Lexicon replace-severity rules are hand-crafted and high-precision.
        # For languages where the semantic model has poor coverage (ZU, HA), the
        # embedding similarity score is unreliable — bypass the threshold entirely.
        # For other languages use 0.40 (lower than ML threshold) to allow paraphrases.
        has_replace_edits = any(e.get("severity") == "replace" for e in edits)
        if has_replace_edits and lang in ("zu", "ha"):
            effective_threshold = 0.0  # semantic model not reliable for these languages
        elif has_replace_edits:
            effective_threshold = 0.40
        else:
            effective_threshold = threshold
        score = semantic_metrics.calculate_composite_preservation_score(text, rewritten)
        semantic_score = score["composite_score"]
        if semantic_score < effective_threshold:
            rewritten, edits, source, semantic_score = text, [], "preserved", 1.0

    # Stage 1: ML detector — fires when lexicon found no replace-severity correction.
    # Covers sentences the lexicon misses entirely, and reinforces warn-only lexicon hits.
    # Uses juakazike/multilingual-bias-classifier-v1 (afro-xlmr-base, all 6 languages).
    # Adds a warn-severity edit so Stage 3 corrector can fire downstream.
    lexicon_replaced = any(e.get("severity") == "replace" for e in edits)
    ml_detector_score: Optional[float] = None
    if _ML_DETECTOR_ENABLED and not lexicon_replaced:
        try:
            from eval.ml_classifier import classify as ml_classify
            from eval.models import Language as _Lang
            _lang_map = {
                "sw": _Lang.SWAHILI, "ha": _Lang.HAUSA, "zu": _Lang.ZULU,
                "ki": _Lang.GIKUYU, "en": _Lang.ENGLISH, "fr": _Lang.FRENCH,
            }
            _lang_enum = _lang_map.get(lang)
            if _lang_enum:
                ml_detector_score = ml_classify(text, _lang_enum)
                if ml_detector_score >= _ML_DETECTOR_THRESHOLD:
                    edits = [{
                        "from": "",
                        "to": "",
                        "severity": "warn",
                        "bias_type": "ml-detected",
                        "stereotype_category": "",
                        "reason": f"ML detector: gender bias likely (confidence {ml_detector_score:.0%})",
                        "source": "ml",
                    }]
                elif not edits:
                    pass  # ML below threshold and lexicon silent — no bias signal
        except Exception:
            pass  # ML unavailable — lexicon result stands

    # Stage 3: ML corrector — fires only when bias is detected AND lexicon found no match.
    # Uses juakazike/multilingual-bias-corrector-v3 (AfriTeVa fine-tuned on 10K clean pairs, guardrails added).
    # Skipped when lexicon already produced a correction (edits non-empty with replace severity).
    # ZU and HA corrector output is not yet reliable (insufficient training pairs) — for those
    # languages we suppress the ML corrector and flag for human review instead of showing
    # hallucinated or truncated output.
    _ML_CORRECTOR_LANGS = {"sw", "en", "fr", "ki"}
    lexicon_corrected = lexicon_replaced
    has_any_bias_signal = bool(edits) or (aibridge_result is not None and aibridge_result.has_bias)
    ml_unavailable = False
    if not lexicon_corrected and has_any_bias_signal:
        if lang not in _ML_CORRECTOR_LANGS:
            # Corrector not reliable for this language — flag for human review
            ml_unavailable = True
        else:
            ml_result = ml_rewrite(text, lang=lang)
            if ml_result["model"] != "unavailable":
                candidate = ml_result["best"]
                if candidate and candidate.strip():
                    from .ml_rewriter import validate_correction
                    verdict, verdict_reason = validate_correction(text, candidate, lang)
                    if verdict == "accept":
                        rewritten = candidate
                        source = "ml"
                        ml_info = {"model": ml_result["model"], "latency_ms": ml_result["latency_ms"]}
                        edits = [{
                            "from": text,
                            "to": rewritten,
                            "severity": "warn",
                            "tags": "ml-correction",
                            "bias_type": "ml-detected",
                            "stereotype_category": "",
                            "reason": f"ML corrector suggestion ({ml_result['model'].split('/')[-1]})",
                        }]
                    else:
                        # Correction failed guardrails — flag for human review, don't show bad output
                        ml_unavailable = True
            else:
                ml_unavailable = True

    # If corrector was unavailable or failed guardrails, and no replace-severity lexicon
    # correction exists, flag as low_confidence so UI shows "human review needed"
    has_replace = any(e.get("severity") == "replace" for e in edits)
    if ml_unavailable and not has_replace:
        source = "low_confidence"

    latency_ms = int((time.time() - t0) * 1000)
    confidence = REWRITE_CONFIDENCE_BY_SOURCE.get(source, DEFAULT_REWRITE_CONFIDENCE)
    needs_review = source in ("ml", "low_confidence") or len(edits) == 0
    reason = build_reason(source, edits, skipped, aibridge_detected=False)
    has_bias_detected = (
        any(e.get("severity") in ("replace", "warn") for e in edits)
        or source == "low_confidence"
    )

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
        aibridge_confidence=None,   # populated async by background task in main.py
        aibridge_detected=None,
    )
    audit_info = {
        "model_info": ml_info or {"model": "rulepack-v0.3"},
        "latency_ms": latency_ms,
        "region_dialect": region_dialect or "unknown",
    }
    return response, audit_info
