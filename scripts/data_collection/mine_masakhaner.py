#!/usr/bin/env python3
"""
Mine MasakhaNER Swahili dataset for occupational terms and gender contexts

MasakhaNER format (BIO tagging):
- B-PER / I-PER: Person entities
- B-ORG / I-ORG: Organization entities
- B-LOC / I-LOC: Location entities
- B-DATE / I-DATE: Date entities
- O: Outside any entity

This script extracts sentences containing PER entities and analyzes surrounding
context for occupational terms (m-wa class nouns indicating professions).
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple


class MasakhaNERMiner:
    """Mines MasakhaNER Swahili data for occupational terms"""

    # M-wa class prefixes for people/professions
    M_WA_PREFIXES = ['m', 'mw', 'mu']
    WA_PREFIXES = ['wa']

    # Known occupation seeds to validate
    OCCUPATION_SEEDS = [
        'daktari', 'mwalimu', 'mhandisi', 'muuguzi', 'karani',
        'mkulima', 'mfanyabiashara', 'polisi', 'askari',
        'mwanasheria', 'mwanaharakati', 'mwandishi', 'mchoraji',
        'dereva', 'seremala', 'fundi', 'waziri', 'rais',
        'mbunge', 'mhadhiri', 'profesa', 'mwuguzi', 'mwalimu',
        'tajiri', 'maskini', 'meneja', 'mkurugenzi'
    ]

    def __init__(self, data_file: str):
        self.data_file = Path(data_file)
        self.sentences = []
        self.occupation_terms = Counter()
        self.person_contexts = []

    def load_bio_format(self):
        """Load BIO-tagged data and extract sentences"""
        print(f"📂 Loading {self.data_file.name}...")

        current_sentence = []
        current_tags = []

        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:  # Empty line = sentence boundary
                    if current_sentence:
                        self.sentences.append({
                            'tokens': current_sentence,
                            'tags': current_tags,
                            'text': ' '.join(current_sentence)
                        })
                        current_sentence = []
                        current_tags = []
                else:
                    parts = line.split()
                    if len(parts) == 2:
                        token, tag = parts
                        current_sentence.append(token)
                        current_tags.append(tag)

        print(f"  Loaded {len(self.sentences)} sentences")

    def extract_m_wa_nouns(self, tokens: List[str]) -> List[str]:
        """Extract m-wa class nouns (professions)"""
        candidates = []

        for token in tokens:
            token_lower = token.lower()
            # Check m-wa prefix and minimum length
            if any(token_lower.startswith(prefix) for prefix in self.M_WA_PREFIXES):
                if len(token_lower) >= 4:  # Avoid short words like "m", "mu"
                    candidates.append(token_lower)

        return candidates

    def has_person_entity(self, tags: List[str]) -> bool:
        """Check if sentence contains PER entity"""
        return any('PER' in tag for tag in tags)

    def extract_person_contexts(self):
        """Extract sentences with PER entities and analyze occupation context"""
        print("\n🔍 Extracting person contexts...")

        for sent in self.sentences:
            if self.has_person_entity(sent['tags']):
                # Extract m-wa class nouns
                m_wa_nouns = self.extract_m_wa_nouns(sent['tokens'])

                # Check for known occupation seeds
                tokens_lower = [t.lower() for t in sent['tokens']]
                found_occupations = []

                for occ in self.OCCUPATION_SEEDS:
                    if occ in tokens_lower:
                        found_occupations.append(occ)
                        self.occupation_terms[occ] += 1

                # Track new candidates from m-wa nouns
                for noun in m_wa_nouns:
                    if noun not in self.OCCUPATION_SEEDS:
                        self.occupation_terms[noun] += 1

                if found_occupations or m_wa_nouns:
                    self.person_contexts.append({
                        'text': sent['text'],
                        'occupations': found_occupations,
                        'm_wa_nouns': m_wa_nouns
                    })

        print(f"  Found {len(self.person_contexts)} sentences with PER + occupation terms")
        print(f"  Total occupation candidates: {len(self.occupation_terms)}")

    def analyze_occupations(self):
        """Analyze and report occupation terms"""
        print("\n📊 Occupation term analysis:")
        print(f"  Total unique terms: {len(self.occupation_terms)}")
        print(f"  Total occurrences: {sum(self.occupation_terms.values())}")

        # Separate known vs new
        known = {k: v for k, v in self.occupation_terms.items() if k in self.OCCUPATION_SEEDS}
        new = {k: v for k, v in self.occupation_terms.items() if k not in self.OCCUPATION_SEEDS}

        print(f"\n  Known occupation terms: {len(known)}")
        print("  Top 10 known:")
        for term, count in sorted(known.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {term:20s} (n={count})")

        print(f"\n  New candidate terms: {len(new)}")
        print("  Top 20 new candidates:")
        for term, count in sorted(new.items(), key=lambda x: x[1], reverse=True)[:20]:
            status = "✓ Likely occupation" if count >= 3 else "? Needs validation"
            print(f"    {term:20s} (n={count:3d})  {status}")

    def generate_candidates_csv(self, output_file: str, min_frequency: int = 2):
        """Generate CSV of occupation candidates"""
        print(f"\n💾 Generating candidates CSV (min frequency: {min_frequency})...")

        candidates = []
        for term, count in self.occupation_terms.most_common():
            if count >= min_frequency:
                # Determine if known or new
                is_known = term in self.OCCUPATION_SEEDS
                validation_status = "known" if is_known else "needs_validation"

                candidates.append({
                    'term': term,
                    'frequency': count,
                    'source': 'masakhaner',
                    'validation_status': validation_status,
                    'category': 'occupation',
                    'notes': f'Extracted from MasakhaNER Swahili (PER contexts)'
                })

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['term', 'frequency', 'source', 'validation_status', 'category', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

        print(f"  Saved {len(candidates)} candidates to {output_path}")

    def generate_example_sentences(self, output_file: str, max_examples: int = 50):
        """Generate example sentences for annotation"""
        print(f"\n💾 Generating example sentences (max: {max_examples})...")

        examples = []
        for i, ctx in enumerate(self.person_contexts[:max_examples]):
            examples.append({
                'id': f'MASAKA-SW-{i+1:04d}',
                'text': ctx['text'],
                'occupations_found': ', '.join(ctx['occupations']) if ctx['occupations'] else '',
                'm_wa_candidates': ', '.join(ctx['m_wa_nouns']) if ctx['m_wa_nouns'] else '',
                'source': 'masakhaner_swa',
                'has_person_entity': 'true',
                'annotation_status': 'needs_review'
            })

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'text', 'occupations_found', 'm_wa_candidates',
                         'source', 'has_person_entity', 'annotation_status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(examples)

        print(f"  Saved {len(examples)} example sentences to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Mine MasakhaNER Swahili dataset for occupational terms"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw/masakhaner_swa_train.txt',
        help="Input MasakhaNER BIO file"
    )
    parser.add_argument(
        '--output-candidates',
        type=str,
        default='data/analysis/masakhaner_occupation_candidates.csv',
        help="Output CSV for occupation candidates"
    )
    parser.add_argument(
        '--output-examples',
        type=str,
        default='data/analysis/masakhaner_example_sentences.csv',
        help="Output CSV for example sentences"
    )
    parser.add_argument(
        '--min-frequency',
        type=int,
        default=2,
        help="Minimum frequency for candidates (default: 2)"
    )
    parser.add_argument(
        '--max-examples',
        type=int,
        default=50,
        help="Maximum example sentences to export (default: 50)"
    )

    args = parser.parse_args()

    print("="*60)
    print("🔬 MASAKHANER SWAHILI OCCUPATION MINER")
    print("="*60)

    miner = MasakhaNERMiner(args.input)
    miner.load_bio_format()
    miner.extract_person_contexts()
    miner.analyze_occupations()
    miner.generate_candidates_csv(args.output_candidates, min_frequency=args.min_frequency)
    miner.generate_example_sentences(args.output_examples, max_examples=args.max_examples)

    print("\n" + "="*60)
    print("✅ Mining complete!")
    print("="*60)


if __name__ == "__main__":
    main()
