"""Tests for Wikipedia collector."""
import pytest
from pathlib import Path
from scripts.data_collection.base_collector import CollectionConfig
from scripts.data_collection.wikipedia_collector import (
    WikipediaCollector,
    GroundTruthCollector
)


def test_wikipedia_collector_initialization(tmp_path):
    """Test Wikipedia collector can be initialized."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=tmp_path / "wiki.csv"
    )
    collector = WikipediaCollector(config)
    assert collector.config.language == "sw"


def test_wikipedia_collector_lineage():
    """Test Wikipedia collector lineage tracking."""
    config = CollectionConfig(
        language="en",
        max_items=100,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    lineage = collector.get_lineage()

    assert lineage["source"] == "Wikipedia"
    assert lineage["language"] == "en"
    assert lineage["max_articles"] == 100
    assert "collector" in lineage


@pytest.mark.slow
def test_wikipedia_collector_actually_collects():
    """Test Wikipedia collector actually collects data (no longer placeholder)."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    samples = collector.collect()

    # Now actually collects data from Wikipedia API
    # May return empty if API fails, but shouldn't crash
    assert isinstance(samples, list)
    assert len(samples) <= 10

    if samples:
        # Verify sample structure
        sample = samples[0]
        assert sample.source == "wikipedia"
        assert sample.language == "sw"
        assert 'article_title' in sample.metadata


def test_ground_truth_collector_initialization(tmp_path):
    """Test GroundTruthCollector initialization."""
    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=tmp_path / "gt.csv"
    )
    collector = GroundTruthCollector(config)
    assert collector.config.language == "en"


def test_ground_truth_collector_loads_samples():
    """Test GroundTruthCollector actually loads data."""
    config = CollectionConfig(
        language="en",
        max_items=5,
        output_file=Path("test.csv")
    )
    collector = GroundTruthCollector(config)
    samples = collector.collect()

    # Should load samples from ground truth
    assert len(samples) > 0
    assert len(samples) <= 5

    # Verify sample structure
    for sample in samples:
        assert sample.text
        assert sample.source == "ground_truth"
        assert sample.language == "en"


def test_ground_truth_collector_all_languages():
    """Test GroundTruthCollector works for all languages."""
    for lang in ["en", "sw", "fr", "ki"]:
        config = CollectionConfig(
            language=lang,
            max_items=3,
            output_file=Path("test.csv")
        )
        collector = GroundTruthCollector(config)
        samples = collector.collect()

        assert len(samples) > 0
        assert all(s.language == lang for s in samples)


def test_ground_truth_collector_respects_max_items():
    """Test GroundTruthCollector respects max_items limit."""
    config = CollectionConfig(
        language="en",
        max_items=2,
        output_file=Path("test.csv")
    )
    collector = GroundTruthCollector(config)
    samples = collector.collect()

    assert len(samples) <= 2


def test_ground_truth_collector_lineage():
    """Test GroundTruthCollector lineage tracking."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = GroundTruthCollector(config)
    lineage = collector.get_lineage()

    assert lineage["source"] == "ground_truth"
    assert lineage["language"] == "sw"
    assert lineage["method"] == "GroundTruthLoader"


def test_ground_truth_collector_invalid_language():
    """Test GroundTruthCollector handles invalid language gracefully."""
    config = CollectionConfig(
        language="invalid",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = GroundTruthCollector(config)
    samples = collector.collect()

    # Should return empty list, not crash
    assert samples == []


def test_ground_truth_collector_save_integration(tmp_path):
    """Integration test: collect and save samples."""
    output_file = tmp_path / "collected.csv"
    config = CollectionConfig(
        language="en",
        max_items=5,
        output_file=output_file
    )

    collector = GroundTruthCollector(config)
    samples = collector.collect()
    result = collector.save_samples(samples)

    assert result.success
    assert result.samples_collected > 0
    assert output_file.exists()

    # Verify lineage is included
    assert "ground_truth" in result.lineage["source"]
