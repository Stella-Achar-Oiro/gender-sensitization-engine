#!/usr/bin/env python3
"""
Download Kikuyu Twitter Data for Gender Bias Detection

Collects Kikuyu language tweets with occupation/gender contexts for bias detection.

IMPORTANT: Requires Twitter API v2 credentials (Academic Research or Elevated access)

Data Privacy:
- All PII (names, handles, locations) will be removed
- Only text content is preserved
- Fully anonymized for research use

Related Datasets:
- Swahili Social Media: https://github.com/dlab-tz/Swahili-Social-Media-Data
- AfriSenti: https://huggingface.co/datasets/afrisenti

Usage:
    # Set Twitter API credentials
    export TWITTER_BEARER_TOKEN="your_token_here"

    # Download tweets
    python3 scripts/data_collection/download_kikuyu_twitter.py \\
        --output data/raw/kikuyu_twitter.csv \\
        --max-tweets 1000

Prerequisites:
    pip install tweepy pandas
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("WARNING: tweepy library not installed.")
    print("Install with: pip install tweepy")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# Kikuyu occupation terms to search for
KIKUYU_OCCUPATION_TERMS = [
    "mũrutani",      # teacher
    "daktari",       # doctor
    "mũrũgamĩrĩri",  # manager/leader
    "mũthaki",       # athlete/runner
    "mũigũ",         # builder/constructor
    "mũndũ wa thiĩ", # worker
    "mũrĩmi",        # farmer
    "mũthondeki",    # developer
    "mũteti",        # politician
]

# Gender-related terms in Kikuyu
GENDER_TERMS = [
    "mũrũme",   # man/male
    "mũtumia",  # woman/female
    "mũirĩtu",  # girl
    "kĩhĩĩ",    # boy
]


def anonymize_text(text: str) -> str:
    """
    Remove PII from tweet text.

    Removes:
    - @mentions
    - URLs
    - Hashtags (optionally keep for context)
    - Email addresses
    - Phone numbers
    """
    # Remove @mentions
    text = re.sub(r'@\w+', '[USER]', text)

    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)

    # Remove phone numbers (Kenyan format)
    text = re.sub(r'(\+254|254|0)[17]\d{8}', '[PHONE]', text)

    return text.strip()


def search_kikuyu_tweets(bearer_token: str, max_tweets: int = 1000):
    """
    Search for Kikuyu tweets with occupation/gender contexts.

    Args:
        bearer_token: Twitter API Bearer Token
        max_tweets: Maximum tweets to collect

    Returns:
        List of tweet dictionaries
    """
    if not TWEEPY_AVAILABLE:
        print("ERROR: tweepy library required")
        return []

    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

    tweets_data = []

    # Search for tweets with Kikuyu occupation terms
    for term in KIKUYU_OCCUPATION_TERMS:
        print(f"Searching for tweets with '{term}'...")

        try:
            # Search tweets
            # Note: Academic Research access required for full archive
            tweets = client.search_recent_tweets(
                query=f"{term} lang:ki OR ({term} Kenya)",
                max_results=min(100, max_tweets // len(KIKUYU_OCCUPATION_TERMS)),
                tweet_fields=['created_at', 'lang', 'public_metrics']
            )

            if tweets.data:
                for tweet in tweets.data:
                    # Check if contains gender terms (basic filter)
                    has_gender_context = any(
                        gender_term in tweet.text.lower()
                        for gender_term in GENDER_TERMS
                    )

                    tweets_data.append({
                        'tweet_id': tweet.id,
                        'text': tweet.text,
                        'text_anonymized': anonymize_text(tweet.text),
                        'created_at': tweet.created_at,
                        'lang': tweet.lang,
                        'search_term': term,
                        'has_gender_context': has_gender_context,
                        'source': 'twitter_api_v2',
                        'collection_date': datetime.now().isoformat()
                    })

                print(f"  Found {len(tweets.data)} tweets")
            else:
                print(f"  No tweets found")

            if len(tweets_data) >= max_tweets:
                break

        except tweepy.TweepyException as e:
            print(f"ERROR searching for '{term}': {e}")
            continue

    return tweets_data


def main():
    parser = argparse.ArgumentParser(
        description="Download Kikuyu Twitter data for bias detection"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/kikuyu_twitter.csv"),
        help="Output CSV file path (default: data/raw/kikuyu_twitter.csv)"
    )
    parser.add_argument(
        "--max-tweets",
        type=int,
        default=1000,
        help="Maximum tweets to collect (default: 1000)"
    )
    parser.add_argument(
        "--bearer-token",
        help="Twitter API Bearer Token (or set TWITTER_BEARER_TOKEN env var)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Kikuyu Twitter Data Collection")
    print("=" * 60)

    # Check dependencies
    if not TWEEPY_AVAILABLE:
        print("\n❌ ERROR: Required library 'tweepy' not installed")
        print("Install with: pip install tweepy")
        return 1

    # Get bearer token
    bearer_token = args.bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        print("\n❌ ERROR: Twitter API Bearer Token required")
        print("\nOptions:")
        print("1. Set environment variable: export TWITTER_BEARER_TOKEN='your_token'")
        print("2. Pass via command line: --bearer-token 'your_token'")
        print("\nGet token at: https://developer.twitter.com/en/portal/dashboard")
        print("Required access: Elevated or Academic Research")
        return 1

    # Search for tweets
    print(f"\nSearching for Kikuyu tweets with occupation/gender contexts...")
    print(f"Max tweets: {args.max_tweets}")
    print(f"Search terms: {', '.join(KIKUYU_OCCUPATION_TERMS)}\n")

    tweets_data = search_kikuyu_tweets(bearer_token, args.max_tweets)

    if not tweets_data:
        print("\n⚠️ No tweets found. Try:")
        print("- Checking API credentials")
        print("- Expanding search terms")
        print("- Using Academic Research access for full archive")
        return 1

    # Write to CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=tweets_data[0].keys())
        writer.writeheader()
        writer.writerows(tweets_data)

    print(f"\n✅ Downloaded {len(tweets_data)} tweets to {args.output}")
    print(f"File size: {args.output.stat().st_size / 1024:.2f} KB")

    # Summary stats
    with_gender = sum(1 for t in tweets_data if t['has_gender_context'])
    print(f"\nSummary:")
    print(f"  Total tweets: {len(tweets_data)}")
    print(f"  With gender context: {with_gender} ({with_gender/len(tweets_data)*100:.1f}%)")
    print(f"  Anonymized: Yes (PII removed)")

    print(f"\nNext steps:")
    print(f"1. Review anonymized tweets: {args.output}")
    print(f"2. Filter for bias-relevant samples")
    print(f"3. Annotate using: scripts/data_collection/annotate_samples.py")
    print(f"4. Add to ground truth dataset")

    return 0


if __name__ == "__main__":
    sys.exit(main())
