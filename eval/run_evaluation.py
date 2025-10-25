import csv
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from eval.simple_bias_detector import detect_bias_simple
from eval.metrics import EvaluationMetrics

class BiasEvaluator:
    def __init__(self):
        self.metrics = EvaluationMetrics()
    
    def load_ground_truth(self, filepath: str):
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'text': row['text'],
                    'has_bias': row['has_bias'].lower() == 'true',
                    'bias_category': row['bias_category'],
                    'expected_correction': row['expected_correction']
                })
        return data
    
    def evaluate_language(self, language: str):
        ground_truth_file = f"eval/ground_truth_{language}.csv"
        ground_truth = self.load_ground_truth(ground_truth_file)
        
        predictions = []
        categories = []
        
        for item in ground_truth:
            detected_edits = detect_bias_simple(item['text'], language)
            predictions.append(len(detected_edits) > 0)
            categories.append(item['bias_category'])
        
        actual_labels = [item['has_bias'] for item in ground_truth]
        
        overall_metrics = self.metrics.calculate_metrics(predictions, actual_labels)
        category_metrics = self.metrics.calculate_by_category(predictions, actual_labels, categories)
        
        return {
            'language': language,
            'overall': overall_metrics,
            'by_category': category_metrics,
            'total_samples': len(ground_truth)
        }
    
    def generate_report(self, results):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"eval/results/f1_report_{timestamp}.csv"
        
        os.makedirs("eval/results", exist_ok=True)
        
        with open(report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Language', 'Category', 'Precision', 'Recall', 'F1_Score', 'TP', 'FP', 'FN', 'TN'])
            
            for result in results:
                lang = result['language']
                overall = result['overall']
                writer.writerow([
                    lang, 'OVERALL', 
                    f"{overall['precision']:.3f}",
                    f"{overall['recall']:.3f}",
                    f"{overall['f1_score']:.3f}",
                    overall['true_positives'],
                    overall['false_positives'],
                    overall['false_negatives'],
                    overall['true_negatives']
                ])
                
                for category, metrics in result['by_category'].items():
                    writer.writerow([
                        lang, category,
                        f"{metrics['precision']:.3f}",
                        f"{metrics['recall']:.3f}",
                        f"{metrics['f1_score']:.3f}",
                        metrics['true_positives'],
                        metrics['false_positives'],
                        metrics['false_negatives'],
                        metrics['true_negatives']
                    ])
        
        return report_file

def main():
    evaluator = BiasEvaluator()
    
    languages = ['en', 'sw']
    results = []
    
    print("Running bias detection evaluation...")
    
    for lang in languages:
        print(f"Evaluating {lang}...")
        result = evaluator.evaluate_language(lang)
        results.append(result)
        
        print(f"{lang.upper()} Results:")
        print(f"  Overall F1: {result['overall']['f1_score']:.3f}")
        print(f"  Precision: {result['overall']['precision']:.3f}")
        print(f"  Recall: {result['overall']['recall']:.3f}")
        print()
    
    report_file = evaluator.generate_report(results)
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()