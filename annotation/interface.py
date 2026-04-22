"""Interactive CLI for annotating gender bias samples.

This module provides a user-friendly command-line interface for human annotators
to review and annotate samples following the AI BRIDGE 24-field schema.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from annotation.models import (
    AnnotationSample,
    AnnotationBatch,
    AnnotatorInfo,
    ConfidenceLevel,
    BiasCategory,
    DemographicGroup,
    GenderReferent,
    SeverityLevel,
    AnnotationStats,
)


class AnnotationInterface:
    """Interactive CLI for annotation workflow."""

    def __init__(
        self,
        annotator: AnnotatorInfo,
        output_dir: Path = Path("data/annotations"),
    ):
        """Initialize annotation interface.

        Args:
            annotator: Annotator information
            output_dir: Directory to save annotations
        """
        self.annotator = annotator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_batch: Optional[AnnotationBatch] = None

    def create_batch(
        self, batch_id: str, language: str, samples: List[str]
    ) -> AnnotationBatch:
        """Create a new annotation batch from text samples.

        Args:
            batch_id: Unique batch identifier
            language: Language code (en, sw, fr, ki)
            samples: List of text strings to annotate

        Returns:
            Created AnnotationBatch
        """
        annotation_samples = []
        for text in samples:
            # Create minimal sample - will be fully annotated in interactive session
            sample = AnnotationSample(
                text=text,
                has_bias=False,  # Will be updated during annotation
                annotator_id=self.annotator.annotator_id,
                confidence=ConfidenceLevel.MEDIUM,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
                annotation_timestamp=None,  # Not yet annotated
            )
            annotation_samples.append(sample)

        batch = AnnotationBatch(
            batch_id=batch_id,
            language=language,
            samples=annotation_samples,
            annotator_id=self.annotator.annotator_id,
        )
        self.current_batch = batch
        return batch

    def load_batch(self, batch_file: Path) -> AnnotationBatch:
        """Load existing annotation batch from file.

        Args:
            batch_file: Path to batch JSON file

        Returns:
            Loaded AnnotationBatch
        """
        with open(batch_file) as f:
            data = json.load(f)
        batch = AnnotationBatch(**data)
        self.current_batch = batch
        return batch

    def save_batch(self, batch: Optional[AnnotationBatch] = None) -> Path:
        """Save annotation batch to file.

        Args:
            batch: Batch to save (defaults to current_batch)

        Returns:
            Path to saved file
        """
        batch = batch or self.current_batch
        if not batch:
            raise ValueError("No batch to save")

        output_file = (
            self.output_dir / f"{batch.batch_id}_{batch.language}.json"
        )
        with open(output_file, "w") as f:
            json.dump(batch.to_dict(), f, indent=2)

        return output_file

    def annotate_sample(
        self,
        sample: AnnotationSample,
        has_bias: bool,
        bias_category: Optional[BiasCategory] = None,
        expected_correction: Optional[str] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        demographic_group: DemographicGroup = DemographicGroup.NEUTRAL_REFERENT,
        gender_referent: GenderReferent = GenderReferent.NEUTRAL,
        severity: SeverityLevel = SeverityLevel.REPLACE,
        context_requires_gender: bool = False,
        notes: Optional[str] = None,
        **kwargs,
    ) -> AnnotationSample:
        """Annotate a single sample with all required fields.

        Args:
            sample: Sample to annotate
            has_bias: Whether bias is present
            bias_category: Category of bias if present
            expected_correction: Expected neutral correction
            confidence: Annotator confidence
            demographic_group: Demographic group
            gender_referent: Gender referent
            severity: Severity level
            context_requires_gender: Whether gender is contextually required
            notes: Additional notes
            **kwargs: Additional optional fields

        Returns:
            Updated AnnotationSample
        """
        # Update core fields
        sample.has_bias = has_bias
        sample.bias_category = bias_category
        sample.expected_correction = expected_correction
        sample.confidence = confidence
        sample.annotation_timestamp = datetime.now()

        # Update fairness fields
        sample.demographic_group = demographic_group
        sample.gender_referent = gender_referent

        # Update context fields
        sample.context_requires_gender = context_requires_gender
        sample.severity = severity
        sample.notes = notes

        # Update any additional fields passed via kwargs
        for key, value in kwargs.items():
            if hasattr(sample, key):
                setattr(sample, key, value)

        return sample

    def interactive_annotate(
        self, sample_index: int = 0, auto_save: bool = True
    ) -> None:
        """Run interactive annotation session.

        Args:
            sample_index: Index of sample to start from
            auto_save: Whether to auto-save after each annotation
        """
        if not self.current_batch:
            raise ValueError("No batch loaded. Call create_batch() or load_batch()")

        total = len(self.current_batch.samples)
        print(f"\n{'='*70}")
        print(f"Annotation Session: {self.current_batch.batch_id}")
        print(f"Language: {self.current_batch.language}")
        print(f"Total samples: {total}")
        print(f"Annotator: {self.annotator.annotator_id}")
        print(f"{'='*70}\n")

        for i in range(sample_index, total):
            sample = self.current_batch.samples[i]

            # Skip already annotated samples
            if sample.annotation_timestamp:
                continue

            print(f"\n[Sample {i+1}/{total}]")
            print(f"Text: {sample.text}")
            print()

            # Get has_bias
            while True:
                has_bias_input = input("Does this text contain gender bias? (y/n): ").lower()
                if has_bias_input in ["y", "n"]:
                    has_bias = has_bias_input == "y"
                    break
                print("Invalid input. Please enter 'y' or 'n'.")

            bias_category = None
            expected_correction = None

            if has_bias:
                # Get bias category
                print("\nBias categories:")
                categories = list(BiasCategory)
                for idx, cat in enumerate(categories, 1):
                    print(f"  {idx}. {cat.value}")

                while True:
                    try:
                        cat_input = input("Select category (1-6): ")
                        cat_idx = int(cat_input) - 1
                        if 0 <= cat_idx < len(categories):
                            bias_category = categories[cat_idx]
                            break
                        print(f"Invalid input. Enter 1-{len(categories)}.")
                    except ValueError:
                        print("Invalid input. Enter a number.")

                # Get correction
                expected_correction = input("Enter expected neutral correction: ").strip()
                if not expected_correction:
                    expected_correction = None

            # Get confidence
            print("\nConfidence levels:")
            confidence_levels = list(ConfidenceLevel)
            for idx, conf in enumerate(confidence_levels, 1):
                print(f"  {idx}. {conf.value}")

            while True:
                try:
                    conf_input = input("Select confidence (1-5, default=4): ") or "4"
                    conf_idx = int(conf_input) - 1
                    if 0 <= conf_idx < len(confidence_levels):
                        confidence = confidence_levels[conf_idx]
                        break
                    print(f"Invalid input. Enter 1-{len(confidence_levels)}.")
                except ValueError:
                    print("Invalid input. Enter a number.")

            # Get demographic group
            print("\nDemographic groups:")
            demo_groups = list(DemographicGroup)
            for idx, group in enumerate(demo_groups, 1):
                print(f"  {idx}. {group.value}")

            while True:
                try:
                    demo_input = input(f"Select demographic group (1-{len(demo_groups)}, default=3): ") or "3"
                    demo_idx = int(demo_input) - 1
                    if 0 <= demo_idx < len(demo_groups):
                        demographic_group = demo_groups[demo_idx]
                        break
                    print(f"Invalid input. Enter 1-{len(demo_groups)}.")
                except ValueError:
                    print("Invalid input. Enter a number.")

            # Get gender referent
            print("\nGender referents:")
            gender_refs = list(GenderReferent)
            for idx, ref in enumerate(gender_refs, 1):
                print(f"  {idx}. {ref.value}")

            while True:
                try:
                    gender_input = input(f"Select gender referent (1-{len(gender_refs)}, default=3): ") or "3"
                    gender_idx = int(gender_input) - 1
                    if 0 <= gender_idx < len(gender_refs):
                        gender_referent = gender_refs[gender_idx]
                        break
                    print(f"Invalid input. Enter 1-{len(gender_refs)}.")
                except ValueError:
                    print("Invalid input. Enter a number.")

            # Optional notes
            notes = input("\nNotes (optional): ").strip() or None

            # Annotate the sample
            self.annotate_sample(
                sample,
                has_bias=has_bias,
                bias_category=bias_category,
                expected_correction=expected_correction,
                confidence=confidence,
                demographic_group=demographic_group,
                gender_referent=gender_referent,
                notes=notes,
            )

            print(f"\n✓ Sample {i+1} annotated")

            # Auto-save if enabled
            if auto_save:
                self.save_batch()

            # Ask to continue
            if i < total - 1:
                continue_input = input("\nContinue to next sample? (y/n, default=y): ") or "y"
                if continue_input.lower() != "y":
                    print(f"\nSession paused at sample {i+2}. Progress saved.")
                    break

        # Mark batch as complete if all samples annotated
        annotated_count = sum(
            1 for s in self.current_batch.samples if s.annotation_timestamp
        )
        if annotated_count == total:
            self.current_batch.is_complete = True
            self.current_batch.completed_at = datetime.now()
            self.save_batch()
            print(f"\n✅ Batch complete! All {total} samples annotated.")
        else:
            print(f"\n📊 Progress: {annotated_count}/{total} samples annotated")

    def export_to_csv(
        self,
        batch: Optional[AnnotationBatch] = None,
        output_file: Optional[Path] = None,
    ) -> Path:
        """Export annotation batch to CSV format.

        Args:
            batch: Batch to export (defaults to current_batch)
            output_file: Output CSV file path

        Returns:
            Path to exported CSV file
        """
        batch = batch or self.current_batch
        if not batch:
            raise ValueError("No batch to export")

        if not output_file:
            output_file = (
                self.output_dir / f"{batch.batch_id}_{batch.language}.csv"
            )

        # Write CSV with all 24 fields
        fieldnames = [
            "text",
            "has_bias",
            "bias_category",
            "expected_correction",
            "annotator_id",
            "confidence",
            "annotation_timestamp",
            "notes",
            "demographic_group",
            "gender_referent",
            "protected_attribute",
            "fairness_score",
            "context_requires_gender",
            "severity",
            "language_variant",
            "ml_prediction",
            "ml_confidence",
            "human_model_agreement",
            "correction_accepted",
            "source_dataset",
            "source_url",
            "collection_date",
            "multi_annotator",
            "version",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sample in batch.samples:
                row = sample.to_dict()
                writer.writerow(row)

        return output_file

    def get_stats(self, batch: Optional[AnnotationBatch] = None) -> AnnotationStats:
        """Get statistics for annotation batch.

        Args:
            batch: Batch to analyze (defaults to current_batch)

        Returns:
            AnnotationStats with computed metrics
        """
        batch = batch or self.current_batch
        if not batch:
            raise ValueError("No batch to analyze")

        return AnnotationStats.from_batch(batch)

    def print_stats(self, batch: Optional[AnnotationBatch] = None) -> None:
        """Print formatted statistics for batch.

        Args:
            batch: Batch to analyze (defaults to current_batch)
        """
        stats = self.get_stats(batch)

        print(f"\n{'='*70}")
        print("Annotation Statistics")
        print(f"{'='*70}")
        print(f"Total samples:      {stats.total_samples}")
        print(f"Annotated:          {stats.annotated_samples}")
        print(f"Bias detected:      {stats.bias_detected} ({stats.bias_percentage:.1f}%)")
        print(f"Avg confidence:     {stats.avg_confidence:.2f}/5.0")

        if stats.agreement_rate is not None:
            print(f"Agreement rate:     {stats.agreement_rate:.1%}")

        if stats.category_distribution:
            print("\nBias category distribution:")
            for category, count in sorted(
                stats.category_distribution.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {category:20s}: {count}")

        print(f"{'='*70}\n")
