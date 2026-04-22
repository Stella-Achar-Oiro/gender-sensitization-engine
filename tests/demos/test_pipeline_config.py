"""Tests for pipeline configuration."""
import pytest
from pathlib import Path
from demos.pipeline_config import PipelineConfig
from eval.models import Language


def test_pipeline_config_defaults():
    """Test default configuration values."""
    config = PipelineConfig(language=Language.SWAHILI)

    assert config.language == Language.SWAHILI
    assert config.sample_size == 100
    assert config.enable_ml is True
    assert config.output_dir.exists()
    assert config.verbose is True


def test_pipeline_config_custom_values(tmp_path):
    """Test configuration with custom values."""
    output = tmp_path / "custom_output"
    config = PipelineConfig(
        language=Language.FRENCH,
        sample_size=50,
        data_source="wikipedia",
        enable_ml=False,
        output_dir=output,
        verbose=False
    )

    assert config.language == Language.FRENCH
    assert config.sample_size == 50
    assert config.data_source == "wikipedia"
    assert config.enable_ml is False
    assert config.output_dir == output
    assert output.exists()


def test_pipeline_config_validation_sample_size_too_small():
    """Test that sample_size validation works."""
    with pytest.raises(ValueError, match="sample_size must be >= 10"):
        PipelineConfig(language=Language.ENGLISH, sample_size=5)


def test_pipeline_config_validation_sample_size_boundary():
    """Test sample_size boundary condition."""
    # Should work with exactly 10
    config = PipelineConfig(language=Language.ENGLISH, sample_size=10)
    assert config.sample_size == 10

    # Should fail with 9
    with pytest.raises(ValueError):
        PipelineConfig(language=Language.ENGLISH, sample_size=9)


def test_pipeline_config_validation_invalid_data_source():
    """Test data_source validation."""
    with pytest.raises(ValueError, match="data_source must be one of"):
        PipelineConfig(
            language=Language.ENGLISH,
            data_source="invalid_source"
        )


def test_pipeline_config_creates_output_dir(tmp_path):
    """Test output directory creation."""
    output = tmp_path / "test_output"
    assert not output.exists()

    config = PipelineConfig(
        language=Language.GIKUYU,
        output_dir=output
    )

    assert output.exists()
    assert output.is_dir()


def test_pipeline_config_summary():
    """Test summary generation."""
    config = PipelineConfig(
        language=Language.SWAHILI,
        sample_size=75,
        data_source="news",
        enable_ml=False
    )

    summary = config.summary()

    assert "sw" in summary  # Language value is "sw" not "Swahili"
    assert "75" in summary
    assert "news" in summary
    assert "False" in summary


def test_pipeline_config_all_languages():
    """Test configuration works with all supported languages."""
    for language in [Language.ENGLISH, Language.SWAHILI, Language.FRENCH, Language.GIKUYU]:
        config = PipelineConfig(language=language)
        assert config.language == language


def test_pipeline_config_all_data_sources():
    """Test all valid data sources."""
    valid_sources = ["ground_truth", "wikipedia", "news"]

    for source in valid_sources:
        config = PipelineConfig(
            language=Language.ENGLISH,
            data_source=source
        )
        assert config.data_source == source
