import csv
import json
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from simple_bias_detector import detect_bias_simple

class FailureAnalyzer:
    def __init__(self):
        self.failure_cases = []
    
    def analyze_failures(self, ground_truth_file, language):
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ground_truth = list(reader)
        
        failures = []
        
        for item in ground_truth:
            text = item['text']
            expected_bias = item['has_bias'].lower() == 'true'
            category = item['bias_category']
            expected_correction = item['expected_correction']
            
            detected_edits = detect_bias_simple(text, language)
            predicted_bias = len(detected_edits) > 0
            
            # False Negative: Expected bias but not detected
            if expected_bias and not predicted_bias:
                failures.append({
                    'type': 'false_negative',
                    'input': text,
                    'expected': True,
                    'predicted': False,
                    'category': category,
                    'expected_correction': expected_correction,
                    'diagnosis': self._diagnose_false_negative(text, category, language),
                    'language': language
                })
            
            # False Positive: No bias expected but detected
            elif not expected_bias and predicted_bias:
                failures.append({
                    'type': 'false_positive',
                    'input': text,
                    'expected': False,
                    'predicted': True,
                    'category': category,
                    'detected_edits': detected_edits,
                    'diagnosis': self._diagnose_false_positive(text, detected_edits),
                    'language': language
                })
        
        return failures
    
    def _diagnose_false_negative(self, text, category, language):
        # Check if bias term exists but not in our rules
        common_bias_terms = {
            'en': ['chairman', 'waitress', 'policeman', 'businessman', 'fireman', 'mailman', 'stewardess', 'congressman', 'weatherman', 'repairman', 'doorman', 'anchorman', 'deliveryman', 'handyman'],
            'sw': ['mwalimu mkuu', 'askari', 'mfanyabiashara', 'mzimamoto', 'mpeleka barua', 'mhudumu wa ndege', 'mbunge', 'mtabiri wa hali ya hewa', 'fundi', 'mlezi wa mlango', 'mwandishi wa habari', 'mpeleka mizigo', 'fundi wa nyumba']
        }
        
        text_lower = text.lower()
        missing_terms = []
        
        for term in common_bias_terms.get(language, []):
            if term.lower() in text_lower:
                missing_terms.append(term)
        
        if missing_terms:
            return f"Missing rule for: {', '.join(missing_terms)}"
        elif category == 'pronoun_generic':
            return "Generic pronoun pattern not captured by word-level rules"
        elif category == 'pronoun_assumption':
            return "Gender assumption requires contextual analysis beyond current rules"
        else:
            return "Unknown bias pattern - needs manual rule creation"
    
    def _diagnose_false_positive(self, text, detected_edits):
        if detected_edits:
            detected_terms = [edit['from'] for edit in detected_edits]
            return f"Rule too broad - incorrectly flagged: {', '.join(detected_terms)}"
        return "Unknown false positive cause"
    
    def generate_failure_report(self, languages=['en', 'sw']):
        all_failures = []
        
        for lang in languages:
            ground_truth_file = f"eval/ground_truth_{lang}.csv"
            failures = self.analyze_failures(ground_truth_file, lang)
            all_failures.extend(failures)
        
        # Select top 3 failures per type for reporting
        false_negatives = [f for f in all_failures if f['type'] == 'false_negative']
        false_positives = [f for f in all_failures if f['type'] == 'false_positive']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_false_negatives': len(false_negatives),
                'total_false_positives': len(false_positives),
                'languages_analyzed': languages
            },
            'top_failures': {
                'false_negatives': false_negatives[:3],
                'false_positives': false_positives[:3]
            },
            'improvement_recommendations': self._generate_recommendations(all_failures)
        }
        
        return report
    
    def _generate_recommendations(self, failures):
        recommendations = []
        
        false_negatives = [f for f in failures if f['type'] == 'false_negative']
        missing_terms = []
        
        for failure in false_negatives:
            if 'Missing rule for:' in failure['diagnosis']:
                terms = failure['diagnosis'].replace('Missing rule for: ', '').split(', ')
                missing_terms.extend(terms)
        
        if missing_terms:
            unique_terms = list(set(missing_terms))
            recommendations.append(f"Add rules for: {', '.join(unique_terms[:5])}")
        
        pronoun_failures = len([f for f in false_negatives if 'pronoun' in f['category']])
        if pronoun_failures > 2:
            recommendations.append("Implement contextual pronoun analysis beyond word-level matching")
        
        false_positives = [f for f in failures if f['type'] == 'false_positive']
        if len(false_positives) > 1:
            recommendations.append("Review rule specificity to reduce false positives")
        
        return recommendations

def main():
    analyzer = FailureAnalyzer()
    report = analyzer.generate_failure_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"eval/results/failure_analysis_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("Failure Analysis Summary")
    print("=" * 40)
    print(f"False Negatives: {report['summary']['total_false_negatives']}")
    print(f"False Positives: {report['summary']['total_false_positives']}")
    print()
    
    print("Top 3 False Negatives:")
    for i, failure in enumerate(report['top_failures']['false_negatives'], 1):
        print(f"{i}. '{failure['input']}' - {failure['diagnosis']}")
    
    print("\nImprovement Recommendations:")
    for rec in report['improvement_recommendations']:
        print(f"- {rec}")
    
    print(f"\nFull report saved to: {report_file}")

if __name__ == "__main__":
    main()