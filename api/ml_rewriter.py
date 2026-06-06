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
            )
        corrected = _tokenizer.decode(out[0], skip_special_tokens=True)
        return {
            "best": corrected,
            "candidates": [corrected],
            "model": _CORRECTOR_MODEL,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception:
        return _unavailable
