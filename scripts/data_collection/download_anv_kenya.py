#!/usr/bin/env python3
"""
Download ANV Data Kenya from Hugging Face
Dataset: MCAA1-MSU/anv_data_ke

This dataset contains Kenyan news and social media data
including Kikuyu language content.

Usage:
    pip install datasets
    python3 scripts/data_collection/download_anv_kenya.py --output data/raw/anv_kenya.csv
"""

import argparse
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("❌ Please install: pip install datasets")
    exit(1)


def download_anv_data(output_file: str, language_filter: str = None):
    """Download ANV Kenya dataset from Hugging Face."""

    print("\n" + "="*70)
    print("DOWNLOADING ANV DATA KENYA")
    print("="*70 + "\n")

    try:
        # Load dataset
        print("Loading dataset from Hugging Face...")
        dataset = load_dataset("MCAA1-MSU/anv_data_ke")

        # Get train split (usually the largest)
        train_data = dataset['train'] if 'train' in dataset else dataset[list(dataset.keys())[0]]

        print(f"✅ Loaded {len(train_data)} samples")
        print(f"\nDataset features: {train_data.features}")

        # Filter for Kikuyu if specified
        if language_filter:
            print(f"\nFiltering for language: {language_filter}")
            # Check if there's a language column
            if 'language' in train_data.features:
                train_data = train_data.filter(lambda x: x['language'] == language_filter)
                print(f"Filtered to {len(train_data)} {language_filter} samples")

        # Save to CSV
        import pandas as pd
        df = pd.DataFrame(train_data)
        df.to_csv(output_file, index=False, encoding='utf-8')

        print(f"\n✅ Saved to: {output_file}")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {list(df.columns)}")

        # Show sample
        print("\nSample (first 3 rows):")
        print(df.head(3))

    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify dataset exists: https://huggingface.co/datasets/MCAA1-MSU/anv_data_ke")
        print("3. Install dependencies: pip install datasets pandas")


def main():
    parser = argparse.ArgumentParser(description="Download ANV Kenya dataset")
    parser.add_argument('--output', '-o', type=str, default='data/raw/anv_kenya.csv',
                       help='Output CSV file path')
    parser.add_argument('--language', '-l', type=str, default=None,
                       help='Filter by language (e.g., kikuyu, swahili)')

    args = parser.parse_args()

    # Create output directory
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    download_anv_data(args.output, args.language)


if __name__ == "__main__":
    main()
