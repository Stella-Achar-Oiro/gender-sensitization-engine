#!/usr/bin/env python3
"""
Simple baseline gender bias detector using basic keyword matching.
Used as sanity check baseline for comparison with rule-based approach.
"""

import csv
import re
from typing import List, Tuple, Dict

class SimpleBaselineDetector:
    """Basic keyword-based bias detector as baseline"""
    
    def __init__(self):
        # Simple gendered keywords for baseline detection
        self.gendered_keywords = {
            'en': ['he', 'she', 'his', 'her', 'him', 'chairman', 'waitress', 'policeman', 'businessman'],
            'sw': ['yeye', 'mwanaume', 'mwanamke', 'baba', 'mama'],
            'ha': ['shi', 'ita', 'namiji', 'mace'],
            'ig': ['nwoke', 'nwanyi', 'ya', 'o'],
            'yo': ['ọkunrin', 'obinrin', 'o', 'oun']
        }
    
    def detect_bias(self, text: str, language: str) -> bool:
        """Simple detection: return True if any gendered keyword found"""
        if language not in self.gendered_keywords:
            return False
        
        text_lower = text.lower()
        keywords = self.gendered_keywords[language]
        
        for keyword in keywords:
            if re.search(r'\b' + keyword + r'\b', text_lower):
                return True
        return False

def evaluate_baseline(ground_truth_file: str, language: str) -> Dict:
    """Evaluate baseline detector on ground truth"""
    detector = SimpleBaselineDetector()
    
    tp = fp = tn = fn = 0
    
    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row['text'].strip('"')
            actual_bias = row['has_bias'] == 'true'
            predicted_bias = detector.detect_bias(text, language)
            
            if actual_bias and predicted_bias:
                tp += 1
            elif not actual_bias and predicted_bias:
                fp += 1
            elif not actual_bias and not predicted_bias:
                tn += 1
            else:  # actual_bias and not predicted_bias
                fn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'language': language,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn
    }

if __name__ == "__main__":
    languages = ['en', 'sw', 'ha', 'ig', 'yo']
    
    print("Baseline Evaluation Results:")
    print("=" * 50)
    
    for lang in languages:
        try:
            results = evaluate_baseline(f'ground_truth_{lang}.csv', lang)
            print(f"{lang.upper()}: F1={results['f1']:.3f}, P={results['precision']:.3f}, R={results['recall']:.3f}")
        except FileNotFoundError:
            print(f"{lang.upper()}: File not found")