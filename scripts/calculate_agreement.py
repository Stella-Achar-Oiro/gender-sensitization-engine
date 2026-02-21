"""CLI script for calculating inter-annotator agreement.

This script calculates Cohen's Kappa (2 annotators) or Krippendorff's Alpha
(2+ annotators) from annotation batch files.

Usage:
    # Cohen's Kappa (2 annotators)
    python3 scripts/calculate_agreement.py \\
        --batch1 data/annotations/batch_annotator1.json \\
        --batch2 data/annotations/batch_annotator2.json \\
        --output reports/agreement.json

    # Krippendorff's Alpha (3+ annotators)
    python3 scripts/calculate_agreement.py \\
        --batches data/annotations/batch_*.json \\
        --output reports/agreement.json \\
        --use-alpha
"""

import argparse
import json
import sys
from pathlib import Path
from glob import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from annotation.interface import AnnotationInterface
from annotation.models import AnnotatorInfo
from annotation.agreement import (
    calculate_kappa_with_details,
    format_kappa_report,
    calculate_alpha_with_details,
    format_alpha_report,
)
from annotation.export import AnnotationExporter


def main():
    parser = argparse.ArgumentParser(
        description="Calculate inter-annotator agreement (Cohen's Kappa or Krippendorff's Alpha)"
    )
    parser.add_argument(
        "--batch1",
        type=str,
        help="First annotation batch JSON file (for Kappa)",
    )
    parser.add_argument(
        "--batch2",
        type=str,
        help="Second annotation batch JSON file (for Kappa)",
    )
    parser.add_argument(
        "--batches",
        type=str,
        nargs="+",
        help="Multiple batch JSON files (for Alpha), or glob pattern",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for agreement results",
    )
    parser.add_argument(
        "--use-alpha",
        action="store_true",
        help="Use Krippendorff's Alpha instead of Cohen's Kappa",
    )
    parser.add_argument(
        "--export-disagreements",
        type=str,
        help="Export disagreement samples to CSV file",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("Inter-Annotator Agreement Calculator")
    print("=" * 70)

    # Determine metric to use
    if args.use_alpha or args.batches:
        metric = "Krippendorff's Alpha"
    else:
        metric = "Cohen's Kappa"

    print(f"\nMetric: {metric}")

    # Load batches
    if metric == "Cohen's Kappa":
        if not args.batch1 or not args.batch2:
            print("❌ Error: --batch1 and --batch2 required for Cohen's Kappa")
            return 1

        print(f"\nLoading batches...")
        print(f"  Batch 1: {args.batch1}")
        print(f"  Batch 2: {args.batch2}")

        # Create dummy annotator for loading
        dummy_annotator = AnnotatorInfo(
            annotator_id="loader",
            native_language="en",
            expertise_level="expert",
        )
        interface = AnnotationInterface(dummy_annotator)

        batch1 = interface.load_batch(Path(args.batch1))
        batch2 = interface.load_batch(Path(args.batch2))

        print(f"✓ Loaded {len(batch1.samples)} samples from batch 1")
        print(f"✓ Loaded {len(batch2.samples)} samples from batch 2")

        # Calculate Kappa
        print(f"\nCalculating Cohen's Kappa...")
        details = calculate_kappa_with_details(batch1.samples, batch2.samples)

        # Print report
        report = format_kappa_report(
            details, batch1.annotator_id, batch2.annotator_id
        )
        print(report)

        # Export disagreements if requested
        if args.export_disagreements and details["disagreements"] > 0:
            disagreement_samples = []
            for idx in details["disagreement_indices"]:
                disagreement_samples.extend([batch1.samples[idx], batch2.samples[idx]])

            output_file = AnnotationExporter.export_disagreements(
                disagreement_samples, Path(args.export_disagreements)
            )
            print(f"✓ Disagreements exported to: {output_file}")

        # Save results if output specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            result_data = {
                "metric": "cohens_kappa",
                "annotator1": batch1.annotator_id,
                "annotator2": batch2.annotator_id,
                "n_samples": details["total_samples"],
                **details,
            }
            # Remove non-serializable fields
            result_data.pop("disagreement_indices", None)

            with open(output_path, "w") as f:
                json.dump(result_data, f, indent=2)
            print(f"✓ Results saved to: {output_path}")

    else:  # Krippendorff's Alpha
        if not args.batches:
            print("❌ Error: --batches required for Krippendorff's Alpha")
            return 1

        # Expand glob patterns
        batch_files = []
        for pattern in args.batches:
            if "*" in pattern:
                batch_files.extend(glob(pattern))
            else:
                batch_files.append(pattern)

        if len(batch_files) < 2:
            print(f"❌ Error: Need at least 2 batches, found {len(batch_files)}")
            return 1

        print(f"\nLoading {len(batch_files)} batches...")

        # Load all batches
        dummy_annotator = AnnotatorInfo(
            annotator_id="loader",
            native_language="en",
            expertise_level="expert",
        )
        interface = AnnotationInterface(dummy_annotator)

        annotations_by_annotator = {}
        for batch_file in batch_files:
            batch = interface.load_batch(Path(batch_file))
            annotations_by_annotator[batch.annotator_id] = batch.samples
            print(f"  ✓ {batch.annotator_id}: {len(batch.samples)} samples")

        # Calculate Alpha
        print(f"\nCalculating Krippendorff's Alpha...")
        details = calculate_alpha_with_details(annotations_by_annotator)

        # Print report
        report = format_alpha_report(details)
        print(report)

        # Save results if output specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            result_data = {
                "metric": "krippendorff_alpha",
                "annotators": details["annotator_ids"],
                "n_annotators": details["n_annotators"],
                "n_samples": details["n_samples"],
                **details,
            }

            with open(output_path, "w") as f:
                json.dump(result_data, f, indent=2)
            print(f"✓ Results saved to: {output_path}")

    print("\n✅ Agreement calculation complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
