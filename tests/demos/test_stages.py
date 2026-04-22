"""Tests for pipeline stages."""
import pytest
from demos.stages import (
    DataCollectionStage,
    BiasDetectionStage,
    EvaluationStage,
    StageResult
)
from eval.models import Language, GroundTruthSample, BiasCategory
from tests.test_helpers import assert_no_false_positives


def test_stage_result_structure():
    """Test StageResult data structure."""
    result = StageResult(
        stage_name="Test Stage",
        success=True,
        samples_processed=10,
        output_summary="Processed 10 samples",
        metrics={"accuracy": 0.95}
    )

    assert result.stage_name == "Test Stage"
    assert result.success is True
    assert result.samples_processed == 10
    assert result.metrics["accuracy"] == 0.95


def test_stage_result_defaults():
    """Test StageResult with default metrics."""
    result = StageResult(
        stage_name="Test",
        success=True,
        samples_processed=5,
        output_summary="Done"
    )

    assert result.metrics == {}


def test_data_collection_stage_basic():
    """Test data collection stage basic functionality."""
    stage = DataCollectionStage()
    result, samples = stage.run(Language.ENGLISH, count=10)

    assert result.success is True
    assert result.samples_processed == 10
    assert len(samples) == 10
    assert "Loaded 10 samples" in result.output_summary


def test_data_collection_stage_different_languages():
    """Test data collection works for all languages."""
    stage = DataCollectionStage()

    for language in [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]:
        result, samples = stage.run(language, count=5)
        assert result.success is True
        assert len(samples) == 5


def test_data_collection_stage_large_count():
    """Test data collection with count larger than available samples."""
    stage = DataCollectionStage()
    # Request more samples than available - should return what's available
    result, samples = stage.run(Language.ENGLISH, count=10000)

    assert result.success is True
    assert result.samples_processed > 0
    assert len(samples) == result.samples_processed


def test_bias_detection_stage_initialization():
    """Test bias detection stage initialization."""
    stage_with_ml = BiasDetectionStage(enable_ml=True)
    stage_without_ml = BiasDetectionStage(enable_ml=False)

    assert stage_with_ml.enable_ml is True
    assert stage_without_ml.enable_ml is False


def test_bias_detection_stage_with_biased_texts(sample_biased_texts):
    """Test bias detection on known biased texts."""
    stage = BiasDetectionStage(enable_ml=False)
    result, detections = stage.run(sample_biased_texts, Language.ENGLISH)

    assert result.success is True
    assert result.samples_processed == len(sample_biased_texts)
    assert result.metrics["method"] == "rules-only"
    assert len(detections) == len(sample_biased_texts)

    # Should detect at least some bias
    assert result.metrics["detection_rate"] > 0


def test_bias_detection_stage_with_neutral_texts(sample_neutral_texts):
    """Test bias detection preserves precision (no false positives)."""
    stage = BiasDetectionStage(enable_ml=False)
    result, detections = stage.run(sample_neutral_texts, Language.ENGLISH)

    assert result.success is True
    assert result.samples_processed == len(sample_neutral_texts)

    # CRITICAL: No false positives (perfect precision)
    assert result.metrics["detection_rate"] == 0, "False positive detected!"
    assert_no_false_positives(detections)


def test_bias_detection_stage_ml_flag():
    """Test that ML flag affects method reported."""
    texts = ["The chairman leads"]

    stage_rules = BiasDetectionStage(enable_ml=False)
    result_rules, _ = stage_rules.run(texts, Language.ENGLISH)
    assert result_rules.metrics["method"] == "rules-only"

    stage_ml = BiasDetectionStage(enable_ml=True)
    result_ml, _ = stage_ml.run(texts, Language.ENGLISH)
    assert result_ml.metrics["method"] == "rules+ml"


def test_bias_detection_stage_empty_input():
    """Test detection stage handles empty input gracefully."""
    stage = BiasDetectionStage()
    result, detections = stage.run([], Language.ENGLISH)

    assert result.success is True
    assert result.samples_processed == 0
    assert len(detections) == 0
    assert result.metrics["detection_rate"] == 0


def test_evaluation_stage_perfect_match():
    """Test evaluation with perfect predictions."""
    ground_truth = [
        GroundTruthSample(
            text="The chairman leads",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="The chair leads"
        ),
        GroundTruthSample(
            text="The table is wooden",
            has_bias=False,
            bias_category=None,
            expected_correction=None
        )
    ]

    from eval.models import BiasDetectionResult
    results = [
        BiasDetectionResult(
            text="The chairman leads",
            has_bias_detected=True,
            detected_edits=[{"original": "chairman", "replacement": "chair", "position": 4}],
            confidence=0.95
        ),
        BiasDetectionResult(
            text="The table is wooden",
            has_bias_detected=False,
            detected_edits=[],
            confidence=0.9
        )
    ]

    stage = EvaluationStage()
    result = stage.run(ground_truth, results)

    assert result.success is True
    assert result.metrics["precision"] == 1.0
    assert result.metrics["recall"] == 1.0
    assert result.metrics["f1"] == 1.0
    assert result.metrics["tp"] == 1
    assert result.metrics["fp"] == 0
    assert result.metrics["fn"] == 0
    assert result.metrics["tn"] == 1


def test_evaluation_stage_with_false_negative():
    """Test evaluation with missed bias (false negative)."""
    ground_truth = [
        GroundTruthSample(
            text="The chairman leads",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="The chair leads"
        )
    ]

    from eval.models import BiasDetectionResult
    results = [
        BiasDetectionResult(
            text="The chairman leads",
            has_bias_detected=False,  # Missed it!
            detected_edits=[],
            confidence=0.9
        )
    ]

    stage = EvaluationStage()
    result = stage.run(ground_truth, results)

    assert result.success is True
    assert result.metrics["fn"] == 1  # One false negative
    assert result.metrics["recall"] < 1.0


def test_evaluation_stage_mismatched_lengths():
    """Test evaluation fails gracefully with mismatched inputs."""
    ground_truth = [
        GroundTruthSample(
            text="Test",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Test"
        )
    ]

    from eval.models import BiasDetectionResult
    results = [
        BiasDetectionResult(text="Test1", has_bias_detected=True, detected_edits=[], confidence=0.9),
        BiasDetectionResult(text="Test2", has_bias_detected=True, detected_edits=[], confidence=0.9)
    ]

    stage = EvaluationStage()
    result = stage.run(ground_truth, results)

    assert result.success is False
    assert "Mismatch" in result.output_summary or "mismatch" in result.output_summary


def test_evaluation_stage_all_metrics_calculated():
    """Test that all required metrics are calculated."""
    ground_truth = [
        GroundTruthSample(
            text="The chairman leads",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="The chair leads"
        )
    ]

    from eval.models import BiasDetectionResult
    results = [
        BiasDetectionResult(
            text="The chairman leads",
            has_bias_detected=True,
            detected_edits=[{"original": "chairman", "replacement": "chair", "position": 4}],
            confidence=0.95
        )
    ]

    stage = EvaluationStage()
    result = stage.run(ground_truth, results)

    # Check all required metrics exist
    required_metrics = ["f1", "precision", "recall", "tp", "fp", "fn", "tn"]
    for metric in required_metrics:
        assert metric in result.metrics, f"Missing metric: {metric}"
