import time
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# I decided to choose a multilingual small seq2seq model
MODEL_ID = "google/mt5-small"  
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Lazy load
_tokenizer = None
_model = None

def _ensure_model():
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if _model is None:
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
        _model.to(DEVICE)
        _model.eval()

def ml_rewrite(text: str, lang: str = "en", num_return_sequences: int = 3, max_new_tokens: int = 64) -> Dict[str, Any]:
    """
    Returns dict:
      {
        "best": "string",
        "candidates": ["a","b","c"],
        "model": MODEL_ID,
        "latency_ms": 123
      }
    """
    _ensure_model()
    start = time.time()

    # This prompt to instruct model (works reasonably with mt5)
    prompt = f"Rewrite to remove gender bias while preserving meaning (language={lang}): {text}"

    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(DEVICE)
    # I decided to use num_return_sequences via beam search
    outputs = _model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        num_beams=max(2, num_return_sequences),
        num_return_sequences=num_return_sequences,
        early_stopping=True
    )
    candidates = [_tokenizer.decode(o, skip_special_tokens=True, clean_up_tokenization_spaces=True) for o in outputs]
    latency_ms = int((time.time() - start) * 1000)
    return {"best": candidates[0], "candidates": candidates, "model": MODEL_ID, "latency_ms": latency_ms}
