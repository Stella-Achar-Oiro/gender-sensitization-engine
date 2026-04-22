"""AI BRIDGE schema enforcement and validation.

This module ensures all annotations comply with the AI BRIDGE framework's
24-field schema requirements for comprehensive bias detection evaluation.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime

from annotation.models import (
    AnnotationSample,
    AnnotationBatch,
    BiasCategory,
    ConfidenceLevel,
    DemographicGroup,
    GenderReferent,
    SeverityLevel,
)


# AI BRIDGE 24 Required Fields
REQUIRED_FIELDS = [
    # Core fields (1-4)
    "text",
    "has_bias",
    "bias_category",
    "expected_correction",
    # Metadata (5-8)
    "annotator_id",
    "confidence",
    "annotation_timestamp",
    "notes",
    # Fairness (9-12)
    "demographic_group",
    "gender_referent",
    "protected_attribute",
    "fairness_score",
    # Context (13-15)
    "context_requires_gender",
    "severity",
    "language_variant",
    # HITL (16-19)
    "ml_prediction",
    "ml_confidence",
    "human_model_agreement",
    "correction_accepted",
    # Provenance (20-23)
    "source_dataset",
    "source_url",
    "collection_date",
    "multi_annotator",
    # Version (24)
    "version",
]


class AIBRIDGESchemaEnforcer:
    """Enforces AI BRIDGE schema compliance on annotations."""

    def __init__(self):
        """Initialize schema enforcer."""
        self.required_fields = set(REQUIRED_FIELDS)

    def validate_schema(
        self, sample: AnnotationSample
    ) -> tuple[bool, List[str]]:
        """Validate that sample has all required AI BRIDGE fields.

        Args:
            sample: Annotation sample to validate

        Returns:
            Tuple of (is_valid, list of missing fields)
        """
        sample_dict = sample.to_dict()
        sample_fields = set(sample_dict.keys())
        missing_fields = self.required_fields - sample_fields

        return len(missing_fields) == 0, sorted(missing_fields)

    def validate_batch(
        self, batch: AnnotationBatch
    ) -> Dict[str, any]:
        """Validate entire batch for AI BRIDGE compliance.

        Args:
            batch: Annotation batch to validate

        Returns:
            Validation report dictionary
        """
        report = {
            "total_samples": len(batch.samples),
            "compliant_samples": 0,
            "non_compliant_samples": 0,
            "missing_fields_by_sample": {},
            "all_compliant": False,
        }

        for i, sample in enumerate(batch.samples):
            is_valid, missing = self.validate_schema(sample)
            if is_valid:
                report["compliant_samples"] += 1
            else:
                report["non_compliant_samples"] += 1
                report["missing_fields_by_sample"][i] = missing

        report["all_compliant"] = report["non_compliant_samples"] == 0
        return report

    def enforce_schema(self, sample_dict: Dict) -> AnnotationSample:
        """Enforce schema on dictionary, filling defaults for missing fields.

        Args:
            sample_dict: Dictionary with annotation data

        Returns:
            AnnotationSample with all required fields

        Raises:
            ValueError: If required core fields are missing
        """
        # Ensure core fields are present
        required_core = ["text", "has_bias", "annotator_id"]
        missing_core = [f for f in required_core if f not in sample_dict]
        if missing_core:
            raise ValueError(
                f"Missing required core fields: {', '.join(missing_core)}"
            )

        # Set defaults for optional fields
        defaults = {
            "bias_category": None,
            "expected_correction": None,
            "confidence": ConfidenceLevel.MEDIUM,
            "annotation_timestamp": datetime.now(),
            "notes": None,
            "demographic_group": DemographicGroup.NEUTRAL_REFERENT,
            "gender_referent": GenderReferent.NEUTRAL,
            "protected_attribute": None,
            "fairness_score": None,
            "context_requires_gender": False,
            "severity": SeverityLevel.REPLACE,
            "language_variant": None,
            "ml_prediction": None,
            "ml_confidence": None,
            "human_model_agreement": None,
            "correction_accepted": None,
            "source_dataset": None,
            "source_url": None,
            "collection_date": None,
            "multi_annotator": False,
            "version": "1.0",
        }

        # Merge with defaults
        full_dict = {**defaults, **sample_dict}

        # Create and return AnnotationSample
        return AnnotationSample(**full_dict)

    def check_field_coverage(
        self, samples: List[AnnotationSample]
    ) -> Dict[str, float]:
        """Check field coverage across samples.

        Args:
            samples: List of annotation samples

        Returns:
            Dictionary mapping field name to coverage percentage
        """
        if not samples:
            return {}

        field_counts = {field: 0 for field in self.required_fields}

        for sample in samples:
            sample_dict = sample.to_dict()
            for field in self.required_fields:
                value = sample_dict.get(field)
                # Count as covered if not None (except for boolean False)
                if value is not None or isinstance(value, bool):
                    field_counts[field] += 1

        total = len(samples)
        coverage = {
            field: (count / total) * 100
            for field, count in field_counts.items()
        }

        return coverage

    def generate_compliance_report(
        self, batch: AnnotationBatch
    ) -> str:
        """Generate human-readable compliance report.

        Args:
            batch: Annotation batch to report on

        Returns:
            Formatted report string
        """
        validation = self.validate_batch(batch)
        coverage = self.check_field_coverage(batch.samples)

        lines = [
            "\n" + "=" * 70,
            "AI BRIDGE Schema Compliance Report",
            "=" * 70,
            f"Batch ID: {batch.batch_id}",
            f"Language: {batch.language}",
            f"Total Samples: {validation['total_samples']}",
            "",
            "Schema Validation:",
            f"  Compliant:     {validation['compliant_samples']} samples",
            f"  Non-compliant: {validation['non_compliant_samples']} samples",
            f"  Status:        {'✅ PASS' if validation['all_compliant'] else '❌ FAIL'}",
        ]

        if validation["missing_fields_by_sample"]:
            lines.append("\nNon-compliant Samples:")
            for idx, missing in list(
                validation["missing_fields_by_sample"].items()
            )[:5]:
                lines.append(f"  Sample {idx}: Missing {', '.join(missing)}")
            if len(validation["missing_fields_by_sample"]) > 5:
                remaining = len(validation["missing_fields_by_sample"]) - 5
                lines.append(f"  ... and {remaining} more")

        # Field coverage summary
        lines.append("\nField Coverage:")
        for field in sorted(coverage.keys()):
            pct = coverage[field]
            status = "✅" if pct == 100.0 else "⚠️"
            lines.append(f"  {status} {field:30s}: {pct:5.1f}%")

        # Overall compliance
        avg_coverage = sum(coverage.values()) / len(coverage)
        lines.extend([
            "",
            f"Average Coverage: {avg_coverage:.1f}%",
            "=" * 70,
            "",
        ])

        return "\n".join(lines)


def validate_ai_bridge_compliance(
    batch: AnnotationBatch,
) -> tuple[bool, Dict]:
    """Convenience function to validate AI BRIDGE compliance.

    Args:
        batch: Annotation batch to validate

    Returns:
        Tuple of (is_compliant, validation_report)
    """
    enforcer = AIBRIDGESchemaEnforcer()
    report = enforcer.validate_batch(batch)
    return report["all_compliant"], report


def print_compliance_report(batch: AnnotationBatch) -> None:
    """Print AI BRIDGE compliance report to console.

    Args:
        batch: Annotation batch to report on
    """
    enforcer = AIBRIDGESchemaEnforcer()
    report = enforcer.generate_compliance_report(batch)
    print(report)
