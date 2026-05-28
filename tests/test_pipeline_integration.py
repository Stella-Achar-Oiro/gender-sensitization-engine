"""
Phase 0 — Pipeline integration tests.

End-to-end: known biased + known neutral sentence per language through the full
pipeline (Stage 1 detect → Stage 2 lexicon → Stage 3 correct).

Rules:
- Biased sentence  → detected=True, corrected != original, reason non-empty
- Neutral sentence → detected=False, corrected == original

These tests pass for SW now. HA/ZU/KI are xfail until classifiers are trained.

Run:
    pytest tests/test_pipeline_integration.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.bias_detector import BiasDetector
from eval.models import Language
from api.rules_engine import apply_rules_on_spans

ROOT = Path(__file__).parent.parent
RULES_DIR = ROOT / "rules"

# ── Known sentences per language ─────────────────────────────────────────────
# biased: a sentence we KNOW should be detected
# neutral: a sentence we KNOW should NOT be detected
SENTENCES = {
    "sw": {
        "biased":  "Daktari wa kiume alifika hospitalini asubuhi.",
        "neutral": "Mvua ilianza kunyesha asubuhi na mapema.",
    },
    "ha": {
        "biased":  "Likitan namiji ya zo asibiti safe.",
        "neutral": "Ruwan sama ya fara zuwa da safe.",
    },
    "zu": {
        "biased":  "Udokotela wesilisa weza esibhedlela ekuseni.",
        "neutral": "Imvula yaqala ukuna ekuseni.",
    },
    "ki": {
        "biased":  "Mũndũ wa mũrũme nĩwe ũngĩ gũtwara mũciĩ.",
        "neutral": "Mbura yaambĩrĩria gũthira rũciinĩ.",
    },
    "fr": {
        "biased":  "Le président a dirigé la réunion comme un vrai homme.",
        "neutral": "Il pleut ce matin dans la ville.",
    },
    "en": {
        "biased":  "The chairman will lead the board meeting.",
        "neutral": "The rain started early in the morning.",
    },
}

LANG_ENUM = {
    "sw": Language.SWAHILI,
    "ha": Language.HAUSA,
    "zu": Language.ZULU,
    "ki": Language.GIKUYU,
    "fr": Language.FRENCH,
    "en": Language.ENGLISH,
}


def _run_pipeline(text: str, lang_code: str) -> dict:
    """Run full detection + correction pipeline, return structured result."""
    lang = LANG_ENUM[lang_code]
    detector = BiasDetector(rules_dir=RULES_DIR, enable_ml_fallback=True)
    detection = detector.detect_bias(text, lang)

    corrected_text, edits, _, _ = apply_rules_on_spans(text, lang_code)

    # Try MT5 corrector if no lexicon match and bias detected
    if detection.has_bias_detected and corrected_text == text:
        try:
            from eval.mt5_corrector import MT5BiasCorrector
            corrector = MT5BiasCorrector()
            result = corrector.correct(text, lang)
            if result and result != text:
                corrected_text = result
        except Exception:
            pass

    reason = ""
    if edits:
        from api.rules_engine import build_reason
        reason = build_reason("rules", edits, [])

    return {
        "detected": detection.has_bias_detected,
        "corrected": corrected_text,
        "changed": corrected_text != text,
        "reason": reason,
        "edits": edits,
    }


def _assert_biased(lang_code: str, result: dict, original: str):
    assert result["detected"], \
        f"[{lang_code.upper()}] Biased sentence not detected: '{original}'"


def _assert_neutral(lang_code: str, result: dict, original: str):
    assert not result["detected"], \
        f"[{lang_code.upper()}] Neutral sentence incorrectly flagged: '{original}'"
    assert result["corrected"] == original, \
        f"[{lang_code.upper()}] Neutral sentence was modified: '{original}' → '{result['corrected']}'"


# ── Swahili (must pass now) ──────────────────────────────────────────────────

def test_sw_biased_sentence():
    s = SENTENCES["sw"]
    result = _run_pipeline(s["biased"], "sw")
    print(f"\nSW biased result: {result}")
    _assert_biased("sw", result, s["biased"])


def test_sw_neutral_sentence():
    s = SENTENCES["sw"]
    result = _run_pipeline(s["neutral"], "sw")
    print(f"\nSW neutral result: {result}")
    _assert_neutral("sw", result, s["neutral"])


# ── English (must pass now) ──────────────────────────────────────────────────

def test_en_biased_sentence():
    s = SENTENCES["en"]
    result = _run_pipeline(s["biased"], "en")
    print(f"\nEN biased result: {result}")
    _assert_biased("en", result, s["biased"])


def test_en_neutral_sentence():
    s = SENTENCES["en"]
    result = _run_pipeline(s["neutral"], "en")
    print(f"\nEN neutral result: {result}")
    _assert_neutral("en", result, s["neutral"])


# ── Hausa (xfail until Phase 1) ─────────────────────────────────────────────

@pytest.mark.xfail(reason="HA classifier not trained — Phase 1 target", strict=True)
def test_ha_biased_sentence():
    s = SENTENCES["ha"]
    result = _run_pipeline(s["biased"], "ha")
    print(f"\nHA biased result: {result}")
    _assert_biased("ha", result, s["biased"])


def test_ha_neutral_sentence():
    """Neutral HA should not be modified regardless of classifier state."""
    s = SENTENCES["ha"]
    result = _run_pipeline(s["neutral"], "ha")
    print(f"\nHA neutral result: {result}")
    _assert_neutral("ha", result, s["neutral"])


# ── Zulu (xfail until Phase 2) ──────────────────────────────────────────────

def test_zu_biased_sentence():
    s = SENTENCES["zu"]
    result = _run_pipeline(s["biased"], "zu")
    print(f"\nZU biased result: {result}")
    _assert_biased("zu", result, s["biased"])


def test_zu_neutral_sentence():
    """Neutral ZU should not be modified."""
    s = SENTENCES["zu"]
    result = _run_pipeline(s["neutral"], "zu")
    print(f"\nZU neutral result: {result}")
    _assert_neutral("zu", result, s["neutral"])


# ── Kikuyu (xfail until Phase 3) ────────────────────────────────────────────

def test_ki_biased_sentence():
    s = SENTENCES["ki"]
    result = _run_pipeline(s["biased"], "ki")
    print(f"\nKI biased result: {result}")
    _assert_biased("ki", result, s["biased"])


def test_ki_neutral_sentence():
    """Neutral KI should not be modified."""
    s = SENTENCES["ki"]
    result = _run_pipeline(s["neutral"], "ki")
    print(f"\nKI neutral result: {result}")
    _assert_neutral("ki", result, s["neutral"])


# ── French (xfail until Phase 1b) ───────────────────────────────────────────

def test_fr_biased_sentence():
    s = SENTENCES["fr"]
    result = _run_pipeline(s["biased"], "fr")
    print(f"\nFR biased result: {result}")
    _assert_biased("fr", result, s["biased"])


def test_fr_neutral_sentence():
    """Neutral FR should not be modified."""
    s = SENTENCES["fr"]
    result = _run_pipeline(s["neutral"], "fr")
    print(f"\nFR neutral result: {result}")
    _assert_neutral("fr", result, s["neutral"])
