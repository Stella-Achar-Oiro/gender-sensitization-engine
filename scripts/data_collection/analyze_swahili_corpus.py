#!/usr/bin/env python3
"""
Analyze Swahili corpus for potential gender bias terms

This script analyzes the collected Swahili Wikipedia corpus to extract:
1. Occupational terms (profession, roles)
2. Gender-marked words (wanawake, wanaume)
3. Context patterns that suggest bias

Outputs candidate terms for lexicon expansion.
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SwahiliCorpusAnalyzer:
    """Analyzes Swahili text for gender bias patterns"""

    # Known Swahili occupational terms (seed list)
    OCCUPATION_SEEDS = [
        'daktari', 'mwalimu', 'mhandisi', 'muuguzi', 'karani',
        'mkulima', 'mfanyabiashara', 'mwana', 'polisi', 'askari',
        'mwanasheria', 'mwanaharakati', 'mwandishi', 'mchoraji',
        'dereva', 'seremala', 'fundi', 'tajiri', 'maskini'
    ]

    # Gender markers
    GENDER_MARKERS = {
        'female': ['wanawake', 'mwanamke', 'mama', 'dada', 'binti', 'bibi'],
        'male': ['wanaume', 'mwanamume', 'baba', 'kaka', 'mvulana', 'bwana'],
        'neutral': ['yeye', 'mtu', 'watu', 'mwenzangu', 'rafiki']
    }

    # Swahili noun class prefixes (m-wa class for people)
    M_WA_PREFIXES = ['m', 'mw', 'mu']  # singular
    WA_PREFIXES = ['wa']  # plural

    def __init__(self, corpus_file: str):
        self.corpus_file = Path(corpus_file)
        self.samples = []
        self.occupation_candidates = Counter()
        self.gender_associations = {}
        self.context_patterns = []

    def load_corpus(self):
        """Load CSV corpus"""
        with open(self.corpus_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.samples = list(reader)
        print(f"📂 Loaded {len(self.samples)} samples from {self.corpus_file.name}")

    def extract_nouns_with_m_wa_class(self, text: str) -> List[str]:
        """Extract nouns that use m-wa class (typically people/professions)"""
        words = text.lower().split()
        candidates = []

        for word in words:
            # Check if word starts with m-wa prefix
            if any(word.startswith(prefix) for prefix in self.M_WA_PREFIXES):
                # Minimum length filter (avoid 'm' alone)
                if len(word) >= 4:
                    candidates.append(word)

        return candidates

    def detect_gender_context(self, text: str) -> Tuple[str, List[str]]:
        """
        Detect gender context of a sentence

        Returns:
            (gender_type, markers_found)
            gender_type: 'male', 'female', 'neutral', 'mixed'
        """
        text_lower = text.lower()
        markers_found = []

        has_female = False
        has_male = False

        for marker in self.GENDER_MARKERS['female']:
            if marker in text_lower:
                has_female = True
                markers_found.append(('female', marker))

        for marker in self.GENDER_MARKERS['male']:
            if marker in text_lower:
                has_male = True
                markers_found.append(('male', marker))

        for marker in self.GENDER_MARKERS['neutral']:
            if marker in text_lower:
                markers_found.append(('neutral', marker))

        if has_female and has_male:
            return 'mixed', markers_found
        elif has_female:
            return 'female', markers_found
        elif has_male:
            return 'male', markers_found
        else:
            return 'neutral', markers_found

    def analyze_occupational_terms(self):
        """Extract and analyze occupational terms from corpus"""
        print("\n🔍 Analyzing occupational terms...")

        occupation_contexts = {}

        for sample in self.samples:
            text = sample.get('text', '')
            words = text.lower().split()

            # Extract m-wa class nouns
            m_wa_nouns = self.extract_nouns_with_m_wa_class(text)

            # Check for known occupation seeds
            for word in words:
                if word in self.OCCUPATION_SEEDS:
                    self.occupation_candidates[word] += 1

                    # Track gender context
                    gender_type, markers = self.detect_gender_context(text)
                    if word not in occupation_contexts:
                        occupation_contexts[word] = Counter()
                    occupation_contexts[word][gender_type] += 1

            # Track new m-wa candidates
            for noun in m_wa_nouns:
                if noun not in self.OCCUPATION_SEEDS:
                    self.occupation_candidates[noun] += 1

        # Analyze gender bias in occupational terms
        print(f"\n📊 Found {len(self.occupation_candidates)} occupation candidates")
        print("\nTop 20 occupational terms:")
        for term, count in self.occupation_candidates.most_common(20):
            contexts = occupation_contexts.get(term, Counter())
            print(f"  {term:20s} (n={count:2d})  "
                  f"Female: {contexts['female']}, "
                  f"Male: {contexts['male']}, "
                  f"Mixed: {contexts['mixed']}, "
                  f"Neutral: {contexts['neutral']}")

    def analyze_gender_patterns(self):
        """Analyze gender marker patterns"""
        print("\n🔍 Analyzing gender marker patterns...")

        gender_counts = Counter()
        gendered_samples = []

        for sample in self.samples:
            text = sample.get('text', '')
            gender_type, markers = self.detect_gender_context(text)

            if gender_type != 'neutral':
                gender_counts[gender_type] += 1
                gendered_samples.append({
                    'text': text,
                    'gender_type': gender_type,
                    'markers': markers
                })

        print(f"\n📊 Gender distribution:")
        print(f"  Female-marked: {gender_counts['female']}")
        print(f"  Male-marked: {gender_counts['male']}")
        print(f"  Mixed: {gender_counts['mixed']}")
        print(f"  Neutral: {len(self.samples) - sum(gender_counts.values())}")

        # Show examples
        print(f"\n📝 Sample gendered sentences:")
        for sample in gendered_samples[:5]:
            print(f"  [{sample['gender_type']}] {sample['text'][:80]}...")
            print(f"    Markers: {[m[1] for m in sample['markers']]}")

    def extract_bias_patterns(self):
        """Extract potential bias patterns"""
        print("\n🔍 Extracting bias patterns...")

        bias_patterns = []

        for sample in self.samples:
            text = sample.get('text', '')
            text_lower = text.lower()

            # Pattern 1: "wanawake" + verb/role (women are expected to...)
            if 'wanawake' in text_lower:
                # Extract context (20 words after wanawake)
                words = text_lower.split()
                for i, word in enumerate(words):
                    if word == 'wanawake':
                        context = ' '.join(words[i:min(i+10, len(words))])
                        bias_patterns.append(('wanawake_context', context))

            # Pattern 2: "wanaume" + verb/role (men are expected to...)
            if 'wanaume' in text_lower:
                words = text_lower.split()
                for i, word in enumerate(words):
                    if word == 'wanaume':
                        context = ' '.join(words[i:min(i+10, len(words))])
                        bias_patterns.append(('wanaume_context', context))

            # Pattern 3: Role + gender assumption
            for occ in self.OCCUPATION_SEEDS:
                if occ in text_lower:
                    gender_type, _ = self.detect_gender_context(text)
                    if gender_type in ['male', 'female']:
                        bias_patterns.append((f'{occ}_gender_context', (text, gender_type)))

        print(f"\n📊 Found {len(bias_patterns)} potential bias patterns")

        # Show examples
        wanawake_patterns = [p[1] for p in bias_patterns if p[0] == 'wanawake_context']
        wanaume_patterns = [p[1] for p in bias_patterns if p[0] == 'wanaume_context']

        print(f"\n'Wanawake' contexts (n={len(wanawake_patterns)}):")
        for pattern in wanawake_patterns[:3]:
            print(f"  {pattern}")

        print(f"\n'Wanaume' contexts (n={len(wanaume_patterns)}):")
        for pattern in wanaume_patterns[:3]:
            print(f"  {pattern}")

    def generate_lexicon_candidates(self, output_file: str):
        """Generate candidate terms for lexicon expansion"""
        print(f"\n💾 Generating lexicon candidates...")

        candidates = []

        # Get top occupation terms with bias potential
        for term, count in self.occupation_candidates.most_common(50):
            # Filter: must appear at least twice and be reasonable length
            if count >= 2 and 4 <= len(term) <= 15:
                candidates.append({
                    'biased': term,
                    'neutral_primary': term,  # Swahili is naturally neutral
                    'severity': 'context_dependent',
                    'tags': 'occupation,needs_validation',
                    'notes': f'Extracted from Wikipedia corpus (n={count})',
                    'frequency': count
                })

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['biased', 'neutral_primary', 'severity', 'tags', 'notes', 'frequency']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

        print(f"  Saved {len(candidates)} candidates to {output_path}")

    def generate_report(self, output_file: str):
        """Generate analysis report"""
        print(f"\n📄 Generating analysis report...")

        report_lines = []
        report_lines.append("# Swahili Wikipedia Corpus Analysis Report")
        report_lines.append(f"\n**Generated**: {Path(__file__).name}")
        report_lines.append(f"**Corpus**: {self.corpus_file.name}")
        report_lines.append(f"**Samples**: {len(self.samples)}")

        report_lines.append("\n## Occupational Terms Found\n")
        report_lines.append("| Term | Frequency | Status |")
        report_lines.append("|------|-----------|--------|")
        for term, count in self.occupation_candidates.most_common(30):
            status = "Known" if term in self.OCCUPATION_SEEDS else "New candidate"
            report_lines.append(f"| {term} | {count} | {status} |")

        report_lines.append("\n## Next Steps\n")
        report_lines.append("1. Native speaker validation of candidate terms")
        report_lines.append("2. Context-based bias annotation")
        report_lines.append("3. Integration into lexicon_sw_v2.csv")
        report_lines.append("4. Ground truth dataset expansion")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"  Saved report to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Swahili corpus for gender bias patterns"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw/wikipedia_sw_raw.csv',
        help="Input corpus CSV file"
    )
    parser.add_argument(
        '--output-candidates',
        type=str,
        default='data/analysis/swahili_lexicon_candidates.csv',
        help="Output file for lexicon candidates"
    )
    parser.add_argument(
        '--output-report',
        type=str,
        default='data/analysis/swahili_corpus_analysis.md',
        help="Output file for analysis report"
    )

    args = parser.parse_args()

    print("="*60)
    print("🔬 SWAHILI CORPUS ANALYZER")
    print("="*60)

    analyzer = SwahiliCorpusAnalyzer(args.input)
    analyzer.load_corpus()
    analyzer.analyze_occupational_terms()
    analyzer.analyze_gender_patterns()
    analyzer.extract_bias_patterns()
    analyzer.generate_lexicon_candidates(args.output_candidates)
    analyzer.generate_report(args.output_report)

    print("\n" + "="*60)
    print("✅ Analysis complete!")
    print("="*60)


if __name__ == "__main__":
    main()
