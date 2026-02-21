"""Wikipedia data collector.

Wraps existing extract_wikipedia.py functionality in the unified interface.
"""
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
from .base_collector import DataCollector, CollectedSample, CollectionConfig


class WikipediaCollector(DataCollector):
    """
    Collect data from Wikipedia articles.

    Integrates existing extract_wikipedia.py functionality
    to provide a standardized interface for data collection.
    """

    # Wikipedia API endpoints by language
    WIKI_APIS = {
        'en': 'https://en.wikipedia.org/w/api.php',
        'sw': 'https://sw.wikipedia.org/w/api.php',
        'fr': 'https://fr.wikipedia.org/w/api.php',
        'ki': 'https://ki.wikipedia.org/w/api.php',
    }

    # Gender-relevant search terms by language
    SEARCH_TERMS = {
        'en': {
            'occupations': ['engineer', 'nurse', 'teacher', 'doctor', 'CEO', 'secretary'],
            'stereotypes': ['women in STEM', 'gender roles'],
            'biographies': ['women leaders', 'female scientists'],
        },
        'sw': {
            'occupations': ['muuguzi', 'mwalimu', 'daktari', 'mhandisi', 'karani'],
            'stereotypes': ['wanawake', 'wanaume', 'jinsia'],
            'biographies': ['viongozi wanawake'],
        },
        'fr': {
            'occupations': ['infirmière', 'enseignant', 'médecin', 'ingénieur'],
            'stereotypes': ['rôles de genre'],
            'biographies': ['femmes leaders'],
        },
        'ki': {
            'occupations': ['mũrutani', 'mũgoti'],
            'biographies': ['atumia', 'aanake'],
        },
    }

    # Gender keywords for filtering
    GENDER_KEYWORDS = {
        'en': ['he', 'she', 'his', 'her', 'man', 'woman', 'male', 'female', 'gender'],
        'sw': ['yeye', 'mwanamke', 'mwanamume', 'mama', 'baba', 'jinsia', 'wanawake', 'wanaume'],
        'fr': ['il', 'elle', 'son', 'sa', 'homme', 'femme', 'genre'],
        'ki': ['mũndũ-wa-nja', 'mũndũ-wa-njamba', 'atumia', 'aanake'],
    }

    def __init__(self, config: CollectionConfig):
        super().__init__(config)
        self.api_url = self.WIKI_APIS.get(config.language)
        if not self.api_url:
            raise ValueError(f"Language '{config.language}' not supported for Wikipedia")
        self.stats = {'articles_fetched': 0, 'sentences_extracted': 0, 'api_calls': 0}

    def _make_api_request(self, params: Dict) -> Dict:
        """Make request to Wikipedia API with rate limiting."""
        params['format'] = 'json'
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'JuaKaziDataCollector/1.0 (Gender Bias Research)')

            with urllib.request.urlopen(req, timeout=10) as response:
                self.stats['api_calls'] += 1
                time.sleep(0.1)  # Rate limiting
                return json.loads(response.read().decode('utf-8'))
        except Exception:
            return {}

    def _search_articles(self, search_term: str, max_results: int = 5) -> List[str]:
        """Search for articles."""
        params = {
            'action': 'opensearch',
            'search': search_term,
            'limit': max_results,
            'namespace': 0,
        }

        result = self._make_api_request(params)
        if result and len(result) > 1:
            return result[1]
        return []

    def _get_article_content(self, title: str) -> Tuple[str, str]:
        """Get article content and URL."""
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'extracts|info',
            'explaintext': True,
            'exsectionformat': 'plain',
            'inprop': 'url',
        }

        result = self._make_api_request(params)
        if not result or 'query' not in result:
            return "", ""

        pages = result['query'].get('pages', {})
        for page_id, page_data in pages.items():
            if page_id == '-1':
                continue
            content = page_data.get('extract', '')
            url = page_data.get('fullurl', '')
            return content, url

        return "", ""

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract gender-relevant sentences."""
        sentences = re.split(r'[.!?]+', text)
        keywords = self.GENDER_KEYWORDS.get(self.config.language, self.GENDER_KEYWORDS['en'])

        filtered = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 40 or len(sentence) > 200:
                continue

            if any(keyword in sentence.lower() for keyword in keywords):
                filtered.append(sentence)

        return filtered

    def collect(self) -> List[CollectedSample]:
        """
        Collect Wikipedia articles for the configured language.

        Returns:
            List of collected samples from Wikipedia
        """
        samples = []
        search_terms = self.SEARCH_TERMS.get(self.config.language, {}).get('occupations', [])

        for search_term in search_terms:
            if len(samples) >= self.config.max_items:
                break

            article_titles = self._search_articles(search_term, max_results=3)

            for title in article_titles:
                if len(samples) >= self.config.max_items:
                    break

                content, url = self._get_article_content(title)
                if not content:
                    continue

                sentences = self._extract_sentences(content)

                for sentence in sentences[:3]:  # Max 3 sentences per article
                    if len(samples) >= self.config.max_items:
                        break

                    sample = CollectedSample(
                        text=sentence,
                        source="wikipedia",
                        language=self.config.language,
                        metadata={
                            'article_title': title,
                            'source_url': url,
                            'search_term': search_term,
                        }
                    )
                    samples.append(sample)
                    self.stats['sentences_extracted'] += 1

                self.stats['articles_fetched'] += 1

        return samples

    def get_lineage(self) -> Dict:
        """
        Return Wikipedia data lineage.

        Returns:
            Dictionary with provenance information
        """
        return {
            "source": "Wikipedia",
            "language": self.config.language,
            "collection_date": datetime.now().isoformat(),
            "method": "wikipedia_api",
            "max_articles": self.config.max_items,
            "collector": "WikipediaCollector",
            "api_url": self.api_url,
            "stats": self.stats
        }


class GroundTruthCollector(DataCollector):
    """
    Collector that loads from existing ground truth files.

    This is used for demos and testing.
    """

    def collect(self) -> List[CollectedSample]:
        """
        Load samples from ground truth files.

        Returns:
            List of samples from ground truth
        """
        from eval.data_loader import GroundTruthLoader
        from eval.models import Language

        # Map language code to enum
        lang_map = {
            "en": Language.ENGLISH,
            "sw": Language.SWAHILI,
            "fr": Language.FRENCH,
            "ki": Language.GIKUYU
        }

        if self.config.language not in lang_map:
            return []

        language = lang_map[self.config.language]
        loader = GroundTruthLoader()

        try:
            gt_samples = loader.load_ground_truth(language)
            gt_samples = gt_samples[:self.config.max_items]

            samples = []
            for gt_sample in gt_samples:
                sample = CollectedSample(
                    text=gt_sample.text,
                    source="ground_truth",
                    language=self.config.language,
                    metadata={
                        "has_bias": gt_sample.has_bias,
                        "category": gt_sample.bias_category.value if gt_sample.bias_category else None
                    }
                )
                samples.append(sample)

            return samples

        except Exception as e:
            print(f"Warning: Failed to load ground truth: {e}")
            return []

    def get_lineage(self) -> Dict:
        """Return ground truth data lineage."""
        return {
            "source": "ground_truth",
            "language": self.config.language,
            "method": "GroundTruthLoader",
            "max_items": self.config.max_items,
            "collector": "GroundTruthCollector",
            "version": "1.0"
        }
