"""Tests for annotation interface and models.

This module tests the annotation workflow, validation, and data models
following the AI BRIDGE 24-field schema.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

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
from annotation.interface import AnnotationInterface
from annotation.validator import AnnotationValidator, ValidationError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def annotator():
    """Create test annotator."""
    return AnnotatorInfo(
        annotator_id="test_annotator_001",
        name="Test Annotator",
        native_language="en",
        expertise_level="expert",
    )


@pytest.fixture
def sample_texts():
    """Sample texts for annotation."""
    return [
        "The chairman led the meeting",
        "The nurse cared for her patients",
        "Every student should bring his textbook",
        "The teacher explained the lesson",
        "A good programmer writes clean code",
    ]


@pytest.fixture
def annotation_interface(annotator):
    """Create annotation interface with temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        interface = AnnotationInterface(
            annotator=annotator, output_dir=Path(tmpdir)
        )
        yield interface


@pytest.fixture
def valid_sample():
    """Create a valid annotation sample."""
    return AnnotationSample(
        text="The chairman led the meeting",
        has_bias=True,
        bias_category=BiasCategory.OCCUPATION,
        expected_correction="The chairperson led the meeting",
        annotator_id="test_annotator_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.MALE_REFERENT,
        gender_referent=GenderReferent.MALE,
    )


@pytest.fixture
def validator():
    """Create validator instance."""
    return AnnotationValidator(strict=False)


# ============================================================================
# MODEL TESTS (7 tests)
# ============================================================================


def test_annotation_sample_creation_valid(valid_sample):
    """Test creating valid annotation sample."""
    assert valid_sample.text == "The chairman led the meeting"
    assert valid_sample.has_bias is True
    assert valid_sample.bias_category == BiasCategory.OCCUPATION
    assert valid_sample.expected_correction == "The chairperson led the meeting"
    assert valid_sample.annotator_id == "test_annotator_001"


def test_annotation_sample_validation_requires_correction():
    """Test that has_bias=True requires expected_correction."""
    with pytest.raises(ValueError, match="expected_correction is required"):
        AnnotationSample(
            text="The chairman led the meeting",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction=None,  # Should fail
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
        )


def test_annotation_sample_validation_requires_category():
    """Test that has_bias=True requires bias_category."""
    with pytest.raises(ValueError, match="bias_category is required"):
        AnnotationSample(
            text="The chairman led the meeting",
            has_bias=True,
            bias_category=None,  # Should fail
            expected_correction="The chairperson led the meeting",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
        )


def test_annotation_sample_no_bias_valid():
    """Test creating valid sample with no bias."""
    sample = AnnotationSample(
        text="The teacher explained the lesson",
        has_bias=False,
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )
    assert sample.has_bias is False
    assert sample.bias_category is None
    assert sample.expected_correction is None


def test_annotation_sample_human_model_agreement():
    """Test auto-computing human_model_agreement."""
    sample = AnnotationSample(
        text="The chairman led",
        has_bias=True,
        bias_category=BiasCategory.OCCUPATION,
        expected_correction="The chairperson led",
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.MALE_REFERENT,
        gender_referent=GenderReferent.MALE,
        ml_prediction=True,  # Matches has_bias
    )
    assert sample.human_model_agreement is True


def test_annotation_sample_to_dict():
    """Test converting sample to dictionary."""
    sample = AnnotationSample(
        text="Test text",
        has_bias=False,
        annotator_id="test_001",
        confidence=ConfidenceLevel.MEDIUM,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )
    data = sample.to_dict()

    assert data["text"] == "Test text"
    assert data["has_bias"] is False
    assert "annotation_timestamp" in data


