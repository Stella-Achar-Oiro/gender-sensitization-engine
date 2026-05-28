"""
ML bias classifier — Stage 1 detector for the pipeline.

Each language has its own fine-tuned model loaded lazily on first call.
Falls back gracefully when a model is not yet trained (returns 0.0).

Supported:
  SW  → juakazike/sw-bias-classifier-v3  (trained, production)
  HA  → juakazike/ha-bias-classifier-v1  (Phase 1 — set env var when trained)
  ZU  → juakazike/zu-bias-classifier-v1  (Phase 2 — set env var when trained)
  KI  → juakazike/ki-bias-classifier-v1  (Phase 3 — uses 76L base)
  EN  → juakazike/sw-bias-classifier-v3  (shared SW model, acceptable)
  FR  → juakazike/sw-bias-classifier-v3  (shared SW model until FR trained)
"""
from __future__ import annotations

import os
from typing import Optional

from .models import Language

# ── Per-language model IDs (override via env vars after training) ────────────
_MODEL_IDS: dict[Language, str] = {
    Language.SWAHILI: os.environ.get("JUAKAZI_SW_MODEL", "juakazike/sw-bias-classifier-v3"),
    Language.HAUSA:   os.environ.get("JUAKAZI_HA_MODEL", "juakazike/ha-bias-classifier-v1"),
    Language.ZULU:    os.environ.get("JUAKAZI_ZU_MODEL", "juakazike/zu-bias-classifier-v1"),
    Language.GIKUYU:  os.environ.get("JUAKAZI_KI_MODEL", "juakazike/ki-bias-classifier-v1"),
    Language.ENGLISH: os.environ.get("JUAKAZI_EN_MODEL", "juakazike/sw-bias-classifier-v3"),
    Language.FRENCH:  os.environ.get("JUAKAZI_FR_MODEL", "juakazike/sw-bias-classifier-v3"),
}

# ── Per-language thresholds ──────────────────────────────────────────────────
_THRESHOLDS: dict[Language, float] = {
    Language.SWAHILI: float(os.environ.get("JUAKAZI_SW_THRESHOLD", "0.30")),
    Language.HAUSA:   float(os.environ.get("JUAKAZI_HA_THRESHOLD", "0.50")),
    Language.ZULU:    float(os.environ.get("JUAKAZI_ZU_THRESHOLD", "0.50")),
    Language.GIKUYU:  float(os.environ.get("JUAKAZI_KI_THRESHOLD", "0.50")),
    Language.ENGLISH: float(os.environ.get("JUAKAZI_EN_THRESHOLD", "0.50")),
    Language.FRENCH:  float(os.environ.get("JUAKAZI_FR_THRESHOLD", "0.50")),
}

# Legacy env var support (existing deployments)
_LEGACY_THRESHOLD = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.56"))
_LEGACY_MODEL     = os.environ.get("JUAKAZI_ML_MODEL", "")
if _LEGACY_MODEL:
    # If old-style env var is set, apply it to SW (backwards compat)
    _MODEL_IDS[Language.SWAHILI] = _LEGACY_MODEL

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
    Return a bias confidence score 0.0–1.0 for the given language.

    Returns 0.0 if:
    - model not yet trained / not available on HF
    - model failed to load
    - text is empty

    Score > threshold(language) → caller should flag as possible bias.
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
    return _THRESHOLDS.get(language, 0.50)


def is_available(language: Language) -> bool:
    """True if the model for this language loaded successfully."""
    _ensure_loaded(language)
    return language in _pipes and language not in _load_errors


def model_id(language: Language | None = None) -> str:
    """Return the model ID for a language (or SW model for legacy callers)."""
    if language is None:
        return _MODEL_IDS.get(Language.SWAHILI, "")
    return _MODEL_IDS.get(language, "")
