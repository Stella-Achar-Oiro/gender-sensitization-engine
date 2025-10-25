import csv
import shutil
from datetime import datetime

def backup_lexicon(lang):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original = f"rules/lexicon_{lang}_v2.csv"
    backup = f"rules/lexicon_{lang}_v2_backup_{timestamp}.csv"
    shutil.copy2(original, backup)
    print(f"Backed up {original} to {backup}")

def add_improvements_to_lexicon(lang="en"):
    backup_lexicon(lang)
    
    # Read improvements
    improvements = []
    with open("eval/rule_improvements.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['language'] == lang:
                improvements.append(row)
    
    # Read existing lexicon
    existing_rules = []
    lexicon_file = f"rules/lexicon_{lang}_v2.csv"
    with open(lexicon_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_rules = list(reader)
    
    # Get existing biased terms to avoid duplicates
    existing_biased = {row['biased'].lower() for row in existing_rules}
    
    # Add new rules
    new_rules = []
    for improvement in improvements:
        if improvement['biased'].lower() not in existing_biased:
            new_rule = {
                'language': lang,
                'biased': improvement['biased'],
                'neutral_primary': improvement['neutral_primary'],
                'neutral_alternatives': improvement.get('neutral_alternatives', ''),
                'tags': improvement.get('tags', 'gender|occupation'),
                'pos': improvement.get('pos', 'noun'),
                'scope': improvement.get('scope', 'general'),
                'register': improvement.get('register', 'formal'),
                'severity': improvement.get('severity', 'replace'),
                'ngeli': '',
                'number': '',
                'requires_agreement': '',
                'agreement_notes': '',
                'patterns': '',
                'constraints': '',
                'avoid_when': '',
                'example_biased': improvement.get('example_biased', ''),
                'example_neutral': improvement.get('example_neutral', '')
            }
            new_rules.append(new_rule)
            print(f"Adding rule: {improvement['biased']} → {improvement['neutral_primary']}")
    
    # Write updated lexicon
    if new_rules:
        all_rules = existing_rules + new_rules
        
        with open(lexicon_file, 'w', newline='', encoding='utf-8') as f:
            if all_rules:
                fieldnames = all_rules[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rules)
        
        print(f"Added {len(new_rules)} new rules to {lexicon_file}")
    else:
        print("No new rules to add (all already exist)")

def main():
    print("Applying failure analysis improvements...")
    add_improvements_to_lexicon("en")
    print("Improvements applied successfully!")

if __name__ == "__main__":
    main()