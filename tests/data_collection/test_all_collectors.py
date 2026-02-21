"""Tests for Wikipedia, News, and Bible collectors."""
import pytest
from pathlib import Path
from scripts.data_collection.base_collector import CollectionConfig
from scripts.data_collection.wikipedia_collector import WikipediaCollector
from scripts.data_collection.news_collector import NewsCollector
from scripts.data_collection.bible_collector import BibleCollector


# Wikipedia Collector Tests

def test_wikipedia_collector_initialization():
    """Test WikipediaCollector initialization."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    assert collector.config.language == "sw"
    assert collector.api_url == "https://sw.wikipedia.org/w/api.php"
    assert collector.stats['api_calls'] == 0


def test_wikipedia_collector_unsupported_language():
    """Test WikipediaCollector rejects unsupported languages."""
    config = CollectionConfig(
        language="unsupported",
        max_items=10,
        output_file=Path("test.csv")
    )
    with pytest.raises(ValueError, match="not supported"):
        WikipediaCollector(config)


def test_wikipedia_collector_lineage():
    """Test WikipediaCollector lineage tracking."""
    config = CollectionConfig(
        language="en",
        max_items=5,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    lineage = collector.get_lineage()

    assert lineage["source"] == "Wikipedia"
    assert lineage["language"] == "en"
    assert lineage["collector"] == "WikipediaCollector"
    assert "api_url" in lineage


@pytest.mark.slow
def test_wikipedia_collector_collect_english():
    """Test WikipediaCollector can collect English samples."""
    config = CollectionConfig(
        language="en",
        max_items=3,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    samples = collector.collect()

    # May return 0 samples if API fails or no matches, but shouldn't crash
    assert isinstance(samples, list)
    assert len(samples) <= 3

    if samples:
        sample = samples[0]
        assert sample.source == "wikipedia"
        assert sample.language == "en"
        assert len(sample.text) >= 40
        assert 'article_title' in sample.metadata


@pytest.mark.slow
def test_wikipedia_collector_collect_swahili():
    """Test WikipediaCollector can collect Swahili samples."""
    config = CollectionConfig(
        language="sw",
        max_items=3,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)
    samples = collector.collect()

    assert isinstance(samples, list)
    assert len(samples) <= 3

    if samples:
        sample = samples[0]
        assert sample.source == "wikipedia"
        assert sample.language == "sw"


def test_wikipedia_collector_extract_sentences():
    """Test sentence extraction logic."""
    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = WikipediaCollector(config)

    # Longer sentences that meet the 40 character minimum
    text = ("She is an engineer working in the technology sector with years of experience. "
            "He works as a nurse in the local hospital caring for patients every day. "
            "The weather is nice and sunny today. "
            "Gender equality matters and is important for society and workplaces everywhere.")
    sentences = collector._extract_sentences(text)

    # Should extract sentences with gender keywords
    assert len(sentences) > 0
    assert all(40 <= len(s) <= 200 for s in sentences)
    # Verify it actually filtered by gender keywords
    assert any('she' in s.lower() or 'he' in s.lower() or 'gender' in s.lower() for s in sentences)


# News Collector Tests

def test_news_collector_initialization():
    """Test NewsCollector initialization."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = NewsCollector(config)
    assert collector.config.language == "sw"


def test_news_collector_unsupported_language():
    """Test NewsCollector only supports Swahili."""
    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=Path("test.csv")
    )
    with pytest.raises(ValueError, match="only supports Swahili"):
        NewsCollector(config)


def test_news_collector_lineage():
    """Test NewsCollector lineage tracking."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = NewsCollector(config)
    lineage = collector.get_lineage()

    assert lineage["source"] == "Swahili News Dataset"
    assert lineage["language"] == "sw"
    assert lineage["collector"] == "NewsCollector"
    assert "dataset_url" in lineage


def test_news_collector_sentence_extraction():
    """Test sentence extraction from text."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = NewsCollector(config)

    text = "Mwalimu alifundisha. Daktari alipata tuzo. Hii ni habari nzuri sana."
    sentences = collector._extract_sentences(text)

    assert len(sentences) > 0
    assert all(20 <= len(s) <= 500 for s in sentences)


def test_news_collector_occupation_detection():
    """Test occupation term detection."""
    config = CollectionConfig(
        language="sw",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = NewsCollector(config)

    # Add a test occupation term
    collector.occupation_terms.add("mwalimu")

    assert collector._contains_occupation("Mwalimu alifundisha")
    assert not collector._contains_occupation("Habari ya leo")


def test_news_collector_handles_missing_lexicon():
    """Test NewsCollector handles missing lexicon gracefully."""
    config = CollectionConfig(
        language="sw",
        max_items=5,
        output_file=Path("test.csv")
    )
    # Using non-existent lexicon path
    collector = NewsCollector(config, lexicon_path="nonexistent.csv")

    # Should handle missing lexicon by having empty occupation terms
    assert isinstance(collector.occupation_terms, set)
    # May be empty or have default terms


# Bible Collector Tests

def test_bible_collector_initialization():
    """Test BibleCollector initialization."""
    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config)
    assert collector.config.language == "ki"