def test_annotation_batch_creation():
    """Test creating annotation batch."""
    samples = [
        AnnotationSample(
            text="Text 1",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction 1",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
        ),
        AnnotationSample(
            text="Text 2",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        ),
    ]

    batch = AnnotationBatch(
        batch_id="test_batch_001",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    assert batch.batch_id == "test_batch_001"
    assert batch.language == "en"
    assert len(batch.samples) == 2
    assert batch.completion_rate == 1.0  # Both have timestamps


# ============================================================================
# INTERFACE TESTS (8 tests)
# ============================================================================


def test_create_batch(annotation_interface, sample_texts):
    """Test creating annotation batch from texts."""
    batch = annotation_interface.create_batch(
        batch_id="test_batch_001", language="en", samples=sample_texts
    )

    assert batch.batch_id == "test_batch_001"
    assert batch.language == "en"
    assert len(batch.samples) == len(sample_texts)
    assert all(s.text == text for s, text in zip(batch.samples, sample_texts))


def test_save_and_load_batch(annotation_interface, sample_texts):
    """Test saving and loading annotation batch."""
    # Create and save batch
    batch = annotation_interface.create_batch(
        batch_id="test_batch_002", language="sw", samples=sample_texts
    )
    saved_file = annotation_interface.save_batch(batch)

    assert saved_file.exists()
    assert saved_file.name == "test_batch_002_sw.json"

    # Load batch
    loaded_batch = annotation_interface.load_batch(saved_file)
    assert loaded_batch.batch_id == batch.batch_id
    assert loaded_batch.language == batch.language
    assert len(loaded_batch.samples) == len(batch.samples)


def test_annotate_sample(annotation_interface):
    """Test annotating a single sample."""
    sample = AnnotationSample(
        text="The chairman led",
        has_bias=False,  # Will be updated
        annotator_id="test_001",
        confidence=ConfidenceLevel.MEDIUM,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
        annotation_timestamp=None,
    )

    # Annotate
    updated = annotation_interface.annotate_sample(
        sample,
        has_bias=True,
        bias_category=BiasCategory.OCCUPATION,
        expected_correction="The chairperson led",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.MALE_REFERENT,
        gender_referent=GenderReferent.MALE,
    )

    assert updated.has_bias is True
    assert updated.bias_category == BiasCategory.OCCUPATION
    assert updated.expected_correction == "The chairperson led"
    assert updated.annotation_timestamp is not None


def test_export_to_csv(annotation_interface, valid_sample):
    """Test exporting batch to CSV."""
    batch = AnnotationBatch(
        batch_id="test_batch_003",
        language="en",
        samples=[valid_sample],
        annotator_id="test_001",
    )
    annotation_interface.current_batch = batch

    csv_file = annotation_interface.export_to_csv()

    assert csv_file.exists()
    assert csv_file.suffix == ".csv"

    # Read CSV and verify
    with open(csv_file) as f:
        content = f.read()
        assert "text" in content
        assert "has_bias" in content
        assert "The chairman led the meeting" in content


def test_get_stats(annotation_interface):
    """Test getting annotation statistics."""
    samples = [
        AnnotationSample(
            text="Text 1",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction 1",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
        ),
        AnnotationSample(
            text="Text 2",
            has_bias=True,
            bias_category=BiasCategory.PRONOUN_ASSUMPTION,
            expected_correction="Correction 2",
            annotator_id="test_001",
            confidence=ConfidenceLevel.MEDIUM,
            demographic_group=DemographicGroup.FEMALE_REFERENT,
            gender_referent=GenderReferent.FEMALE,
        ),
        AnnotationSample(
            text="Text 3",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        ),
    ]

    batch = AnnotationBatch(
        batch_id="test_batch_004",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )
    annotation_interface.current_batch = batch

    stats = annotation_interface.get_stats()

    assert stats.total_samples == 3
    assert stats.bias_detected == 2
    assert stats.bias_percentage == pytest.approx(66.7, abs=0.1)
    assert "occupation" in stats.category_distribution
    assert "pronoun_assumption" in stats.category_distribution


def test_batch_completion_rate():
    """Test calculating batch completion rate."""
    samples = [
        AnnotationSample(
            text="Text 1",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
            annotation_timestamp=datetime.now(),  # Annotated
        ),
        AnnotationSample(
            text="Text 2",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
            annotation_timestamp=None,  # Not annotated
        ),
    ]

    batch = AnnotationBatch(
        batch_id="test_batch_005",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    assert batch.completion_rate == 0.5  # 1 out of 2 annotated


def test_batch_agreement_rate():
    """Test calculating batch agreement rate."""
    samples = [
        AnnotationSample(
            text="Text 1",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
            ml_prediction=True,
            human_model_agreement=True,
        ),
        AnnotationSample(
            text="Text 2",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
            ml_prediction=True,
            human_model_agreement=False,
        ),
    ]

    batch = AnnotationBatch(
        batch_id="test_batch_006",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    assert batch.agreement_rate == 0.5  # 1 agreement out of 2


def test_annotation_from_ground_truth():
    """Test creating AnnotationSample from ground truth data."""
    sample = AnnotationSample.from_ground_truth(
        text="The chairman led",
        has_bias=True,
        annotator_id="test_001",
        bias_category="occupation",
        expected_correction="The chairperson led",
        demographic_group="male_referent",
        gender_referent="male",
    )

    assert sample.text == "The chairman led"
    assert sample.has_bias is True
    assert sample.bias_category == BiasCategory.OCCUPATION
    assert sample.confidence == ConfidenceLevel.HIGH  # Default


# ============================================================================
# VALIDATOR TESTS (7 tests)
# ============================================================================


def test_validate_valid_sample(validator, valid_sample):
    """Test validating a valid sample."""
    is_valid, errors = validator.validate_sample(valid_sample)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_missing_correction(validator):
    """Test validating sample with missing correction."""
    # Use model_construct to bypass Pydantic validation and test validator
    sample = AnnotationSample.model_construct(
        text="The chairman led",
        has_bias=True,
        bias_category=BiasCategory.OCCUPATION,
        expected_correction="",  # Empty
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.MALE_REFERENT,
        gender_referent=GenderReferent.MALE,
    )

    is_valid, errors = validator.validate_sample(sample)
    assert is_valid is False
    assert any("expected_correction" in err for err in errors)


def test_validate_bias_category_mismatch(validator):
    """Test validating sample with has_bias=False but category provided."""
    sample = AnnotationSample(
        text="Neutral text",
        has_bias=False,
        bias_category=BiasCategory.OCCUPATION,  # Should not be provided
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )

    is_valid, errors = validator.validate_sample(sample)
    assert is_valid is False
    assert any("has_bias is False" in err for err in errors)


def test_validate_empty_text(validator):
    """Test validating sample with empty text."""
    # Use model_construct to bypass Pydantic validation and test validator
    sample = AnnotationSample.model_construct(
        text="",  # Empty
        has_bias=False,
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )

    is_valid, errors = validator.validate_sample(sample)
    assert is_valid is False
    assert any("text field is empty" in err for err in errors)


def test_validate_batch_valid(validator, valid_sample):
    """Test validating valid batch."""
    batch = AnnotationBatch(
        batch_id="test_batch_007",
        language="en",
        samples=[valid_sample],
        annotator_id="test_annotator_001",
    )

    is_valid, report = validator.validate_batch(batch)
    assert is_valid is True
    assert report["valid_samples"] == 1
    assert report["invalid_samples"] == 0


def test_validate_batch_invalid_language(validator, valid_sample):
    """Test validating batch with invalid language."""
    batch = AnnotationBatch(
        batch_id="test_batch_008",
        language="xyz",  # Invalid
        samples=[valid_sample],
        annotator_id="test_annotator_001",
    )

    is_valid, report = validator.validate_batch(batch)
    assert is_valid is False
    assert any("Invalid language" in err for err in report["batch_errors"])


def test_validate_ai_bridge_bronze_tier(validator):
    """Test validating AI BRIDGE Bronze tier requirements."""
    # Create 1200 samples (minimum for Bronze)
    samples = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=i % 2 == 0,
            bias_category=BiasCategory.OCCUPATION if i % 2 == 0 else None,
            expected_correction=f"Correction {i}" if i % 2 == 0 else None,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
            multi_annotator=(i < 120),  # 10% multi-annotator
        )
        for i in range(1200)
    ]

    batch = AnnotationBatch(
        batch_id="bronze_test",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    meets_req, report = validator.validate_ai_bridge_requirements(batch, tier="bronze")
    assert meets_req is True
    assert report["meets_requirements"] is True
    assert report["total_samples"] == 1200
    assert report["multi_annotator_samples"] == 120


# ============================================================================
# EDGE CASES (3 tests)
# ============================================================================


def test_annotation_stats_empty_batch():
    """Test stats with empty batch."""
    batch = AnnotationBatch(
        batch_id="empty_batch",
        language="en",
        samples=[],
        annotator_id="test_001",
    )

    stats = AnnotationStats.from_batch(batch)
    assert stats.total_samples == 0
    assert stats.bias_percentage == 0.0


def test_validator_strict_mode():
    """Test validator in strict mode raises exceptions."""
    strict_validator = AnnotationValidator(strict=True)

    # Use model_construct to bypass Pydantic validation and test validator
    sample = AnnotationSample.model_construct(
        text="",  # Invalid
        has_bias=False,
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )

    with pytest.raises(ValidationError):
        strict_validator.validate_sample(sample)


def test_format_validation_report(validator, valid_sample):
    """Test formatting validation report."""
    batch = AnnotationBatch(
        batch_id="report_test",
        language="en",
        samples=[valid_sample],
        annotator_id="test_annotator_001",
    )

    is_valid, report = validator.validate_batch(batch)
    formatted = validator.format_validation_report(report, report_type="batch")

    assert "Validation Report" in formatted
    assert "Total samples:" in formatted
    assert "1" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
