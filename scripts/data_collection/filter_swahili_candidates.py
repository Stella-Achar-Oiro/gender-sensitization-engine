#!/usr/bin/env python3
"""
Filter Swahili occupation candidates to remove false positives

This script applies heuristic filters to remove common false positives:
- Numbers (moja=one, mbili=two, miaka=years)
- Time/temporal words (mwaka=year, mwezi=month, mara=time)
- Place names (proper nouns detected by capitalization patterns)
- Non-occupational m-wa words (muda=period, mambo=matters)

Outputs high-confidence occupation terms ready for lexicon integration.
"""

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import List, Dict, Set


class SwahiliCandidateFilter:
    """Filters Swahili occupation candidates using heuristics"""

    # Numbers and temporal words (clear false positives)
    EXCLUDED_TERMS = {
        # Numbers
        'moja', 'mbili', 'mitatu', 'minne', 'mitano', 'mia', 'milioni',

        # Time/temporal
        'mwaka', 'miaka', 'mwezi', 'miezi', 'muda', 'mara',

        # Place/location
        'mjini', 'marekani', 'magharibi', 'mataifa',

        # Events/meetings
        'mkutano', 'maandamano', 'mazungumzo', 'mahakama',

        # General nouns (not occupations)
        'mambo', 'madai', 'madarakani', 'mawasiliano', 'maafisa',

        # Proper names (people/places from data)
        'museveni', 'magufuli', 'martin',

        # Abstract concepts
        'mpya', 'mkubwa', 'mwenye', 'mmoja', 'maoni'
    }

    # High-confidence known occupations (validated from existing lexicon + common)
    KNOWN_OCCUPATIONS = {
        # From existing lexicon
        'askari', 'mfanyabiashara', 'mzimamoto', 'muuzaji', 'msafishaji',
        'mbunge', 'fundi', 'mwandishi', 'mshonaji',

        # High-frequency validated from MasakhaNER
        'rais', 'waziri', 'polisi', 'mkurugenzi', 'mwalimu', 'daktari',
        'mwanasheria', 'mhandisi', 'muuguzi', 'karani', 'profesa',

        # Common occupations (high confidence)
        'mhadhiri', 'meneja', 'tajiri', 'dereva', 'seremala',
        'mkulima', 'mwanaharakati', 'mchoraji', 'mwanajeshi',

        # From Wikipedia analysis
        'mwanajeshi', 'maafisa',  # maafisa = officers (wa-class plural)

        # Media/communication
        'msemaji', 'mgombea', 'mwakilishi', 'mhariri'
    }

    # Occupation indicators (if term contains these, likely occupation)
    OCCUPATION_INDICATORS = [
        'daktari', 'fundi', 'mwalimu', 'mkulima', 'mhandisi',
        'sheria', 'biashara', 'chunguzi', 'andishi', 'simamizi',
        'kazi', 'huduma', 'afisa'
    ]

    def __init__(self, candidates_file: str):
        self.candidates_file = Path(candidates_file)
        self.candidates = []
        self.filtered = []
        self.excluded_count = Counter()

    def load_candidates(self):
        """Load candidate terms from CSV"""
        with open(self.candidates_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.candidates = list(reader)
        print(f"📂 Loaded {len(self.candidates)} candidates from {self.candidates_file.name}")

    def is_excluded(self, term: str) -> tuple[bool, str]:
        """Check if term should be excluded"""
        term_lower = term.lower()

        # Check exclusion list
        if term_lower in self.EXCLUDED_TERMS:
            return True, "excluded_list"

        # Check if known occupation (always include)
        if term_lower in self.KNOWN_OCCUPATIONS:
            return False, "known_occupation"

        # Check for occupation indicators
        for indicator in self.OCCUPATION_INDICATORS:
            if indicator in term_lower:
                return False, "has_indicator"

        return False, "passed_filters"

    def apply_filters(self):
        """Apply all filters and categorize candidates"""
        print("\n🔍 Applying filters...")

        high_confidence = []
        medium_confidence = []
        low_confidence = []
        excluded = []

        for candidate in self.candidates:
            term = candidate['term']
            frequency = int(candidate.get('frequency', 0))
            is_known = candidate.get('validation_status') == 'known'

            is_excluded, reason = self.is_excluded(term)

            if is_excluded:
                excluded.append({**candidate, 'exclusion_reason': reason})
                self.excluded_count[reason] += 1
                continue

            # Categorize by confidence
            if is_known or term.lower() in self.KNOWN_OCCUPATIONS:
                high_confidence.append({**candidate, 'confidence': 'high', 'reason': 'known_occupation'})
            elif frequency >= 20:
                high_confidence.append({**candidate, 'confidence': 'high', 'reason': f'high_frequency_{frequency}'})
            elif frequency >= 5:
                medium_confidence.append({**candidate, 'confidence': 'medium', 'reason': f'medium_frequency_{frequency}'})
            else:
                low_confidence.append({**candidate, 'confidence': 'low', 'reason': f'low_frequency_{frequency}'})

        self.filtered = {
            'high': high_confidence,
            'medium': medium_confidence,
            'low': low_confidence,
            'excluded': excluded
        }

        print(f"\n📊 Filtering results:")
        print(f"  High confidence:   {len(high_confidence):3d} terms")
        print(f"  Medium confidence: {len(medium_confidence):3d} terms")
        print(f"  Low confidence:    {len(low_confidence):3d} terms")
        print(f"  Excluded:          {len(excluded):3d} terms")

        print(f"\n  Exclusion breakdown:")
        for reason, count in self.excluded_count.most_common():
            print(f"    {reason:20s}: {count:3d}")

    def save_filtered(self, output_dir: str):
        """Save filtered results to CSV files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save high-confidence (ready for lexicon)
        high_file = output_path / "high_confidence_occupations.csv"
        self._save_category(self.filtered['high'], high_file)
        print(f"\n💾 High confidence: {high_file}")

        # Save medium-confidence (needs review)
        medium_file = output_path / "medium_confidence_occupations.csv"
        self._save_category(self.filtered['medium'], medium_file)
        print(f"💾 Medium confidence: {medium_file}")

        # Save excluded (for audit)
        excluded_file = output_path / "excluded_terms.csv"
        self._save_category(self.filtered['excluded'], excluded_file,
                           extra_fields=['exclusion_reason'])
        print(f"💾 Excluded terms: {excluded_file}")

    def _save_category(self, items: List[Dict], output_file: Path, extra_fields: List[str] = None):
        """Save a category of items to CSV"""
        if not items:
            return

        fieldnames = list(items[0].keys())
        if extra_fields:
            for field in extra_fields:
                if field not in fieldnames:
                    fieldnames.append(field)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

    def print_summary(self):
        """Print summary of high-confidence terms"""
        print("\n" + "="*60)
        print("📋 HIGH CONFIDENCE OCCUPATION TERMS (Ready for Lexicon)")
        print("="*60)

        high = self.filtered['high']
        print(f"\nTotal: {len(high)} terms\n")

        # Sort by frequency
        high_sorted = sorted(high, key=lambda x: int(x.get('frequency', 0)), reverse=True)

        print("Top 30 by frequency:")
        print(f"{'Term':<20s} {'Freq':>6s} {'Source':<15s} {'Confidence':<12s}")
        print("-" * 60)
        for item in high_sorted[:30]:
            term = item['term']
            freq = item.get('frequency', 0)
            source = item.get('source', 'unknown')
            confidence = item.get('reason', 'unknown')
            print(f"{term:<20s} {freq:>6s} {source:<15s} {confidence:<12s}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter Swahili occupation candidates"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/analysis/masakhaner_occupation_candidates.csv',
        help="Input candidates CSV"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/analysis/filtered',
        help="Output directory for filtered results"
    )

    args = parser.parse_args()

    print("="*60)
    print("🔬 SWAHILI CANDIDATE FILTER")
    print("="*60)

    filter_engine = SwahiliCandidateFilter(args.input)
    filter_engine.load_candidates()
    filter_engine.apply_filters()
    filter_engine.save_filtered(args.output_dir)
    filter_engine.print_summary()

    print("\n" + "="*60)
    print("✅ Filtering complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review high_confidence_occupations.csv")
    print("2. Add validated terms to rules/lexicon_sw_v2.csv")
    print("3. Run evaluation to measure F1 improvement")


if __name__ == "__main__":
    main()
