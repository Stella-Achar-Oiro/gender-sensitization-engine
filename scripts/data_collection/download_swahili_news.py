#!/usr/bin/env python3
"""
Download and mine Swahili News Dataset from Zenodo.

Dataset: Swahili News Dataset (31,000+ articles from Kenya)
Source: https://zenodo.org/record/5514203
Coverage: 2015-2020
Quality: Professional journalism

This script:
1. Downloads the dataset from Zenodo
2. Extracts sentences containing occupation terms
3. Filters for quality (length, capitalization, punctuation)
4. Outputs real-world Swahili text with occupations
"""

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path
from typing import List, Dict, Set
import urllib.request

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = lambda x, **kwargs: x  # Fallback: no progress bar


class SwahiliNewsDownloader:
    """Downloads and processes Swahili News Dataset"""

    # Zenodo dataset URL
    ZENODO_URL = "https://zenodo.org/record/5514203/files/swahili-news.zip"

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_path = self.output_dir / "swahili-news.zip"
        self.extracted_dir = self.output_dir / "swahili-news"

    def download(self, force: bool = False):
        """Download dataset from Zenodo"""
        if self.dataset_path.exists() and not force:
            print(f"✓ Dataset already downloaded: {self.dataset_path}")
            return

        print(f"📥 Downloading Swahili News Dataset from Zenodo...")
        print(f"   URL: {self.ZENODO_URL}")
        print(f"   Size: ~200MB (this may take a few minutes)")

        try:
            if HAS_TQDM:
                with tqdm(unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                    def update_progress(block_num, block_size, total_size):
                        pbar.total = total_size
                        pbar.update(block_size)

                    urllib.request.urlretrieve(
                        self.ZENODO_URL,
                        self.dataset_path,
                        reporthook=update_progress
                    )
            else:
                # No progress bar, just download
                print("   Downloading... (no progress bar available)")
                urllib.request.urlretrieve(
                    self.ZENODO_URL,
                    self.dataset_path
                )

            print(f"✅ Downloaded to: {self.dataset_path}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("\nAlternative: Download manually from:")
            print("https://zenodo.org/record/5514203")
            print(f"Save to: {self.dataset_path}")
            raise

    def extract(self):
        """Extract downloaded zip file"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        print(f"\n📂 Extracting dataset...")
        try:
            with zipfile.ZipFile(self.dataset_path, 'r') as zip_ref:
                zip_ref.extractall(self.extracted_dir)
            print(f"✅ Extracted to: {self.extracted_dir}")
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            raise

    def get_data_files(self) -> List[Path]:
        """Find all data files in extracted directory"""
        # Look for JSON or CSV files
        json_files = list(self.extracted_dir.rglob("*.json"))
        csv_files = list(self.extracted_dir.rglob("*.csv"))
        txt_files = list(self.extracted_dir.rglob("*.txt"))

        all_files = json_files + csv_files + txt_files
        print(f"\n📄 Found {len(all_files)} data files")
        return all_files


class OccupationSentenceMiner:
    """Mines sentences containing occupation terms from news articles"""

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
                    # Add both biased and neutral forms
                    biased = row['biased'].lower()
                    neutral = row.get('neutral_primary', '').lower()

                    self.occupation_terms.add(biased)
                    if neutral and neutral != biased:
                        self.occupation_terms.add(neutral)

        print(f"📚 Loaded {len(self.occupation_terms)} occupation terms from lexicon")

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Split on sentence endings
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            # Minimum length check
            if len(sent) < 20 or len(sent) > 500:
                continue
            # Must have at least one word character
            if not re.search(r'\w', sent):
                continue
            cleaned.append(sent)
        return cleaned

    def contains_occupation(self, sentence: str) -> bool:
        """Check if sentence contains any occupation term"""
        sentence_lower = sentence.lower()
        for term in self.occupation_terms:
            # Word boundary search
            if re.search(r'\b' + re.escape(term) + r'\b', sentence_lower):
                return True
        return False

    def mine_file(self, file_path: Path) -> List[Dict]:
        """Mine occupation sentences from a single file"""
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    # JSON format
                    data = json.load(f)
                    # Handle different JSON structures
                    if isinstance(data, list):
                        texts = [item.get('text', '') or item.get('content', '') for item in data]
                    elif isinstance(data, dict):
                        texts = [data.get('text', '') or data.get('content', '')]
                    else:
                        texts = []
                elif file_path.suffix == '.csv':
                    # CSV format
                    reader = csv.DictReader(f)
                    texts = [row.get('text', '') or row.get('content', '') or row.get('article', '') for row in reader]
                else:
                    # Plain text
                    texts = [f.read()]

            # Process each text
            for text in texts:
                if not text:
                    continue

                sentences = self.extract_sentences(text)
                for sentence in sentences:
                    if self.contains_occupation(sentence):
                        results.append({
                            'text': sentence,
                            'source': 'swahili_news',
                            'file': str(file_path.name)
                        })

        except Exception as e:
            print(f"⚠️  Error processing {file_path.name}: {e}")

        return results

    def mine_all(self, files: List[Path]) -> List[Dict]:
        """Mine all files for occupation sentences"""
        all_results = []

        print(f"\n🔍 Mining {len(files)} files for occupation sentences...")
        for file_path in tqdm(files, desc="Mining files"):
            results = self.mine_file(file_path)
            all_results.extend(results)

        print(f"\n✅ Found {len(all_results)} sentences with occupations")
        return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Download and mine Swahili News Dataset"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help="Directory to download dataset"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/analysis/swahili_news_occupations.csv',
        help="Output file for mined sentences"
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help="Force re-download even if file exists"
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help="Skip download, use existing files"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🗞️  SWAHILI NEWS DATASET MINER")
    print("=" * 70)

    # Download and extract
    downloader = SwahiliNewsDownloader(args.output_dir)

    if not args.skip_download:
        downloader.download(force=args.force_download)
        downloader.extract()

    files = downloader.get_data_files()

    if not files:
        print("❌ No data files found. Check extraction.")
        return

    # Mine occupation sentences
    miner = OccupationSentenceMiner()
    results = miner.mine_all(files)

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'source', 'file']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("✅ Mining complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
