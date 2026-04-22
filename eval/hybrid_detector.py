"""
Hybrid bias detector combining rules-based and ML approaches
"""
from typing import List, Dict
from .bias_detector import BiasDetector
from .ml_detector import MLBiasDetector
from .models import BiasDetectionResult, Language

class HybridBiasDetector:
    """Combines rules-based and ML approaches for enhanced accuracy"""
    
    def __init__(self):
        self.rules_detector = BiasDetector()
        self.ml_detector = MLBiasDetector()
        
    def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
        """Detect bias using both approaches and combine results"""
        # Get results from both detectors
        rules_result = self.rules_detector.detect_bias(text, language)
        ml_result = self.ml_detector.detect_bias(text, language)
        
        # Combine results with weighted confidence
        combined_edits = self._merge_edits(rules_result.detected_edits, ml_result.detected_edits)
        
        # Bias detected if either approach finds it
        has_bias = rules_result.has_bias_detected or ml_result.has_bias_detected

        # Combined confidence (rules get higher weight for precision)
        # Note: BiasDetectionResult doesn't store confidence, but we calculate it for internal use
        rules_weight = 0.7
        ml_weight = 0.3
        combined_confidence = (
            rules_weight * (1.0 if rules_result.has_bias_detected else 0.0) +
            ml_weight * (0.8 if ml_result.has_bias_detected else 0.2)
        )

        return BiasDetectionResult(
            text=text,
            has_bias_detected=has_bias,
            detected_edits=combined_edits
        )
    
    def _merge_edits(self, rules_edits: List[Dict[str, str]], ml_edits: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Merge edits from both approaches, avoiding duplicates"""
        merged = list(rules_edits)  # Start with rules-based edits
        
        # Add ML edits that don't overlap with rules
        for ml_edit in ml_edits:
            if not any(self._edits_overlap(ml_edit, rule_edit) for rule_edit in rules_edits):
                merged.append(ml_edit)
        
        return merged
    
    def _edits_overlap(self, edit1: Dict[str, str], edit2: Dict[str, str]) -> bool:
        """Check if two edits target the same text"""
        return edit1.get('from', '').lower() == edit2.get('from', '').lower()
    
    def get_detection_breakdown(self, text: str, language: Language) -> Dict:
        """Get detailed breakdown of detection methods"""
        rules_result = self.rules_detector.detect_bias(text, language)
        ml_result = self.ml_detector.detect_bias(text, language)
        
        return {
            'rules_based': {
                'detected': rules_result.has_bias_detected,
                'edits_count': len(rules_result.detected_edits),
                'method': 'lexicon_matching'
            },
            'ml_based': {
                'detected': ml_result.has_bias_detected,
                'confidence': getattr(ml_result, 'confidence_score', 0.0),
                'edits_count': len(ml_result.detected_edits),
                'method': 'transformer_model'
            },
            'agreement': rules_result.has_bias_detected == ml_result.has_bias_detected
        }