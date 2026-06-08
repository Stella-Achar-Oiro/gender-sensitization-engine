"""
Stage 3 ML corrector — seq2seq bias correction.

Model: juakazike/multilingual-bias-corrector-v1
Base:  castorini/afriteva_v2_base
Input: "correct bias {lang}: {biased sentence}"
Output: corrected/neutral sentence

Falls back gracefully when model unavailable (local dev, unit tests).
"""
import os
import time
from typing import Any

_CORRECTOR_MODEL = os.environ.get(
    "JUAKAZI_CORRECTOR_MODEL",
    "juakazike/multilingual-bias-corrector-v2",
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


def _clean_output(corrected: str, original: str) -> str:
    """Remove common seq2seq repetition artifacts without altering content."""
    import re
    # Truncate at first occurrence of .. or multiple punctuation-fillers
    corrected = re.split(r'\.{2,}|\[\.+\]', corrected)[0].strip().rstrip(".,;")
    # Detect token-level repetition: if any 1-3 word phrase repeats ≥3 times, truncate before it
    words = corrected.split()
    for n in (1, 2, 3):
        for i in range(len(words) - n * 3):
            phrase = tuple(words[i:i + n])
            # Count occurrences of this phrase after position i
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
        # Strip beam-search repetition artifacts
        corrected = _clean_output(corrected, text)
        return {
            "best": corrected,
            "candidates": [corrected],
            "model": _CORRECTOR_MODEL,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception:
        return _unavailable
