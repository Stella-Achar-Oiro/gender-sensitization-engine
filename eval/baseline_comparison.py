import csv
import json
from datetime import datetime

class SimpleBaselineDetector:
    """Naive baseline: detect common gendered terms without sophisticated rules"""
    
    def __init__(self):
        self.gendered_terms = {
            'en': ['he', 'she', 'his', 'her', 'him', 'man', 'woman', 'male', 'female', 'boy', 'girl'],
            'sw': ['yeye', 'mwanaume', 'mwanamke', 'mvulana', 'msichana', 'baba', 'mama']
        }
    
    def detect_bias(self, text, lang):
        text_lower = text.lower()
        terms = self.gendered_terms.get(lang, [])
        
        for term in terms:
            if term in text_lower:
                return True
        return False

def run_baseline_evaluation():
    baseline = SimpleBaselineDetector()
    results = {}
    
    for lang in ['en', 'sw']:
        ground_truth_file = f"eval/ground_truth_{lang}.csv"
        
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ground_truth = list(reader)
        
        predictions = []
        actual_labels = []
        
        for item in ground_truth:
            predicted = baseline.detect_bias(item['text'], lang)
            actual = item['has_bias'].lower() == 'true'
            
            predictions.append(predicted)
            actual_labels.append(actual)
        
        # Calculate metrics
        tp = sum(1 for p, a in zip(predictions, actual_labels) if p and a)
        fp = sum(1 for p, a in zip(predictions, actual_labels) if p and not a)
        fn = sum(1 for p, a in zip(predictions, actual_labels) if not p and a)
        tn = sum(1 for p, a in zip(predictions, actual_labels) if not p and not a)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results[lang] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn
        }
    
    return results

def compare_with_juakazi():
    print("Baseline Comparison: Simple Gendered Terms vs JuaKazi Rules")
    print("=" * 60)
    
    baseline_results = run_baseline_evaluation()
    
    # JuaKazi results (from latest evaluation)
    juakazi_results = {
        'en': {'precision': 1.000, 'recall': 0.680, 'f1_score': 0.810},
        'sw': {'precision': 1.000, 'recall': 0.040, 'f1_score': 0.077}
    }
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'baseline_method': 'Simple gendered term detection',
        'juakazi_method': 'Rules-based lexicon matching with improvements',
        'results': {}
    }
    
    for lang in ['en', 'sw']:
        lang_name = 'English' if lang == 'en' else 'Swahili'
        
        baseline = baseline_results[lang]
        juakazi = juakazi_results[lang]
        
        print(f"\n{lang_name} Results:")
        print(f"{'Method':<20} {'Precision':<10} {'Recall':<10} {'F1-Score':<10}")
        print("-" * 50)
        print(f"{'Baseline':<20} {baseline['precision']:<10.3f} {baseline['recall']:<10.3f} {baseline['f1_score']:<10.3f}")
        print(f"{'JuaKazi':<20} {juakazi['precision']:<10.3f} {juakazi['recall']:<10.3f} {juakazi['f1_score']:<10.3f}")
        
        f1_improvement = ((juakazi['f1_score'] - baseline['f1_score']) / baseline['f1_score'] * 100) if baseline['f1_score'] > 0 else float('inf')
        print(f"F1 Improvement: {f1_improvement:+.1f}%")
        
        comparison['results'][lang] = {
            'baseline': baseline,
            'juakazi': juakazi,
            'f1_improvement_percent': f1_improvement
        }
    
    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"eval/results/baseline_comparison_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"\nComparison report saved to: {report_file}")
    
    return comparison

if __name__ == "__main__":
    compare_with_juakazi()