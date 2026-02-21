"""CLI script for validating annotation quality.

This script validates annotation batches and generates quality reports
to ensure annotation consistency and detect potential issues.

Usage:
    python3 scripts/validate_annotations.py \\
        --input data/annotations/batch_*.json \\
        --output reports/quality_report.txt
"""

import argparse
import sys
from pathlib import Path
from glob import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from annotation.interface import AnnotationInterface
from annotation.models import AnnotatorInfo
from annotation.quality import AnnotationQualityChecker
from annotation.reports import (
    format_quality_report,
    format_multi_batch_report,
    generate_multi_batch_report,
    save_quality_report,
)


def main():
    parser = argparse.ArgumentParser(
        description="Validate annotation quality and generate reports"
    )
    parser.add_argument(
        "--input",
        type=str,
        nargs="+",
        required=True,
        help="Input batch JSON file(s) or glob pattern",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output report file (text or JSON)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=60.0,
        help="Minimum quality score to pass (default: 60)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("Annotation Quality Validation")
    print("=" * 70)

    # Expand glob patterns
    batch_files = []
    for pattern in args.input:
        if "*" in pattern:
            batch_files.extend(glob(pattern))
        else:
            batch_files.append(pattern)

    if not batch_files:
        print("❌ Error: No batch files found")
        return 1

    print(f"\nLoading {len(batch_files)} batch(es)...")

    # Load batches
    dummy_annotator = AnnotatorInfo(
        annotator_id="validator",
        native_language="en",
        expertise_level="expert",
    )
    interface = AnnotationInterface(dummy_annotator)

    batches = []
    for batch_file in batch_files:
        try:
            batch = interface.load_batch(Path(batch_file))
            batches.append(batch)
            print(f"  ✓ Loaded: {batch.batch_id} ({len(batch.samples)} samples)")
        except Exception as e:
            print(f"  ❌ Error loading {batch_file}: {e}")

    if not batches:
        print("\n❌ Error: No batches loaded successfully")
        return 1

    # Validate
    print(f"\nValidating annotation quality...")
    checker = AnnotationQualityChecker()

    if len(batches) == 1:
        # Single batch report
        report = checker.generate_quality_report(batches[0])
        formatted_report = format_quality_report(report)
        print(formatted_report)

        # Check if passes
        if report["quality_score"] < args.min_score:
            print(f"❌ Quality check FAILED (score: {report['quality_score']:.0f} < {args.min_score:.0f})")
            exit_code = 1
        else:
            print(f"✅ Quality check PASSED (score: {report['quality_score']:.0f})")
            exit_code = 0

    else:
        # Multi-batch report
        report = generate_multi_batch_report(batches)
        formatted_report = format_multi_batch_report(report)
        print(formatted_report)

        # Check if passes
        if report["avg_quality_score"] < args.min_score:
            print(f"❌ Quality check FAILED (avg score: {report['avg_quality_score']:.0f} < {args.min_score:.0f})")
            exit_code = 1
        else:
            print(f"✅ Quality check PASSED (avg score: {report['avg_quality_score']:.0f})")
            exit_code = 0

    # Save report if output specified
    if args.output:
        output_path = save_quality_report(
            report, Path(args.output), format_type=args.format
        )
        print(f"\n✓ Report saved to: {output_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