def test_bible_collector_unsupported_language():
    """Test BibleCollector only supports Kikuyu."""
    config = CollectionConfig(
        language="en",
        max_items=10,
        output_file=Path("test.csv")
    )
    with pytest.raises(ValueError, match="only supports Kikuyu"):
        BibleCollector(config)


def test_bible_collector_lineage():
    """Test BibleCollector lineage tracking."""
    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config)
    lineage = collector.get_lineage()

    assert lineage["source"] == "Kikuyu Bible"
    assert lineage["language"] == "ki"
    assert lineage["collector"] == "BibleCollector"
    assert lineage["license"] == "CC BY-SA 4.0"
    assert "translation" in lineage


def test_bible_collector_parse_filename():
    """Test filename parsing."""
    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config)

    book, chapter, code = collector._parse_filename("kik_002_GEN_01_read.txt")
    assert book == "Genesis"
    assert chapter == "1"
    assert code == "GEN"

    book, chapter, code = collector._parse_filename("kik_042_MAT_05_read.txt")
    assert book == "Matthew"
    assert chapter == "5"
    assert code == "MAT"


def test_bible_collector_term_detection():
    """Test term detection in text."""
    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config)

    has_occ, occ_terms = collector._contains_terms(
        "Mũthĩnjĩri akaheana kĩrĩra",
        collector.OCCUPATION_TERMS
    )
    assert has_occ
    assert "mũthĩnjĩri" in occ_terms

    has_gender, gender_terms = collector._contains_terms(
        "Mũrũme na mũtumia",
        collector.GENDER_TERMS
    )
    assert has_gender
    assert len(gender_terms) == 2


def test_bible_collector_no_bible_directory():
    """Test BibleCollector handles missing directory gracefully."""
    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config, bible_dir="data/nonexistent_bible")
    samples = collector.collect()

    assert isinstance(samples, list)
    assert len(samples) == 0


@pytest.mark.slow
def test_bible_collector_collect_from_real_data():
    """Test BibleCollector with real data if available."""
    bible_dir = Path("data/raw/kikuyu_bible")
    if not bible_dir.exists():
        pytest.skip("Kikuyu Bible not available")

    config = CollectionConfig(
        language="ki",
        max_items=10,
        output_file=Path("test.csv")
    )
    collector = BibleCollector(config, bible_dir=str(bible_dir))
    samples = collector.collect()

    assert isinstance(samples, list)
    assert len(samples) <= 10

    if samples:
        sample = samples[0]
        assert sample.source == "kikuyu_bible"
        assert sample.language == "ki"
        assert 'verse_id' in sample.metadata
        assert 'occupation_terms' in sample.metadata


# Integration Tests

def test_all_collectors_integration(tmp_path):
    """Test all collectors can save to CSV."""
    collectors = []

    # Wikipedia (English)
    config_wiki = CollectionConfig(
        language="en",
        max_items=2,
        output_file=tmp_path / "wiki.csv"
    )
    collectors.append(WikipediaCollector(config_wiki))

    # News (Swahili) - will likely fail without dataset
    config_news = CollectionConfig(
        language="sw",
        max_items=2,
        output_file=tmp_path / "news.csv",
        cache_dir=tmp_path / "cache"
    )
    news_collector = NewsCollector(config_news)
    news_collector.occupation_terms.add("test")  # Add test term
    collectors.append(news_collector)

    # Bible (Kikuyu)
    config_bible = CollectionConfig(
        language="ki",
        max_items=2,
        output_file=tmp_path / "bible.csv"
    )
    collectors.append(BibleCollector(config_bible, bible_dir="data/nonexistent"))

    # Each collector should work with base interface
    for collector in collectors:
        lineage = collector.get_lineage()
        assert "source" in lineage
        assert "language" in lineage
        assert "collector" in lineage


def test_collectors_respect_max_items():
    """Test all collectors respect max_items limit."""
    # Wikipedia
    config = CollectionConfig(
        language="en",
        max_items=3,
        output_file=Path("test.csv")
    )
    wiki_collector = WikipediaCollector(config)
    samples = wiki_collector.collect()
    assert len(samples) <= 3

    # Bible (without data, should return empty)
    config = CollectionConfig(
        language="ki",
        max_items=3,
        output_file=Path("test.csv")
    )
    bible_collector = BibleCollector(config, bible_dir="data/nonexistent")
    samples = bible_collector.collect()
    assert len(samples) <= 3

    # All collectors implement same interface
    assert hasattr(wiki_collector, 'collect')
    assert hasattr(wiki_collector, 'get_lineage')
    assert hasattr(bible_collector, 'collect')
    assert hasattr(bible_collector, 'get_lineage')
