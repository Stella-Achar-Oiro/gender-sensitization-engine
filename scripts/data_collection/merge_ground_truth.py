#!/usr/bin/env python3
"""
Merge generated test templates with existing ground truth.

This script:
1. Loads existing ground_truth_sw.csv (63 hand-curated samples)
2. Loads generated swahili_test_templates.csv (1,261 systematic templates)
3. Deduplicates based on text
4. Shuffles to avoid bias clustering
5. Saves merged ground truth for evaluation

Target: 1,200+ samples for AI BRIDGE Bronze tier compliance.
"""

import argparse
import csv
import random
from pathlib import Path
from typing import List, Dict, Set


def load_csv(file_path: str) -> List[Dict]:
    """Load CSV file into list of dicts"""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def deduplicate(samples: List[Dict]) -> List[Dict]:
    """Remove duplicate texts, keeping first occurrence"""
    seen_texts: Set[str] = set()
    unique = []

    for sample in samples:
        text = sample['text'].strip().lower()
        if text not in seen_texts:
            seen_texts.add(text)
            unique.append(sample)

    return unique


def merge_ground_truth(existing_path: str, templates_path: str, output_path: str, shuffle: bool = True):
    """Merge existing ground truth with generated templates"""
    print("=" * 70)
    print("🔗 MERGING GROUND TRUTH DATA")
    print("=" * 70)

    # Load existing ground truth
    print(f"\n📂 Loading existing ground truth: {existing_path}")
    existing = load_csv(existing_path)
    print(f"  Loaded: {len(existing)} samples")

    # Load generated templates
    print(f"\n📂 Loading generated templates: {templates_path}")
    templates = load_csv(templates_path)
    print(f"  Loaded: {len(templates)} samples")

    # Combine
    combined = existing + templates
    print(f"\n📊 Combined: {len(combined)} total samples")

    # Deduplicate
    unique = deduplicate(combined)
    duplicates_removed = len(combined) - len(unique)
    print(f"  Removed {duplicates_removed} duplicates")
    print(f"  Unique samples: {len(unique)}")

    # Shuffle to avoid clustering (optional)
    if shuffle:
        random.seed(42)  # Reproducible shuffle
        random.shuffle(unique)
        print(f"  ✓ Shuffled samples (seed=42)")

    # Count categories
    bias_counts = {}
    for sample in unique:
        category = sample.get('bias_category', 'none')
        bias_counts[category] = bias_counts.get(category, 0) + 1

    print(f"\n📈 Category distribution:")
    for category, count in sorted(bias_counts.items(), key=lambda x: -x[1]):
        percentage = (count / len(unique)) * 100
        print(f"  {category:20s}: {count:4d} ({percentage:5.1f}%)")

    # Calculate bias ratio
    biased_count = sum(1 for s in unique if s.get('has_bias') == 'true')
    neutral_count = len(unique) - biased_count
    print(f"\n⚖️  Bias ratio:")
    print(f"  Biased:  {biased_count:4d} ({(biased_count/len(unique))*100:5.1f}%)")
    print(f"  Neutral: {neutral_count:4d} ({(neutral_count/len(unique))*100:5.1f}%)")

    # Save merged ground truth
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'has_bias', 'bias_category', 'expected_correction']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n💾 Merged ground truth saved to: {output_file}")

    # Check AI BRIDGE compliance
    print(f"\n" + "=" * 70)
    print("🏆 AI BRIDGE BRONZE TIER COMPLIANCE CHECK")
    print("=" * 70)

    bronze_target = 1200
    if len(unique) >= bronze_target:
        print(f"✅ PASSES Bronze tier: {len(unique)} ≥ {bronze_target} samples")
    else:
        deficit = bronze_target - len(unique)
        print(f"⚠️  NEEDS {deficit} more samples for Bronze tier ({len(unique)}/{bronze_target})")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Merge ground truth with generated test templates"
    )
    parser.add_argument(
        '--existing',
        type=str,
        default='eval/ground_truth_sw.csv',
        help="Path to existing ground truth CSV"
    )
    parser.add_argument(
        '--templates',
        type=str,
        default='data/analysis/swahili_test_templates.csv',
        help="Path to generated templates CSV"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='eval/ground_truth_sw.csv',
        help="Output path for merged ground truth"
    )
    parser.add_argument(
        '--no-shuffle',
        action='store_true',
        help="Don't shuffle samples (keep original order)"
    )

    args = parser.parse_args()

    merge_ground_truth(
        args.existing,
        args.templates,
        args.output,
        shuffle=not args.no_shuffle
    )

    print("\n✅ Merge complete!")
    print("\nNext steps:")
    print("1. Run evaluation: make eval")
    print("2. Verify F1 score maintains 1.000 (Gold tier)")
    print("3. Check for any false positives or negatives")


if __name__ == "__main__":
    main()
