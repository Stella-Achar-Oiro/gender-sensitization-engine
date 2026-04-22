"""Quality assurance checks for annotation data.

This module provides quality metrics and checks to ensure annotation
consistency, detect fatigue, identify bias imbalance, and validate
overall annotation quality.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np

from annotation.models import (
    AnnotationSample,
    AnnotationBatch,
    ConfidenceLevel,
)


class AnnotationQualityChecker:
    """Quality assurance checker for annotations."""

    def __init__(self):
        """Initialize quality checker."""
        self.thresholds = {
            "min_confidence_high": 0.40,  # At least 40% high confidence
            "max_confidence_high": 0.70,  # At most 70% high confidence
            "min_bias_rate": 0.30,  # At least 30% biased samples
            "max_bias_rate": 0.70,  # At most 70% biased samples
            "max_time_per_sample_seconds": 600,  # 10 minutes max
            "min_samples_for_fatigue_check": 20,  # Need 20+ samples to check fatigue
        }

    def check_confidence_distribution(
        self, samples: List[AnnotationSample]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if confidence distribution is balanced.

        Args:
            samples: List of annotation samples

        Returns:
            Tuple of (is_balanced, distribution_dict)
        """
        if not samples:
            return False, {"error": "No samples provided"}

        confidence_counts = {
            "very_low": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0,
        }

        for sample in samples:
            conf = str(sample.confidence)
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

        total = len(samples)
        confidence_pcts = {
            level: (count / total) * 100
            for level, count in confidence_counts.items()
        }

        # Check if distribution is balanced (not all one level)
        high_pct = confidence_pcts.get("high", 0) + confidence_pcts.get("very_high", 0)
        is_balanced = (
            high_pct >= self.thresholds["min_confidence_high"] * 100
            and high_pct <= self.thresholds["max_confidence_high"] * 100
        )

        return is_balanced, {
            "counts": confidence_counts,
            "percentages": confidence_pcts,
            "high_confidence_pct": high_pct,
            "is_balanced": is_balanced,
            "issue": None if is_balanced else "Confidence distribution imbalanced",
        }

    def check_bias_balance(
        self, samples: List[AnnotationSample]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if bias labels are balanced (not all biased or all neutral).

        Args:
            samples: List of annotation samples

        Returns:
            Tuple of (is_balanced, balance_dict)
        """
        if not samples:
            return False, {"error": "No samples provided"}

        biased_count = sum(1 for s in samples if s.has_bias)
        total = len(samples)
        bias_rate = biased_count / total if total > 0 else 0

        is_balanced = (
            self.thresholds["min_bias_rate"]
            <= bias_rate
            <= self.thresholds["max_bias_rate"]
        )

        return is_balanced, {
            "biased_count": biased_count,
            "neutral_count": total - biased_count,
            "total": total,
            "bias_rate": bias_rate,
            "is_balanced": is_balanced,
            "issue": None
            if is_balanced
            else f"Bias rate {bias_rate:.1%} outside acceptable range",
        }

    def check_annotator_consistency(
        self, samples: List[AnnotationSample], window_size: int = 10
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check annotator consistency over time (sliding window).

        Args:
            samples: List of annotation samples (in chronological order)
            window_size: Size of sliding window for consistency check

        Returns:
            Tuple of (is_consistent, consistency_dict)
        """
        if len(samples) < window_size * 2:
            return True, {"warning": "Not enough samples for consistency check"}

        # Calculate bias rate in sliding windows
        window_bias_rates = []
        for i in range(len(samples) - window_size + 1):
            window = samples[i : i + window_size]
            bias_rate = sum(1 for s in window if s.has_bias) / len(window)
            window_bias_rates.append(bias_rate)

        # Check variance
        variance = np.var(window_bias_rates)
        std_dev = np.std(window_bias_rates)

        # Consistent if std dev is low (< 0.20)
        is_consistent = std_dev < 0.20

        return is_consistent, {
            "window_size": window_size,
            "num_windows": len(window_bias_rates),
            "mean_bias_rate": np.mean(window_bias_rates),
            "std_dev": std_dev,
            "variance": variance,
            "is_consistent": is_consistent,
            "issue": None
            if is_consistent
            else f"High variance in annotation pattern (σ={std_dev:.3f})",
        }

    def detect_fatigue(
        self, samples: List[AnnotationSample]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Detect annotation fatigue by analyzing temporal patterns.

        Args:
            samples: List of annotation samples with timestamps

        Returns:
            Tuple of (fatigue_detected, fatigue_dict)
        """
        # Filter samples with timestamps
        timestamped = [s for s in samples if s.annotation_timestamp]

        if len(timestamped) < self.thresholds["min_samples_for_fatigue_check"]:
            return False, {"warning": "Not enough timestamped samples"}

        # Sort by timestamp
        sorted_samples = sorted(
            timestamped, key=lambda s: s.annotation_timestamp
        )

        # Calculate annotation rate over time (samples per minute)
        first_half = sorted_samples[: len(sorted_samples) // 2]
        second_half = sorted_samples[len(sorted_samples) // 2 :]

        def calculate_rate(samples_subset):
            if len(samples_subset) < 2:
                return None
            duration = (
                samples_subset[-1].annotation_timestamp
                - samples_subset[0].annotation_timestamp
            )
            if duration.total_seconds() == 0:
                return None
            return len(samples_subset) / (duration.total_seconds() / 60)

        first_rate = calculate_rate(first_half)
        second_rate = calculate_rate(second_half)

        fatigue_detected = False
        if first_rate and second_rate and first_rate > 0:
            # Fatigue if second half is >30% slower
            slowdown_pct = (first_rate - second_rate) / first_rate
            fatigue_detected = slowdown_pct > 0.30

        return fatigue_detected, {
            "first_half_rate": first_rate,
            "second_half_rate": second_rate,
            "slowdown_detected": fatigue_detected,
            "issue": "Possible fatigue detected (annotation rate decreased)"
            if fatigue_detected
            else None,
        }

    def check_schema_completeness(
        self, samples: List[AnnotationSample]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check schema completeness (all required fields present).

        Args:
            samples: List of annotation samples

        Returns:
            Tuple of (is_complete, completeness_dict)
        """
        if not samples:
            return False, {"error": "No samples provided"}

        required_fields = [
            "text",
            "has_bias",
            "annotator_id",
            "confidence",
            "demographic_group",
            "gender_referent",
        ]

        field_coverage = {}
        for field in required_fields:
            covered = sum(
                1 for s in samples if getattr(s, field, None) is not None
            )
            field_coverage[field] = (covered / len(samples)) * 100

        all_complete = all(coverage == 100.0 for coverage in field_coverage.values())

        return all_complete, {
            "field_coverage": field_coverage,
            "is_complete": all_complete,
            "issue": None if all_complete else "Some required fields incomplete",
        }

    def calculate_quality_score(
        self, samples: List[AnnotationSample]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate overall quality score (0-100).

        Args:
            samples: List of annotation samples

        Returns:
            Tuple of (quality_score, detailed_metrics)
        """
        checks = {
            "confidence_distribution": self.check_confidence_distribution(samples),
            "bias_balance": self.check_bias_balance(samples),
            "annotator_consistency": self.check_annotator_consistency(samples),
            "fatigue_detection": self.detect_fatigue(samples),
            "schema_completeness": self.check_schema_completeness(samples),
        }

        # Calculate score (each check worth 20 points)
        score = 0.0
        for check_name, (passed, details) in checks.items():
            if passed:
                score += 20.0

        detailed_metrics = {
            check_name: details for check_name, (_, details) in checks.items()
        }

        return score, detailed_metrics

    def generate_quality_report(
        self, batch: AnnotationBatch
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report for batch.

        Args:
            batch: Annotation batch to analyze

        Returns:
            Quality report dictionary
        """
        score, metrics = self.calculate_quality_score(batch.samples)

        # Identify issues
        issues = []
        for check_name, details in metrics.items():
            if details.get("issue"):
                issues.append({
                    "check": check_name,
                    "issue": details["issue"],
                })

        # Overall assessment
        if score >= 80:
            assessment = "Excellent"
        elif score >= 60:
            assessment = "Good"
        elif score >= 40:
            assessment = "Fair"
        else:
            assessment = "Poor"

        return {
            "batch_id": batch.batch_id,
            "annotator_id": batch.annotator_id,
            "language": batch.language,
            "total_samples": len(batch.samples),
            "quality_score": score,
            "assessment": assessment,
            "metrics": metrics,
            "issues": issues,
            "passes_quality_check": score >= 60,
        }
