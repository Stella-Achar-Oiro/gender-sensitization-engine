"""Tests for batch annotation, schema enforcement, and export utilities.

This module tests Day 12 functionality: batch processing, AI BRIDGE schema
compliance, and export to ground truth format.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from annotation.models import (
    AnnotationSample,
    AnnotationBatch,
    AnnotatorInfo,
    ConfidenceLevel,
    BiasCategory,
    DemographicGroup,
    GenderReferent,
)
from annotation.schema import AIBRIDGESchemaEnforcer, validate_ai_bridge_compliance
from annotation.export import AnnotationExporter


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def schema_enforcer():
    """Create schema enforcer."""
    return AIBRIDGESchemaEnforcer()


@pytest.fixture
def complete_sample():
    """Create sample with all 24 AI BRIDGE fields."""
    return AnnotationSample(
        # Core (1-4)
        text="The chairman led the meeting",
        has_bias=True,
        bias_category=BiasCategory.OCCUPATION,
        expected_correction="The chairperson led the meeting",
        # Metadata (5-8)
        annotator_id="test_001",
        confidence=ConfidenceLevel.HIGH,
        notes="Clear gender bias",
        # Fairness (9-12)
        demographic_group=DemographicGroup.MALE_REFERENT,
        gender_referent=GenderReferent.MALE,
        protected_attribute="gender",
        fairness_score=0.95,
        # Context (13-15)
        context_requires_gender=False,
        language_variant="US English",
        # HITL (16-19)
        ml_prediction=True,
        ml_confidence=0.89,
        correction_accepted=True,
        # Provenance (20-23)
        source_dataset="wikipedia",
        source_url="https://example.com",
        collection_date=datetime(2026, 2, 5),
        multi_annotator=False,
    )


@pytest.fixture
def sample_batch(complete_sample):
    """Create batch with complete samples."""
    samples = [complete_sample]
    for i in range(4):
        samples.append(
            AnnotationSample(
                text=f"Sample text {i+2}",
                has_bias=i % 2 == 0,
                bias_category=BiasCategory.PRONOUN_ASSUMPTION if i % 2 == 0 else None,
                expected_correction=f"Correction {i+2}" if i % 2 == 0 else None,
                annotator_id="test_001",
                confidence=ConfidenceLevel.MEDIUM,
                demographic_group=DemographicGroup.NEUTRAL_REFERENT,
                gender_referent=GenderReferent.NEUTRAL,
            )
        )

    return AnnotationBatch(
        batch_id="test_batch_001",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )


# ============================================================================
# SCHEMA ENFORCEMENT TESTS (6 tests)
# ============================================================================


def test_validate_complete_sample(schema_enforcer, complete_sample):
    """Test validating sample with all 24 fields."""
    is_valid, missing = schema_enforcer.validate_schema(complete_sample)
    assert is_valid is True
    assert len(missing) == 0


def test_validate_incomplete_sample_mock(schema_enforcer):
    """Test validating sample with missing fields."""
    # Create sample with minimal fields using model_construct
    sample = AnnotationSample.model_construct(
        text="Test",
        has_bias=False,
        annotator_id="test",
        confidence=ConfidenceLevel.HIGH,
        demographic_group=DemographicGroup.NEUTRAL_REFERENT,
        gender_referent=GenderReferent.NEUTRAL,
    )

    # Should be valid (all required fields present in Pydantic model)
    is_valid, missing = schema_enforcer.validate_schema(sample)
    assert is_valid is True  # Pydantic ensures all fields exist


def test_validate_batch_all_compliant(schema_enforcer, sample_batch):
    """Test validating batch where all samples are compliant."""
    report = schema_enforcer.validate_batch(sample_batch)

    assert report["total_samples"] == 5
    assert report["compliant_samples"] == 5
    assert report["non_compliant_samples"] == 0
    assert report["all_compliant"] is True


def test_field_coverage(schema_enforcer, sample_batch):
    """Test checking field coverage across samples."""
    coverage = schema_enforcer.check_field_coverage(sample_batch.samples)

    assert "text" in coverage
    assert "has_bias" in coverage
    assert coverage["text"] == 100.0
    assert coverage["has_bias"] == 100.0


def test_enforce_schema_with_defaults(schema_enforcer):
    """Test enforcing schema with defaults for missing fields."""
    minimal_dict = {
        "text": "Test text",
        "has_bias": False,
        "annotator_id": "test_001",
    }

    sample = schema_enforcer.enforce_schema(minimal_dict)

    assert sample.text == "Test text"
    assert sample.has_bias is False
    assert sample.annotator_id == "test_001"
    assert sample.confidence == ConfidenceLevel.MEDIUM  # Default
    assert sample.version == "1.0"  # Default


def test_enforce_schema_missing_core_fields(schema_enforcer):
    """Test enforcing schema with missing core fields raises error."""
    incomplete_dict = {
        "text": "Test text",
        # Missing has_bias and annotator_id
    }

    with pytest.raises(ValueError, match="Missing required core fields"):
        schema_enforcer.enforce_schema(incomplete_dict)


# ============================================================================
# EXPORT TESTS (7 tests)
# ============================================================================


def test_export_to_ground_truth_csv_all_fields(sample_batch):
    """Test exporting batch to CSV with all 24 fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "output.csv"
        result = AnnotationExporter.to_ground_truth_csv(
            sample_batch, output_file, include_all_fields=True
        )

        assert result.exists()

        # Read and verify headers
        with open(result) as f:
            headers = f.readline().strip().split(",")
            assert "text" in headers
            assert "has_bias" in headers
            assert "bias_category" in headers
            assert "version" in headers  # Should have all 24 fields


