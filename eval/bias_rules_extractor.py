import pandas as pd
import re
from pathlib import Path

def load_rules(lang="en"):
    base_path = Path(__file__).parent.parent
    rules_path = base_path / "rules" / f"lexicon_{lang}_v2.csv"
    
    if not rules_path.exists():
        return []
    
    df = pd.read_csv(rules_path)
    rules = []
    for _, row in df.iterrows():
        rules.append({
            'biased': str(row.get('biased', '')),
            'neutral_primary': str(row.get('neutral_primary', '')),
            'severity': str(row.get('severity', ''))
        })
    return rules

def detect_bias(text: str, lang: str):
    rules = load_rules(lang)
    edits = []
    
    for rule in rules:
        biased = rule['biased']
        pattern = r'\b' + re.escape(biased) + r'\b'
        if re.search(pattern, text, flags=re.IGNORECASE):
            edits.append({
                'from': biased,
                'to': rule['neutral_primary'],
                'severity': rule['severity']
            })
    
    return edits