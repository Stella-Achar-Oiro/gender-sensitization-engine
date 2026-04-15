#!/usr/bin/env python3
"""
Mine CC100 Swahili corpus for gender bias candidates.

Targets three gap categories identified from live testing:
  1. Capability stereotypes  — wajinga, dhaifu, hana akili, hawezi near gender markers
  2. Leadership exclusion    — hawafai kuongoza/kusimamia/kufanya near gender markers
  3. Appearance derogation   — sura, mwili, uzuri as qualifiers for women

Output: data/collection/cc100_bias_candidates.csv
  Each row: text, matched_term, matched_gender_marker, category

Usage:
  python3 scripts/data_collection/download_cc100_swahili.py
  python3 scripts/data_collection/download_cc100_swahili.py --max-docs 50000
"""

import argparse
import csv
import re
import hashlib
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    raise SystemExit("Install with: pip install datasets")

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **kwargs: x


# ── Target patterns ──────────────────────────────────────────────────────────

GENDER_MARKERS = [
    'wasichana', 'wanawake', 'mwanamke', 'msichana',
    'wanaume', 'wavulana', 'mwanamume', 'mvulana',
    'mama', 'baba', 'dada', 'kaka', 'binti',
]

CAPABILITY_TERMS = [
    'wajinga', 'mjinga', 'dhaifu', 'hana akili', 'hawana akili',
    'hawawezi', 'hawezi', 'wanyonge', 'mnyonge', 'hana uwezo',
    'hawana uwezo', 'hawaezi', 'upole kupita kiasi',
]

LEADERSHIP_TERMS = [
    'hawafai kuongoza', 'hawafai kusimamia', 'hawafai kufanya',
    'hawafai kushiriki', 'hawafai kupiga kura', 'hawastahili kuongoza',
    'hawawezi kuongoza', 'hawawezi kusimamia',
]

APPEARANCE_TERMS = [
    'sura yake ndiyo', 'mwili wake ndiyo', 'uzuri wake ndiyo',
    'anathaminiwa kwa sura', 'anathaminiwa kwa mwili',
    'mwanamke mzuri tu', 'msichana mzuri tu',
]

# Combined: (term, category)
ALL_PATTERNS = (
    [(t, 'capability') for t in CAPABILITY_TERMS] +
    [(t, 'leadership_exclusion') for t in LEADERSHIP_TERMS] +
    [(t, 'appearance_derogation') for t in APPEARANCE_TERMS]
)

WINDOW = 120  # characters around match to check for gender marker


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_sentences(text: str):
    for sent in re.split(r'(?<=[.!?])\s+', text):
        sent = sent.strip()
        if 30 <= len(sent) <= 600:
            yield sent


def has_gender_marker(window: str) -> str | None:
    w = window.lower()
    for m in GENDER_MARKERS:
        if m in w:
            return m
    return None


def mine(texts, max_hits: int = 5000):
    seen = set()
    results = []

    for text in tqdm(texts, desc="Mining CC100"):
        for sent in extract_sentences(text):
            sent_lower = sent.lower()
            for term, category in ALL_PATTERNS:
                idx = sent_lower.find(term)
                if idx == -1:
                    continue
                window = sent_lower[max(0, idx - WINDOW): idx + WINDOW]
                marker = has_gender_marker(window)
                if not marker:
                    continue
                key = hashlib.md5(sent.encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                results.append({
                    'text': sent,
                    'matched_term': term,
                    'matched_gender_marker': marker,
                    'category': category,
                    'has_bias': '',       # to be filled by annotator
                    'expected_correction': '',
                })
                if len(results) >= max_hits:
                    return results
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-docs',  type=int, default=100_000,
                        help='Documents to stream from CC100 (default: 100,000)')
    parser.add_argument('--max-hits',  type=int, default=5_000,
                        help='Max candidate sentences to collect (default: 5,000)')
    parser.add_argument('--output',    type=str,
                        default='data/collection/cc100_bias_candidates.csv')
    args = parser.parse_args()

    print("Loading CC100 Swahili (streaming)...")
    ds = load_dataset('statmt/cc100', lang='sw', split='train', streaming=True)

    texts = []
    for i, row in enumerate(ds):
        if i >= args.max_docs:
            break
        if row.get('text', '').strip():
            texts.append(row['text'])

    print(f"Streamed {len(texts):,} documents. Mining...")
    results = mine(texts, max_hits=args.max_hits)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'text', 'matched_term', 'matched_gender_marker',
            'category', 'has_bias', 'expected_correction'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. {len(results):,} candidates saved to {out}")
    print("Next step: annotate has_bias + expected_correction, then merge into GT.")

    # Summary by category
    from collections import Counter
    cats = Counter(r['category'] for r in results)
    print("\nBreakdown by category:")
    for cat, n in cats.most_common():
        print(f"  {cat:<30} {n:>4}")


if __name__ == '__main__':
    main()
