"""Tests for test helper functions."""
import pytest
from tests.test_helpers import (
    assert_no_false_positives,
    assert_detection_quality,
    assert_case_preservation,
    count_bias_detections
)
from eval.models import BiasDetectionResult


def test_assert_no_false_positives_passes():
    """Test that helper passes with valid results."""
    results = [
        BiasDetectionResult(
            text="The chairman will lead",
            has_bias_detected=True,
            detected_edits=[{"original": "chairman", "replacement": "chair", "position": 0}],
            confidence=0.95
        ),
        BiasDetectionResult(
            text="The table is wooden",
            has_bias_detected=False,
            detected_edits=[],
            confidence=0.9
        )
    ]
    # Should not raise
    assert_no_false_positives(results)


def test_assert_no_false_positives_fails():
    """Test that helper catches false positives."""
    results = [
        BiasDetectionResult(
            text="The table is wooden",
            has_bias_detected=True,
            detected_edits=[],  # False positive!
            confidence=0.95
        )
    ]
    with pytest.raises(AssertionError, match="False positive"):
        assert_no_false_positives(results)


def test_assert_detection_quality_with_bias():
    """Test detection quality assertion for biased text."""
    result = BiasDetectionResult(
        text="The chairman will lead",
        has_bias_detected=True,
        detected_edits=[{"original": "chairman", "replacement": "chair", "position": 0}],
        confidence=0.95
    )
    # Should not raise
    assert_detection_quality(result, expected_bias=True, min_confidence=0.7)


def test_assert_detection_quality_without_bias():
    """Test detection quality assertion for neutral text."""
    result = BiasDetectionResult(
        text="The table is wooden",
        has_bias_detected=False,
        detected_edits=[],
        confidence=0.9
    )
    # Should not raise
    assert_detection_quality(result, expected_bias=False)


def test_assert_detection_quality_low_confidence():
    """Test that low confidence is caught."""
    result = BiasDetectionResult(
        text="The chairman will lead",
        has_bias_detected=True,
        detected_edits=[{"original": "chairman", "replacement": "chair", "position": 0}],
        confidence=0.5  # Too low!
    )
    with pytest.raises(AssertionError, match="Confidence"):
        assert_detection_quality(result, expected_bias=True, min_confidence=0.7)


def test_assert_case_preservation_preserved():
    """Test case preservation assertion when case is preserved."""
    assert_case_preservation("Chairman", "Chairperson")  # Should pass


def test_assert_case_preservation_not_preserved():
    """Test case preservation assertion catches violations."""
    with pytest.raises(AssertionError, match="Case not preserved"):
        assert_case_preservation("Chairman", "chairperson")


def test_count_bias_detections_empty():
    """Test counting with empty results."""
    stats = count_bias_detections([])
    assert stats["total"] == 0
    assert stats["bias_detected"] == 0
    assert stats["avg_confidence"] == 0.0


def test_count_bias_detections_mixed():
    """Test counting with mixed results."""
    results = [
        BiasDetectionResult(
            text="The chairman will lead",
            has_bias_detected=True,
            detected_edits=[{"original": "chairman", "replacement": "chair", "position": 0}],
            confidence=0.95
        ),
        BiasDetectionResult(
            text="The table is wooden",
            has_bias_detected=False,
            detected_edits=[],
            confidence=0.85
        ),
        BiasDetectionResult(
            text="The policeman arrested",
            has_bias_detected=True,
            detected_edits=[{"original": "policeman", "replacement": "police officer", "position": 0}],
            confidence=0.90
        )
    ]

    stats = count_bias_detections(results)

    assert stats["total"] == 3
    assert stats["bias_detected"] == 2
    assert stats["no_bias"] == 1
    assert 0.89 < stats["avg_confidence"] < 0.91  # Average of 0.95, 0.85, 0.90
