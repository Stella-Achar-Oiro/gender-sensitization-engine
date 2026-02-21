"""Export utilities for annotation data.

This module provides functions to export annotations to various formats,
including ground truth CSV format compatible with the evaluation pipeline.
"""

import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from annotation.models import AnnotationSample, AnnotationBatch


class AnnotationExporter:
    """Export annotations to various formats."""

    @staticmethod
    def to_ground_truth_csv(
        batch: AnnotationBatch,
        output_file: Path,
        include_all_fields: bool = True,
    ) -> Path:
        """Export batch to ground truth CSV format.

        Args:
            batch: Annotation batch to export
            output_file: Output CSV file path
            include_all_fields: If True, include all 24 AI BRIDGE fields.
                               If False, only include core evaluation fields.

        Returns:
            Path to created CSV file
        """
        if include_all_fields:
            # All 24 AI BRIDGE fields
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
        else:
            # Core fields only (for backward compatibility)
            fieldnames = [
                "text",
                "has_bias",
                "bias_category",
                "expected_correction",
                "annotator_id",
                "confidence",
                "demographic_group",
                "gender_referent",
            ]

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sample in batch.samples:
                row = sample.to_dict()
                # Filter to requested fields
                filtered_row = {k: row[k] for k in fieldnames if k in row}
                writer.writerow(filtered_row)

        return output_file

    @staticmethod
    def merge_batches_to_ground_truth(
        batches: List[AnnotationBatch],
        output_file: Path,
        language: str,
    ) -> Path:
        """Merge multiple batches into single ground truth file.

        Args:
            batches: List of annotation batches to merge
            output_file: Output ground truth CSV path
            language: Language code (en, sw, fr, ki)

        Returns:
            Path to merged ground truth file
        """
        # Combine all samples
        all_samples = []
        for batch in batches:
            all_samples.extend(batch.samples)

        # Create merged batch
        merged_batch = AnnotationBatch(
            batch_id=f"merged_{language}_{datetime.now().strftime('%Y%m%d')}",
            language=language,
            samples=all_samples,
            annotator_id="multiple",
        )

        # Export to ground truth format
        return AnnotationExporter.to_ground_truth_csv(
            merged_batch, output_file, include_all_fields=True
        )

    @staticmethod
    def export_disagreements(
        samples: List[AnnotationSample],
        output_file: Path,
    ) -> Path:
        """Export samples where annotators disagreed.

        Args:
            samples: List of annotation samples with disagreements
            output_file: Output CSV file path

        Returns:
            Path to created CSV file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "text",
            "annotator_id",
            "has_bias",
            "bias_category",
            "expected_correction",
            "confidence",
            "human_model_agreement",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sample in samples:
                row = sample.to_dict()
                filtered_row = {k: row.get(k) for k in fieldnames}
                writer.writerow(filtered_row)

        return output_file

    @staticmethod
    def export_statistics_report(
        batch: AnnotationBatch,
        output_file: Path,
    ) -> Path:
        """Export batch statistics to text report.

        Args:
            batch: Annotation batch
            output_file: Output text file path

        Returns:
            Path to created report file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        total = len(batch.samples)
        bias_count = sum(1 for s in batch.samples if s.has_bias)

        # Category distribution
        categories = {}
        for sample in batch.samples:
            if sample.bias_category:
                cat = str(sample.bias_category)
                categories[cat] = categories.get(cat, 0) + 1

        # Confidence distribution
        confidences = {}
        for sample in batch.samples:
            conf = str(sample.confidence)
            confidences[conf] = confidences.get(conf, 0) + 1

        # Demographic distribution
        demographics = {}
        for sample in batch.samples:
            demo = str(sample.demographic_group)
            demographics[demo] = demographics.get(demo, 0) + 1

        lines = [
            "=" * 70,
            f"Annotation Batch Statistics: {batch.batch_id}",
            "=" * 70,
            "",
            f"Language: {batch.language}",
            f"Annotator: {batch.annotator_id}",
            f"Created: {batch.created_at.isoformat()}",
            f"Completed: {batch.completed_at.isoformat() if batch.completed_at else 'In progress'}",
            "",
            "Sample Statistics:",
            f"  Total samples:    {total}",
            f"  Biased samples:   {bias_count} ({bias_count/total*100:.1f}%)",
            f"  Neutral samples:  {total - bias_count} ({(total-bias_count)/total*100:.1f}%)",
            f"  Completion rate:  {batch.completion_rate:.1%}",
        ]

        if batch.agreement_rate is not None:
            lines.append(f"  Agreement rate:   {batch.agreement_rate:.1%}")

        lines.extend([
            "",
            "Bias Category Distribution:",
        ])
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat:30s}: {count:4d} ({count/total*100:5.1f}%)")

        lines.extend([
            "",
            "Confidence Distribution:",
        ])
        for conf, count in sorted(confidences.items()):
            lines.append(f"  {conf:30s}: {count:4d} ({count/total*100:5.1f}%)")

        lines.extend([
            "",
            "Demographic Distribution:",
        ])
        for demo, count in sorted(demographics.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {demo:30s}: {count:4d} ({count/total*100:5.1f}%)")

        lines.extend([
            "",
            "=" * 70,
        ])

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_file
