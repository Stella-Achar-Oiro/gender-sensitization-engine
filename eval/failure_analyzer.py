#!/usr/bin/env python3

import csv
from pathlib import Path

from config import ground_truth_filename
from core.rules_loader import load_rules as load_rules_from_core


def load_rules(lang):
    """Load bias detection rules (list of lowercased biased terms). Uses core.rules_loader."""
    rules = load_rules_from_core(lang)
    return [r["biased"].lower() for r in rules if r.get("biased")]

def detect_bias_simple(text, lang):
    """Simple bias detection using rules."""
    rules = load_rules(lang)
    text_lower = text.lower()
    return any(rule in text_lower for rule in rules)

def analyze_failures():
    """Analyze false negatives."""
    
    for lang in ['en', 'sw', 'ha', 'yo', 'ig']:
        print(f"\n=== {lang.upper()} FAILURE ANALYSIS ===")
        
        # Load ground truth
        samples = []
        gt_path = Path("eval") / ground_truth_filename(lang)
        with open(gt_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append({
                    'text': row['text'].strip('"'),
                    'expected': row['has_bias'].lower() == 'true'
                })
        
        # Find false negatives
        false_negatives = []
        for sample in samples:
            if sample['expected']:
                detected = detect_bias_simple(sample['text'], lang)
                if not detected:
                    false_negatives.append(sample['text'])
        
        print(f"False Negatives: {len(false_negatives)}")
        
        # Show top 5
        for i, text in enumerate(false_negatives[:5], 1):
            print(f"{i}. \"{text}\"")
        
        if len(false_negatives) > 5:
            print(f"... and {len(false_negatives) - 5} more")

if __name__ == "__main__":
    analyze_failures()