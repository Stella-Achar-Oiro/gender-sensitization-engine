#!/usr/bin/env python3
"""
Download and mine AfriSenti Swahili Twitter dataset for occupation terms.

Dataset: AfriSenti-Twitter (HausaNLP)
Source: https://huggingface.co/datasets/HausaNLP/AfriSenti-Twitter
Coverage: 14 African languages including Swahili
Size: 110,000+ annotated tweets
Quality: Sentiment-labeled Twitter/X data

This script:
1. Downloads AfriSenti Swahili tweets from HuggingFace
2. Extracts sentences containing occupation terms
3. Outputs real-world conversational Swahili text
"""

import argparse
import csv
import re
from pathlib import Path
from typing import List, Dict, Set

try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("⚠️  Warning: 'datasets' library not installed")
    print("   Install with: pip install datasets")

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = lambda x, **kwargs: x


class AfriSentiSwahiliMiner:
    """Mines AfriSenti Swahili Twitter dataset for occupation sentences"""

    DATASET_NAME = "HausaNLP/AfriSenti-Twitter"
    LANGUAGE_CODE = "swh"  # Swahili ISO 639-3 code

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.occupation_terms: Set[str] = set()

    def load_occupations(self, lexicon_path: str = "rules/lexicon_sw_v2.csv"):
        """Load occupation terms from lexicon"""
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('language') == 'sw' and 'occupation' in row.get('tags', ''):
                    biased = row['biased'].lower()
                    neutral = row.get('neutral_primary', '').lower()

                    self.occupation_terms.add(biased)
                    if neutral and neutral != biased:
                        self.occupation_terms.add(neutral)

        print(f"📚 Loaded {len(self.occupation_terms)} occupation terms")

    def download_dataset(self) -> List[Dict]:
        """Download AfriSenti Swahili dataset from HuggingFace"""
        if not HAS_DATASETS:
            raise ImportError(
                "The 'datasets' library is required. "
                "Install with: pip install datasets"
            )

        print(f"📥 Downloading AfriSenti Swahili dataset from HuggingFace...")
        print(f"   Dataset: {self.DATASET_NAME}")
        print(f"   Language: {self.LANGUAGE_CODE} (Swahili)")

        try:
            # Load Swahili subset
            dataset = load_dataset(
                self.DATASET_NAME,
                self.LANGUAGE_CODE,
                trust_remote_code=True
            )

            # Combine all splits
            all_samples = []
            for split in ['train', 'validation', 'test']:
                if split in dataset:
                    samples = dataset[split]
                    print(f"   {split}: {len(samples)} tweets")
                    all_samples.extend(samples)

            print(f"✅ Downloaded {len(all_samples)} total tweets")
            return all_samples

        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("\nAlternative: Download manually from:")
            print("https://huggingface.co/datasets/HausaNLP/AfriSenti-Twitter")
            raise

    def is_high_quality(self, text: str) -> bool:
        """Quality filters for tweets"""
        # Remove leading/trailing whitespace
        text = text.strip()

        # Length check (tweets can be short)
        if len(text) < 20 or len(text) > 280:
            return False

        # Must have alphabetic content
        if not re.search(r'[a-zA-Z]', text):
            return False

        # Avoid retweet markers, URLs, excessive hashtags
        if text.startswith('RT ') or text.startswith('rt '):
            return False
        if text.count('#') > 3:  # Too many hashtags
            return False
        if text.count('http') > 1:  # Too many URLs
            return False

        return True

    def contains_occupation(self, text: str) -> bool:
        """Check if text contains occupation term"""
        text_lower = text.lower()
        for term in self.occupation_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                return True
        return False

    def mine_tweets(self, samples: List[Dict]) -> List[Dict]:
        """Mine occupation sentences from tweets"""
        results = []

        print(f"\n🔍 Mining {len(samples)} tweets for occupation terms...")

        for sample in tqdm(samples, desc="Mining tweets"):
            # Extract text (field name may vary)
            text = sample.get('text', '') or sample.get('tweet', '')
            if not text:
                continue

            # Quality filter
            if not self.is_high_quality(text):
                continue

            # Check for occupation
            if self.contains_occupation(text):
                results.append({
                    'text': text,
                    'source': 'afrisenti_twitter',
                    'sentiment': sample.get('label', 'unknown'),
                    'language': self.LANGUAGE_CODE
                })

        print(f"\n✅ Found {len(results)} tweets with occupations")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Download and mine AfriSenti Swahili Twitter dataset"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help="Directory to store data"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/analysis/afrisenti_swahili_occupations.csv',
        help="Output file for mined tweets"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🐦 AFRISENTI SWAHILI TWITTER MINER")
    print("=" * 70)

    # Initialize miner
    miner = AfriSentiSwahiliMiner(args.output_dir)

    # Load occupations
    miner.load_occupations()

    # Download dataset
    try:
        samples = miner.download_dataset()
    except ImportError:
        print("\n💡 To use this script, install required packages:")
        print("   pip install datasets")
        return
    except Exception as e:
        print(f"\n❌ Failed to download dataset: {e}")
        return

    # Mine tweets
    results = miner.mine_tweets(samples)

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'source', 'sentiment', 'language']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("✅ Mining complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
