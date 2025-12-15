#!/usr/bin/env python3
"""
Scrape Twitter/X for Swahili tweets containing occupation terms.

Uses snscrape (no API key needed) to collect natural Swahili language.

This script:
1. Searches Twitter for occupation terms in Swahili
2. Filters for high-quality tweets (length, language detection)
3. Extracts real conversational Swahili text
4. Outputs diverse, natural language samples

Requirements:
    pip install snscrape
"""

import argparse
import csv
import re
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime, timedelta


class TwitterSwahiliScraper:
    """Scrapes Twitter for Swahili occupation-related tweets"""

    def __init__(self, lexicon_path: str = "rules/lexicon_sw_v2.csv"):
        self.lexicon_path = Path(lexicon_path)
        self.occupation_terms: Set[str] = set()
        self.load_occupations()

    def load_occupations(self):
        """Load occupation terms from lexicon"""
        with open(self.lexicon_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('language') == 'sw' and 'occupation' in row.get('tags', ''):
                    biased = row['biased']
                    neutral = row.get('neutral_primary', '')

                    self.occupation_terms.add(biased)
                    if neutral and neutral != biased:
                        self.occupation_terms.add(neutral)

        print(f"📚 Loaded {len(self.occupation_terms)} occupation terms")

    def is_high_quality(self, text: str) -> bool:
        """Filter for high-quality tweets"""
        # Length check
        if len(text) < 30 or len(text) > 280:
            return False

        # Must contain Swahili characters/patterns
        if not re.search(r'\b(ni|ya|wa|na|kwa|za|la)\b', text.lower()):
            return False

        # Reject if mostly URLs
        url_count = len(re.findall(r'http[s]?://\S+', text))
        if url_count > 2:
            return False

        # Reject if mostly hashtags
        hashtag_count = len(re.findall(r'#\w+', text))
        if hashtag_count > 5:
            return False

        # Reject if too many @ mentions
        mention_count = len(re.findall(r'@\w+', text))
        if mention_count > 3:
            return False

        return True

    def scrape_term(self, term: str, max_tweets: int = 100) -> List[Dict]:
        """Scrape tweets for a single occupation term"""
        results = []

        try:
            import snscrape.modules.twitter as sntwitter
        except ImportError:
            print("❌ snscrape not installed. Install with:")
            print("   pip install snscrape")
            print("\nAlternative: pip install git+https://github.com/JustAnotherArchivist/snscrape.git")
            return []

        # Build query
        # lang:sw for Swahili, filter for Kenya/Tanzania/Uganda
        query = f'{term} lang:sw'

        print(f"  Searching: {query}")

        try:
            # Scrape tweets
            count = 0
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if count >= max_tweets:
                    break

                # Quality filter
                if not self.is_high_quality(tweet.content):
                    continue

                results.append({
                    'text': tweet.content,
                    'source': 'twitter',
                    'term': term,
                    'date': tweet.date.strftime('%Y-%m-%d'),
                    'username': tweet.user.username,
                    'likes': tweet.likeCount,
                    'retweets': tweet.retweetCount
                })

                count += 1

                if count % 10 == 0:
                    print(f"    Found {count} tweets...")

            print(f"  ✓ Collected {len(results)} tweets for '{term}'")

        except Exception as e:
            print(f"  ⚠️  Error scraping '{term}': {e}")

        return results

    def scrape_all(self, max_per_term: int = 100, limit_terms: int = None) -> List[Dict]:
        """Scrape tweets for all occupation terms"""
        all_results = []

        terms_to_scrape = list(self.occupation_terms)
        if limit_terms:
            terms_to_scrape = terms_to_scrape[:limit_terms]

        print(f"\n🐦 Scraping Twitter for {len(terms_to_scrape)} occupation terms...")
        print(f"   Max tweets per term: {max_per_term}")

        for i, term in enumerate(terms_to_scrape, 1):
            print(f"\n[{i}/{len(terms_to_scrape)}] Term: {term}")
            results = self.scrape_term(term, max_per_term)
            all_results.extend(results)

        print(f"\n✅ Total tweets collected: {len(all_results)}")
        return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Twitter for Swahili occupation tweets"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/analysis/twitter_swahili_occupations.csv',
        help="Output file for scraped tweets"
    )
    parser.add_argument(
        '--max-per-term',
        type=int,
        default=100,
        help="Maximum tweets per occupation term"
    )
    parser.add_argument(
        '--limit-terms',
        type=int,
        help="Limit to first N occupation terms (for testing)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🐦 TWITTER SWAHILI OCCUPATION SCRAPER")
    print("=" * 70)
    print("\n⚠️  Note: This uses snscrape (no API key needed)")
    print("   Make sure snscrape is installed: pip install snscrape\n")

    # Check for snscrape
    try:
        import snscrape
    except ImportError:
        print("❌ snscrape not installed!\n")
        print("Install with:")
        print("  pip install snscrape")
        print("\nOr from GitHub:")
        print("  pip install git+https://github.com/JustAnotherArchivist/snscrape.git")
        return

    scraper = TwitterSwahiliScraper()
    results = scraper.scrape_all(
        max_per_term=args.max_per_term,
        limit_terms=args.limit_terms
    )

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'source', 'term', 'date', 'username', 'likes', 'retweets']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("✅ Scraping complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review tweets for quality")
    print("2. Filter for bias/no-bias labels")
    print("3. Add to ground truth dataset")


if __name__ == "__main__":
    main()
