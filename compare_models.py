#!/usr/bin/env python3
"""
Compare Bias Detection Models

Compares performance of rules-based, ML-based, and hybrid approaches.

Usage:
    python3 compare_models.py --language en
    python3 compare_models.py --all-languages
    python3 compare_models.py --language sw --output reports/comparison.txt
"""
import argparse
import sys
from pathlib import Path

from ml.evaluation.model_comparison import ModelComparator
from eval.models import Language


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare bias detection models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare models for English
  %(prog)s --language en

  # Compare for all languages
  %(prog)s --all-languages

  # Save report to file
  %(prog)s --language sw --output reports/comparison_sw.txt
        """
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        choices=['en', 'sw', 'fr', 'ki'],
        help='Language to compare models for'
    )
    parser.add_argument(
        '--all-languages',
        action='store_true',
        help='Compare models for all languages'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output file for report (default: print to stdout)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Validate arguments
    if not args.language and not args.all_languages:
        print("Error: Must specify --language or --all-languages")
        return 1

    if args.language and args.all_languages:
        print("Error: Cannot specify both --language and --all-languages")
        return 1

    # Map language codes
    lang_map = {
        'en': Language.ENGLISH,
        'sw': Language.SWAHILI,
        'fr': Language.FRENCH,
        'ki': Language.GIKUYU
    }

    # Initialize comparator
    comparator = ModelComparator()

    print("=" * 70)
    print("Bias Detection Model Comparison".center(70))
    print("=" * 70)
    print()

    # Run comparison
    if args.all_languages:
        print("Comparing models across all languages...")
        print()

        results = comparator.compare_all_languages()

        if not results:
            print("Error: No data found for any language")
            return 1

        # Generate report
        report = comparator.generate_report(results, args.output)

        if not args.output:
            print(report)

    else:
        language = lang_map[args.language]

        print(f"Comparing models for {language.value}...")
        print()

        try:
            result = comparator.compare_on_language(language)

            # Print summary
            print(result.summary())

            # Save if requested
            if args.output:
                report = result.summary()
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(report)
                print()
                print(f"Report saved to: {args.output}")

        except ValueError as e:
            print(f"Error: {e}")
            return 1

    print()
    print("=" * 70)
    print("Comparison Complete".center(70))
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
