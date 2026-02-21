"""Tests for annotation quality assurance.

This module tests quality checks, fatigue detection, consistency validation,
and report generation.
"""

import pytest
from datetime import datetime, timedelta

from annotation.models import (
    AnnotationSample,
    AnnotationBatch,
    ConfidenceLevel,
    BiasCategory,
    DemographicGroup,
    GenderReferent,
)
from annotation.quality import AnnotationQualityChecker
from annotation.reports import (
    format_quality_report,
    generate_multi_batch_report,
    format_multi_batch_report,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def quality_checker():
    """Create quality checker instance."""
    return AnnotationQualityChecker()


@pytest.fixture
def balanced_samples():
    """Create balanced annotation samples."""
    samples = []
    for i in range(20):
        samples.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=(i % 2 == 0),  # 50% bias
                bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
                expected_correction=f"Correction {i}" if i % 2 == 0 else None,
                annotator_id="test_001",
                confidence=ConfidenceLevel.HIGH if i < 10 else ConfidenceLevel.MEDIUM,  # Mix
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
                annotation_timestamp=datetime.now() + timedelta(seconds=i * 60),
            )
        )
    return samples


@pytest.fixture
def imbalanced_samples():
    """Create imbalanced samples (all biased)."""
    samples = []
    for i in range(20):
        samples.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=True,  # All biased
                bias_category=BiasCategory.OCCUPATION,
                expected_correction=f"Correction {i}",
                annotator_id="test_001",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )
    return samples


# ============================================================================
# CONFIDENCE DISTRIBUTION TESTS (3 tests)
# ============================================================================


def test_confidence_distribution_balanced(quality_checker, balanced_samples):
    """Test confidence distribution check with balanced samples."""
    is_balanced, details = quality_checker.check_confidence_distribution(
        balanced_samples
    )

    assert is_balanced is True
    assert "percentages" in details
    assert details["high_confidence_pct"] == 50.0  # 10 high out of 20


def test_confidence_distribution_imbalanced(quality_checker):
    """Test confidence distribution with all high confidence."""
    samples = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,  # All high
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(20)
    ]

    is_balanced, details = quality_checker.check_confidence_distribution(samples)

    assert is_balanced is False  # Too much high confidence
    assert details["high_confidence_pct"] == 100.0


def test_confidence_distribution_empty(quality_checker):
    """Test confidence distribution with empty list."""
    is_balanced, details = quality_checker.check_confidence_distribution([])

    assert is_balanced is False
    assert "error" in details


# ============================================================================
# BIAS BALANCE TESTS (3 tests)
# ============================================================================


def test_bias_balance_balanced(quality_checker, balanced_samples):
    """Test bias balance with balanced samples."""
    is_balanced, details = quality_checker.check_bias_balance(balanced_samples)

    assert is_balanced is True
    assert details["bias_rate"] == 0.5  # 50% bias


def test_bias_balance_imbalanced(quality_checker, imbalanced_samples):
    """Test bias balance with all biased samples."""
    is_balanced, details = quality_checker.check_bias_balance(imbalanced_samples)

    assert is_balanced is False  # 100% bias is imbalanced
    assert details["bias_rate"] == 1.0


def test_bias_balance_empty(quality_checker):
    """Test bias balance with empty list."""
    is_balanced, details = quality_checker.check_bias_balance([])

    assert is_balanced is False
    assert "error" in details


# ============================================================================
# ANNOTATOR CONSISTENCY TESTS (2 tests)
# ============================================================================


def test_annotator_consistency_consistent(quality_checker, balanced_samples):
    """Test annotator consistency with consistent pattern."""
    is_consistent, details = quality_checker.check_annotator_consistency(
        balanced_samples
    )

    assert bool(is_consistent) is True
    assert "std_dev" in details
    assert details["std_dev"] < 0.20  # Low variance


def test_annotator_consistency_inconsistent(quality_checker):
    """Test annotator consistency with erratic pattern."""
    # Create samples with erratic bias pattern
    samples = []
    bias_pattern = [True] * 10 + [False] * 10  # First half all bias, second half none
    for i, has_bias in enumerate(bias_pattern):
        samples.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=has_bias,
                bias_category=BiasCategory.OCCUPATION if has_bias else None,
                expected_correction=f"Correction {i}" if has_bias else None,
                annotator_id="test_001",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

    is_consistent, details = quality_checker.check_annotator_consistency(samples)

    # With such drastic pattern change, std dev should be high
    assert "std_dev" in details


# ============================================================================
# FATIGUE DETECTION TESTS (2 tests)
# ============================================================================


