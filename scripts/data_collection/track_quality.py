#!/usr/bin/env python3
"""
Quality Tracking Dashboard for Data Collection

This script tracks annotation quality, balance, and progress metrics including:
- Cohen's Kappa for inter-annotator agreement
- Data balance across categories
- Annotation progress
- Quality flags

Usage:
    python scripts/data_collection/track_quality.py --input data/clean/ --report quality_report.md
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class QualityTracker:
    """Track annotation quality and data balance"""

    def __init__(self):
        self.stats = {
            'total_samples': 0,
            'annotated_samples': 0,
            'needs_annotation': 0,
            'languages': Counter(),
            'bias_labels': Counter(),
            'target_genders': Counter(),
            'stereotype_categories': Counter(),
            'annotators': Counter(),
        }

    def calculate_cohens_kappa(self, annotations1: List[str], annotations2: List[str]) -> float:
        """
        Calculate Cohen's Kappa for inter-annotator agreement

        Args:
            annotations1: Labels from annotator 1
            annotations2: Labels from annotator 2

        Returns:
            Cohen's Kappa coefficient (-1 to 1)
        """
        if len(annotations1) != len(annotations2):
            raise ValueError("Annotation lists must be same length")

        n = len(annotations1)
        if n == 0:
            return 0.0

        # Calculate observed agreement
        agreements = sum(1 for a1, a2 in zip(annotations1, annotations2) if a1 == a2)
        p_observed = agreements / n

        # Calculate expected agreement by chance
        labels = set(annotations1 + annotations2)
        p_expected = 0.0

        for label in labels:
            p1 = annotations1.count(label) / n
            p2 = annotations2.count(label) / n
            p_expected += p1 * p2

        # Calculate Kappa
        if p_expected == 1.0:
            return 1.0  # Perfect agreement

        kappa = (p_observed - p_expected) / (1 - p_expected)
        return kappa

    def analyze_file(self, file_path: Path):
        """Analyze a single CSV file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['total_samples'] += 1

                # Track annotation status
                if row.get('qa_status') == 'annotated':
                    self.stats['annotated_samples'] += 1
                elif row.get('qa_status') == 'needs_review':
                    self.stats['needs_annotation'] += 1

                # Track distributions
                self.stats['languages'][row.get('language', 'unknown')] += 1
                self.stats['bias_labels'][row.get('bias_label', 'unknown')] += 1
                self.stats['target_genders'][row.get('target_gender', 'unknown')] += 1

                stereotype_cat = row.get('stereotype_category', '')
                if stereotype_cat and stereotype_cat != 'N/A':
                    self.stats['stereotype_categories'][stereotype_cat] += 1

                annotator = row.get('annotator_id', '')
                if annotator:
                    self.stats['annotators'][annotator] += 1

    def analyze_directory(self, directory: Path):
        """Analyze all CSV files in a directory"""
        csv_files = list(directory.glob('**/*.csv'))
        print(f"\n🔍 Found {len(csv_files)} CSV files to analyze")

        for csv_file in csv_files:
            print(f"  Analyzing: {csv_file.name}")
            self.analyze_file(csv_file)

    def calculate_balance_metrics(self) -> Dict:
        """Calculate data balance metrics"""
        metrics = {}

        # Language balance
        if self.stats['languages']:
            total = sum(self.stats['languages'].values())
            metrics['language_balance'] = {
                lang: (count/total) * 100
                for lang, count in self.stats['languages'].most_common()
            }

        # Bias label balance
        if self.stats['bias_labels']:
            total = sum(self.stats['bias_labels'].values())
            metrics['bias_label_balance'] = {
                label: (count/total) * 100
                for label, count in self.stats['bias_labels'].most_common()
            }

        # Gender balance
        if self.stats['target_genders']:
            total = sum(self.stats['target_genders'].values())
            metrics['gender_balance'] = {
                gender: (count/total) * 100
                for gender, count in self.stats['target_genders'].most_common()
            }

        return metrics

    def generate_report(self, output_file: Path):
        """Generate a quality report in Markdown format"""
        balance_metrics = self.calculate_balance_metrics()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Data Collection Quality Report\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Overall Progress
            f.write("## Overall Progress\n\n")
            f.write(f"- **Total Samples:** {self.stats['total_samples']}\n")
            f.write(f"- **Annotated:** {self.stats['annotated_samples']}")
            if self.stats['total_samples'] > 0:
                pct = (self.stats['annotated_samples'] / self.stats['total_samples']) * 100
                f.write(f" ({pct:.1f}%)\n")
            else:
                f.write("\n")
            f.write(f"- **Needs Annotation:** {self.stats['needs_annotation']}\n\n")

            # Language Distribution
            f.write("## Language Distribution\n\n")
            f.write("| Language | Count | Percentage |\n")
            f.write("|----------|-------|-----------|\n")
            for lang, pct in balance_metrics.get('language_balance', {}).items():
                count = self.stats['languages'][lang]
                f.write(f"| {lang} | {count} | {pct:.1f}% |\n")
            f.write("\n")

            # Bias Label Distribution
            f.write("## Bias Label Distribution\n\n")
            f.write("| Bias Label | Count | Percentage |\n")
            f.write("|------------|-------|-----------|\n")
            for label, pct in balance_metrics.get('bias_label_balance', {}).items():
                count = self.stats['bias_labels'][label]
                f.write(f"| {label} | {count} | {pct:.1f}% |\n")
            f.write("\n")

            # Target Gender Distribution
            f.write("## Target Gender Distribution\n\n")
            f.write("| Gender | Count | Percentage |\n")
            f.write("|--------|-------|-----------|\n")
            for gender, pct in balance_metrics.get('gender_balance', {}).items():
                count = self.stats['target_genders'][gender]
                f.write(f"| {gender} | {count} | {pct:.1f}% |\n")
            f.write("\n")

            # Stereotype Categories
            if self.stats['stereotype_categories']:
                f.write("## Stereotype Category Distribution\n\n")
                f.write("| Category | Count |\n")
                f.write("|----------|-------|\n")
                for cat, count in self.stats['stereotype_categories'].most_common():
                    f.write(f"| {cat} | {count} |\n")
                f.write("\n")

            # Annotator Contributions
            if self.stats['annotators']:
                f.write("## Annotator Contributions\n\n")
                f.write("| Annotator | Samples Annotated |\n")
                f.write("|-----------|-------------------|\n")
                for annotator, count in self.stats['annotators'].most_common():
                    f.write(f"| {annotator} | {count} |\n")
                f.write("\n")

            # Quality Flags
            f.write("## Quality Checks\n\n")

            # Check language balance
            if balance_metrics.get('language_balance'):
                lang_values = list(balance_metrics['language_balance'].values())
                max_imbalance = max(lang_values) - min(lang_values)
                if max_imbalance > 30:
                    f.write(f"- ⚠️ **Language Imbalance:** Max difference is {max_imbalance:.1f}%\n")
                else:
                    f.write(f"- ✅ **Language Balance:** Within acceptable range ({max_imbalance:.1f}% difference)\n")

            # Check gender balance
            if balance_metrics.get('gender_balance'):
                gender_values = list(balance_metrics['gender_balance'].values())
                max_imbalance = max(gender_values) - min(gender_values)
                if max_imbalance > 40:
                    f.write(f"- ⚠️ **Gender Imbalance:** Max difference is {max_imbalance:.1f}%\n")
                else:
                    f.write(f"- ✅ **Gender Balance:** Within acceptable range ({max_imbalance:.1f}% difference)\n")

            # Check annotation progress
            if self.stats['total_samples'] > 0:
                annotation_rate = (self.stats['annotated_samples'] / self.stats['total_samples']) * 100
                if annotation_rate < 50:
                    f.write(f"- ⚠️ **Annotation Progress:** Only {annotation_rate:.1f}% complete\n")
                elif annotation_rate < 100:
                    f.write(f"- 🔄 **Annotation Progress:** {annotation_rate:.1f}% complete\n")
                else:
                    f.write(f"- ✅ **Annotation Progress:** 100% complete\n")

            f.write("\n---\n\n")
            f.write("**Next Steps:**\n")
            f.write("1. Review any imbalance warnings\n")
            f.write("2. Calculate Cohen's Kappa for double-annotated samples\n")
            f.write("3. Proceed with quality assurance review\n")

        print(f"\n✅ Report saved to: {output_file}")

    def print_console_summary(self):
        """Print a summary to console"""
        print("\n" + "="*60)
        print("📊 QUALITY TRACKING SUMMARY")
        print("="*60)
        print(f"  Total samples:        {self.stats['total_samples']}")
        print(f"  Annotated:            {self.stats['annotated_samples']}")
        print(f"  Needs annotation:     {self.stats['needs_annotation']}")
        print()

        print("  Language distribution:")
        for lang, count in self.stats['languages'].most_common():
            pct = (count / self.stats['total_samples']) * 100 if self.stats['total_samples'] > 0 else 0
            print(f"    {lang:10s}: {count:5d} ({pct:5.1f}%)")
        print()

        print("  Bias label distribution:")
        for label, count in self.stats['bias_labels'].most_common(5):
            pct = (count / self.stats['total_samples']) * 100 if self.stats['total_samples'] > 0 else 0
            print(f"    {label:20s}: {count:5d} ({pct:5.1f}%)")
        print()

        if self.stats['annotators']:
            print("  Annotator contributions:")
            for annotator, count in self.stats['annotators'].most_common():
                print(f"    {annotator:20s}: {count:5d} samples")

        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Track annotation quality and data balance"
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help="Input CSV file or directory to analyze"
    )
    parser.add_argument(
        '--report',
        type=str,
        default='quality_report.md',
        help="Output report filename (default: quality_report.md)"
    )

    args = parser.parse_args()

    print("="*60)
    print("📈 QUALITY TRACKING DASHBOARD")
    print("="*60)
    print(f"Input:  {args.input}")
    print(f"Report: {args.report}")
    print("="*60)

    tracker = QualityTracker()

    input_path = Path(args.input)
    if input_path.is_file():
        print(f"\n🔍 Analyzing file: {input_path.name}")
        tracker.analyze_file(input_path)
    elif input_path.is_dir():
        tracker.analyze_directory(input_path)
    else:
        print("❌ Invalid input: must be a file or directory")
        sys.exit(1)

    # Print console summary
    tracker.print_console_summary()

    # Generate report
    output_path = Path(args.report)
    tracker.generate_report(output_path)

    print("\n✅ Quality tracking complete!")


if __name__ == "__main__":
    main()
