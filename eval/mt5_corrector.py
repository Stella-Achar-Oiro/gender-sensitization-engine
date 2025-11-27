"""
MT5-based bias correction using the generative approach from dev branch
"""
import time
from typing import Dict, Any
from .models import Language

class MT5BiasCorrector:
    """MT5-based bias correction system"""
    
    def __init__(self):
        self.model_id = "google/mt5-small"
        self._tokenizer = None
        self._model = None
    
    def _ensure_model(self):
        """Lazy load model to avoid import errors without transformers"""
        if self._tokenizer is None:
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                import torch
                
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
                self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model.to(self._device)
                self._model.eval()
            except ImportError:
                raise ImportError("transformers and torch required for MT5 correction")
    
    def correct_bias(self, text: str, language: Language, num_candidates: int = 3) -> Dict[str, Any]:
        """Generate bias-corrected versions of text"""
        self._ensure_model()
        start = time.time()
        
        # Language-specific prompting
        lang_code = language.value
        prompt = f"Rewrite to remove gender bias while preserving meaning (language={lang_code}): {text}"
        
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(self._device)
        
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=64,
            num_beams=max(2, num_candidates),
            num_return_sequences=num_candidates,
            early_stopping=True
        )
        
        candidates = [
            self._tokenizer.decode(o, skip_special_tokens=True, clean_up_tokenization_spaces=True) 
            for o in outputs
        ]
        
        latency_ms = int((time.time() - start) * 1000)
        
        return {
            "original": text,
            "best_correction": candidates[0] if candidates else text,
            "candidates": candidates,
            "model": self.model_id,
            "language": lang_code,
            "latency_ms": latency_ms
        }