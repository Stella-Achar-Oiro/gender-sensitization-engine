#!/usr/bin/env python3
"""
Apply reviewed SW lexicon suggestions to rules/lexicon_sw_v3.csv.

Usage:
    python3 scripts/sw_apply_suggestions.py [--dry-run]
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUGGESTIONS_PATH = ROOT / "scripts" / "sw_lexicon_suggestions.csv"
LEXICON_PATH = ROOT / "rules" / "lexicon_sw_v3.csv"

LEXICON_COLUMNS = [
    "language", "biased", "neutral_primary", "neutral_alternatives",
    "tags", "pos", "scope", "register", "severity", "bias_label",
    "stereotype_category", "explicitness", "ngeli", "number",
    "requires_agreement", "agreement_notes", "patterns", "constraints",
    "avoid_when", "example_biased", "example_neutral",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SUGGESTIONS_PATH.exists():
        print(f"No suggestions file at {SUGGESTIONS_PATH}")
        print("Run sw_lexicon_expander.py first.")
        return

    existing = set()
    with open(LEXICON_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("language") == "sw":
                existing.add(row.get("biased", "").strip().lower())

    to_add = []
    with open(SUGGESTIONS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = row.get("biased_term", "").strip()
            if not term or row.get("severity", "").lower() == "skip":
                continue
            if term.lower() in existing:
                continue
            if not row.get("neutral_primary", "").strip():
                continue
            to_add.append(row)

    print(f"Approved suggestions to add: {len(to_add)}")

    if not to_add:
        print("Nothing to add.")
        return

    if args.dry_run:
        for s in to_add[:10]:
            print(f"  {s['biased_term']!r} → {s['neutral_primary']!r} ({s['severity']})")
        return

    with open(LEXICON_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEXICON_COLUMNS, extrasaction="ignore")
        for s in to_add:
            term = s["biased_term"].strip()
            row = {
                "language": "sw",
                "biased": term,
                "neutral_primary": s.get("neutral_primary", "").strip(),
                "neutral_alternatives": "",
                "tags": s.get("tags", "gender|stereotype"),
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

    print(f"✓ Added {len(to_add)} entries to {LEXICON_PATH.name}")
    print("\nNext: python3 run_evaluation.py")


if __name__ == "__main__":
    main()
