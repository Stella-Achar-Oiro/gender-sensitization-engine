#!/usr/bin/env python3
"""
Generate WinoBias-style test templates for Swahili ground truth expansion.

This script creates systematic test cases combining:
- Occupation terms from lexicon
- Gender-neutral contexts (no pronouns, no gender markers)
- Pronoun assumption patterns
- Generic pronoun patterns
- Gender morphology patterns

Target: Expand ground_truth_sw.csv from 63 to 1,200+ samples for AI BRIDGE Bronze tier.
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict, Tuple


class SwahiliTestGenerator:
    """Generates systematic test cases for Swahili bias detection"""

    # Sentence templates for occupation + neutral context
    OCCUPATION_TEMPLATES = [
        "{occ} {verb} {object}",
        "Kila {occ} {verb} {object}",
        "{occ} wetu {verb} {object}",
        "Tunah itaji {occ} kwa {trait}",
        "{occ} aliyesajiliwa {verb} {object}",
        "Muulize {occ} kuhusu {topic}",
        "{occ} mpya {verb} {object}",
        "{occ} mzuri {verb} {object}",
        "{occ} hodari {verb} {object}",
        "{occ} mkuu {verb} {object}",
    ]

    # Verbs (tense-marked, third person)
    VERBS = [
        "alifanya",  # did
        "anafanya",  # does
        "atafanya",  # will do
        "alipokea",  # received
        "anapokea",  # receives
        "alisoma",  # read
        "alieleza",  # explained
        "aliwasilisha",  # submitted
        "aliandika",  # wrote
        "alisimamia",  # supervised
        "aliongoza",  # led
        "alisaidia",  # helped
        "alitengeneza",  # created
        "alitatua",  # solved
        "alijadili",  # discussed
    ]

    # Objects/complements
    OBJECTS = [
        "kazi",  # work
        "ripoti",  # report
        "mradi",  # project
        "tatizo",  # problem
        "mipango",  # plans
        "ukaguzi",  # inspection
        "uchunguzi",  # investigation
        "mashauriano",  # negotiations
        "mafunzo",  # training
        "uongozi",  # leadership
    ]

    # Traits for job requirements
    TRAITS = [
        "ujuzi",  # expertise
        "ustadi",  # skill
        "uzoefu",  # experience
        "uwezo",  # ability
        "uelewa",  # understanding
    ]

    # Topics for queries
    TOPICS = [
        "mswada",  # bill
        "sheria",  # law
        "sera",  # policy
        "mpango",  # plan
        "tatizo",  # problem
    ]

    # Pronoun assumption templates
    PRONOUN_TEMPLATES = [
        "Yeye ni {occ} {adj}",
        "yeye ni {occ} {adj}",
        "Yeye anafanya kazi ya {field}",
        "yeye anafanya kazi ya {field}",
        "Yeye ni mama wa nyumbani tu",
        "Yeye ni mama {adj} wa nyumbani",
    ]

    ADJECTIVES = ["mzuri", "hodari", "bora", "mkuu", "mpya"]
    FIELDS = ["uandishi", "uhasibu", "uongozi", "usimamizi", "utafiti"]

    # Generic pronoun templates (possessive agreement)
    POSSESSIVE_TEMPLATES = [
        "Kila {occ} anapaswa kusasisha rekodi {poss}",
        "Kila {occ} anajua wagonjwa {poss}",
        "Kila {occ} anapenda wanafunzi {poss}",
        "Kila {occ} anapaswa kuwasilisha kadi {poss}",
        "{occ} alimwita mshauri {poss}",
    ]

    # Gender morphology templates
    MORPHOLOGY_TEMPLATES = [
        "{occ} wa kike {verb} {object}",
        "{occ} wa kiume {verb} {object}",
    ]

    # Negative examples (no bias)
    NEGATIVE_TEMPLATES = [
        "{occ} alipima mgonjwa kwa uangalifu",
        "{occ} wetu alieleza dhana vizuri",
        "{occ} alibuni daraja jipya",
        "{occ} alitoa huduma nzuri",
        "{occ} aliruka ndege kwa usalama",
        "{occ} aliwasilisha hoja madhubuti",
    ]

    def __init__(self, lexicon_path: str):
        self.lexicon_path = Path(lexicon_path)
        self.occupations = []
        self.load_occupations()

    def load_occupations(self):
        """Load occupation terms from Swahili lexicon"""
        with open(self.lexicon_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('language') == 'sw' and 'occupation' in row.get('tags', ''):
                    biased = row['biased']
                    neutral = row.get('neutral_primary', biased)
                    # Use neutral form if available, otherwise use biased (for gender-neutral terms)
                    term = neutral if neutral else biased
                    self.occupations.append({
                        'term': term,
                        'biased': biased,
                        'neutral': neutral
                    })

        print(f"📂 Loaded {len(self.occupations)} occupation terms")

    def generate_occupation_tests(self) -> List[Dict]:
        """Generate occupation-based test cases (neutral contexts)"""
        tests = []

        for occ_data in self.occupations:
            occ = occ_data['term']

            # Generate multiple templates per occupation - USE ALL for 10K scale
            for template in self.OCCUPATION_TEMPLATES:  # All 10 templates
                for verb in self.VERBS:  # All 15 verbs
                    for obj in self.OBJECTS:  # All 10 objects
                        if '{verb}' in template and '{object}' in template:
                            text = template.format(occ=occ, verb=verb, object=obj)
                            tests.append({
                                'text': text,
                                'has_bias': 'false',
                                'bias_category': 'none',
                                'expected_correction': ''
                            })

                # Templates with traits
                if '{trait}' in template:
                    for trait in self.TRAITS:  # All 5 traits
                        text = template.format(occ=occ, trait=trait)
                        tests.append({
                            'text': text,
                            'has_bias': 'false',
                            'bias_category': 'none',
                            'expected_correction': ''
                        })

                # Templates with topics
                if '{topic}' in template:
                    for topic in self.TOPICS:  # All 5 topics
                        text = template.format(occ=occ, topic=topic)
                        tests.append({
                            'text': text,
                            'has_bias': 'false',
                            'bias_category': 'none',
                            'expected_correction': ''
                        })

        return tests

    def generate_pronoun_assumption_tests(self) -> List[Dict]:
        """Generate pronoun assumption test cases"""
        tests = []

        for occ_data in self.occupations:  # Use ALL occupations for 10K scale
            occ = occ_data['term']

            for template in self.PRONOUN_TEMPLATES:  # ALL templates
                if '{adj}' in template:
                    for adj in self.ADJECTIVES:  # ALL adjectives
                        text = template.format(occ=occ, adj=adj)
                        # Expected: remove "Yeye ni" → "Ni"
                        expected = text.replace("Yeye ni", "Ni").replace("yeye ni", "ni")
                        tests.append({
                            'text': text,
                            'has_bias': 'true',
                            'bias_category': 'pronoun_assumption',
                            'expected_correction': expected
                        })
                elif '{field}' in template:
                    for field in self.FIELDS:  # ALL fields
                        text = template.format(occ=occ, field=field)
                        expected = text.replace("Yeye anafanya", "Anafanya").replace("yeye anafanya", "anafanya")
                        tests.append({
                            'text': text,
                            'has_bias': 'true',
                            'bias_category': 'pronoun_assumption',
                            'expected_correction': expected
                        })
                else:
                    # Direct template (e.g., "Yeye ni mama wa nyumbani tu")
                    text = template
                    expected = text.replace("Yeye ni", "Ni").replace("yeye ni", "ni")
                    tests.append({
                        'text': text,
                        'has_bias': 'true',
                        'bias_category': 'pronoun_assumption',
                        'expected_correction': expected
                    })

        return tests

    def generate_generic_pronoun_tests(self) -> List[Dict]:
        """Generate generic pronoun test cases (possessive agreement)"""
        tests = []

        possessive_pairs = [
            ('zake', 'zao'),  # his/her → their (z- class)
            ('wake', 'wao'),  # his/her → their (w- class)
            ('yake', 'yao'),  # his/her → their (y- class)
        ]

        for occ_data in self.occupations:  # ALL occupations for 10K scale
            occ = occ_data['term']

            for template in self.POSSESSIVE_TEMPLATES:
                for biased_poss, neutral_poss in possessive_pairs:
                    if '{poss}' in template:
                        text = template.format(occ=occ, poss=biased_poss)
                        expected = neutral_poss
                        tests.append({
                            'text': text,
                            'has_bias': 'true',
                            'bias_category': 'pronoun_generic',
                            'expected_correction': expected
                        })

        return tests

    def generate_morphology_tests(self) -> List[Dict]:
        """Generate gender morphology test cases"""
        tests = []

        for occ_data in self.occupations:  # ALL occupations for 10K scale
            occ = occ_data['term']

            for template in self.MORPHOLOGY_TEMPLATES:
                for verb in self.VERBS:  # ALL verbs
                    for obj in self.OBJECTS:  # ALL objects
                        text = template.format(occ=occ, verb=verb, object=obj)
                        # Expected: remove "wa kike" or "wa kiume"
                        expected = occ
                        tests.append({
                            'text': text,
                            'has_bias': 'true',
                            'bias_category': 'morphology',
                            'expected_correction': expected
                        })

        return tests

    def generate_negative_tests(self) -> List[Dict]:
        """Generate negative test cases (no bias, natural usage)"""
        tests = []

        for occ_data in self.occupations:
            occ = occ_data['term']

            for template in self.NEGATIVE_TEMPLATES:  # ALL negative templates
                text = template.format(occ=occ)
                tests.append({
                    'text': text,
                    'has_bias': 'false',
                    'bias_category': 'none',
                    'expected_correction': ''
                })

        return tests

    def generate_all_tests(self) -> List[Dict]:
        """Generate all test cases"""
        print("\n🔧 Generating test cases...")

        all_tests = []

        # Occupation tests (neutral contexts)
        occupation_tests = self.generate_occupation_tests()
        all_tests.extend(occupation_tests)
        print(f"  ✅ Occupation tests: {len(occupation_tests)}")

        # Pronoun assumption tests
        pronoun_tests = self.generate_pronoun_assumption_tests()
        all_tests.extend(pronoun_tests)
        print(f"  ✅ Pronoun assumption tests: {len(pronoun_tests)}")

        # Generic pronoun tests
        generic_tests = self.generate_generic_pronoun_tests()
        all_tests.extend(generic_tests)
        print(f"  ✅ Generic pronoun tests: {len(generic_tests)}")

        # Morphology tests
        morphology_tests = self.generate_morphology_tests()
        all_tests.extend(morphology_tests)
        print(f"  ✅ Morphology tests: {len(morphology_tests)}")

        # Negative tests
        negative_tests = self.generate_negative_tests()
        all_tests.extend(negative_tests)
        print(f"  ✅ Negative tests: {len(negative_tests)}")

        print(f"\n📊 Total tests generated: {len(all_tests)}")

        return all_tests

    def save_tests(self, tests: List[Dict], output_path: str):
        """Save test cases to CSV"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['text', 'has_bias', 'bias_category', 'expected_correction']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tests)

        print(f"\n💾 Tests saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate WinoBias-style test templates for Swahili"
    )
    parser.add_argument(
        '--lexicon',
        type=str,
        default='rules/lexicon_sw_v2.csv',
        help="Path to Swahili lexicon CSV"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/swahili_test_templates.csv',
        help="Output path for generated tests"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🧪 SWAHILI TEST TEMPLATE GENERATOR")
    print("=" * 70)

    generator = SwahiliTestGenerator(args.lexicon)
    tests = generator.generate_all_tests()
    generator.save_tests(tests, args.output)

    print("\n" + "=" * 70)
    print("✅ Test generation complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review generated tests in data/analysis/swahili_test_templates.csv")
    print("2. Merge with existing ground_truth_sw.csv")
    print("3. Run evaluation: make eval")
    print("4. Target: 1,200+ samples for AI BRIDGE Bronze tier")


if __name__ == "__main__":
    main()
