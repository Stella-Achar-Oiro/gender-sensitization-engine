"""Input validation utilities for annotation workflow.

This module provides validation functions to ensure annotation quality
and consistency across the AI BRIDGE 24-field schema.
"""

from typing import List, Optional, Tuple, Dict, Any
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


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


class AnnotationValidator:
    """Validator for annotation data quality and consistency."""

    def __init__(self, strict: bool = True):
        """Initialize validator.

        Args:
            strict: If True, raise exceptions on validation failures.
                   If False, return validation results without raising.
        """
        self.strict = strict

    def validate_sample(
        self, sample: AnnotationSample
    ) -> Tuple[bool, List[str]]:
        """Validate a single annotation sample.

        Args:
            sample: Sample to validate

        Returns:
            Tuple of (is_valid, list of error messages)

        Raises:
            ValidationError: If strict=True and validation fails
        """
        errors = []

        # Rule 1: has_bias=True requires bias_category
        if sample.has_bias and not sample.bias_category:
            errors.append("has_bias is True but bias_category is missing")

        # Rule 2: has_bias=True requires expected_correction
        if sample.has_bias and not sample.expected_correction:
            errors.append("has_bias is True but expected_correction is missing")

        # Rule 3: has_bias=False should not have bias_category
        if not sample.has_bias and sample.bias_category:
            errors.append("has_bias is False but bias_category is provided")

        # Rule 4: has_bias=False should not have expected_correction
        if not sample.has_bias and sample.expected_correction:
            errors.append("has_bias is False but expected_correction is provided")

        # Rule 5: Text should not be empty
        if not sample.text or not sample.text.strip():
            errors.append("text field is empty")

        # Rule 6: Annotator ID should not be empty
        if not sample.annotator_id or not sample.annotator_id.strip():
            errors.append("annotator_id is empty")

        # Rule 7: Confidence should be valid enum
        if sample.confidence not in list(ConfidenceLevel):
            errors.append(f"Invalid confidence level: {sample.confidence}")

        # Rule 8: Demographic group should be valid enum
        if sample.demographic_group not in list(DemographicGroup):
            errors.append(f"Invalid demographic group: {sample.demographic_group}")

        # Rule 9: Gender referent should be valid enum
        if sample.gender_referent not in list(GenderReferent):
            errors.append(f"Invalid gender referent: {sample.gender_referent}")

        # Rule 10: Fairness score should be in [0, 1] if provided
        if sample.fairness_score is not None:
            if not 0.0 <= sample.fairness_score <= 1.0:
                errors.append(
                    f"fairness_score must be in [0, 1], got {sample.fairness_score}"
                )

        # Rule 11: ML confidence should be in [0, 1] if provided
        if sample.ml_confidence is not None:
            if not 0.0 <= sample.ml_confidence <= 1.0:
                errors.append(
                    f"ml_confidence must be in [0, 1], got {sample.ml_confidence}"
                )

        # Rule 12: If ml_prediction is provided, human_model_agreement should match
        if (
            sample.ml_prediction is not None
            and sample.human_model_agreement is not None
        ):
            expected_agreement = sample.ml_prediction == sample.has_bias
            if sample.human_model_agreement != expected_agreement:
                errors.append(
                    f"human_model_agreement={sample.human_model_agreement} "
                    f"but expected {expected_agreement} "
                    f"(ml_prediction={sample.ml_prediction}, has_bias={sample.has_bias})"
                )

        is_valid = len(errors) == 0

        if self.strict and not is_valid:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")

        return is_valid, errors

    def validate_batch(
        self, batch: AnnotationBatch
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate an entire annotation batch.

        Args:
            batch: Batch to validate

        Returns:
            Tuple of (is_valid, validation_report)

        Raises:
            ValidationError: If strict=True and validation fails
        """
        report: Dict[str, Any] = {
            "total_samples": len(batch.samples),
            "valid_samples": 0,
            "invalid_samples": 0,
            "errors_by_sample": {},
            "batch_errors": [],
        }

        # Validate batch-level fields
        if not batch.batch_id or not batch.batch_id.strip():
            report["batch_errors"].append("batch_id is empty")

        if not batch.language or batch.language not in ["en", "sw", "fr", "ki"]:
            report["batch_errors"].append(
                f"Invalid language: {batch.language}. Must be en, sw, fr, or ki"
            )

        if not batch.annotator_id or not batch.annotator_id.strip():
            report["batch_errors"].append("annotator_id is empty")

        # Validate each sample
        for i, sample in enumerate(batch.samples):
            is_valid, errors = self.validate_sample(sample)

            if is_valid:
                report["valid_samples"] += 1
            else:
                report["invalid_samples"] += 1
                report["errors_by_sample"][i] = errors

        # Check for consistency across batch
        if batch.samples:
            annotator_ids = set(s.annotator_id for s in batch.samples)
            if len(annotator_ids) > 1:
                report["batch_errors"].append(
                    f"Multiple annotator_ids in single batch: {annotator_ids}"
                )

        is_valid = (
            report["invalid_samples"] == 0 and len(report["batch_errors"]) == 0
        )

        if self.strict and not is_valid:
            error_summary = f"{report['invalid_samples']} invalid samples"
            if report["batch_errors"]:
                error_summary += f", batch errors: {'; '.join(report['batch_errors'])}"
            raise ValidationError(f"Batch validation failed: {error_summary}")

        return is_valid, report

    def validate_inter_annotator_agreement(
        self, samples: List[AnnotationSample], min_annotators: int = 2
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate multi-annotator agreement requirements.

        Args:
            samples: List of samples (should be multiple annotations of same text)
            min_annotators: Minimum number of annotators required

        Returns:
            Tuple of (is_valid, agreement_report)

        Raises:
            ValidationError: If strict=True and validation fails
        """
        report: Dict[str, Any] = {
            "num_samples": len(samples),
            "unique_annotators": 0,
            "agreement_rate": None,
            "errors": [],
        }

        if not samples:
            report["errors"].append("No samples provided")
            if self.strict:
                raise ValidationError("No samples for agreement validation")
            return False, report

        # Check that all samples have same text
        texts = set(s.text for s in samples)
        if len(texts) > 1:
            report["errors"].append(
                f"Samples have different texts: {len(texts)} unique texts"
            )

        # Count unique annotators
        annotators = set(s.annotator_id for s in samples)
        report["unique_annotators"] = len(annotators)

        if report["unique_annotators"] < min_annotators:
            report["errors"].append(
                f"Need at least {min_annotators} annotators, "
                f"got {report['unique_annotators']}"
            )

        # Calculate agreement rate on has_bias
        if len(samples) >= 2:
            has_bias_votes = [s.has_bias for s in samples]
            # Majority vote
            majority = sum(has_bias_votes) > len(has_bias_votes) / 2
            agreements = sum(1 for vote in has_bias_votes if vote == majority)
            report["agreement_rate"] = agreements / len(has_bias_votes)

        is_valid = len(report["errors"]) == 0

        if self.strict and not is_valid:
            raise ValidationError(
                f"Agreement validation failed: {'; '.join(report['errors'])}"
            )

        return is_valid, report

    def validate_ai_bridge_requirements(
        self, batch: AnnotationBatch, tier: str = "bronze"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate AI BRIDGE framework tier requirements.

        Args:
            batch: Batch to validate
            tier: Target tier (bronze, silver, gold)

        Returns:
            Tuple of (meets_requirements, requirements_report)

        Raises:
            ValidationError: If strict=True and requirements not met
        """
        tier = tier.lower()
        requirements = {
            "bronze": {"min_samples": 1200, "multi_annotator_pct": 0.10},
            "silver": {"min_samples": 5000, "multi_annotator_pct": 0.20},
            "gold": {"min_samples": 10000, "multi_annotator_pct": 0.30},
        }

        if tier not in requirements:
            raise ValueError(f"Invalid tier: {tier}. Must be bronze, silver, or gold")

        req = requirements[tier]
        report: Dict[str, Any] = {
            "tier": tier,
            "total_samples": len(batch.samples),
            "min_required": req["min_samples"],
            "multi_annotator_samples": 0,
            "multi_annotator_pct": 0.0,
            "required_pct": req["multi_annotator_pct"],
            "meets_requirements": False,
            "missing": [],
        }

        # Check sample count
        if report["total_samples"] < req["min_samples"]:
            report["missing"].append(
                f"Need {req['min_samples']} samples, "
                f"got {report['total_samples']}"
            )

        # Check multi-annotator percentage
        multi_annotator_count = sum(1 for s in batch.samples if s.multi_annotator)
        report["multi_annotator_samples"] = multi_annotator_count

        if report["total_samples"] > 0:
            report["multi_annotator_pct"] = (
                multi_annotator_count / report["total_samples"]
            )

        min_multi_annotator = int(req["min_samples"] * req["multi_annotator_pct"])
        if multi_annotator_count < min_multi_annotator:
            report["missing"].append(
                f"Need {min_multi_annotator} multi-annotator samples "
                f"({req['multi_annotator_pct']:.0%}), got {multi_annotator_count}"
            )

        # Check all samples are annotated
        unannotated = sum(
            1 for s in batch.samples if s.annotation_timestamp is None
        )
        if unannotated > 0:
            report["missing"].append(f"{unannotated} samples not yet annotated")

        report["meets_requirements"] = len(report["missing"]) == 0

        if self.strict and not report["meets_requirements"]:
            raise ValidationError(
                f"AI BRIDGE {tier} tier requirements not met: "
                f"{'; '.join(report['missing'])}"
            )

        return report["meets_requirements"], report

    def format_validation_report(
        self, report: Dict[str, Any], report_type: str = "batch"
    ) -> str:
        """Format validation report as human-readable string.

        Args:
            report: Validation report dict
            report_type: Type of report (batch, agreement, requirements)

        Returns:
            Formatted report string
        """
        lines = ["\n" + "=" * 70, f"Validation Report: {report_type.title()}", "=" * 70]

        if report_type == "batch":
            lines.extend([
                f"Total samples:    {report['total_samples']}",
                f"Valid samples:    {report['valid_samples']}",
                f"Invalid samples:  {report['invalid_samples']}",
            ])

            if report["batch_errors"]:
                lines.append("\nBatch-level errors:")
                for error in report["batch_errors"]:
                    lines.append(f"  - {error}")

            if report["errors_by_sample"]:
                lines.append(f"\nSample errors ({len(report['errors_by_sample'])} samples):")
                for idx, errors in list(report["errors_by_sample"].items())[:5]:
                    lines.append(f"  Sample {idx}:")
                    for error in errors:
                        lines.append(f"    - {error}")
                if len(report["errors_by_sample"]) > 5:
                    lines.append(f"  ... and {len(report['errors_by_sample']) - 5} more")

        elif report_type == "agreement":
            lines.extend([
                f"Samples:          {report['num_samples']}",
                f"Unique annotators: {report['unique_annotators']}",
            ])
            if report["agreement_rate"] is not None:
                lines.append(f"Agreement rate:   {report['agreement_rate']:.1%}")

            if report["errors"]:
                lines.append("\nErrors:")
                for error in report["errors"]:
                    lines.append(f"  - {error}")

        elif report_type == "requirements":
            lines.extend([
                f"Target tier:      {report['tier'].upper()}",
                f"Total samples:    {report['total_samples']} / {report['min_required']}",
                f"Multi-annotator:  {report['multi_annotator_samples']} "
                f"({report['multi_annotator_pct']:.1%} / {report['required_pct']:.0%})",
                f"Meets requirements: {'✅ YES' if report['meets_requirements'] else '❌ NO'}",
            ])

            if report["missing"]:
                lines.append("\nMissing requirements:")
                for item in report["missing"]:
                    lines.append(f"  - {item}")

        lines.append("=" * 70 + "\n")
        return "\n".join(lines)
