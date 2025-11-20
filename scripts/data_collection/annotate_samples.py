#!/usr/bin/env python3
"""
Terminal-based Annotation Interface for Bias Detection Samples

This script provides an interactive terminal interface for annotating
gender bias samples with required fields.

Usage:
    python scripts/data_collection/annotate_samples.py --input data/clean/samples.csv --annotator alice
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AnnotationInterface:
    """Terminal-based annotation interface"""

    # Valid values for each annotation field
    VALID_VALUES = {
        'target_gender': ['male', 'female', 'neutral', 'both', 'unknown'],
        'bias_label': ['stereotype', 'counter-stereotype', 'neutral', 'toxic', 'slur'],
        'stereotype_category': [
            'profession', 'appearance', 'ability', 'personality',
            'role', 'behavior', 'emotion', 'other'
        ],
        'explicitness': ['explicit', 'implicit', 'unmarked'],
        'bias_severity': ['low', 'medium', 'high'],
        'sentiment_toward_referent': ['positive', 'negative', 'neutral'],
    }

    def __init__(self, annotator_id: str):
        self.annotator_id = annotator_id
        self.stats = {
            'samples_annotated': 0,
            'samples_skipped': 0,
            'session_start': datetime.now(),
        }

    def display_sample(self, sample: Dict, sample_num: int, total: int):
        """Display a sample for annotation"""
        print("\n" + "="*60)
        print(f"SAMPLE {sample_num}/{total}")
        print("="*60)
        print(f"ID:       {sample.get('id', 'N/A')}")
        print(f"Language: {sample.get('language', 'N/A')}")
        print(f"Source:   {sample.get('source_ref', 'N/A')[:60]}...")
        print()
        print(f"TEXT: {sample.get('text', 'N/A')}")
        print()
        print(f"Domain:   {sample.get('domain', 'N/A')}")
        print(f"Topic:    {sample.get('topic', 'N/A')}")
        print("="*60)

    def prompt_choice(self, field_name: str, valid_choices: List[str], current_value: str = '') -> str:
        """Prompt user to select from valid choices"""
        print(f"\n{field_name.upper().replace('_', ' ')}:")

        # Show current value if exists
        if current_value and current_value not in ['NEEDS_ANNOTATION', '']:
            print(f"  Current: {current_value}")

        # Show options
        for i, choice in enumerate(valid_choices, 1):
            print(f"  {i}. {choice}")
        print(f"  s. Skip (keep current)")
        print(f"  q. Quit annotation session")

        while True:
            response = input(f"\nSelect (1-{len(valid_choices)}, s, q): ").strip().lower()

            if response == 'q':
                return 'QUIT'
            if response == 's':
                return current_value if current_value else 'NEEDS_ANNOTATION'

            try:
                choice_idx = int(response) - 1
                if 0 <= choice_idx < len(valid_choices):
                    return valid_choices[choice_idx]
                else:
                    print(f"  ⚠️  Please enter a number between 1 and {len(valid_choices)}")
            except ValueError:
                print(f"  ⚠️  Invalid input. Please enter a number, 's', or 'q'")

    def annotate_sample(self, sample: Dict) -> Dict:
        """Annotate a single sample"""
        # Check if already annotated by this annotator
        if sample.get('annotator_id') == self.annotator_id:
            print("\n⚠️  This sample was already annotated by you. Re-annotating...")

        # Annotate required fields
        annotations = {}

        # Target Gender
        annotations['target_gender'] = self.prompt_choice(
            'target_gender',
            self.VALID_VALUES['target_gender'],
            sample.get('target_gender', '')
        )
        if annotations['target_gender'] == 'QUIT':
            return {'action': 'QUIT'}

        # Bias Label
        annotations['bias_label'] = self.prompt_choice(
            'bias_label',
            self.VALID_VALUES['bias_label'],
            sample.get('bias_label', '')
        )
        if annotations['bias_label'] == 'QUIT':
            return {'action': 'QUIT'}

        # Stereotype Category (only if biased)
        if annotations['bias_label'] in ['stereotype', 'counter-stereotype']:
            annotations['stereotype_category'] = self.prompt_choice(
                'stereotype_category',
                self.VALID_VALUES['stereotype_category'],
                sample.get('stereotype_category', '')
            )
            if annotations['stereotype_category'] == 'QUIT':
                return {'action': 'QUIT'}
        else:
            annotations['stereotype_category'] = 'N/A'

        # Explicitness
        annotations['explicitness'] = self.prompt_choice(
            'explicitness',
            self.VALID_VALUES['explicitness'],
            sample.get('explicitness', '')
        )
        if annotations['explicitness'] == 'QUIT':
            return {'action': 'QUIT'}

        # Bias Severity (only if biased)
        if annotations['bias_label'] in ['stereotype', 'toxic', 'slur']:
            annotations['bias_severity'] = self.prompt_choice(
                'bias_severity',
                self.VALID_VALUES['bias_severity'],
                sample.get('bias_severity', '')
            )
            if annotations['bias_severity'] == 'QUIT':
                return {'action': 'QUIT'}
        else:
            annotations['bias_severity'] = ''

        # Sentiment
        annotations['sentiment_toward_referent'] = self.prompt_choice(
            'sentiment_toward_referent',
            self.VALID_VALUES['sentiment_toward_referent'],
            sample.get('sentiment_toward_referent', '')
        )
        if annotations['sentiment_toward_referent'] == 'QUIT':
            return {'action': 'QUIT'}

        # Add metadata
        annotations['annotator_id'] = self.annotator_id
        annotations['qa_status'] = 'annotated'

        return annotations

    def process_file(self, input_file: Path, start_from: int = 1):
        """Process a CSV file for annotation"""
        print(f"\n📝 Loading: {input_file.name}")

        if not input_file.exists():
            print(f"  ❌ File not found: {input_file}")
            return

        # Read all samples
        samples = []
        fieldnames = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            samples = list(reader)

        total_samples = len(samples)
        print(f"  ✅ Loaded {total_samples} samples")

        if start_from > total_samples:
            print(f"  ⚠️  Start position {start_from} exceeds total samples")
            return

        print(f"\n🎯 Starting annotation from sample {start_from}")
        print("  Commands: Enter number to select, 's' to skip, 'q' to quit")

        # Annotate samples
        current_idx = start_from - 1
        while current_idx < total_samples:
            sample = samples[current_idx]

            # Display sample
            self.display_sample(sample, current_idx + 1, total_samples)

            # Get annotations
            annotations = self.annotate_sample(sample)

            if annotations.get('action') == 'QUIT':
                print("\n⏸️  Quitting annotation session...")
                break

            # Update sample with annotations
            sample.update(annotations)
            self.stats['samples_annotated'] += 1

            # Show progress
            progress = (self.stats['samples_annotated'] / total_samples) * 100
            print(f"\n✅ Sample annotated! Progress: {progress:.1f}%")

            current_idx += 1

        # Save annotated data
        output_file = input_file.parent / f"{input_file.stem}_annotated.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(samples)

        print(f"\n💾 Saved annotated data to: {output_file}")
        self.print_stats(total_samples)

    def print_stats(self, total: int):
        """Print annotation statistics"""
        duration = datetime.now() - self.stats['session_start']
        duration_mins = duration.total_seconds() / 60

        print("\n" + "="*60)
        print("📊 ANNOTATION SESSION STATISTICS")
        print("="*60)
        print(f"  Annotator ID:         {self.annotator_id}")
        print(f"  Samples annotated:    {self.stats['samples_annotated']}")
        print(f"  Total samples:        {total}")
        print(f"  Completion:           {(self.stats['samples_annotated']/total)*100:.1f}%")
        print(f"  Session duration:     {duration_mins:.1f} minutes")

        if self.stats['samples_annotated'] > 0:
            avg_time = duration_mins / self.stats['samples_annotated']
            print(f"  Avg time per sample:  {avg_time:.1f} minutes")

        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Terminal-based annotation interface for bias detection samples"
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help="Input CSV file to annotate"
    )
    parser.add_argument(
        '--annotator',
        type=str,
        required=True,
        help="Annotator ID (e.g., 'alice', 'bob')"
    )
    parser.add_argument(
        '--start-from',
        type=int,
        default=1,
        help="Start annotation from sample number (default: 1)"
    )

    args = parser.parse_args()

    print("="*60)
    print("📝 ANNOTATION INTERFACE")
    print("="*60)
    print(f"File:      {args.input}")
    print(f"Annotator: {args.annotator}")
    print(f"Start:     Sample #{args.start_from}")
    print("="*60)

    interface = AnnotationInterface(annotator_id=args.annotator)
    input_file = Path(args.input)

    interface.process_file(input_file, start_from=args.start_from)

    print("\n✅ Annotation session complete!")
    print("\nNext steps:")
    print("1. Review annotated samples for quality")
    print("2. Calculate Cohen's Kappa if double annotation")
    print("3. Merge annotations from multiple annotators")


if __name__ == "__main__":
    main()