def test_export_to_ground_truth_csv_core_fields_only(sample_batch):
    """Test exporting batch to CSV with core fields only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "output.csv"
        result = AnnotationExporter.to_ground_truth_csv(
            sample_batch, output_file, include_all_fields=False
        )

        assert result.exists()

        # Read and verify headers
        with open(result) as f:
            headers = f.readline().strip().split(",")
            assert "text" in headers
            assert "has_bias" in headers
            assert len(headers) == 8  # Only core fields


def test_merge_batches_to_ground_truth():
    """Test merging multiple batches into single ground truth file."""
    # Create two small batches
    batch1_samples = [
        AnnotationSample(
            text="Text 1",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction 1",
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
        )
    ]

    batch2_samples = [
        AnnotationSample(
            text="Text 2",
            has_bias=False,
            annotator_id="test_002",
            confidence=ConfidenceLevel.MEDIUM,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
        )
    ]

    batch1 = AnnotationBatch(
        batch_id="batch_001",
        language="en",
        samples=batch1_samples,
        annotator_id="test_001",
    )

    batch2 = AnnotationBatch(
        batch_id="batch_002",
        language="en",
        samples=batch2_samples,
        annotator_id="test_002",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "merged.csv"
        result = AnnotationExporter.merge_batches_to_ground_truth(
            [batch1, batch2], output_file, language="en"
        )

        assert result.exists()

        # Verify merged content
        with open(result) as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 samples


def test_export_disagreements():
    """Test exporting disagreement samples."""
    samples = [
        AnnotationSample(
            text="Disagreement text",
            has_bias=True,
            bias_category=BiasCategory.OCCUPATION,
            expected_correction="Correction",
            annotator_id="annotator_1",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.MALE_REFERENT,
            gender_referent=GenderReferent.MALE,
            human_model_agreement=False,  # Disagreed with ML
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "disagreements.csv"
        result = AnnotationExporter.export_disagreements(samples, output_file)

        assert result.exists()

        # Verify content
        with open(result) as f:
            headers = f.readline().strip().split(",")
            assert "text" in headers
            assert "human_model_agreement" in headers


def test_export_statistics_report(sample_batch):
    """Test exporting statistics report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "report.txt"
        result = AnnotationExporter.export_statistics_report(
            sample_batch, output_file
        )

        assert result.exists()

        # Verify report content
        with open(result) as f:
            content = f.read()
            assert "Annotation Batch Statistics" in content
            assert sample_batch.batch_id in content
            assert "Total samples" in content
            assert "Bias Category Distribution" in content


def test_compliance_report_generation(schema_enforcer, sample_batch):
    """Test generating compliance report."""
    report = schema_enforcer.generate_compliance_report(sample_batch)

    assert "AI BRIDGE Schema Compliance Report" in report
    assert sample_batch.batch_id in report
    assert "✅ PASS" in report or "✓" in report


def test_validate_ai_bridge_compliance_convenience(sample_batch):
    """Test convenience function for compliance validation."""
    is_compliant, report = validate_ai_bridge_compliance(sample_batch)

    assert is_compliant is True
    assert report["all_compliant"] is True
    assert report["total_samples"] == 5


# ============================================================================
# BATCH PROCESSING TESTS (2 tests)
# ============================================================================


def test_batch_with_source_metadata():
    """Test batch with source dataset metadata."""
    samples = [
        AnnotationSample(
            text="Wikipedia sample",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
            source_dataset="wikipedia",
            source_url="https://en.wikipedia.org/wiki/Test",
            collection_date=datetime(2026, 2, 5),
        )
    ]

    batch = AnnotationBatch(
        batch_id="wiki_batch",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    assert batch.samples[0].source_dataset == "wikipedia"
    assert batch.samples[0].source_url is not None
    assert batch.samples[0].collection_date is not None


def test_batch_completion_tracking():
    """Test tracking batch completion status."""
    samples = [
        AnnotationSample(
            text=f"Text {i}",
            has_bias=False,
            annotator_id="test_001",
            confidence=ConfidenceLevel.HIGH,
            demographic_group=DemographicGroup.NEUTRAL_REFERENT,
            gender_referent=GenderReferent.NEUTRAL,
            annotation_timestamp=datetime.now() if i < 3 else None,
        )
        for i in range(5)
    ]

    batch = AnnotationBatch(
        batch_id="progress_batch",
        language="en",
        samples=samples,
        annotator_id="test_001",
    )

    assert batch.completion_rate == 0.6  # 3 out of 5 completed
    assert batch.is_complete is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
