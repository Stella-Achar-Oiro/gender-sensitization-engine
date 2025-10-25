import csv
import re
from pathlib import Path

def load_simple_rules(lang="en"):
    base_path = Path(__file__).parent.parent
    rules_path = base_path / "rules" / f"lexicon_{lang}_v2.csv"
    
    if not rules_path.exists():
        return []
    
    rules = []
    with open(rules_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append({
                'biased': row.get('biased', ''),
                'neutral_primary': row.get('neutral_primary', ''),
                'severity': row.get('severity', '')
            })
    return rules

def detect_bias_simple(text: str, lang: str):
    rules = load_simple_rules(lang)
    detected = []
    
    for rule in rules:
        biased = rule['biased']
        if not biased:
            continue
            
        pattern = r'\b' + re.escape(biased) + r'\b'
        if re.search(pattern, text, flags=re.IGNORECASE):
            detected.append({
                'from': biased,
                'to': rule['neutral_primary'],
                'severity': rule['severity']
            })
    
    return detected