"""Tests for base data collector classes."""
import pytest
from pathlib import Path
from datetime import datetime
from scripts.data_collection.base_collector import (
    CollectionConfig,
    CollectedSample,
    CollectionResult,
    DataCollector
)


def test_collection_config_valid():
    """Test valid collection configuration."""
    config = CollectionConfig(
        language="sw",
        max_items=100,
        output_file=Path("test.csv")
    )
    assert config.language == "sw"
    assert config.max_items == 100
    assert config.cache_dir.exists()


def test_collection_config_validation_max_items():
    """Test max_items validation."""
    with pytest.raises(ValueError, match="max_items must be >= 1"):
        CollectionConfig(
            language="en",
            max_items=0,
            output_file=Path("test.csv")
        )


def test_collection_config_validation_language():
    """Test language validation."""
    with pytest.raises(ValueError, match="language cannot be empty"):
        CollectionConfig(
            language="",
            max_items=10,
            output_file=Path("test.csv")
        )


def test_collected_sample_valid():
    """Test valid collected sample."""
    sample = CollectedSample(
        text="Sample text",
        source="wikipedia",
        language="sw"
    )
    assert sample.text == "Sample text"
    assert sample.source == "wikipedia"
    assert sample.language == "sw"
    assert sample.collection_date  # Should be auto-generated


def test_collected_sample_validation_empty_text():
    """Test text validation."""
    with pytest.raises(ValueError, match="text cannot be empty"):
        CollectedSample(
            text="",
            source="test",
            language="en"
        )


def test_collected_sample_validation_whitespace_text():
    """Test whitespace-only text validation."""
    with pytest.raises(ValueError, match="text cannot be empty"):
        CollectedSample(
            text="   ",
            source="test",
            language="en"
        )


def test_collected_sample_validation_empty_source():
    """Test source validation."""
    with pytest.raises(ValueError, match="source cannot be empty"):
        CollectedSample(
            text="Test",
            source="",
            language="en"
        )


def test_collected_sample_with_metadata():
    """Test sample with metadata."""
    sample = CollectedSample(
        text="Test",
        source="test",
        language="en",
        metadata={"key": "value", "count": 42}
    )
    assert sample.metadata["key"] == "value"
    assert sample.metadata["count"] == 42


def test_collection_result_success():
    """Test successful collection result."""
    result = CollectionResult(
        success=True,
        samples_collected=100,
        output_file=Path("output.csv"),
        lineage={"source": "test"}
    )
    assert result.success
    assert result.samples_collected == 100
    assert "Successfully collected 100 samples" in result.summary()


def test_collection_result_failure():
    """Test failed collection result."""
    result = CollectionResult(
        success=False,
        samples_collected=0,
        output_file=None,
        error_message="Connection failed"
    )
    assert not result.success
    assert "Collection failed: Connection failed" in result.summary()


def test_data_collector_abstract():
    """Test that DataCollector cannot be instantiated directly."""
    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=Path("test.csv")
    )

    with pytest.raises(TypeError):
        DataCollector(config)


def test_data_collector_save_samples_empty(tmp_path):
    """Test saving empty sample list."""
    class TestCollector(DataCollector):
        def collect(self):
            return []

        def get_lineage(self):
            return {"source": "test"}

    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=tmp_path / "output.csv"
    )
    collector = TestCollector(config)
    result = collector.save_samples([])

    assert result.success
    assert result.samples_collected == 0


def test_data_collector_save_samples_valid(tmp_path):
    """Test saving valid samples to CSV."""
    class TestCollector(DataCollector):
        def collect(self):
            return []

        def get_lineage(self):
            return {"source": "test"}

    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=tmp_path / "output.csv"
    )
    collector = TestCollector(config)

    samples = [
        CollectedSample(
            text="First sample",
            source="test",
            language="sw"
        ),
        CollectedSample(
            text="Second sample",
            source="test",
            language="sw",
            metadata={"key": "value"}
        )
    ]

    result = collector.save_samples(samples)

    assert result.success
    assert result.samples_collected == 2
    assert result.output_file.exists()

    # Verify CSV contents
    import csv
    with open(result.output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['text'] == "First sample"
        assert rows[1]['text'] == "Second sample"


def test_data_collector_creates_output_directory(tmp_path):
    """Test that save_samples creates output directory if needed."""
    class TestCollector(DataCollector):
        def collect(self):
            return []

        def get_lineage(self):
            return {}

    output_dir = tmp_path / "nested" / "directory"
    assert not output_dir.exists()

    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=output_dir / "output.csv"
    )
    collector = TestCollector(config)

    samples = [CollectedSample(text="Test", source="test", language="en")]
    result = collector.save_samples(samples)

    assert result.success
    assert output_dir.exists()
    assert result.output_file.exists()
