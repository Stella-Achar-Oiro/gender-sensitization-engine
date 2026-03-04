"""
ML bias classifier — Stage 2 fallback for the rules engine.

Uses Davlan/afro-xlmr-base (zero-shot until fine-tuned).
Only runs when rules find nothing. Always produces warn-severity
edits only — never replace. Preserves precision guarantee.

Supported languages: Swahili, English, French
Kikuyu: rules-only (afro-xlmr-base does not cover Kikuyu)
"""
from __future__ import annotations

import os
from typing import Optional

from .models import Language

# Languages the model covers
_SUPPORTED = {Language.SWAHILI, Language.ENGLISH, Language.FRENCH}

# HuggingFace model — zero-shot until fine-tuned version published
_MODEL_ID = os.environ.get("JUAKAZI_ML_MODEL", "Davlan/afro-xlmr-base")

# Confidence threshold — above this we flag as possible bias
_THRESHOLD = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.75"))

# Lazy-loaded pipeline (None until first call)
_pipe = None
_load_error: Optional[str] = None


def _ensure_loaded() -> None:
    global _pipe, _load_error
    if _pipe is not None or _load_error is not None:
        return
    try:
        from transformers import pipeline as hf_pipeline
        # local_files_only=True — never block on download during inference.
        # Pre-download with: python3 -c "from transformers import pipeline; pipeline('text-classification', model='Davlan/afro-xlmr-base')"
        _pipe = hf_pipeline(
            "text-classification",
            model=_MODEL_ID,
            device=-1,          # CPU always — GPU optional via env
            truncation=True,
            max_length=128,
            local_files_only=True,
        )
    except Exception as exc:
        _load_error = str(exc)


def classify(text: str, language: Language) -> float:
    """
    Return a bias confidence score 0.0–1.0.

    Returns 0.0 if:
    - language not supported by the model
    - model failed to load
    - text is empty

    The score represents probability of gender bias being present.
    Score > _THRESHOLD → caller should surface a warn edit.
    """
    if not text or not text.strip():
        return 0.0
    if language not in _SUPPORTED:
        return 0.0

    _ensure_loaded()
    if _load_error or _pipe is None:
        return 0.0

    try:
        result = _pipe(text)[0]
        label = result["label"].upper()
        score = float(result["score"])
        # afro-xlmr-base is a base model — before fine-tuning its labels
        # are LABEL_0 / LABEL_1. After fine-tuning they'll be BIAS / NEUTRAL.
        # Map either convention: higher score on LABEL_1 or BIAS → bias score
        if label in ("LABEL_1", "BIAS", "STEREOTYPE", "DEROGATION"):
            return score
        elif label in ("LABEL_0", "NEUTRAL", "NO_BIAS"):
            return 1.0 - score
        else:
            # Unknown label — return raw score conservatively
            return score if score > 0.5 else 1.0 - score
    except Exception:
        return 0.0


def is_available() -> bool:
    """True if the ML model loaded successfully."""
    _ensure_loaded()
    return _pipe is not None and _load_error is None


def model_id() -> str:
    return _MODEL_ID
