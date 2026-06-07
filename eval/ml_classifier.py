"""
ML bias classifier -- Stage 1 detector for the pipeline.

Single multilingual model covers all 6 languages (SW, HA, ZU, KI, FR, EN).
Falls back gracefully when the model is unavailable (returns 0.0).

  ALL -> juakazike/multilingual-bias-classifier-v2
         Davlan/afro-xlmr-base fine-tuned on 148K rows across 6 languages
         Trained Jun 2026 on Kaggle T4 x2, Epoch 3: F1_bias=0.893, SW=0.951, HA=0.800, ZU=0.996, KI=0.865, FR=0.891, EN=0.855
"""
from __future__ import annotations

import os
from typing import Optional

from .models import Language

_MULTILINGUAL_MODEL = os.environ.get("JUAKAZI_ML_MODEL", "juakazike/multilingual-bias-classifier-v1")

# ── Per-language model IDs (all point to multilingual; override via env vars) ─
_MODEL_IDS: dict[Language, str] = {
    Language.SWAHILI: os.environ.get("JUAKAZI_SW_MODEL",  _MULTILINGUAL_MODEL),
    Language.HAUSA:   os.environ.get("JUAKAZI_HA_MODEL",  _MULTILINGUAL_MODEL),
    Language.ZULU:    os.environ.get("JUAKAZI_ZU_MODEL",  _MULTILINGUAL_MODEL),
    Language.GIKUYU:  os.environ.get("JUAKAZI_KI_MODEL",  _MULTILINGUAL_MODEL),
    Language.ENGLISH: os.environ.get("JUAKAZI_EN_MODEL",  _MULTILINGUAL_MODEL),
    Language.FRENCH:  os.environ.get("JUAKAZI_FR_MODEL",  _MULTILINGUAL_MODEL),
}

# ── Per-language thresholds ──────────────────────────────────────────────────
_THRESHOLDS: dict[Language, float] = {
    Language.SWAHILI: float(os.environ.get("JUAKAZI_SW_THRESHOLD", "0.75")),
    Language.HAUSA:   float(os.environ.get("JUAKAZI_HA_THRESHOLD", "0.75")),
    Language.ZULU:    float(os.environ.get("JUAKAZI_ZU_THRESHOLD", "0.75")),
    Language.GIKUYU:  float(os.environ.get("JUAKAZI_KI_THRESHOLD", "0.75")),
    Language.ENGLISH: float(os.environ.get("JUAKAZI_EN_THRESHOLD", "0.75")),
    Language.FRENCH:  float(os.environ.get("JUAKAZI_FR_THRESHOLD", "0.75")),
}


# ── Lazy-loaded pipelines per language ──────────────────────────────────────
_pipes:       dict[Language, object]          = {}
_load_errors: dict[Language, Optional[str]]   = {}


def _ensure_loaded(language: Language) -> None:
    if language in _pipes or language in _load_errors:
        return
    model_id = _MODEL_IDS.get(language)
    if not model_id:
        _load_errors[language] = f"No model configured for {language}"
        return
    try:
        from transformers import pipeline as hf_pipeline
        _pipes[language] = hf_pipeline(
            "text-classification",
            model=model_id,
            device=-1,
            truncation=True,
            max_length=128,
        )
    except Exception as exc:
        _load_errors[language] = str(exc)


def classify(text: str, language: Language) -> float:
    """
    Return a bias confidence score 0.0-1.0 for the given language.

    Returns 0.0 if model unavailable or text is empty.
    Score > threshold(language) -> caller should flag as possible bias.
    """
    if not text or not text.strip():
        return 0.0

    _ensure_loaded(language)

    if language in _load_errors or language not in _pipes:
        return 0.0

    try:
        result = _pipes[language](text)[0]
        label  = result["label"].upper()
        score  = float(result["score"])
        if label in ("LABEL_1", "BIAS", "STEREOTYPE", "DEROGATION"):
            return score
        elif label in ("LABEL_0", "NEUTRAL", "NO_BIAS"):
            return 1.0 - score
        else:
            return score if score > 0.5 else 1.0 - score
    except Exception:
        return 0.0


def threshold(language: Language) -> float:
    """Return the detection threshold for this language."""
    return _THRESHOLDS.get(language, 0.75)


def is_available(language: Language) -> bool:
    """True if the model for this language loaded successfully."""
    _ensure_loaded(language)
    return language in _pipes and language not in _load_errors


def model_id(language: Language | None = None) -> str:
    """Return the model ID for a language (or SW model for legacy callers)."""
    if language is None:
        return _MODEL_IDS.get(Language.SWAHILI, "")
    return _MODEL_IDS.get(language, "")