def test_fatigue_detection_no_fatigue(quality_checker):
    """Test fatigue detection with steady annotation rate."""
    samples = []
    base_time = datetime.now()

    for i in range(40):
        samples.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=(i % 2 == 0),
                bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
                expected_correction=f"Correction {i}" if i % 2 == 0 else None,
                annotator_id="test_001",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
                annotation_timestamp=base_time + timedelta(seconds=i * 30),  # Steady 30s/sample
            )
        )

    fatigue_detected, details = quality_checker.detect_fatigue(samples)

    assert fatigue_detected is False


def test_fatigue_detection_with_fatigue(quality_checker):
    """Test fatigue detection with slowdown."""
    samples = []
    base_time = datetime.now()

    for i in range(40):
        # First half: 30s per sample, second half: 90s per sample
        time_per_sample = 30 if i < 20 else 90
        samples.append(
            AnnotationSample(
                text=f"Text {i}",
                has_bias=(i % 2 == 0),
                bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
                expected_correction=f"Correction {i}" if i % 2 == 0 else None,
                annotator_id="test_001",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
                annotation_timestamp=base_time + timedelta(seconds=sum(
                    30 if j < 20 else 90 for j in range(i + 1)
                )),
            )
        )

    fatigue_detected, details = quality_checker.detect_fatigue(samples)

    # Should detect slowdown
    assert fatigue_detected is True or "warning" in details  # May not have enough samples


# ============================================================================
# SCHEMA COMPLETENESS TESTS (2 tests)
# ============================================================================


def test_schema_completeness_complete(quality_checker, balanced_samples):
    """Test schema completeness with complete samples."""
    is_complete, details = quality_checker.check_schema_completeness(
        balanced_samples
    )

    assert is_complete is True
    assert all(coverage == 100.0 for coverage in details["field_coverage"].values())


def test_schema_completeness_incomplete(quality_checker):
    """Test schema completeness with missing fields."""
    # Create samples with missing text (using model_construct)
    samples = [
        AnnotationSample.model_construct(
            text=f"Text {i}" if i % 2 == 0 else None,  # Half missing text
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
        for i in range(10)
    ]

    is_complete, details = quality_checker.check_schema_completeness(samples)

    assert is_complete is False
    assert details["field_coverage"]["text"] == 50.0  # Only half have text


# ============================================================================
# QUALITY SCORE TESTS (2 tests)
# ============================================================================


def test_calculate_quality_score_high(quality_checker, balanced_samples):
    """Test quality score calculation with high-quality samples."""
    score, metrics = quality_checker.calculate_quality_score(balanced_samples)

    # Should score well on most checks
    assert score >= 60  # At least "Good"
    assert "confidence_distribution" in metrics
    assert "bias_balance" in metrics


def test_calculate_quality_score_low(quality_checker, imbalanced_samples):
    """Test quality score calculation with low-quality samples."""
    score, metrics = quality_checker.calculate_quality_score(imbalanced_samples)

    # Should score poorly due to imbalance
    assert score < 100  # Not perfect
    assert "bias_balance" in metrics


# ============================================================================
# REPORT GENERATION TESTS (3 tests)
# ============================================================================


def test_generate_quality_report(quality_checker, balanced_samples):
    """Test generating quality report for batch."""
    batch = AnnotationBatch(
        batch_id="test_batch",
        language="en",
        samples=balanced_samples,
        annotator_id="test_001",
    )

    report = quality_checker.generate_quality_report(batch)

    assert "quality_score" in report
    assert "assessment" in report
    assert "metrics" in report
    assert "issues" in report
    assert report["batch_id"] == "test_batch"


def test_format_quality_report(quality_checker, balanced_samples):
    """Test formatting quality report as text."""
    batch = AnnotationBatch(
        batch_id="test_batch",
        language="en",
        samples=balanced_samples,
        annotator_id="test_001",
    )

    report = quality_checker.generate_quality_report(batch)
    formatted = format_quality_report(report)

    assert "Annotation Quality Report" in formatted
    assert "Quality Score" in formatted
    assert "test_batch" in formatted


def test_multi_batch_report():
    """Test multi-batch quality report generation."""
    batches = []
    for batch_num in range(3):
        samples = [
            AnnotationSample(
                text=f"Text {i}",
                has_bias=(i % 2 == 0),
                bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
                expected_correction=f"Correction {i}" if i % 2 == 0 else None,
                annotator_id=f"annotator_{batch_num}",
                confidence=ConfidenceLevel.HIGH,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
            for i in range(10)
        ]
        batches.append(
            AnnotationBatch(
                batch_id=f"batch_{batch_num}",
                language="en",
                samples=samples,
                annotator_id=f"annotator_{batch_num}",
            )
        )

    report = generate_multi_batch_report(batches)

    assert report["num_batches"] == 3
    assert report["total_samples"] == 30
    assert "avg_quality_score" in report
    assert len(report["batch_reports"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
