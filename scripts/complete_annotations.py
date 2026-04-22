#!/usr/bin/env python3
"""
AI-Powered Annotation Completion Assistant
Interactive tool to complete missing stereotype_category annotations with AI suggestions.

Usage:
    python3 scripts/complete_annotations.py --input eval/ground_truth_ki_v7_aibridge.csv --output eval/ground_truth_ki_v7_complete.csv
"""

import csv
import sys
from typing import Dict, List, Optional, Tuple
import argparse
from datetime import datetime


class AIAnnotationAssistant:
    """AI-powered assistant to suggest stereotype_category for samples."""

    def __init__(self):
        self.categories = [
            'profession',
            'family_role',
            'leadership',
            'education',
            'religion_culture',
            'proverb_idiom',
            'daily_life',
            'appearance',
            'capability'
        ]

        # Keyword patterns for each category
        self.category_keywords = {
            'profession': {
                'kikuyu': ['daktari', 'mũrutani', 'mũruti', 'mũrĩmi', 'mũigũ', 'mũthondeki',
                          'mũteti', 'mũthuurĩ', 'mũcamanĩri', 'mũcungĩ', 'mũrũgamĩrĩri', 'mũthaki'],
                'concepts': ['doctor', 'teacher', 'farmer', 'judge', 'builder', 'mason',
                           'seller', 'driver', 'blacksmith', 'manager', 'administrator', 'work', 'job', 'career']
            },
            'family_role': {
                'kikuyu': ['rera', 'ciana', 'mũciĩ', 'nyũmba', 'mwana', 'ithe', 'nyina'],
                'concepts': ['care', 'children', 'home', 'house', 'child', 'father', 'mother',
                           'parent', 'family', 'household', 'domestic']
            },
            'leadership': {
                'kikuyu': ['mũtongoria', 'mũthaki', 'mũigũ', 'mũthamaki'],
                'concepts': ['leader', 'chief', 'administrator', 'judge', 'king', 'authority',
                           'command', 'govern', 'direct', 'manage']
            },
            'education': {
                'kikuyu': ['mũrutani', 'mũruti', 'kwĩruta', 'ũrutani'],
                'concepts': ['teacher', 'teach', 'learn', 'study', 'education', 'school',
                           'student', 'knowledge', 'training']
            },
            'religion_culture': {
                'kikuyu': ['mũthĩnjĩri', 'kanitha', 'Ngai', 'kũhooya', 'mũigĩ', 'mũguĩ'],
                'concepts': ['priest', 'church', 'God', 'pray', 'healer', 'diviner', 'worship',
                           'sacred', 'tradition', 'ritual', 'spiritual', 'religious']
            },
            'proverb_idiom': {
                'kikuyu': ['thimo', 'mũikarĩre'],
                'concepts': ['proverb', 'saying', 'idiom', 'metaphor', 'wisdom']
            },
            'daily_life': {
                'kikuyu': ['gũthiĩ', 'kũrĩa', 'gũthoma', 'gũcoka'],
                'concepts': ['go', 'eat', 'read', 'return', 'daily', 'routine', 'activity',
                           'everyday', 'chore']
            },
            'appearance': {
                'kikuyu': ['riua', 'thaka', 'ũthaka'],
                'concepts': ['face', 'beauty', 'beautiful', 'appearance', 'look', 'dress',
                           'clothing', 'physical']
            },
            'capability': {
                'kikuyu': ['ũhoti', 'hinya', 'ũgima'],
                'concepts': ['ability', 'strength', 'power', 'capable', 'skill', 'competence',
                           'talent', 'smart', 'intelligent', 'weak', 'strong']
            }
        }

    def suggest_category(self, text: str, bias_label: str, domain: str,
                        old_bias_category: str, notes: str) -> Tuple[str, float, str]:
        """
        Suggest stereotype_category using AI-powered heuristics.

        Returns: (suggested_category, confidence_score, reasoning)
        """
        text_lower = text.lower()

        # Score each category
        scores = {cat: 0.0 for cat in self.categories}
        matches = {cat: [] for cat in self.categories}

        # Check keywords for each category
        for category, keywords in self.category_keywords.items():
            # Kikuyu terms (higher weight)
            for term in keywords.get('kikuyu', []):
                if term in text_lower:
                    scores[category] += 3.0
                    matches[category].append(f"Kikuyu: '{term}'")

            # Concept terms (lower weight)
            for concept in keywords.get('concepts', []):
                if concept in text_lower or concept in notes.lower():
                    scores[category] += 1.0
                    matches[category].append(f"concept: '{concept}'")

        # Domain-based boosting
        if domain in ['religious_text', 'culture_and_religion']:
            scores['religion_culture'] += 5.0
            matches['religion_culture'].append("domain: religious_text")

        # Old category mapping
        if old_bias_category == 'occupation':
            scores['profession'] += 4.0
            matches['profession'].append("old_category: occupation")
        elif old_bias_category == 'pronoun_assumption':
            # Check context
            if any(term in text_lower for term in self.category_keywords['family_role']['kikuyu']):
                scores['family_role'] += 3.0
                matches['family_role'].append("pronoun_assumption + family context")
            elif any(term in text_lower for term in self.category_keywords['leadership']['kikuyu']):
                scores['leadership'] += 3.0
                matches['leadership'].append("pronoun_assumption + leadership context")

        # Bias label hints
        if bias_label == 'counter-stereotype':
            # Counter-stereotypes often in family_role or leadership
            if any(term in text_lower for term in ['rera', 'ciana', 'mũrũme']):
                scores['family_role'] += 2.0
                matches['family_role'].append("counter-stereotype + caregiving")
            if any(term in text_lower for term in ['mũtongoria', 'mũtumia']):
                scores['leadership'] += 2.0
                matches['leadership'].append("counter-stereotype + leadership")

        # Get top suggestion
        if max(scores.values()) == 0:
            return 'profession', 0.3, "Default: No strong matches found"

        top_category = max(scores, key=scores.get)
        confidence = min(scores[top_category] / 10.0, 0.95)  # Cap at 95%

        # Build reasoning
        reasoning = "; ".join(matches[top_category][:3])  # Top 3 matches

        return top_category, confidence, reasoning

    def format_sample_display(self, row: Dict, suggestion: Tuple[str, float, str],
                              sample_num: int, total: int) -> str:
        """Format a nice display for the user."""
        category, confidence, reasoning = suggestion

        display = f"""
{'=' * 80}
SAMPLE {sample_num} of {total}
{'=' * 80}

📝 TEXT (first 200 chars):
{row['text'][:200]}{"..." if len(row['text']) > 200 else ""}

🎯 CURRENT ANNOTATIONS:
  target_gender:   {row.get('target_gender', 'N/A')}
  bias_label:      {row.get('bias_label', 'N/A')}
  explicitness:    {row.get('explicitness', 'N/A')}
  sentiment:       {row.get('sentiment', 'N/A')}
  device:          {row.get('device', 'N/A')}
  domain:          {row.get('domain', 'N/A')}

❓ MISSING FIELD:
  stereotype_category: (EMPTY - needs annotation)

🤖 AI SUGGESTION ({confidence*100:.0f}% confidence):
  ✨ {category}

📊 REASONING:
  {reasoning}

🔢 ALL OPTIONS:
  1. profession        - Jobs, occupations, careers
  2. family_role       - Caregiving, parenting, household
  3. leadership        - Authority, governance, decision-making
  4. education         - Teaching, learning, academic
  5. religion_culture  - Religious roles, traditions, rituals
  6. proverb_idiom     - Sayings, metaphors, wisdom
  7. daily_life        - Everyday activities, routines
  8. appearance        - Physical looks, beauty, dress
  9. capability        - Skills, strength, competence

{'=' * 80}
"""
        return display


