#!/usr/bin/env python3

import csv

def load_rules(lang):
    """Load bias detection rules."""
    rules = []
    with open(f"rules/lexicon_{lang}_v3.csv", 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('biased'):
                rules.append(row['biased'].lower())
    return rules

def detect_bias_main(text, lang):
    """Main detector using rules."""
    rules = load_rules(lang)
    text_lower = text.lower()
    return any(rule in text_lower for rule in rules)

def detect_bias_baseline(text, lang):
    """Simple baseline detector."""
    gendered_words = {
        'en': ['he', 'she', 'his', 'her', 'him', 'man', 'woman', 'boy', 'girl'],
        'sw': ['yeye', 'mwanaume', 'mwanamke', 'mvulana', 'msichana'],
        'ha': ['shi', 'ita', 'mwanaume', 'mwanamke', 'yaro', 'yarinya'],
        'yo': ['o', 'oun', 'ọkunrin', 'obinrin', 'ọmọkunrin', 'ọmọbinrin'],
        'ig': ['o', 'ọ', 'nwoke', 'nwanyị', 'nwa nwoke', 'nwa nwanyị']
    }
    words = gendered_words.get(lang, [])
    return any(word in text.lower() for word in words)

def calculate_f1(expected, predicted):
    """Calculate F1 score."""
    tp = sum(1 for e, p in zip(expected, predicted) if e and p)
    fp = sum(1 for e, p in zip(expected, predicted) if not e and p)
    fn = sum(1 for e, p in zip(expected, predicted) if e and not p)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return f1

def compare_baselines():
    """Compare main detector vs baseline."""
    
    for lang in ['en', 'sw', 'ha', 'yo', 'ig']:
        print(f"\n=== {lang.upper()} BASELINE COMPARISON ===")
        
        # Load ground truth
        samples = []
        with open(f"eval/ground_truth_{lang}.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append({
                    'text': row['text'].strip('"'),
                    'expected': row['has_bias'].lower() == 'true'
                })
        
        # Get predictions
        expected = [s['expected'] for s in samples]
        main_pred = [detect_bias_main(s['text'], lang) for s in samples]
        baseline_pred = [detect_bias_baseline(s['text'], lang) for s in samples]
        
        # Calculate F1 scores
        main_f1 = calculate_f1(expected, main_pred)
        baseline_f1 = calculate_f1(expected, baseline_pred)
        
        print(f"Main Detector F1: {main_f1:.3f}")
        print(f"Baseline F1: {baseline_f1:.3f}")
        
        if baseline_f1 > 0:
            improvement = ((main_f1 - baseline_f1) / baseline_f1 * 100)
            print(f"Improvement: {improvement:+.1f}%")
        else:
            print("Improvement: N/A (baseline F1 = 0)")

if __name__ == "__main__":
    compare_baselines()