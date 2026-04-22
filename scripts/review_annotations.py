#!/usr/bin/env python3
"""
AI-Powered Annotation Review Tool
Interactive assistant to review and improve AIBRIDGE annotations.

Usage:
    python3 scripts/review_annotations.py --input eval/ground_truth_ki_aibridge.csv --interactive
"""

import csv
import json
import sys
from typing import Dict, List, Optional
import argparse


class AnnotationReviewer:
    """Interactive review assistant for AIBRIDGE annotations."""

    def __init__(self):
        self.aibridge_values = {
            'target_gender': ['female', 'male', 'neutral', 'mixed', 'nonbinary', 'unknown'],
            'bias_label': ['stereotype', 'counter-stereotype', 'neutral', 'derogation'],
            'explicitness': ['explicit', 'implicit', ''],
            'stereotype_category': [
                'profession', 'family_role', 'leadership', 'education',
                'religion_culture', 'proverb_idiom', 'daily_life', 'appearance', 'capability', ''
            ],
            'sentiment': ['positive', 'neutral', 'negative'],
            'device': [
                'scripture_quote', 'proverb', 'metaphor', 'narrative',
                'question', 'directive', 'sarcasm', ''
            ],
        }

    def validate_row(self, row: Dict) -> List[str]:
        """
        Validate a row against AIBRIDGE requirements.

        Returns list of issues found.
        """
        issues = []

        # Required fields
        required = ['sample_id', 'text', 'language', 'target_gender', 'bias_label', 'sentiment']
        for field in required:
            if not row.get(field):
                issues.append(f"Missing required field: {field}")

        # Value validation
        for field, valid_values in self.aibridge_values.items():
            value = row.get(field, '')
            if value and value not in valid_values:
                issues.append(f"Invalid {field}: '{value}' (must be one of: {', '.join(valid_values)})")

        # Conditional requirements
        bias_label = row.get('bias_label', '')
        if bias_label != 'neutral':
            # explicitness required for biased samples
            if not row.get('explicitness'):
                issues.append("explicitness required when bias_label ≠ neutral")

            # stereotype_category recommended for biased samples
            if not row.get('stereotype_category'):
                issues.append("stereotype_category recommended for biased samples")

        # Bible verses must have specific fields
        domain = row.get('domain', '')
        if domain in ['religious_text', 'culture_and_religion']:
            if row.get('device') != 'scripture_quote':
                issues.append("Bible verses should have device=scripture_quote")
            if row.get('safety_flag') != 'sensitive':
                issues.append("Religious content should have safety_flag=sensitive")
            if not row.get('stereotype_category'):
                issues.append("Bible verses should have stereotype_category (usually religion_culture)")

        return issues

    def suggest_improvements(self, row: Dict) -> Dict[str, str]:
        """
        Generate AI-powered suggestions for improving annotations.

        Returns dict of field → suggested_value.
        """
        suggestions = {}
        text = row.get('text', '').lower()

        # Suggest bias_label
        if row.get('bias_label') == 'stereotype':
            # Check for counter-stereotypes
            if 'mũrũme' in text and 'rera' in text:  # man caring
                suggestions['bias_label'] = 'counter-stereotype (male in caregiving role)'
            if 'mũtumia' in text and 'mũtongoria' in text:  # woman leader
                suggestions['bias_label'] = 'counter-stereotype (female in leadership)'

        # Suggest stereotype_category
        if not row.get('stereotype_category') and row.get('bias_label') != 'neutral':
            if 'mũthĩnjĩri' in text:  # priest
                suggestions['stereotype_category'] = 'religion_culture'
            elif any(term in text for term in ['daktari', 'mũrutani', 'mũrĩmi']):
                suggestions['stereotype_category'] = 'profession'
            elif 'rera' in text or 'ciana' in text:  # care, children
                suggestions['stereotype_category'] = 'family_role'
            elif 'mũtongoria' in text:  # leader
                suggestions['stereotype_category'] = 'leadership'

        # Suggest device for Bible verses
        if row.get('domain') == 'religious_text' and not row.get('device'):
            suggestions['device'] = 'scripture_quote'

        return suggestions

    def display_row_summary(self, row: Dict, issues: List[str], suggestions: Dict[str, str]):
        """Display a nicely formatted row summary."""
        print("=" * 80)
        print(f"Sample ID: {row.get('sample_id', 'N/A')}")
        print("-" * 80)
        print(f"Text: {row.get('text', '')[:200]}...")
        print()

        # Current annotations
        print("CURRENT ANNOTATIONS:")
        print(f"  target_gender:        {row.get('target_gender', '(empty)')}")
        print(f"  bias_label:           {row.get('bias_label', '(empty)')}")
        print(f"  explicitness:         {row.get('explicitness', '(empty)')}")
        print(f"  stereotype_category:  {row.get('stereotype_category', '(empty)')}")
        print(f"  sentiment:            {row.get('sentiment', '(empty)')}")
        print(f"  device:               {row.get('device', '(empty)')}")
        print(f"  domain:               {row.get('domain', '(empty)')}")
        print()

        # Issues
        if issues:
            print("❌ ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print()

        # Suggestions
        if suggestions:
            print("💡 SUGGESTIONS:")
            for field, suggestion in suggestions.items():
                print(f"  {field}: {suggestion}")
            print()

    def interactive_review(self, csv_path: str, filter_issues_only: bool = True):
        """
        Interactive review mode - step through samples and fix issues.
        """
        print("=" * 80)
        print("AIBRIDGE ANNOTATION REVIEW - Interactive Mode")
        print("=" * 80)
        print()

        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Loaded {len(rows):,} samples")

        # Filter to only samples with issues
        if filter_issues_only:
            rows_with_issues = []
            for row in rows:
                issues = self.validate_row(row)
                if issues:
                    rows_with_issues.append((row, issues))
            print(f"Found {len(rows_with_issues):,} samples with issues")
            print()

            if not rows_with_issues:
                print("✅ No issues found! Dataset is AIBRIDGE-compliant.")
                return

            print("Showing samples with issues only...")
            print("Commands: [n]ext, [s]kip, [q]uit, or enter new value")
            print()

            for i, (row, issues) in enumerate(rows_with_issues, 1):
                suggestions = self.suggest_improvements(row)
                self.display_row_summary(row, issues, suggestions)

                print(f"Sample {i} of {len(rows_with_issues)}")
                cmd = input("Command (n/s/q or field=value): ").strip().lower()

                if cmd == 'q':
                    print("Exiting...")
                    break
                elif cmd in ['n', 's', '']:
                    continue
                else:
                    print(f"  (Manual edits not implemented yet - use CSV editor)")

    def generate_report(self, csv_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Generate validation report for entire dataset.
        """
        print("=" * 80)
        print("AIBRIDGE VALIDATION REPORT")
        print("=" * 80)
        print()

        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        stats = {
            'total_samples': len(rows),
            'samples_with_issues': 0,
            'issue_types': {},
            'field_completeness': {},
            'value_distribution': {},
        }

        # Validate each row
        all_issues = []
        for row in rows:
            issues = self.validate_row(row)
            if issues:
                stats['samples_with_issues'] += 1
                all_issues.extend(issues)

                for issue in issues:
                    # Extract issue type
                    issue_type = issue.split(':')[0] if ':' in issue else issue
                    stats['issue_types'][issue_type] = stats['issue_types'].get(issue_type, 0) + 1

        # Field completeness
        required_fields = ['target_gender', 'bias_label', 'explicitness',
                          'stereotype_category', 'sentiment', 'device']
        for field in required_fields:
            filled = sum(1 for row in rows if row.get(field))
            stats['field_completeness'][field] = {
                'filled': filled,
                'empty': len(rows) - filled,
                'percentage': (filled / len(rows)) * 100
            }

        # Value distributions
        for field in ['bias_label', 'stereotype_category', 'device', 'target_gender']:
            distribution = {}
            for row in rows:
                value = row.get(field, '(empty)')
                distribution[value] = distribution.get(value, 0) + 1
            stats['value_distribution'][field] = distribution

        # Print report
        print(f"Total samples: {stats['total_samples']:,}")
        print(f"Samples with issues: {stats['samples_with_issues']:,} ({stats['samples_with_issues']/stats['total_samples']*100:.1f}%)")
        print()

        print("FIELD COMPLETENESS:")
        for field, data in stats['field_completeness'].items():
            print(f"  {field:20s}: {data['filled']:5,} / {stats['total_samples']:5,} ({data['percentage']:5.1f}%)")
        print()

        print("COMMON ISSUES:")
        for issue_type, count in sorted(stats['issue_types'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {count:5,}× {issue_type}")
        print()

        print("BIAS LABEL DISTRIBUTION:")
        for value, count in sorted(stats['value_distribution']['bias_label'].items()):
            pct = (count / stats['total_samples']) * 100
            print(f"  {value:20s}: {count:5,} ({pct:5.1f}%)")
        print()

        compliance_rate = ((stats['total_samples'] - stats['samples_with_issues']) / stats['total_samples']) * 100
        print(f"AIBRIDGE COMPLIANCE RATE: {compliance_rate:.1f}%")

        if compliance_rate >= 95:
            print("✅ EXCELLENT - Ready for submission")
        elif compliance_rate >= 80:
            print("⚠️  GOOD - Minor fixes needed")
        else:
            print("❌ NEEDS WORK - Significant issues to address")

        # Save report
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"\n📁 Report saved to: {output_path}")

        return stats


def main():
    parser = argparse.ArgumentParser(description='Review AIBRIDGE annotations')
    parser.add_argument('--input', '-i', required=True, help='AIBRIDGE CSV path')
    parser.add_argument('--interactive', '-I', action='store_true',
                       help='Interactive review mode')
    parser.add_argument('--report', '-r', help='Generate validation report (JSON output)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Show all samples (default: issues only)')

    args = parser.parse_args()

    reviewer = AnnotationReviewer()

    if args.interactive:
        reviewer.interactive_review(args.input, filter_issues_only=not args.all)
    else:
        reviewer.generate_report(args.input, args.report)


if __name__ == '__main__':
    main()
