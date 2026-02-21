#!/usr/bin/env python3
"""
AIBRIDGE Dataset Migration Tool
Converts ground_truth_ki.csv to AIBRIDGE-compliant format with automated annotation assistance.

Usage:
    python3 scripts/migrate_to_aibridge.py --input eval/ground_truth_ki.csv --output eval/ground_truth_ki_aibridge.csv
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class AIBRIDGEAnnotator:
    """Automated annotation assistant for AIBRIDGE compliance."""

    def __init__(self):
        # Kikuyu gender markers
        self.male_pronouns = {'we', 'ũcio'}  # he, that one (masc)
        self.female_pronouns = {'ĩyo'}  # that one (fem)
        self.male_terms = {'mũrũme', 'kĩhĩĩ', 'arũme', 'athuri'}  # man, boy, men, elders
        self.female_terms = {'mũtumia', 'mũirĩtu', 'andũ-a-nja', 'atumia'}  # woman, girl, women

        # Old to new category mapping
        self.category_mapping = {
            'occupation': 'profession',
            'pronoun_assumption': None,  # Context-dependent
            'pronoun_generic': None,  # Context-dependent
            'none': None,
        }

        # Device detection patterns
        self.device_patterns = {
            'scripture_quote': ['Bible verse', 'Genesis', 'Exodus', 'Scripture'],
            'proverb': ['thimo', 'mũikarĩre'],  # Kikuyu proverb markers
            'question': [r'\?$'],
            'directive': ['reka', 'tiga'],  # imperative markers
        }

        # Sentiment keywords
        self.positive_words = {'mwega', 'ega', 'nĩ wega', 'kĩega'}  # good
        self.negative_words = {'ũru', 'gũthũka', 'kĩũru'}  # bad, insult

    def detect_target_gender(self, text: str, current_gender: str, notes: str) -> str:
        """
        Detect target_gender from text analysis.

        Priority:
        1. Explicit pronouns (we, ĩyo)
        2. Explicit gender terms (mũrũme, mũtumia)
        3. Current annotation
        4. Default to neutral if ambiguous
        """
        text_lower = text.lower()

        # Check pronouns
        if any(p in text_lower for p in self.male_pronouns):
            return 'male'
        if any(p in text_lower for p in self.female_pronouns):
            return 'female'

        # Check explicit gender terms
        male_count = sum(1 for term in self.male_terms if term in text_lower)
        female_count = sum(1 for term in self.female_terms if term in text_lower)

        if male_count > 0 and female_count == 0:
            return 'male'
        if female_count > 0 and male_count == 0:
            return 'female'
        if male_count > 0 and female_count > 0:
            return 'mixed'

        # Fall back to current annotation
        return current_gender if current_gender else 'neutral'

    def detect_bias_label(self, has_bias: bool, bias_category: str, text: str,
                          target_gender: str, notes: str) -> str:
        """
        Detect bias_label: stereotype, counter-stereotype, neutral, derogation.

        Logic:
        - If no bias → neutral
        - Check for derogatory language → derogation
        - Check for counter-stereotypes (male caregiver, female leader) → counter-stereotype
        - Default → stereotype
        """
        if not has_bias or bias_category == 'none':
            return 'neutral'

        text_lower = text.lower()

        # Check for derogatory patterns
        if any(word in text_lower for word in self.negative_words):
            # If combined with gender prohibition (e.g., "women can't")
            if 'mati' in text_lower or 'ndũ' in text_lower:  # can't, shouldn't
                return 'derogation'

        # Check for counter-stereotypes
        # Male in caregiving/domestic
        if target_gender == 'male':
            if 'rera' in text_lower or 'ciana' in text_lower:  # caring for children
                return 'counter-stereotype'

        # Female in leadership/authority
        if target_gender == 'female':
            if 'mũtongoria' in text_lower or 'mũthaki' in text_lower:  # leader, administrator
                return 'counter-stereotype'

        # Default: reinforces traditional assumption
        return 'stereotype'

    def detect_stereotype_category(self, old_category: str, text: str,
                                    domain: str, notes: str) -> Optional[str]:
        """
        Map old bias_category to new stereotype_category.

        Categories: profession, family_role, leadership, education,
                   religion_culture, proverb_idiom, daily_life, appearance, capability
        """
        # Direct mapping
        if old_category == 'occupation':
            return 'profession'

        # Context-based detection
        text_lower = text.lower()

        # Religion/culture
        if domain in ['religious_text', 'culture_and_religion']:
            return 'religion_culture'

        # Occupation terms
        occupation_terms = ['mũthĩnjĩri', 'daktari', 'mũrutani', 'mũrĩmi', 'mũtongoria']
        if any(term in text_lower for term in occupation_terms):
            # But if it's a religious role, use religion_culture
            if 'mũthĩnjĩri' in text_lower:  # priest
                return 'religion_culture'
            return 'profession'

        # Family/caregiving
        family_terms = ['rera', 'ciana', 'nyũmba', 'mũciĩ']  # care for, children, house, home
        if any(term in text_lower for term in family_terms):
            return 'family_role'

        # Leadership
        leadership_terms = ['mũtongoria', 'mũthaki', 'mũigũ']  # leader, admin, judge
        if any(term in text_lower for term in leadership_terms):
            return 'leadership'

        # Proverb
        if 'thimo' in notes.lower() or 'proverb' in notes.lower():
            return 'proverb_idiom'

        # Default: return None (needs manual annotation)
        return None

    def detect_device(self, text: str, notes: str, domain: str) -> Optional[str]:
        """
        Detect literary device: scripture_quote, proverb, narrative, etc.
        """
        notes_lower = notes.lower()

        # Bible verses - CRITICAL
        if any(keyword in notes_lower for keyword in self.device_patterns['scripture_quote']):
            return 'scripture_quote'
        if domain == 'religious_text':
            return 'scripture_quote'

        # Proverbs
        if any(keyword in notes_lower for keyword in self.device_patterns['proverb']):
            return 'proverb'

        # Questions
        if text.strip().endswith('?'):
            return 'question'

        # Directives (commands)
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in self.device_patterns['directive']):
            return 'directive'

        # Default: narrative
        return 'narrative'

    def detect_sentiment(self, text: str, bias_label: str) -> str:
        """
        Detect sentiment: positive, neutral, negative.

        Based on tone toward the gendered referent.
        """
        if bias_label == 'derogation':
            return 'negative'

        text_lower = text.lower()

        # Positive indicators
        if any(word in text_lower for word in self.positive_words):
            return 'positive'

        # Negative indicators
        if any(word in text_lower for word in self.negative_words):
            return 'negative'

        # Default: neutral (factual description)
        return 'neutral'

    def detect_explicitness(self, text: str, current_value: str,
                           target_gender: str, bias_label: str) -> Optional[str]:
        """
        Detect explicitness: explicit or implicit.

        Explicit = pronouns, explicit gender markers
        Implicit = cultural assumption, proverb
        """
        if bias_label == 'neutral':
            return None  # Can be empty for neutral

        if current_value and current_value in ['explicit', 'implicit']:
            return current_value  # Keep existing annotation

        text_lower = text.lower()

        # Explicit: has pronouns
        if any(p in text_lower for p in self.male_pronouns | self.female_pronouns):
            return 'explicit'

        # Explicit: has gender terms
        if any(t in text_lower for t in self.male_terms | self.female_terms):
            return 'explicit'

        # Implicit: cultural assumption
        return 'implicit'


def migrate_row(row: Dict, annotator: AIBRIDGEAnnotator, row_num: int) -> Dict:
    """
    Migrate a single row to AIBRIDGE format.

    Adds 5 required fields:
    1. target_gender (rename from gender_referent)
    2. bias_label (new)
    3. stereotype_category (new, maps from bias_category)
    4. sentiment (new)
    5. device (new)

    Also adds safety_flag for religious content.
    """
    # Extract current values
    text = row.get('text', '')
    has_bias = row.get('has_bias', '').lower() == 'true'
    old_category = row.get('bias_category', '')
    current_gender = row.get('gender_referent', '')
    current_explicitness = row.get('explicitness', '')
    notes = row.get('notes', '')
    domain = row.get('domain', '')

    # Detect new fields
    target_gender = annotator.detect_target_gender(text, current_gender, notes)
    bias_label = annotator.detect_bias_label(has_bias, old_category, text, target_gender, notes)
    stereotype_category = annotator.detect_stereotype_category(old_category, text, domain, notes)
    device = annotator.detect_device(text, notes, domain)
    sentiment = annotator.detect_sentiment(text, bias_label)
    explicitness = annotator.detect_explicitness(text, current_explicitness, target_gender, bias_label)

    # Safety flag for religious content
    safety_flag = 'sensitive' if domain in ['religious_text', 'culture_and_religion'] else 'none'

    # Build new row
    new_row = {
        # Core identification
        'sample_id': row.get('sample_id', f'ki_{row_num:05d}'),
        'text': text,
        'language': row.get('language', 'ki'),

        # AIBRIDGE required fields (5 new + 1 renamed)
        'target_gender': target_gender,  # RENAMED from gender_referent
        'bias_label': bias_label,  # NEW
        'explicitness': explicitness if explicitness else '',
        'stereotype_category': stereotype_category if stereotype_category else '',  # NEW
        'sentiment': sentiment,  # NEW
        'device': device if device else '',  # NEW

        # Domain and safety
        'domain': domain,
        'safety_flag': safety_flag,  # NEW

        # Legacy fields (keep for backward compatibility)
        'has_bias': str(has_bias).lower(),
        'expected_correction': row.get('expected_correction', ''),

        # Metadata
        'annotator_id': row.get('annotator_id', 'ann_001'),
        'annotation_date': row.get('annotation_date', datetime.now().isoformat() + 'Z'),
        'annotation_confidence': row.get('annotation_confidence', '0.75'),
        'annotation_method': row.get('annotation_method', 'automated'),
        'notes': notes,

        # Fairness/demographic
        'demographic_group': row.get('demographic_group', ''),
        'gender_referent': current_gender,  # Keep old field for compatibility
        'protected_attribute': row.get('protected_attribute', 'gender'),
        'fairness_score': row.get('fairness_score', ''),

        # Classification details
        'severity': row.get('severity', ''),
        'bias_source': row.get('bias_source', 'original'),
        'context_requires_gender': row.get('context_requires_gender', ''),
        'bias_category': old_category,  # Keep old field as internal_bias_type

        # Provenance
        'validation_status': row.get('validation_status', 'needs_review'),
        'data_source': row.get('data_source', ''),
        'source_url': row.get('source_url', ''),
        'collection_date': row.get('collection_date', ''),
        'multi_annotator': row.get('multi_annotator', 'false'),
        'regional_variant': row.get('regional_variant', 'kenya'),
        'version': '7',  # AIBRIDGE-compliant version
    }

    return new_row


def migrate_dataset(input_path: str, output_path: str, sample_size: Optional[int] = None) -> Dict:
    """
    Migrate entire dataset to AIBRIDGE format.

    Args:
        input_path: Path to current CSV
        output_path: Path to new AIBRIDGE CSV
        sample_size: If set, only process first N rows (for testing)

    Returns:
        Statistics dictionary
    """
    annotator = AIBRIDGEAnnotator()

    stats = {
        'total_rows': 0,
        'migrated_rows': 0,
        'fields_added': ['target_gender', 'bias_label', 'stereotype_category', 'sentiment', 'device', 'safety_flag'],
        'bias_label_counts': {},
        'device_counts': {},
        'needs_manual_review': 0,
    }

    # New column order (AIBRIDGE fields first)
    output_columns = [
        'sample_id', 'text', 'language',
        # AIBRIDGE required
        'target_gender', 'bias_label', 'explicitness', 'stereotype_category', 'sentiment', 'device',
        # Domain
        'domain', 'safety_flag',
        # Legacy
        'has_bias', 'expected_correction',
        # Metadata
        'annotator_id', 'annotation_date', 'annotation_confidence', 'annotation_method', 'notes',
        # Demographic
        'demographic_group', 'gender_referent', 'protected_attribute', 'fairness_score',
        # Classification
        'severity', 'bias_source', 'context_requires_gender', 'bias_category',
        # Provenance
        'validation_status', 'data_source', 'source_url', 'collection_date',
        'multi_annotator', 'regional_variant', 'version'
    ]

    print(f"🔄 Starting migration: {input_path} → {output_path}")
    print(f"📊 Adding {len(stats['fields_added'])} new AIBRIDGE fields")
    print()

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=output_columns)
        writer.writeheader()

        for i, row in enumerate(reader, 1):
            stats['total_rows'] += 1

            # Sample size limit
            if sample_size and i > sample_size:
                print(f"⚠️  Reached sample limit ({sample_size}), stopping")
                break

            # Migrate row
            new_row = migrate_row(row, annotator, i)
            writer.writerow(new_row)
            stats['migrated_rows'] += 1

            # Track stats
            bias_label = new_row['bias_label']
            stats['bias_label_counts'][bias_label] = stats['bias_label_counts'].get(bias_label, 0) + 1

            device = new_row.get('device', '')
            if device:
                stats['device_counts'][device] = stats['device_counts'].get(device, 0) + 1

            # Flag for manual review if critical fields missing
            if not new_row.get('stereotype_category') and bias_label != 'neutral':
                stats['needs_manual_review'] += 1

            # Progress
            if i % 1000 == 0:
                print(f"  ✓ Processed {i:,} rows...")

    print()
    print(f"✅ Migration complete!")
    print(f"   Total rows: {stats['total_rows']:,}")
    print(f"   Migrated: {stats['migrated_rows']:,}")
    print(f"   Needs manual review: {stats['needs_manual_review']:,} ({stats['needs_manual_review']/stats['migrated_rows']*100:.1f}%)")
    print()
    print("📊 Bias Label Distribution:")
    for label, count in sorted(stats['bias_label_counts'].items()):
        pct = (count / stats['migrated_rows']) * 100
        print(f"   {label:20s}: {count:5,} ({pct:5.1f}%)")
    print()
    print("📖 Device Distribution:")
    for device, count in sorted(stats['device_counts'].items()):
        pct = (count / stats['migrated_rows']) * 100
        print(f"   {device:20s}: {count:5,} ({pct:5.1f}%)")

    return stats


def main():
    parser = argparse.ArgumentParser(description='Migrate dataset to AIBRIDGE format')
    parser.add_argument('--input', '-i', required=True, help='Input CSV path')
    parser.add_argument('--output', '-o', required=True, help='Output CSV path')
    parser.add_argument('--sample', '-n', type=int, help='Test on first N rows only')
    parser.add_argument('--stats-output', '-s', help='Save stats to JSON file')

    args = parser.parse_args()

    # Run migration
    stats = migrate_dataset(args.input, args.output, args.sample)

    # Save stats
    if args.stats_output:
        with open(args.stats_output, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\n📁 Stats saved to: {args.stats_output}")

    print(f"\n🎉 New AIBRIDGE-compliant dataset: {args.output}")
    print()
    print("⚠️  IMPORTANT: Review samples flagged 'needs_manual_review'")
    print("   Run: python3 scripts/review_annotations.py --input", args.output)


if __name__ == '__main__':
    main()
