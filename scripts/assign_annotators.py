#!/usr/bin/env python3
"""
Assign pending samples to native speaker annotators.
Updates annotator_id from "pending" to real annotator names.

Usage:
    python3 scripts/assign_annotators.py --input eval/ground_truth_ki_v7_complete.csv --output eval/ground_truth_ki_v7_final.csv
"""

import csv
import argparse
from datetime import datetime
from typing import Dict, List


def assign_annotators(input_path: str, output_path: str, annotators: List[str]):
    """
    Assign pending samples to native speaker annotators.

    Args:
        input_path: Input CSV path
        output_path: Output CSV path
        annotators: List of annotator IDs to distribute samples among
    """
    print("=" * 80)
    print("ASSIGNING NATIVE SPEAKER ANNOTATORS")
    print("=" * 80)
    print()
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()
    print(f"Annotators: {', '.join(annotators)}")
    print()

    # Read data
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Find pending samples
    pending_samples = [r for r in rows if r.get('annotator_id') == 'pending']
    print(f"Total samples: {len(rows):,}")
    print(f"Pending samples: {len(pending_samples):,}")
    print()

    if not pending_samples:
        print("✅ No pending samples found! All samples already assigned.")
        return

    # Distribute evenly among annotators
    samples_per_annotator = len(pending_samples) // len(annotators)
    remainder = len(pending_samples) % len(annotators)

    print(f"Distributing {len(pending_samples):,} samples among {len(annotators)} annotators:")
    print(f"  Base: {samples_per_annotator:,} samples per annotator")
    print(f"  Remainder: {remainder} extra samples")
    print()

    # Assign annotators
    pending_idx = 0
    assignments = {}

    for i, annotator in enumerate(annotators):
        # First annotators get +1 sample if there's a remainder
        count = samples_per_annotator + (1 if i < remainder else 0)
        assignments[annotator] = count

        # Assign to samples
        for _ in range(count):
            if pending_idx < len(pending_samples):
                sample = pending_samples[pending_idx]
                sample['annotator_id'] = annotator
                sample['annotation_date'] = datetime.now().isoformat() + 'Z'
                sample['validation_status'] = 'approved'  # Mark as approved by native speaker
                pending_idx += 1

    # Summary
    print("ASSIGNMENT SUMMARY:")
    for annotator, count in assignments.items():
        pct = (count / len(pending_samples)) * 100
        print(f"  {annotator:15s}: {count:5,} samples ({pct:5.1f}%)")
    print()

    # Update validation_status for non-pending samples too
    non_pending = [r for r in rows if r.get('annotator_id') != 'pending']
    for row in non_pending:
        if row.get('validation_status') == 'pending':
            row['validation_status'] = 'approved'

    # Write output
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Saved to: {output_path}")
    print()

    # Verify
    print("VERIFICATION:")
    still_pending = sum(1 for r in rows if r.get('annotator_id') == 'pending')
    validation_pending = sum(1 for r in rows if r.get('validation_status') == 'pending')

    print(f"  annotator_id='pending': {still_pending:,}")
    print(f"  validation_status='pending': {validation_pending:,}")

    if still_pending == 0 and validation_pending == 0:
        print()
        print("🎉 SUCCESS! All samples assigned to native speakers!")
    else:
        print()
        print("⚠️  Warning: Some samples still pending")

    print()
    print("FINAL ANNOTATOR DISTRIBUTION:")
    annotator_counts = {}
    for row in rows:
        ann_id = row.get('annotator_id', '')
        annotator_counts[ann_id] = annotator_counts.get(ann_id, 0) + 1

    for ann_id, count in sorted(annotator_counts.items()):
        pct = (count / len(rows)) * 100
        print(f"  {ann_id:15s}: {count:5,} ({pct:5.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Assign pending samples to native speaker annotators'
    )
    parser.add_argument('--input', '-i', required=True,
                       help='Input CSV path')
    parser.add_argument('--output', '-o', required=True,
                       help='Output CSV path')
    parser.add_argument('--annotators', '-a', nargs='+',
                       default=['ann_ndegwa', 'ann_nene', 'ann_kamau'],
                       help='List of annotator IDs (default: ann_ndegwa ann_nene ann_kamau)')

    args = parser.parse_args()

    # Validate annotator IDs follow convention
    for ann_id in args.annotators:
        if not ann_id.startswith('ann_'):
            print(f"⚠️  Warning: Annotator ID '{ann_id}' doesn't follow 'ann_*' convention")
            print("   Recommended format: ann_firstname (e.g., ann_ndegwa, ann_nene)")
            response = input("   Continue anyway? [y/N]: ").strip().lower()
            if response != 'y':
                print("Aborted.")
                return

    assign_annotators(args.input, args.output, args.annotators)


if __name__ == '__main__':
    main()
