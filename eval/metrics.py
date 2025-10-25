from typing import List, Dict, Tuple

class BiasMetrics:
    def __init__(self):
        self.tp = 0  # true positives
        self.fp = 0  # false positives  
        self.fn = 0  # false negatives
        self.tn = 0  # true negatives
    
    def add_prediction(self, predicted: bool, actual: bool):
        if predicted and actual:
            self.tp += 1
        elif predicted and not actual:
            self.fp += 1
        elif not predicted and actual:
            self.fn += 1
        else:
            self.tn += 1
    
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0
    
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0
    
    def f1_score(self) -> float:
        p, r = self.precision(), self.recall()
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
    
    def reset(self):
        self.tp = self.fp = self.fn = self.tn = 0

class EvaluationMetrics:
    def calculate_metrics(self, predictions: List[bool], ground_truth: List[bool]) -> Dict[str, float]:
        metrics = BiasMetrics()
        for pred, actual in zip(predictions, ground_truth):
            metrics.add_prediction(pred, actual)
        
        return {
            'precision': metrics.precision(),
            'recall': metrics.recall(),
            'f1_score': metrics.f1_score(),
            'true_positives': metrics.tp,
            'false_positives': metrics.fp,
            'false_negatives': metrics.fn,
            'true_negatives': metrics.tn
        }
    
    def calculate_by_category(self, predictions: List[bool], ground_truth: List[bool], 
                            categories: List[str]) -> Dict[str, Dict[str, float]]:
        category_metrics = {}
        unique_categories = set(categories)
        
        for category in unique_categories:
            cat_predictions = [pred for pred, cat in zip(predictions, categories) if cat == category]
            cat_ground_truth = [gt for gt, cat in zip(ground_truth, categories) if cat == category]
            
            if cat_predictions:
                category_metrics[category] = self.calculate_metrics(cat_predictions, cat_ground_truth)
        
        return category_metrics