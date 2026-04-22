#!/usr/bin/env python3
"""
Apply reviewed KI lexicon suggestions to rules/lexicon_ki_v3.csv.

Reads scripts/ki_lexicon_suggestions.csv (human-reviewed).
Skips rows where severity=skip or biased_term is empty.
Appends approved rows as valid lexicon entries.

Usage:
    python3 scripts/ki_apply_suggestions.py [--dry-run]
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUGGESTIONS_PATH = ROOT / "scripts" / "ki_lexicon_suggestions.csv"
LEXICON_PATH = ROOT / "rules" / "lexicon_ki_v3.csv"


LEXICON_COLUMNS = [
    "language", "biased", "neutral_primary", "neutral_alternatives",
    "tags", "pos", "scope", "register", "severity", "bias_label",
    "stereotype_category", "explicitness", "ngeli", "number",
    "requires_agreement", "agreement_notes", "patterns", "constraints",
    "avoid_when", "example_biased", "example_neutral",
]

BIAS_CATEGORY_TO_TAGS = {
    "occupation": "gender|occupation",
    "family_role": "gender|family_role",
    "capability": "gender|capability",
    "pronoun_assumption": "pronoun|gender",
    "pronoun_generic": "pronoun|gender",
    "stereotype": "gender|stereotype",
    "religion_culture": "gender|religion_culture",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SUGGESTIONS_PATH.exists():
        print(f"Suggestions file not found: {SUGGESTIONS_PATH}")
        print("Run ki_lexicon_expander.py first.")
        return

    # Load existing terms to avoid duplicates
    existing = set()
    with open(LEXICON_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("language") == "ki":
                existing.add(row.get("biased", "").strip().lower())

    suggestions = []
    with open(SUGGESTIONS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            suggestions.append(row)

    to_add = []
    skipped = []
    for s in suggestions:
        term = s.get("biased_term", "").strip()
        if not term:
            skipped.append(("empty term", s))
            continue
        if s.get("severity", "").lower() == "skip":
            skipped.append(("marked skip", s))
            continue
        if term.lower() in existing:
            skipped.append(("already in lexicon", s))
            continue
        if not s.get("neutral_primary", "").strip():
            skipped.append(("no neutral_primary", s))
            continue
        to_add.append(s)

    print(f"Suggestions: {len(suggestions)} total")
    print(f"  To add:  {len(to_add)}")
    print(f"  Skipped: {len(skipped)}")
    for reason, s in skipped[:5]:
        print(f"    [{reason}] {s.get('biased_term', '')!r}")

    if not to_add:
        print("Nothing to add.")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would add these entries:")
        for s in to_add[:10]:
            print(f"  {s['biased_term']!r} → {s['neutral_primary']!r} ({s['severity']})")
        return

    # Append to lexicon
    with open(LEXICON_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEXICON_COLUMNS, extrasaction="ignore")
        for s in to_add:
            bias_cat = s.get("bias_category", "stereotype")
            tags = BIAS_CATEGORY_TO_TAGS.get(bias_cat, "gender|stereotype")
            term = s["biased_term"].strip()
            row = {
                "language": "ki",
                "biased": term,
                "neutral_primary": s.get("neutral_primary", "").strip(),
                "neutral_alternatives": "",
                "tags": tags,
                "pos": "phrase" if " " in term else "noun",
                "scope": "general",
                "register": "neutral",
                "severity": s.get("severity", "warn"),
                "bias_label": "stereotype",
                "stereotype_category": s.get("stereotype_category", "daily_life"),
                "explicitness": s.get("explicitness", "implicit"),
                "ngeli": "",
                "number": "",
                "requires_agreement": "false",
                "agreement_notes": f"Gemini suggestion: {s.get('reason', '')[:80]}",
                "patterns": "",
                "constraints": "",
                "avoid_when": "",
                "example_biased": s.get("source_sentence", "")[:100],
                "example_neutral": "",
            }
            writer.writerow(row)

    print(f"\n✓ Added {len(to_add)} entries to {LEXICON_PATH.name}")
    print("\nNext: python3 run_evaluation.py  (check KI recall improvement)")


if __name__ == "__main__":
    main()
