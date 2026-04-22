#!/usr/bin/env python3
"""
Merge Bible Verses into Kikuyu v5 Dataset with Full AI BRIDGE Schema

This script converts extracted Bible verses to full 27-field AI BRIDGE format
and merges them with the existing Kikuyu v5 dataset, updating source percentages.

Usage:
    python3 scripts/data_collection/merge_bible_to_v5.py \\
        --bible data/raw/kikuyu_bible_extracted.csv \\
        --existing eval/ground_truth_ki_v5.csv \\
        --output eval/ground_truth_ki_v6.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

def convert_bible_verse_to_v5_schema(verse: dict, sample_id: str) -> dict:
    """
    Convert Bible verse to Kikuyu v5 27-field schema.

    Bible verses are marked as requiring manual annotation for bias fields.
    """
    return {
        # Core identification (fields 1-3)
        'sample_id': sample_id,
        'text': verse['text'],
        'language': 'ki',  # Kikuyu

        # Bias detection (fields 4-6) - requires manual annotation
        'has_bias': 'NEEDS_ANNOTATION',  # yes/no - Manual review needed
        'bias_category': 'NEEDS_ANNOTATION',  # occupation/pronoun/etc
        'expected_correction': 'NEEDS_ANNOTATION',  # Neutral alternative

        # Annotation metadata (fields 7-11)
        'annotator_id': 'PENDING',  # Awaiting human annotation
        'annotation_date': '',  # Will be filled during annotation
        'annotation_confidence': '0.0',  # Not yet annotated
        'annotation_time_seconds': '',  # Will be tracked during annotation
        'annotation_method': 'manual_pending',  # Awaiting manual annotation

        # Multi-annotator fields (fields 12-15)
        'annotator_2_label': '',  # For second annotator
        'annotator_3_label': '',  # For third annotator
        'consensus_method': '',  # Will be set if multi-annotated
        'inter_annotator_kappa': '',  # Cohen's Kappa if multi-annotated

        # Demographics and context (fields 16-17)
        'demographic_group': verse.get('has_gender_context', 'no') == 'yes' and 'gender_marked' or 'neutral',
        'domain': 'religion',  # All Bible verses

        # Linguistic metadata (field 18)
        'regional_variant': 'central_kenya',  # Standard Kikuyu

        # Bias characteristics (fields 19-21)
        'severity': 'NEEDS_ANNOTATION',  # low/medium/high
        'explicitness': 'NEEDS_ANNOTATION',  # explicit/implicit/unmarked
        'bias_source': 'occupation_gender',  # occupation terms + potential gender bias

        # Validation (field 22)
        'validation_status': 'pending',  # Awaiting annotation

        # Notes and source metadata (fields 23-27)
        'notes': f"Bible verse: {verse['book']} {verse['chapter']}:{verse['verse']}. "
                 f"Occupation terms: {verse.get('occupation_terms', 'N/A')}. "
                 f"Gender context: {verse.get('has_gender_context', 'no')}. "
                 f"Source: Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013) | "
                 f"Collected: {verse.get('collection_date', '2026-02-05')} | "
                 f"License: {verse.get('license', 'CC BY-SA 4.0')}",
        'data_source': 'bible',
        'source_url': verse.get('source_url', 'https://eBible.org/Scriptures/kik_readaloud.zip'),
        'source_ref': f"{verse.get('verse_id', 'UNKNOWN')}",
        'collection_date': verse.get('collection_date', '2026-02-05'),
    }


def merge_datasets(bible_csv: Path, existing_csv: Path, output_csv: Path, max_bible_samples: int = None):
    """Merge Bible verses with existing dataset."""

    print(f"Reading existing dataset: {existing_csv}")
    existing_samples = []
    with open(existing_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_samples = list(reader)

    print(f"  Existing samples: {len(existing_samples)}")

    # Read Bible verses
    print(f"\nReading Bible verses: {bible_csv}")
    bible_verses = []
    with open(bible_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        bible_verses = list(reader)

    print(f"  Bible verses available: {len(bible_verses)}")

    # Filter to high-quality samples (with gender context preferred)
    high_priority = [v for v in bible_verses if v.get('has_gender_context') == 'yes']
    medium_priority = [v for v in bible_verses if v.get('has_gender_context') == 'no']

    print(f"  High priority (with gender context): {len(high_priority)}")
    print(f"  Medium priority (occupation only): {len(medium_priority)}")

    # Select samples to add
    if max_bible_samples:
        # Take all high priority, then fill with medium priority
        selected = high_priority[:max_bible_samples]
        if len(selected) < max_bible_samples:
            remaining = max_bible_samples - len(selected)
            selected.extend(medium_priority[:remaining])
    else:
        selected = bible_verses  # Add all

    print(f"\nSelected {len(selected)} Bible verses to add")

    # Get next sample ID
    existing_ids = [int(s['sample_id'].split('_')[1]) for s in existing_samples if s['sample_id'].startswith('ki_')]
    next_id = max(existing_ids) + 1 if existing_ids else 1

    # Convert Bible verses to v5 schema format
    print("\nConverting Bible verses to v5 schema format...")
    new_samples = []
    for i, verse in enumerate(selected):
        sample_id = f"ki_{next_id + i:05d}"
        v5_sample = convert_bible_verse_to_v5_schema(verse, sample_id)
        new_samples.append(v5_sample)

    # Combine datasets
    all_samples = existing_samples + new_samples
    print(f"\nTotal samples after merge: {len(all_samples)}")

    # Calculate source percentages
    source_counts = Counter(s['data_source'] for s in all_samples)
    print(f"\nSource distribution:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(all_samples)) * 100
        print(f"  {source:20} {count:5} ({pct:5.1f}%)")

    # Write merged dataset
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_samples)

    print(f"\n✅ Merged dataset written to: {output_csv}")
    print(f"   File size: {output_csv.stat().st_size / 1024 / 1024:.2f} MB")

    # Print summary statistics
    bible_samples = [s for s in all_samples if s['data_source'] == 'bible']
    print(f"\n📊 Bible Sample Statistics:")
    print(f"   Total Bible samples: {len(bible_samples)}")
    print(f"   Percentage of dataset: {len(bible_samples)/len(all_samples)*100:.1f}%")
    print(f"   Awaiting annotation: {len([s for s in bible_samples if s['has_bias'] == 'NEEDS_ANNOTATION'])}")

    return len(all_samples), source_counts


def main():
    parser = argparse.ArgumentParser(
        description="Merge Bible verses into Kikuyu v5 dataset"
    )
    parser.add_argument(
        "--bible",
        type=Path,
        default=Path("data/raw/kikuyu_bible_extracted.csv"),
        help="Bible verses CSV (default: data/raw/kikuyu_bible_extracted.csv)"
    )
    parser.add_argument(
        "--existing",
        type=Path,
        default=Path("eval/ground_truth_ki_v5.csv"),
        help="Existing dataset (default: eval/ground_truth_ki_v5.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval/ground_truth_ki_v6.csv"),
        help="Output merged dataset (default: eval/ground_truth_ki_v6.csv)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum Bible samples to add (default: all with gender context)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Add all 794 Bible verses (default: only high-priority with gender context)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.bible.exists():
        print(f"❌ ERROR: Bible verses file not found: {args.bible}")
        print(f"\nExtract Bible verses first:")
        print(f"  python3 scripts/data_collection/extract_bible_verses.py")
        return 1

    if not args.existing.exists():
        print(f"❌ ERROR: Existing dataset not found: {args.existing}")
        return 1

    # Determine how many samples to add
    if args.all:
        max_samples = None  # Add all
        print("Mode: Adding ALL Bible verses (794 total)")
    elif args.max_samples:
        max_samples = args.max_samples
        print(f"Mode: Adding up to {max_samples} Bible verses")
    else:
        # Default: Add all high-priority (with gender context)
        max_samples = 307  # Number with gender context
        print(f"Mode: Adding high-priority Bible verses (with gender context)")

    # Merge datasets
    total_samples, source_dist = merge_datasets(
        args.bible,
        args.existing,
        args.output,
        max_samples
    )

    print(f"\n🎯 Dataset v6 Statistics:")
    print(f"   v5 samples: 5,200")
    print(f"   v6 samples: {total_samples} (+{total_samples - 5200})")
    print(f"   Progress to Gold tier (10,000): {total_samples/10000*100:.1f}%")

    print(f"\n📝 Next Steps:")
    print(f"1. Review Bible samples marked NEEDS_ANNOTATION")
    print(f"2. Annotate bias fields using annotation script or manual review")
    print(f"3. Update confidence scores after human validation")
    print(f"4. Calculate Cohen's Kappa for multi-annotator samples")

    return 0


if __name__ == "__main__":
    sys.exit(main())
