#!/usr/bin/env python3
"""
Download and mine CC100 Swahili corpus for occupation terms.

Dataset: CC100 Swahili (CommonCrawl monolingual corpus)
Source: https://data.statmt.org/cc-100/
HuggingFace: https://huggingface.co/datasets/statmt/cc100
Size: Large monolingual Swahili corpus from web crawl
Quality: Web text, mixed quality (news, blogs, forums)

This script:
1. Downloads CC100 Swahili corpus from HuggingFace
2. Samples sentences (corpus is very large)
3. Extracts sentences containing occupation terms
4. Outputs real-world Swahili text
"""

import argparse
import csv
import re
from pathlib import Path
from typing import List, Dict, Set
import random

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


class CC100SwahiliMiner:
    """Mines CC100 Swahili corpus for occupation sentences"""

    DATASET_NAME = "statmt/cc100"
    LANGUAGE_CODE = "sw"  # Swahili

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

    def download_dataset(self, max_samples: int = 10000) -> List[str]:
        """Download CC100 Swahili corpus (sampled)"""
        if not HAS_DATASETS:
            raise ImportError(
                "The 'datasets' library is required. "
                "Install with: pip install datasets"
            )

        print(f"📥 Downloading CC100 Swahili corpus from HuggingFace...")
        print(f"   Dataset: {self.DATASET_NAME}")
        print(f"   Language: {self.LANGUAGE_CODE} (Swahili)")
        print(f"   Sampling: {max_samples:,} documents (corpus is very large)")

        try:
            # Load with streaming to avoid downloading entire corpus
            dataset = load_dataset(
                self.DATASET_NAME,
                lang=self.LANGUAGE_CODE,
                split="train",
                streaming=True  # Important: stream instead of download all
            )

            # Sample documents
            texts = []
            print("\n   Streaming and sampling documents...")

            for i, item in enumerate(dataset):
                if i >= max_samples:
                    break

                text = item.get('text', '')
                if text:
                    texts.append(text)

                if (i + 1) % 1000 == 0:
                    print(f"   Processed: {i+1:,} documents")

            print(f"\n✅ Sampled {len(texts):,} documents")
            return texts

        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("\nAlternative: Download from:")
            print("https://data.statmt.org/cc-100/")
            raise

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Split on sentence endings
        sentences = re.split(r'[.!?]+', text)
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            # Length check
            if len(sent) < 20 or len(sent) > 500:
                continue
            cleaned.append(sent)
        return cleaned

    def is_high_quality(self, sentence: str) -> bool:
        """Quality filter for sentences"""
        # Must have alphabetic content
        if not re.search(r'[a-zA-Z]', sentence):
            return False

        # Not too much punctuation
        punct_ratio = sum(c in '.,!?;:' for c in sentence) / len(sentence)
        if punct_ratio > 0.15:
            return False

        return True

    def contains_occupation(self, sentence: str) -> bool:
        """Check if sentence contains occupation term"""
        sentence_lower = sentence.lower()
        for term in self.occupation_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', sentence_lower):
                return True
        return False

    def mine_corpus(self, texts: List[str]) -> List[Dict]:
        """Mine occupation sentences from corpus"""
        results = []

        print(f"\n🔍 Mining {len(texts):,} documents for occupation terms...")

        for text in tqdm(texts, desc="Mining documents"):
            sentences = self.extract_sentences(text)

            for sentence in sentences:
                if not self.is_high_quality(sentence):
                    continue

                if self.contains_occupation(sentence):
                    results.append({
                        'text': sentence,
                        'source': 'cc100_swahili',
                        'corpus': 'commonweb'
                    })

        print(f"\n✅ Found {len(results):,} sentences with occupations")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Download and mine CC100 Swahili corpus"
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=10000,
        help="Max documents to sample from corpus (default: 10000)"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/analysis/cc100_swahili_occupations.csv',
        help="Output file for mined sentences"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🌐 CC100 SWAHILI CORPUS MINER")
    print("=" * 70)

    # Initialize miner
    miner = CC100SwahiliMiner()

    # Load occupations
    miner.load_occupations()

    # Download dataset (streamed/sampled)
    try:
        texts = miner.download_dataset(args.max_samples)
    except ImportError:
        print("\n💡 To use this script, install: pip install datasets")
        return
    except Exception as e:
        print(f"\n❌ Failed to download: {e}")
        return

    # Mine sentences
    results = miner.mine_corpus(texts)

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'source', 'corpus']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("✅ Mining complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
