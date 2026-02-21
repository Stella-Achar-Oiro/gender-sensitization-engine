"""Demo script for annotation workflow.

This script demonstrates the annotation interface by creating a batch of 10 samples
and annotating them programmatically (without user interaction for testing purposes).
"""

import argparse
from pathlib import Path

from annotation.models import (
    AnnotatorInfo,
    BiasCategory,
    ConfidenceLevel,
    DemographicGroup,
    GenderReferent,
)
from annotation.interface import AnnotationInterface
from annotation.validator import AnnotationValidator


def main():
    parser = argparse.ArgumentParser(description="Demo annotation workflow")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/annotations",
        help="Output directory for annotations",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify annotations with validator",
    )
    args = parser.parse_args()

    # Create annotator
    annotator = AnnotatorInfo(
        annotator_id="demo_annotator_001",
        name="Demo Annotator",
        native_language="en",
        expertise_level="expert",
    )

    # Initialize interface
    interface = AnnotationInterface(
        annotator=annotator, output_dir=Path(args.output_dir)
    )

    # Sample texts for annotation
    sample_texts = [
        "The chairman led the meeting efficiently",
        "The nurse cared for her patients with compassion",
        "Every student should bring his textbook to class",
        "The teacher explained the lesson clearly",
        "A good programmer writes clean code",
        "The secretary answered the phone politely",
        "The doctor examined his patient thoroughly",
        "A businessman must be professional",
        "The stewardess served drinks to passengers",
        "Every person deserves respect",
    ]

    # Expected annotations (pre-defined for demo)
    expected_annotations = [
        {
            "has_bias": True,
            "bias_category": BiasCategory.OCCUPATION,
            "expected_correction": "The chairperson led the meeting efficiently",
            "demographic_group": DemographicGroup.MALE_REFERENT,
            "gender_referent": GenderReferent.MALE,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.PRONOUN_ASSUMPTION,
            "expected_correction": "The nurse cared for their patients with compassion",
            "demographic_group": DemographicGroup.FEMALE_REFERENT,
            "gender_referent": GenderReferent.FEMALE,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.PRONOUN_GENERIC,
            "expected_correction": "Every student should bring their textbook to class",
            "demographic_group": DemographicGroup.MALE_REFERENT,
            "gender_referent": GenderReferent.MALE,
        },
        {
            "has_bias": False,
            "bias_category": None,
            "expected_correction": None,
            "demographic_group": DemographicGroup.NEUTRAL_REFERENT,
            "gender_referent": GenderReferent.NEUTRAL,
        },
        {
            "has_bias": False,
            "bias_category": None,
            "expected_correction": None,
            "demographic_group": DemographicGroup.NEUTRAL_REFERENT,
            "gender_referent": GenderReferent.NEUTRAL,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.OCCUPATION,
            "expected_correction": "The administrative assistant answered the phone politely",
            "demographic_group": DemographicGroup.FEMALE_REFERENT,
            "gender_referent": GenderReferent.FEMALE,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.PRONOUN_ASSUMPTION,
            "expected_correction": "The doctor examined their patient thoroughly",
            "demographic_group": DemographicGroup.MALE_REFERENT,
            "gender_referent": GenderReferent.MALE,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.OCCUPATION,
            "expected_correction": "A businessperson must be professional",
            "demographic_group": DemographicGroup.MALE_REFERENT,
            "gender_referent": GenderReferent.MALE,
        },
        {
            "has_bias": True,
            "bias_category": BiasCategory.OCCUPATION,
            "expected_correction": "The flight attendant served drinks to passengers",
            "demographic_group": DemographicGroup.FEMALE_REFERENT,
            "gender_referent": GenderReferent.FEMALE,
        },
        {
            "has_bias": False,
            "bias_category": None,
            "expected_correction": None,
            "demographic_group": DemographicGroup.NEUTRAL_REFERENT,
            "gender_referent": GenderReferent.NEUTRAL,
        },
    ]

    print("\n" + "=" * 70)
    print("Annotation Workflow Demo")
    print("=" * 70)

    # Create batch
    print(f"\nCreating batch with {len(sample_texts)} samples...")
    batch = interface.create_batch(
        batch_id="demo_batch_001", language="en", samples=sample_texts
    )
    print(f"✓ Batch created: {batch.batch_id}")

    # Annotate each sample
    print("\nAnnotating samples...")
    for i, sample in enumerate(batch.samples):
        annotation = expected_annotations[i]
        interface.annotate_sample(
            sample,
            has_bias=annotation["has_bias"],
            bias_category=annotation["bias_category"],
            expected_correction=annotation["expected_correction"],
            confidence=ConfidenceLevel.HIGH,
            demographic_group=annotation["demographic_group"],
            gender_referent=annotation["gender_referent"],
        )
        print(f"  [{i+1}/10] Annotated: {sample.text[:50]}...")

    print(f"\n✓ All {len(batch.samples)} samples annotated")

    # Save batch
    print("\nSaving batch...")
    json_file = interface.save_batch()
    print(f"✓ Batch saved to: {json_file}")

    # Export to CSV
    print("\nExporting to CSV...")
    csv_file = interface.export_to_csv()
    print(f"✓ CSV exported to: {csv_file}")

    # Show statistics
    print("\n" + "=" * 70)
    interface.print_stats()

    # Validate if requested
    if args.verify:
        print("=" * 70)
        print("Validation Results")
        print("=" * 70)

        validator = AnnotationValidator(strict=False)
        is_valid, report = validator.validate_batch(batch)

        print(f"\nBatch valid: {is_valid}")
        print(f"Valid samples: {report['valid_samples']}/{report['total_samples']}")
        print(f"Invalid samples: {report['invalid_samples']}")

        if report["batch_errors"]:
            print("\nBatch errors:")
            for error in report["batch_errors"]:
                print(f"  - {error}")

        if report["errors_by_sample"]:
            print(f"\nSample errors ({len(report['errors_by_sample'])} samples):")
            for idx, errors in list(report["errors_by_sample"].items())[:3]:
                print(f"  Sample {idx}:")
                for error in errors:
                    print(f"    - {error}")

        print("=" * 70)

    print("\n✅ Demo complete!")
    print(f"\nNext steps:")
    print(f"1. View annotations: cat {json_file}")
    print(f"2. View CSV: cat {csv_file}")
    print(f"3. Start interactive annotation: python3 -c \"")
    print(f"   from annotation.interface import AnnotationInterface")
    print(f"   from annotation.models import AnnotatorInfo")
    print(f"   annotator = AnnotatorInfo(annotator_id='user', native_language='en', expertise_level='expert')")
    print(f"   interface = AnnotationInterface(annotator)")
    print(f"   batch = interface.load_batch('{json_file}')")
    print(f"   interface.interactive_annotate()")
    print(f"   \"")


if __name__ == "__main__":
    main()
