#!/usr/bin/env python3
"""
Download All Kikuyu Language Data Sources

This script downloads from all identified sources with accurate live links:
1. CGIAR/KikuyuEnglish_translation (Hugging Face)
2. Kikuyu-Kiswahili GitHub repository
3. African NLP datasets repository
4. Google WAXAL (if available)

Usage:
    python3 scripts/data_collection/download_all_kikuyu_sources.py
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure data directories exist
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/external").mkdir(parents=True, exist_ok=True)


def download_huggingface_dataset(dataset_name: str, output_file: str, source_url: str):
    """Download dataset from Hugging Face."""
    print(f"\n{'='*70}")
    print(f"DOWNLOADING: {dataset_name}")
    print(f"{'='*70}")
    print(f"Source URL: {source_url}")

    try:
        from datasets import load_dataset
        import pandas as pd

        print(f"Loading dataset from Hugging Face...")
        dataset = load_dataset(dataset_name)

        # Get train split or first available
        split_name = 'train' if 'train' in dataset else list(dataset.keys())[0]
        data = dataset[split_name]

        print(f"✅ Loaded {len(data):,} samples")

        # Convert to DataFrame and add metadata
        df = pd.DataFrame(data)
        df['source_url'] = source_url
        df['source_dataset'] = dataset_name.split('/')[-1]
        df['collection_date'] = datetime.now().strftime('%Y-%m-%d')

        # Save
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Saved to: {output_file}")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {list(df.columns)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def clone_github_repo(repo_url: str, dest_dir: str):
    """Clone GitHub repository."""
    print(f"\n{'='*70}")
    print(f"CLONING GITHUB REPO: {repo_url}")
    print(f"{'='*70}")

    try:
        if Path(dest_dir).exists():
            print(f"⚠️  Directory already exists: {dest_dir}")
            print(f"   Pulling latest changes...")
            subprocess.run(['git', '-C', dest_dir, 'pull'], check=True)
        else:
            print(f"Cloning to: {dest_dir}")
            subprocess.run(['git', 'clone', repo_url, dest_dir], check=True)

        print(f"✅ Repository ready: {dest_dir}")
        return True

    except Exception as e:
        print(f"❌ Error cloning: {e}")
        return False


def extract_from_repo(repo_dir: str, patterns: list, output_file: str, source_url: str):
    """Extract data files from cloned repository."""
    print(f"\n{'='*70}")
    print(f"EXTRACTING DATA FROM: {repo_dir}")
    print(f"{'='*70}")

    import glob
    import pandas as pd

    all_data = []

    for pattern in patterns:
        files = glob.glob(f"{repo_dir}/**/{pattern}", recursive=True)
        print(f"Found {len(files)} files matching '{pattern}'")

        for file in files:
            try:
                if file.endswith('.csv'):
                    df = pd.read_csv(file, encoding='utf-8')
                elif file.endswith('.tsv'):
                    df = pd.read_csv(file, sep='\t', encoding='utf-8')
                elif file.endswith('.txt'):
                    # Read as single column
                    with open(file, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    df = pd.DataFrame({'text': lines})
                else:
                    continue

                df['source_file'] = file
                df['source_url'] = source_url
                all_data.append(df)
                print(f"  ✅ Loaded {len(df):,} rows from {Path(file).name}")

            except Exception as e:
                print(f"  ⚠️  Skipped {Path(file).name}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined['collection_date'] = datetime.now().strftime('%Y-%m-%d')
        combined.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n✅ Saved combined data: {output_file}")
        print(f"   Total rows: {len(combined):,}")
        return True
    else:
        print(f"❌ No data extracted")
        return False


def main():
    print("\n" + "="*70)
    print("DOWNLOADING ALL KIKUYU LANGUAGE DATA SOURCES")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # ========================================================================
    # 1. CGIAR Kikuyu-English Translation (Hugging Face)
    # ========================================================================
    results['cgiar'] = download_huggingface_dataset(
        dataset_name='CGIAR/KikuyuEnglish_translation',
        output_file='data/raw/cgiar_kikuyu_english.csv',
        source_url='https://huggingface.co/datasets/CGIAR/KikuyuEnglish_translation'
    )

    # ========================================================================
    # 2. DigiGreen Kikuyu-English (Alternative mirror)
    # ========================================================================
    results['digigreen'] = download_huggingface_dataset(
        dataset_name='DigiGreen/KikuyuEnglish_translation',
        output_file='data/raw/digigreen_kikuyu_english.csv',
        source_url='https://huggingface.co/datasets/DigiGreen/KikuyuEnglish_translation'
    )

    # ========================================================================
    # 3. Kikuyu-Kiswahili Translation Repository
    # ========================================================================
    repo_url = 'https://github.com/starnleymbote/Kikuyu_Kiswahili-translation.git'
    repo_dir = 'data/external/kikuyu_kiswahili_translation'

    if clone_github_repo(repo_url, repo_dir):
        results['kikuyu_kiswahili'] = extract_from_repo(
            repo_dir=repo_dir,
            patterns=['*.csv', '*.tsv', '*.txt'],
            output_file='data/raw/kikuyu_kiswahili_data.csv',
            source_url='https://github.com/starnleymbote/Kikuyu_Kiswahili-translation'
        )
    else:
        results['kikuyu_kiswahili'] = False

    # ========================================================================
    # 4. African NLP Datasets Repository
    # ========================================================================
    repo_url = 'https://github.com/Andrews2017/africanlp-public-datasets.git'
    repo_dir = 'data/external/africanlp_datasets'

    if clone_github_repo(repo_url, repo_dir):
        results['africanlp'] = extract_from_repo(
            repo_dir=repo_dir,
            patterns=['*kikuyu*.csv', '*gikuyu*.csv', '*swahili*.csv'],
            output_file='data/raw/africanlp_data.csv',
            source_url='https://github.com/Andrews2017/africanlp-public-datasets'
        )
    else:
        results['africanlp'] = False

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)

    for source, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {source:<25} {status}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # List downloaded files
    print("="*70)
    print("DOWNLOADED FILES")
    print("="*70)

    import glob
    raw_files = glob.glob('data/raw/*.csv')

    if raw_files:
        for file in sorted(raw_files):
            size = Path(file).stat().st_size / 1024  # KB
            print(f"  {Path(file).name:<40} {size:>10,.1f} KB")
    else:
        print("  No files downloaded")

    print()

    # ========================================================================
    # NEXT STEPS
    # ========================================================================
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Review downloaded datasets in data/raw/")
    print("2. Filter for occupation terms and gender context")
    print("3. Convert to AI BRIDGE 24-field schema")
    print("4. Merge with existing Gold tier dataset")
    print("5. Run annotation workflow")
    print()
    print("Commands:")
    print("  ls -lh data/raw/")
    print("  python3 scripts/data_collection/process_new_sources.py")
    print()


if __name__ == "__main__":
    main()