def complete_annotations(input_path: str, output_path: str, auto_approve_threshold: float = 0.90):
    """
    Interactive annotation completion with AI assistance.

    Args:
        input_path: Input CSV with missing stereotype_category
        output_path: Output CSV with completed annotations
        auto_approve_threshold: Auto-approve suggestions above this confidence (default 90%)
    """
    assistant = AIAnnotationAssistant()

    # Load data
    print("=" * 80)
    print("AI-POWERED ANNOTATION COMPLETION ASSISTANT")
    print("=" * 80)
    print()
    print(f"Loading: {input_path}")

    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Find samples needing annotation
    needs_annotation = []
    for row in rows:
        bias_label = row.get('bias_label', '')
        stereotype_category = row.get('stereotype_category', '')

        # Need annotation if bias_label ≠ neutral AND stereotype_category is empty
        if bias_label != 'neutral' and not stereotype_category:
            needs_annotation.append(row)

    print(f"Total samples: {len(rows):,}")
    print(f"Needs annotation: {len(needs_annotation):,}")
    print()

    if not needs_annotation:
        print("✅ All samples already annotated! Nothing to do.")
        return

    print(f"Auto-approve threshold: {auto_approve_threshold*100:.0f}% confidence")
    print()
    print("COMMANDS:")
    print("  [Enter]     - Accept AI suggestion")
    print("  1-9         - Choose different category")
    print("  s           - Skip this sample")
    print("  q           - Quit and save progress")
    print("  ?           - Show category options")
    print()
    input("Press Enter to start...")
    print()

    # Process each sample
    completed = 0
    skipped = 0
    auto_approved = 0

    for i, row in enumerate(needs_annotation, 1):
        # Get AI suggestion
        suggestion = assistant.suggest_category(
            text=row.get('text', ''),
            bias_label=row.get('bias_label', ''),
            domain=row.get('domain', ''),
            old_bias_category=row.get('bias_category', ''),
            notes=row.get('notes', '')
        )

        category, confidence, reasoning = suggestion

        # Auto-approve high confidence
        if confidence >= auto_approve_threshold:
            row['stereotype_category'] = category
            row['annotation_method'] = 'ai_assisted'
            row['annotation_confidence'] = f"{confidence:.2f}"
            completed += 1
            auto_approved += 1
            print(f"✅ [{i}/{len(needs_annotation)}] AUTO-APPROVED ({confidence*100:.0f}%): {category}")
            continue

        # Show sample to user
        display = assistant.format_sample_display(row, suggestion, i, len(needs_annotation))
        print(display)

        # Get user input
        while True:
            choice = input("👉 Your choice [Enter=accept, 1-9=category, s=skip, q=quit]: ").strip().lower()

            if choice == '':
                # Accept suggestion
                row['stereotype_category'] = category
                row['annotation_method'] = 'ai_assisted'
                row['annotation_confidence'] = f"{confidence:.2f}"
                completed += 1
                print(f"✅ Accepted: {category}")
                break

            elif choice == 's':
                # Skip
                skipped += 1
                print("⏭️  Skipped")
                break

            elif choice == 'q':
                # Quit
                print("\n⚠️  Quitting and saving progress...")
                save_and_exit(rows, output_path, fieldnames, completed, skipped, auto_approved,
                             i, len(needs_annotation))
                return

            elif choice == '?':
                # Show options
                print("\nCATEGORY OPTIONS:")
                for j, cat in enumerate(assistant.categories, 1):
                    print(f"  {j}. {cat}")
                print()
                continue

            elif choice.isdigit() and 1 <= int(choice) <= 9:
                # Manual category selection
                selected = assistant.categories[int(choice) - 1]
                row['stereotype_category'] = selected
                row['annotation_method'] = 'manual'
                row['annotation_confidence'] = '1.00'
                completed += 1
                print(f"✅ Manually selected: {selected}")
                break

            else:
                print("❌ Invalid choice. Try again.")

    # Save final results
    print()
    print("=" * 80)
    print("ANNOTATION COMPLETE!")
    print("=" * 80)
    save_and_exit(rows, output_path, fieldnames, completed, skipped, auto_approved,
                 len(needs_annotation), len(needs_annotation))


