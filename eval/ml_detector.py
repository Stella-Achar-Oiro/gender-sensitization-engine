"""
ML-based bias detector using transformer models for African languages
"""
import re
from typing import Dict, List, Optional
from .models import BiasDetectionResult, Language

class MLBiasDetector:
    """Machine learning bias detector using pre-trained models"""
    
    def __init__(self):
        self.models = self._load_models()
        
    def _load_models(self) -> Dict[Language, str]:
        """Load appropriate models for each language"""
        return {
            Language.ENGLISH: "distilbert-base-uncased",
            Language.SWAHILI: "xlm-roberta-base",
            Language.FRENCH: "xlm-roberta-base",
            Language.GIKUYU: "xlm-roberta-base"
        }
    
    def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
        """Detect bias using ML model (simplified implementation)"""
        # Simulate ML model prediction
        bias_score = self._predict_bias_score(text, language)
        
        if bias_score > 0.7:  # High confidence threshold
            edits = self._extract_biased_terms(text, language)
            return BiasDetectionResult(
                text=text,
                has_bias_detected=True,
                detected_edits=edits
            )

        return BiasDetectionResult(
            text=text,
            has_bias_detected=False,
            detected_edits=[]
        )
    
    def _predict_bias_score(self, text: str, language: Language) -> float:
        """Simulate ML model bias prediction"""
        # Simplified bias indicators for demo
        bias_patterns = {
            Language.ENGLISH: ['chairman', 'businessman', 'policeman', 'fireman'],
            Language.SWAHILI: ['mwanaume', 'bwana'],
            Language.FRENCH: ['président', 'directeur', 'policier'],
            Language.GIKUYU: ['mũndũ mũrũme', 'mũrũme']
        }
        
        patterns = bias_patterns.get(language, [])
        text_lower = text.lower()
        
        # Simple scoring based on pattern matches
        matches = sum(1 for pattern in patterns if pattern in text_lower)
        return min(matches * 0.4, 1.0)
    
    def _extract_biased_terms(self, text: str, language: Language) -> List[Dict[str, str]]:
        """Extract biased terms and suggest corrections"""
        corrections = {
            Language.ENGLISH: {
                'chairman': 'chair',
                'businessman': 'businessperson',
                'policeman': 'police officer',
                'fireman': 'firefighter'
            },
            Language.SWAHILI: {
                'mwanaume': 'mtu',
                'bwana': 'mkuu'
            }
        }
        
        lang_corrections = corrections.get(language, {})
        edits = []
        
        for biased_term, correction in lang_corrections.items():
            if biased_term.lower() in text.lower():
                edits.append({
                    'from': biased_term,
                    'to': correction,
                    'severity': 'replace'
                })
        
        return edits