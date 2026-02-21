"""Main CLI script for batch annotation of samples.

This script provides a command-line interface for annotating batches of samples
following the AI BRIDGE 24-field schema.

Usage:
    python3 scripts/annotate_samples.py \\
        --input data/raw/samples.csv \\
        --count 50 \\
        --annotator expert_1 \\
        --language sw \\
        --output data/annotated/sw_batch_001.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from annotation.models import AnnotatorInfo
from annotation.interface import AnnotationInterface
from annotation.schema import print_compliance_report
from annotation.export import AnnotationExporter


def load_samples_from_csv(csv_file: Path, count: int) -> list[str]:
    """Load sample texts from CSV file.

    Args:
        csv_file: Path to CSV file with 'text' column
        count: Number of samples to load

    Returns:
        List of text strings
    """
    samples = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= count:
                break
            text = row.get("text", "").strip()
            if text:
                samples.append(text)

    return samples


def main():
    parser = argparse.ArgumentParser(
        description="Batch annotation of samples for gender bias detection"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input CSV file with samples (must have 'text' column)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of samples to annotate (default: 50)",
    )
    parser.add_argument(
        "--annotator",
        type=str,
        required=True,
        help="Annotator ID (e.g., expert_1)",
    )
    parser.add_argument(
        "--language",
        type=str,
        required=True,
        choices=["en", "sw", "fr", "ki"],
        help="Language code",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output CSV file for annotations",
    )
    parser.add_argument(
        "--native-language",
        type=str,
        default=None,
        help="Annotator's native language (defaults to --language)",
    )
    parser.add_argument(
        "--expertise",
        type=str,
        default="expert",
        choices=["novice", "intermediate", "expert"],
        help="Annotator expertise level (default: expert)",
    )
    parser.add_argument(
        "--source-dataset",
        type=str,
        default=None,
        help="Source dataset name (e.g., wikipedia, news, bible)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive mode (prompt for each sample)",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Output file for statistics report",
    )
    parser.add_argument(
        "--check-compliance",
        action="store_true",
        help="Check AI BRIDGE schema compliance after annotation",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("Batch Annotation Tool")
    print("=" * 70)

    # Load samples
    print(f"\nLoading samples from {args.input}...")
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return 1

    samples = load_samples_from_csv(input_file, args.count)
    print(f"✓ Loaded {len(samples)} samples")

    if len(samples) == 0:
        print("❌ Error: No samples loaded. Check CSV format (needs 'text' column)")
        return 1

    # Create annotator
    native_lang = args.native_language or args.language
    annotator = AnnotatorInfo(
        annotator_id=args.annotator,
        native_language=native_lang,
        expertise_level=args.expertise,
    )

    print(f"\nAnnotator: {args.annotator}")
    print(f"Language: {args.language}")
    print(f"Expertise: {args.expertise}")

    # Create annotation interface
    interface = AnnotationInterface(annotator=annotator)

    # Create batch
    batch_id = f"{args.language}_{args.annotator}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nBatch ID: {batch_id}")

    batch = interface.create_batch(
        batch_id=batch_id, language=args.language, samples=samples
    )

    # Set source dataset if provided
    if args.source_dataset:
        for sample in batch.samples:
            sample.source_dataset = args.source_dataset
            sample.collection_date = datetime.now()

    # Annotate
    if args.interactive:
        print("\n" + "=" * 70)
        print("Starting Interactive Annotation")
        print("=" * 70)
        print("\nNote: You can stop at any time. Progress is auto-saved.\n")
        interface.interactive_annotate(auto_save=True)
    else:
        print("\n" + "=" * 70)
        print("Non-Interactive Mode")
        print("=" * 70)
        print("\nℹ️  Interactive mode not enabled.")
        print("Use --interactive flag to annotate samples interactively.")
        print("\nℹ️  Samples loaded but not annotated. Exporting batch template...")

    # Save batch
    print(f"\nSaving batch to {args.output}...")
    output_file = Path(args.output)
    json_file = interface.save_batch(batch)
    print(f"✓ JSON saved: {json_file}")

    # Export to CSV
    csv_file = AnnotationExporter.to_ground_truth_csv(
        batch, output_file, include_all_fields=True
    )
    print(f"✓ CSV exported: {csv_file}")

    # Generate statistics report if requested
    if args.report:
        report_file = AnnotationExporter.export_statistics_report(
            batch, Path(args.report)
        )
        print(f"✓ Report saved: {report_file}")

    # Check compliance if requested
    if args.check_compliance:
        print("\n" + "=" * 70)
        print("AI BRIDGE Schema Compliance Check")
        print("=" * 70)
        print_compliance_report(batch)

    # Show summary
    print("\n" + "=" * 70)
    print("Batch Summary")
    print("=" * 70)
    interface.print_stats(batch)

    print("✅ Batch annotation complete!")
    print(f"\nNext steps:")
    if not args.interactive and interface.current_batch.completion_rate < 1.0:
        print(f"1. Load batch and annotate interactively:")
        print(f"   python3 -c \"")
        print(f"   from annotation.interface import AnnotationInterface")
        print(f"   from annotation.models import AnnotatorInfo")
        print(f"   annotator = AnnotatorInfo(annotator_id='{args.annotator}', native_language='{native_lang}', expertise_level='{args.expertise}')")
        print(f"   interface = AnnotationInterface(annotator)")
        print(f"   batch = interface.load_batch('{json_file}')")
        print(f"   interface.interactive_annotate()")
        print(f"   \"")
    else:
        print(f"1. Review annotations: cat {csv_file}")
        print(f"2. Merge to ground truth: python3 scripts/merge_annotations.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