def save_and_exit(rows: List[Dict], output_path: str, fieldnames: List[str],
                  completed: int, skipped: int, auto_approved: int,
                  processed: int, total: int):
    """Save progress and show summary."""

    # Write output
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"✅ Saved to: {output_path}")
    print()
    print("SUMMARY:")
    print(f"  Processed:      {processed:,} / {total:,} ({processed/total*100:.1f}%)")
    print(f"  Completed:      {completed:,}")
    print(f"  Auto-approved:  {auto_approved:,}")
    print(f"  Skipped:        {skipped:,}")
    print(f"  Remaining:      {total - processed:,}")
    print()

    if processed < total:
        print("⚠️  Not all samples processed. Run again to continue from where you left off.")
    else:
        print("🎉 ALL ANNOTATIONS COMPLETE!")
        print()
        print("Next step: Validate your dataset")
        print(f"  python3 scripts/review_annotations.py --input {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='AI-powered assistant to complete missing stereotype_category annotations'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input CSV (e.g., eval/ground_truth_ki_v7_aibridge.csv)')
    parser.add_argument('--output', '-o', required=True,
                       help='Output CSV (e.g., eval/ground_truth_ki_v7_complete.csv)')
    parser.add_argument('--auto-approve', '-a', type=float, default=0.90,
                       help='Auto-approve threshold (0.0-1.0, default 0.90)')

    args = parser.parse_args()

    # Validate threshold
    if not 0.0 <= args.auto_approve <= 1.0:
        print("❌ Error: --auto-approve must be between 0.0 and 1.0")
        sys.exit(1)

    # Run completion
    complete_annotations(args.input, args.output, args.auto_approve)


if __name__ == '__main__':
    main()
