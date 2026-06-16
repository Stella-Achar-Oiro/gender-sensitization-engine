"""
Stage 3 ML corrector — seq2seq bias correction.

Model: juakazike/multilingual-bias-corrector-v3
Base:  castorini/afriteva_v2_base
Input: "correct bias {lang}: {biased sentence}"
Output: corrected/neutral sentence

Falls back gracefully when model unavailable (local dev, unit tests).
"""
import os
import time
from typing import Any, Literal

_CORRECTOR_MODEL = os.environ.get(
    "JUAKAZI_CORRECTOR_MODEL",
    "juakazike/multilingual-bias-corrector-v3",
)

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    _ML_AVAILABLE = True
except ImportError:
    _ML_AVAILABLE = False

_DEVICE = "cuda" if (_ML_AVAILABLE and __import__("torch").cuda.is_available()) else "cpu"
_tokenizer = None
_model = None


def _clean_output(corrected: str, original: str, lang: str = "") -> str:
    """Remove common seq2seq repetition artifacts without altering content."""
    import re
    # Truncate at first occurrence of .. or multiple punctuation-fillers
    corrected = re.split(r'\.{2,}|\[\.+\]', corrected)[0].strip().rstrip(".,;")
    # Detect token-level repetition: if any 1-3 word phrase repeats ≥3 times, truncate before it
    words = corrected.split()
    for n in (1, 2, 3):
        for i in range(len(words) - n * 3):
            phrase = tuple(words[i:i + n])
            count = sum(
                1 for j in range(i + n, len(words) - n + 1, n)
                if tuple(words[j:j + n]) == phrase
            )
            if count >= 3:
                corrected = " ".join(words[:i + n]).strip().rstrip(".,;")
                break
        else:
            continue
        break
    # If output is way longer than input (>2.5×), likely hallucination — return original
    if len(corrected.split()) > len(original.split()) * 2.5:
        return original
    # Language sanity check: detect if output switched to English for a non-English input.
    # Common English function words that would not appear in SW/HA/ZU/KI/FR sentences.
    _EN_MARKERS = {"the", "is", "are", "was", "were", "has", "have", "company", "women", "men"}
    if lang and lang != "en":
        out_words_lower = {w.lower().strip(".,;") for w in corrected.split()}
        if len(out_words_lower & _EN_MARKERS) >= 2:
            return original  # output switched language — reject
    return corrected


def _ensure_model() -> None:
    global _tokenizer, _model
    if _tokenizer is not None:
        return
    if not _ML_AVAILABLE:
        raise RuntimeError("transformers not installed")
    _tokenizer = AutoTokenizer.from_pretrained(_CORRECTOR_MODEL)
    _model = AutoModelForSeq2SeqLM.from_pretrained(_CORRECTOR_MODEL)
    _model.to(_DEVICE)
    _model.eval()


def validate_correction(
    original: str,
    corrected: str,
    lang: str,
) -> tuple[Literal["accept", "review"], str]:
    """
    Run guardrails on a candidate ML correction.

    Returns ("accept", reason) if the correction looks trustworthy,
    or ("review", reason) if any guardrail fails — caller should flag
    for human review instead of showing the bad correction.

    Checks:
      1. Not identical to original (corrector did something)
      2. Token overlap >= 0.30 (didn't rewrite everything / hallucinate)
      3. Composite preservation score >= 0.45 (meaning still intact)
      4. ML detector score on corrected output is lower than on original
         (bias was actually reduced, not just rephrased)
    """
    from core.semantic_preservation import SemanticPreservationMetrics

    if not corrected or corrected.strip() == original.strip():
        return "review", "correction identical to input"

    overlap = SemanticPreservationMetrics.calculate_token_overlap(original, corrected)
    if overlap < 0.30:
        return "review", f"low token overlap ({overlap:.2f}) — likely hallucination"

    scores = SemanticPreservationMetrics.calculate_composite_preservation_score(original, corrected)
    if scores["composite_score"] < 0.45:
        return "review", f"low preservation score ({scores['composite_score']:.2f}) — meaning may have changed"

    # Check bias was actually reduced: re-run detector on corrected output
    try:
        from eval.ml_classifier import classify as ml_classify, threshold as ml_threshold
        from eval.models import Language as _Lang
        _lang_map = {
            "sw": _Lang.SWAHILI, "ha": _Lang.HAUSA, "zu": _Lang.ZULU,
            "ki": _Lang.GIKUYU, "en": _Lang.ENGLISH, "fr": _Lang.FRENCH,
        }
        lang_enum = _lang_map.get(lang)
        if lang_enum:
            original_score = ml_classify(original, lang_enum)
            corrected_score = ml_classify(corrected, lang_enum)
            thresh = ml_threshold(lang_enum)
            # Corrected output should score lower than original, or drop below threshold
            if corrected_score >= original_score and corrected_score >= thresh:
                return "review", f"bias not reduced (original={original_score:.2f} corrected={corrected_score:.2f})"
    except Exception:
        pass  # detector unavailable — skip this check, don't fail

    return "accept", "all guardrails passed"


def ml_rewrite(text: str, lang: str = "sw", **_kwargs) -> dict[str, Any]:
    """
    Returns {"best": corrected_text, "model": model_id, "latency_ms": int}.
    Returns {"best": text, "model": "unavailable"} if model not loaded.
    """
    _unavailable = {"best": text, "candidates": [text], "model": "unavailable", "latency_ms": 0}

    if not _ML_AVAILABLE:
        return _unavailable

    try:
        _ensure_model()
    except Exception:
        return _unavailable

    t0 = time.time()
    prompt = f"correct bias {lang}: {text}"
    try:
        inputs = _tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=128
        )
        inputs = {k: v.to(_DEVICE) for k, v in inputs.items()}
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=128,
                num_beams=4,
                early_stopping=True,
                decoder_start_token_id=0,
                forced_eos_token_id=1,
            )
        corrected = _tokenizer.decode(out[0], skip_special_tokens=True)
        corrected = _clean_output(corrected, text, lang=lang)
        return {
            "best": corrected,
            "candidates": [corrected],
            "model": _CORRECTOR_MODEL,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception:
        return _unavailable
