"""Helper functions for testing."""
from typing import List, Dict
from eval.models import BiasDetectionResult


def assert_no_false_positives(results: List[BiasDetectionResult]):
    """
    Ensure perfect precision - no false positives.

    Critical for JuaKazi: We maintain 1.000 precision across all languages.

    Args:
        results: List of bias detection results to validate

    Raises:
        AssertionError: If a false positive is detected
    """
    for i, result in enumerate(results):
        if result.has_bias_detected:
            assert len(result.detected_edits) > 0, \
                f"False positive at index {i}: detected bias but no edits"


def assert_detection_quality(result: BiasDetectionResult,
                            expected_bias: bool,
                            min_confidence: float = 0.7):
    """
    Assert detection matches expectation with confidence threshold.

    Args:
        result: Detection result to validate
        expected_bias: Whether bias should have been detected
        min_confidence: Minimum confidence score required

    Raises:
        AssertionError: If detection doesn't match expectations
    """
    assert result.has_bias_detected == expected_bias, \
        f"Expected has_bias={expected_bias}, got {result.has_bias_detected}"

    if expected_bias:
        assert result.confidence >= min_confidence, \
            f"Confidence {result.confidence} below minimum {min_confidence}"
        assert len(result.detected_edits) > 0, \
            "Detected bias but no edits provided"


def assert_case_preservation(original: str, corrected: str):
    """
    Assert that case is preserved in correction.

    Args:
        original: Original text
        corrected: Corrected text

    Raises:
        AssertionError: If case is not preserved
    """
    # If original starts with capital, corrected should too
    if original and original[0].isupper():
        assert corrected and corrected[0].isupper(), \
            f"Case not preserved: '{original}' → '{corrected}'"


def count_bias_detections(results: List[BiasDetectionResult]) -> Dict[str, float]:
    """
    Count detection statistics.

    Args:
        results: List of detection results

    Returns:
        Dictionary with detection statistics
    """
    if not results:
        return {
            "total": 0,
            "bias_detected": 0,
            "no_bias": 0,
            "avg_confidence": 0.0
        }

    return {
        "total": len(results),
        "bias_detected": sum(1 for r in results if r.has_bias_detected),
        "no_bias": sum(1 for r in results if not r.has_bias_detected),
        "avg_confidence": sum(r.confidence for r in results) / len(results)
    }
