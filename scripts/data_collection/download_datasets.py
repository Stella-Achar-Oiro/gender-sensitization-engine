#!/usr/bin/env python3
"""
Download free open-source bias detection datasets

This script downloads publicly licensed bias datasets and converts them
to our standard format for annotation.

Usage:
    python scripts/data_collection/download_datasets.py --datasets winobias winogender --output data/raw/
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import csv
from datetime import datetime
import urllib.request
import zipfile
import tarfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DatasetDownloader:
    """Downloads and converts open-source bias datasets"""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {}

    def download_winobias(self):
        """
        Download WinoBias dataset
        License: MIT
        Source: https://github.com/uclanlp/corefBias
        """
        print("\n📥 Downloading WinoBias...")

        # WinoBias URLs - 4 files (pro/anti stereotyped, type1/type2)
        urls = [
            ("https://raw.githubusercontent.com/uclanlp/corefBias/master/WinoBias/wino/data/pro_stereotyped_type1.txt.test", "pro_stereotyped_type1"),
            ("https://raw.githubusercontent.com/uclanlp/corefBias/master/WinoBias/wino/data/anti_stereotyped_type1.txt.test", "anti_stereotyped_type1"),
            ("https://raw.githubusercontent.com/uclanlp/corefBias/master/WinoBias/wino/data/pro_stereotyped_type2.txt.test", "pro_stereotyped_type2"),
            ("https://raw.githubusercontent.com/uclanlp/corefBias/master/WinoBias/wino/data/anti_stereotyped_type2.txt.test", "anti_stereotyped_type2"),
        ]

        samples = []
        sample_id = 1

        for url, file_type in urls:
            try:
                print(f"  Fetching {file_type}...")
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode('utf-8')

                # Parse WinoBias format: "1 The janitor reprimanded [the accountant] because [she] made a mistake..."
                for line in content.strip().split('\n'):
                    if not line.strip():
                        continue

                    # Remove line number prefix (e.g., "1 ")
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        text = parts[1].strip()

                        # Remove annotation brackets for cleaner text
                        text_clean = text.replace('[', '').replace(']', '')

                        # Basic gender detection (simple heuristic)
                        text_lower = text_clean.lower()
                        has_female = any(term in text_lower for term in ['she', 'her', 'woman', 'female', 'actress', 'waitress', 'nurse'])
                        has_male = any(term in text_lower for term in ['he', 'him', 'man', 'male', 'actor', 'waiter', 'doctor'])

                        if has_female and not has_male:
                            target_gender = 'female'
                        elif has_male and not has_female:
                            target_gender = 'male'
                        else:
                            target_gender = 'neutral'

                        # Determine bias label from file type
                        if 'pro_stereotyped' in file_type:
                            bias_label = 'stereotype'
                        elif 'anti_stereotyped' in file_type:
                            bias_label = 'counter-stereotype'
                        else:
                            bias_label = 'NEEDS_ANNOTATION'

                        sample = {
                            'id': f'ENG-WINOBIAS-{sample_id:04d}',
                            'language': 'en',
                            'script': 'latin',
                            'country': 'USA',
                            'region_dialect': '',
                            'source_type': 'web_public',
                            'source_ref': 'https://github.com/uclanlp/corefBias',
                            'collection_date': datetime.now().strftime('%Y-%m-%d'),
                            'text': text_clean,
                            'translation': '',  # Already English
                            'domain': 'livelihoods_and_work',
                            'topic': 'occupations',
                            'theme': 'stereotypes',
                            'sensitive_characteristic': 'gender',
                            'target_gender': target_gender,
                            'bias_label': bias_label,
                            'stereotype_category': 'profession',
                            'explicitness': 'implicit',
                            'bias_severity': '',
                            'sentiment_toward_referent': '',
                            'device': '',
                            'safety_flag': 'safe',
                            'pii_removed': 'true',
                            'annotator_id': '',
                            'qa_status': 'needs_review',
                            'approver_id': '',
                            'cohen_kappa': '',
                            'notes': f'Source: WinoBias {file_type}. Occupation bias dataset.',
                            'eval_split': 'test'
                        }
                        samples.append(sample)
                        sample_id += 1

            except Exception as e:
                print(f"  ⚠️  Error downloading {file_type}: {e}")

        # Save to CSV
        output_file = self.output_dir / "winobias_raw.csv"
        self._save_to_csv(samples, output_file)

        self.stats['winobias'] = len(samples)
        print(f"  ✅ Downloaded {len(samples)} samples from WinoBias")
        return samples

    def download_winogender(self):
        """
        Download WinoGender dataset
        License: CC BY 4.0
        Source: https://github.com/rudinger/winogender-schemas
        """
        print("\n📥 Downloading WinoGender...")

        url = "https://raw.githubusercontent.com/rudinger/winogender-schemas/master/data/all_sentences.tsv"

        samples = []
        sample_id = 1

        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')

            # Parse TSV format
            lines = content.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    sentid = parts[0].strip()  # e.g., technician.customer.1.male.txt
                    sentence = parts[1].strip()  # The actual sentence

                    # Extract occupation from sentid
                    occupation = sentid.split('.')[0] if '.' in sentid else ''

                    # Determine gender from pronouns
                    sentence_lower = sentence.lower()
                    if 'her ' in sentence_lower or 'she ' in sentence_lower:
                        target_gender = 'female'
                    elif 'his ' in sentence_lower or 'he ' in sentence_lower:
                        target_gender = 'male'
                    elif 'their ' in sentence_lower or 'they ' in sentence_lower:
                        target_gender = 'neutral'
                    else:
                        target_gender = 'unknown'

                    sample = {
                        'id': f'ENG-WINOGENDER-{sample_id:04d}',
                        'language': 'en',
                        'script': 'latin',
                        'country': 'USA',
                        'region_dialect': '',
                        'source_type': 'web_public',
                        'source_ref': 'https://github.com/rudinger/winogender-schemas',
                        'collection_date': datetime.now().strftime('%Y-%m-%d'),
                        'text': sentence,
                        'translation': '',
                        'domain': 'livelihoods_and_work',
                        'topic': occupation,
                        'theme': 'stereotypes',
                        'sensitive_characteristic': 'gender',
                        'target_gender': target_gender,
                        'bias_label': 'NEEDS_ANNOTATION',
                        'stereotype_category': 'profession',
                        'explicitness': 'NEEDS_ANNOTATION',
                        'bias_severity': '',
                        'sentiment_toward_referent': '',
                        'device': '',
                        'safety_flag': 'safe',
                        'pii_removed': 'true',
                        'annotator_id': '',
                        'qa_status': 'needs_review',
                        'approver_id': '',
                        'cohen_kappa': '',
                        'notes': f'Source: WinoGender. Pronoun resolution with occupation: {occupation}',
                        'eval_split': 'test'
                    }
                    samples.append(sample)
                    sample_id += 1

        except Exception as e:
            print(f"  ⚠️  Error downloading WinoGender: {e}")

        # Save to CSV
        output_file = self.output_dir / "winogender_raw.csv"
        self._save_to_csv(samples, output_file)

        self.stats['winogender'] = len(samples)
        print(f"  ✅ Downloaded {len(samples)} samples from WinoGender")
        return samples

    def download_crowspairs(self):
        """
        Download CrowS-Pairs dataset
        License: CC BY-SA 4.0
        Source: https://github.com/nyu-mll/crows-pairs
        """
        print("\n📥 Downloading CrowS-Pairs...")

        url = "https://raw.githubusercontent.com/nyu-mll/crows-pairs/master/data/crows_pairs_anonymized.csv"

        samples = []
        sample_id = 1

        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')

            # Parse CSV
            reader = csv.DictReader(content.splitlines())
            for row in reader:
                # CrowS-Pairs has stereotypical and anti-stereotypical sentences
                sent_more = row.get('sent_more', '').strip()
                sent_less = row.get('sent_less', '').strip()
                bias_type = row.get('bias_type', '').strip()
                stereo_antistereo = row.get('stereo_antistereo', '').strip()

                # Filter for gender bias only
                if not sent_more or bias_type != 'gender':
                    continue

                # Process stereotypical sentence
                if sent_more:
                    sample = {
                        'id': f'ENG-CROWSPAIRS-{sample_id:04d}',
                        'language': 'en',
                        'script': 'latin',
                        'country': 'USA',
                        'region_dialect': '',
                        'source_type': 'web_public',
                        'source_ref': 'https://github.com/nyu-mll/crows-pairs',
                        'collection_date': datetime.now().strftime('%Y-%m-%d'),
                        'text': sent_more,
                        'translation': '',
                        'domain': 'mixed',
                        'topic': bias_type,
                        'theme': 'stereotypes',
                        'sensitive_characteristic': 'gender',
                        'target_gender': 'NEEDS_ANNOTATION',
                        'bias_label': 'stereotype' if stereo_antistereo == 'stereo' else 'NEEDS_ANNOTATION',
                        'stereotype_category': 'NEEDS_ANNOTATION',
                        'explicitness': 'NEEDS_ANNOTATION',
                        'bias_severity': '',
                        'sentiment_toward_referent': '',
                        'device': '',
                        'safety_flag': 'safe',
                        'pii_removed': 'true',
                        'annotator_id': '',
                        'qa_status': 'needs_review',
                        'approver_id': '',
                        'cohen_kappa': '',
                        'notes': f'Source: CrowS-Pairs. Minimal pair (stereotypical). Pair: {sample_id}',
                        'eval_split': 'test'
                    }
                    samples.append(sample)
                    sample_id += 1

                # Process anti-stereotypical sentence
                if sent_less:
                    sample = {
                        'id': f'ENG-CROWSPAIRS-{sample_id:04d}',
                        'language': 'en',
                        'script': 'latin',
                        'country': 'USA',
                        'region_dialect': '',
                        'source_type': 'web_public',
                        'source_ref': 'https://github.com/nyu-mll/crows-pairs',
                        'collection_date': datetime.now().strftime('%Y-%m-%d'),
                        'text': sent_less,
                        'translation': '',
                        'domain': 'mixed',
                        'topic': bias_type,
                        'theme': 'stereotypes',
                        'sensitive_characteristic': 'gender',
                        'target_gender': 'NEEDS_ANNOTATION',
                        'bias_label': 'counter-stereotype' if stereo_antistereo == 'antistereo' else 'NEEDS_ANNOTATION',
                        'stereotype_category': 'NEEDS_ANNOTATION',
                        'explicitness': 'NEEDS_ANNOTATION',
                        'bias_severity': '',
                        'sentiment_toward_referent': '',
                        'device': '',
                        'safety_flag': 'safe',
                        'pii_removed': 'true',
                        'annotator_id': '',
                        'qa_status': 'needs_review',
                        'approver_id': '',
                        'cohen_kappa': '',
                        'notes': f'Source: CrowS-Pairs. Minimal pair (counter-stereotypical). Pair: {sample_id-1}',
                        'eval_split': 'test'
                    }
                    samples.append(sample)
                    sample_id += 1

        except Exception as e:
            print(f"  ⚠️  Error downloading CrowS-Pairs: {e}")

        # Save to CSV
        output_file = self.output_dir / "crowspairs_raw.csv"
        self._save_to_csv(samples, output_file)

        self.stats['crowspairs'] = len(samples)
        print(f"  ✅ Downloaded {len(samples)} samples from CrowS-Pairs")
        return samples

    def _save_to_csv(self, samples: List[Dict], output_file: Path):
        """Save samples to CSV with standard schema"""
        if not samples:
            print(f"  ⚠️  No samples to save")
            return

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

    def download_all_english(self):
        """Download all English datasets"""
        print("\n" + "="*60)
        print("📦 DOWNLOADING ENGLISH DATASETS")
        print("="*60)

        self.download_winobias()
        self.download_winogender()
        self.download_crowspairs()

        # Summary
        total = sum(self.stats.values())
        print("\n" + "="*60)
        print("📊 DOWNLOAD SUMMARY")
        print("="*60)
        for dataset, count in self.stats.items():
            print(f"  {dataset}: {count} samples")
        print(f"\n  TOTAL: {total} samples")
        print(f"  Output: {self.output_dir}")
        print("\n✅ All downloads complete!")
        print("\nNext steps:")
        print("1. Review samples in data/raw/")
        print("2. Recruit annotators")
        print("3. Annotate bias_label, target_gender, etc.")
        print("4. Run quality checks (Cohen's Kappa)")


def main():
    parser = argparse.ArgumentParser(
        description="Download free open-source bias detection datasets"
    )
    parser.add_argument(
        '--datasets',
        nargs='+',
        choices=['winobias', 'winogender', 'crowspairs', 'all'],
        default=['all'],
        help="Which datasets to download (default: all)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw',
        help="Output directory (default: data/raw)"
    )

    args = parser.parse_args()

    downloader = DatasetDownloader(output_dir=args.output)

    if 'all' in args.datasets:
        downloader.download_all_english()
    else:
        if 'winobias' in args.datasets:
            downloader.download_winobias()
        if 'winogender' in args.datasets:
            downloader.download_winogender()
        if 'crowspairs' in args.datasets:
            downloader.download_crowspairs()


if __name__ == "__main__":
    main()
