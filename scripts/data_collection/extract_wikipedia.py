#!/usr/bin/env python3
"""
Extract gender-relevant text from Wikipedia for bias detection

This script extracts text from Wikipedia articles in multiple languages,
focusing on gender-relevant topics like occupations, biographies, and social roles.

Usage:
    python scripts/data_collection/extract_wikipedia.py --language en --topics occupations --output data/raw/
    python scripts/data_collection/extract_wikipedia.py --language sw --topics all --max-articles 100
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import csv
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class WikipediaExtractor:
    """Extracts gender-relevant text from Wikipedia"""

    # Wikipedia API endpoints by language
    WIKI_APIS = {
        'en': 'https://en.wikipedia.org/w/api.php',
        'sw': 'https://sw.wikipedia.org/w/api.php',
        'fr': 'https://fr.wikipedia.org/w/api.php',
        'ki': 'https://ki.wikipedia.org/w/api.php',  # Gikuyu
    }

    # Gender-relevant search terms by language
    SEARCH_TERMS = {
        'en': {
            'occupations': ['engineer', 'nurse', 'teacher', 'doctor', 'CEO', 'secretary', 'programmer'],
            'stereotypes': ['women in STEM', 'gender roles', 'gender stereotypes', 'working mothers'],
            'biographies': ['women leaders', 'female scientists', 'male nurses', 'women engineers'],
        },
        'sw': {
            'occupations': ['muuguzi', 'mwalimu', 'daktari', 'mhandisi', 'karani'],  # nurse, teacher, doctor, engineer, clerk
            'stereotypes': ['wanawake', 'wanaume', 'jinsia'],  # women, men, gender
            'biographies': ['viongozi wanawake', 'wanasayansi wanawake'],  # women leaders, women scientists
        },
        'fr': {
            'occupations': ['infirmière', 'enseignant', 'médecin', 'ingénieur', 'secrétaire'],
            'stereotypes': ['femmes dans STEM', 'rôles de genre', 'stéréotypes de genre'],
            'biographies': ['femmes leaders', 'femmes scientifiques', 'femmes ingénieurs'],
        },
        'ki': {
            'occupations': ['mũrutani', 'mũgoti'],  # teacher, nurse (limited - needs verification)
            'biographies': ['atumia', 'aanake'],  # women, men
        },
    }

    def __init__(self, language: str = 'en', output_dir: str = 'data/raw'):
        self.language = language
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = self.WIKI_APIS.get(language)
        self.stats = {'articles_fetched': 0, 'sentences_extracted': 0, 'api_calls': 0}

        if not self.api_url:
            raise ValueError(f"Language '{language}' not supported. Use: {list(self.WIKI_APIS.keys())}")

    def _make_api_request(self, params: Dict) -> Dict:
        """Make a request to Wikipedia API with rate limiting"""
        params['format'] = 'json'
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"

        try:
            # Add User-Agent header to avoid 403 errors
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'JuaKaziDataCollector/1.0 (Gender Bias Research; achar@juakazi.org)')

            with urllib.request.urlopen(req) as response:
                self.stats['api_calls'] += 1
                time.sleep(0.1)  # Rate limiting: 10 requests/second max
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"  ⚠️  API request failed: {e}")
            return {}

    def search_articles(self, search_term: str, max_results: int = 10) -> List[str]:
        """Search for articles matching a term"""
        params = {
            'action': 'opensearch',
            'search': search_term,
            'limit': max_results,
            'namespace': 0,  # Main namespace only
        }

        result = self._make_api_request(params)
        if result and len(result) > 1:
            return result[1]  # List of article titles
        return []

    def get_article_content(self, title: str) -> Tuple[str, str]:
        """Get article content and URL"""
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
            if page_id == '-1':  # Page doesn't exist
                continue

            content = page_data.get('extract', '')
            url = page_data.get('fullurl', '')
            return content, url

        return "", ""

    def extract_sentences(self, text: str, min_length: int = 40, max_length: int = 200) -> List[str]:
        """Extract sentences from text, filtering by length and gender relevance"""
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]+', text)

        # Gender-relevant keywords for filtering
        gender_keywords = {
            'en': ['he', 'she', 'his', 'her', 'man', 'woman', 'male', 'female', 'boy', 'girl',
                   'father', 'mother', 'son', 'daughter', 'husband', 'wife', 'gender'],
            'sw': ['yeye', 'mwanamke', 'mwanamume', 'mama', 'baba', 'jinsia', 'wanawake', 'wanaume'],
            'fr': ['il', 'elle', 'son', 'sa', 'homme', 'femme', 'masculin', 'féminin', 'genre'],
            'ki': ['mũndũ-wa-nja', 'mũndũ-wa-njamba', 'atumia', 'aanake'],  # woman, man, women, men
        }

        keywords = gender_keywords.get(self.language, gender_keywords['en'])

        filtered_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()

            # Length filter
            if len(sentence) < min_length or len(sentence) > max_length:
                continue

            # Gender relevance filter
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                filtered_sentences.append(sentence)

        return filtered_sentences

    def extract_by_topic(self, topic_category: str, max_articles: int = 50) -> List[Dict]:
        """Extract samples for a specific topic category"""
        print(f"\n📥 Extracting {topic_category} articles...")

        search_terms = self.SEARCH_TERMS.get(self.language, {}).get(topic_category, [])
        if not search_terms:
            print(f"  ⚠️  No search terms defined for topic '{topic_category}' in language '{self.language}'")
            return []

        samples = []
        sample_id = 1
        articles_processed = 0

        for search_term in search_terms:
            if articles_processed >= max_articles:
                break

            print(f"  Searching: '{search_term}'...")
            article_titles = self.search_articles(search_term, max_results=5)

            for title in article_titles:
                if articles_processed >= max_articles:
                    break

                print(f"    Extracting: {title}")
                content, url = self.get_article_content(title)

                if not content:
                    continue

                # Extract gender-relevant sentences
                sentences = self.extract_sentences(content)

                for sentence in sentences[:5]:  # Max 5 sentences per article
                    # Map language codes to full names
                    lang_map = {'en': 'en', 'sw': 'sw', 'fr': 'fr', 'ki': 'ki'}
                    country_map = {'en': 'USA', 'sw': 'Kenya', 'fr': 'France', 'ki': 'Kenya'}

                    sample = {
                        'id': f'{lang_map[self.language].upper()}-WIKI-{sample_id:04d}',
                        'language': lang_map[self.language],
                        'script': 'latin',
                        'country': country_map.get(self.language, ''),
                        'region_dialect': '',
                        'source_type': 'web_public',
                        'source_ref': url,
                        'collection_date': datetime.now().strftime('%Y-%m-%d'),
                        'text': sentence,
                        'translation': '',
                        'domain': self._map_topic_to_domain(topic_category),
                        'topic': search_term,
                        'theme': 'stereotypes',
                        'sensitive_characteristic': 'gender',
                        'target_gender': 'NEEDS_ANNOTATION',
                        'bias_label': 'NEEDS_ANNOTATION',
                        'stereotype_category': 'NEEDS_ANNOTATION',
                        'explicitness': 'NEEDS_ANNOTATION',
                        'bias_severity': '',
                        'sentiment_toward_referent': '',
                        'device': '',
                        'safety_flag': 'safe',
                        'pii_removed': 'false',  # May need PII check
                        'annotator_id': '',
                        'qa_status': 'needs_review',
                        'approver_id': '',
                        'cohen_kappa': '',
                        'notes': f'Source: {self.language}.wikipedia.org. Article: {title}. Topic: {topic_category}.',
                        'eval_split': 'train'
                    }
                    samples.append(sample)
                    sample_id += 1
                    self.stats['sentences_extracted'] += 1

                articles_processed += 1
                self.stats['articles_fetched'] += 1

        return samples

    def _map_topic_to_domain(self, topic: str) -> str:
        """Map topic category to domain"""
        mapping = {
            'occupations': 'livelihoods_and_work',
            'stereotypes': 'mixed',
            'biographies': 'leadership_and_representation',
        }
        return mapping.get(topic, 'mixed')

    def extract_all_topics(self, max_articles_per_topic: int = 50) -> List[Dict]:
        """Extract samples from all topic categories"""
        all_samples = []

        topics = self.SEARCH_TERMS.get(self.language, {}).keys()
        for topic in topics:
            samples = self.extract_by_topic(topic, max_articles=max_articles_per_topic)
            all_samples.extend(samples)

        return all_samples

    def save_to_csv(self, samples: List[Dict], filename: str):
        """Save samples to CSV with standard schema"""
        if not samples:
            print(f"  ⚠️  No samples to save")
            return

        output_file = self.output_dir / filename

        # All fields from our schema
        fieldnames = [
            'id', 'language', 'script', 'country', 'region_dialect',
            'source_type', 'source_ref', 'collection_date',
            'text', 'translation', 'domain', 'topic', 'theme',
            'sensitive_characteristic', 'target_gender', 'bias_label',
            'stereotype_category', 'explicitness', 'bias_severity',
            'sentiment_toward_referent', 'device', 'safety_flag',
            'pii_removed', 'annotator_id', 'qa_status', 'approver_id',
            'cohen_kappa', 'notes', 'eval_split'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(samples)

        print(f"  💾 Saved to {output_file}")

    def print_stats(self):
        """Print extraction statistics"""
        print("\n" + "="*60)
        print("📊 EXTRACTION STATISTICS")
        print("="*60)
        print(f"  Language:           {self.language}")
        print(f"  Articles fetched:   {self.stats['articles_fetched']}")
        print(f"  Sentences extracted: {self.stats['sentences_extracted']}")
        print(f"  API calls made:     {self.stats['api_calls']}")
        print(f"  Output directory:   {self.output_dir}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Extract gender-relevant text from Wikipedia"
    )
    parser.add_argument(
        '--language',
        type=str,
        choices=['en', 'sw', 'fr', 'ki'],
        default='en',
        help="Language code (en=English, sw=Swahili, fr=French, ki=Gikuyu)"
    )
    parser.add_argument(
        '--topics',
        nargs='+',
        default=['all'],
        help="Topic categories to extract (occupations, stereotypes, biographies, or 'all')"
    )
    parser.add_argument(
        '--max-articles',
        type=int,
        default=50,
        help="Maximum articles to fetch per topic (default: 50)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw',
        help="Output directory (default: data/raw)"
    )

    args = parser.parse_args()

    print("="*60)
    print("📖 WIKIPEDIA EXTRACTOR")
    print("="*60)
    print(f"Language: {args.language}")
    print(f"Topics: {', '.join(args.topics)}")
    print(f"Max articles per topic: {args.max_articles}")
    print("="*60)

    extractor = WikipediaExtractor(language=args.language, output_dir=args.output)

    if 'all' in args.topics:
        samples = extractor.extract_all_topics(max_articles_per_topic=args.max_articles)
    else:
        samples = []
        for topic in args.topics:
            topic_samples = extractor.extract_by_topic(topic, max_articles=args.max_articles)
            samples.extend(topic_samples)

    # Save results
    filename = f"wikipedia_{args.language}_raw.csv"
    extractor.save_to_csv(samples, filename)

    extractor.print_stats()

    print("\n✅ Extraction complete!")
    print("\nNext steps:")
    print("1. Run PII detection on extracted samples")
    print("2. Review samples for quality")
    print("3. Annotate bias_label, target_gender, etc.")
    print("4. Validate with domain experts")


if __name__ == "__main__":
    main()
