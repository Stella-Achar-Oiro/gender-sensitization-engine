"""
ML model evaluation comparing rules-based vs ML vs hybrid approaches
"""
import csv
from typing import Dict, List
from .bias_detector import BiasDetector
from .ml_detector import MLBiasDetector
from .hybrid_detector import HybridBiasDetector
from .models import Language, EvaluationMetrics

class MLEvaluationFramework:
    """Evaluate and compare different detection approaches"""
    
    def __init__(self):
        self.rules_detector = BiasDetector()
        self.ml_detector = MLBiasDetector()
        self.hybrid_detector = HybridBiasDetector()
    
    def run_comparative_evaluation(self) -> Dict:
        """Run evaluation across all approaches and languages"""
        results = {}
        
        for language in Language:
            print(f"\nEvaluating {language.value}...")
            
            # Load ground truth
            ground_truth = self._load_ground_truth(language)
            
            # Evaluate each approach
            rules_metrics = self._evaluate_approach(self.rules_detector, ground_truth, language)
            ml_metrics = self._evaluate_approach(self.ml_detector, ground_truth, language)
            hybrid_metrics = self._evaluate_approach(self.hybrid_detector, ground_truth, language)
            
            results[language.value] = {
                'rules_based': rules_metrics,
                'ml_based': ml_metrics,
                'hybrid': hybrid_metrics,
                'sample_count': len(ground_truth)
            }
            
            # Print comparison
            self._print_comparison(language, rules_metrics, ml_metrics, hybrid_metrics)
        
        return results
    
    def _evaluate_approach(self, detector, ground_truth: List, language: Language) -> EvaluationMetrics:
        """Evaluate single detection approach"""
        tp = fp = fn = tn = 0
        
        for sample in ground_truth:
            result = detector.detect_bias(sample['text'], language)
            predicted = result.has_bias_detected
            actual = sample['has_bias'] == 'True'
            
            if predicted and actual:
                tp += 1
            elif predicted and not actual:
                fp += 1
            elif not predicted and actual:
                fn += 1
            else:
                tn += 1
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn
        )
    
    def _load_ground_truth(self, language: Language) -> List[Dict]:
        """Load ground truth data for language"""
        filename = f"eval/ground_truth_{language.value}.csv"
        ground_truth = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                ground_truth = list(reader)
        except FileNotFoundError:
            print(f"Warning: Ground truth file {filename} not found")
        
        return ground_truth
    
    def _print_comparison(self, language: Language, rules: EvaluationMetrics, 
                         ml: EvaluationMetrics, hybrid: EvaluationMetrics):
        """Print comparison table for language"""
        print(f"\n{language.value.upper()} COMPARISON:")
        print("Approach    | F1    | Precision | Recall")
        print("-" * 40)
        print(f"Rules-based | {rules.f1_score:.3f} | {rules.precision:.3f}     | {rules.recall:.3f}")
        print(f"ML-based    | {ml.f1_score:.3f} | {ml.precision:.3f}     | {ml.recall:.3f}")
        print(f"Hybrid      | {hybrid.f1_score:.3f} | {hybrid.precision:.3f}     | {hybrid.recall:.3f}")

if __name__ == "__main__":
    evaluator = MLEvaluationFramework()
    results = evaluator.run_comparative_evaluation()
    
    print("\n" + "="*60)
    print("SUMMARY: Best F1 Scores by Language")
    print("="*60)
    
    for lang, metrics in results.items():
        best_f1 = max(
            metrics['rules_based'].f1_score,
            metrics['ml_based'].f1_score, 
            metrics['hybrid'].f1_score
        )
        
        best_approach = 'rules' if metrics['rules_based'].f1_score == best_f1 else \
                       'ml' if metrics['ml_based'].f1_score == best_f1 else 'hybrid'
        
        print(f"{lang}: {best_f1:.3f} ({best_approach})")