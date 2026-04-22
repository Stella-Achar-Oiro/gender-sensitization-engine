#!/usr/bin/env python3
"""
Smart sampling of collected data for human annotation.

This script:
1. Loads collected sentences from news/Wikipedia
2. Filters for quality (length, clarity, occupation diversity)
3. Samples stratified by occupation term (balanced coverage)
4. Outputs annotation-ready CSV with AI BRIDGE schema
"""

import argparse
import csv
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set


class AnnotationSampler:
    """Smart sampling for human annotation"""

    # Core occupation terms from lexicon
    OCCUPATION_TERMS = [
        'mbunge', 'waziri', 'spika', 'mwanasiasa', 'katibu', 'meya',
        'mfanyabiashara', 'wakili', 'jaji', 'daktari', 'mwalimu',
        'mgombea', 'msemaji', 'mwakilishi', 'mhudumu', 'mfalme',
        'mjumbe', 'mstaafu', 'mtendaji', 'mpinzani', 'wafanyabiashara',
        'majaji', 'mawakili', 'askari', 'mhandisi', 'mhasibu',
        'mwuguzi', 'mkulima', 'dereva', 'mwandishi', 'mwimbaji'
    ]

    def __init__(self, min_length: int = 50, max_length: int = 400):
        self.min_length = min_length
        self.max_length = max_length
        self.occupation_buckets: Dict[str, List[Dict]] = defaultdict(list)

    def is_high_quality(self, text: str) -> bool:
        """Quality filters for annotation candidates"""
        # Remove leading/trailing whitespace and quotes
        text = text.strip().strip('"').strip("'").strip()

        # Length check
        if len(text) < self.min_length or len(text) > self.max_length:
            return False

        # Should not be mostly punctuation/numbers
        if len(text) > 0:
            alpha_chars = sum(c.isalpha() for c in text)
            if alpha_chars / len(text) < 0.6:  # Relaxed from 0.7
                return False

        # Avoid metadata/URLs
        if 'http' in text.lower() or '@' in text or '#' in text:
            return False

        return True

    def extract_occupation_terms(self, text: str) -> Set[str]:
        """Extract all occupation terms from text"""
        text_lower = text.lower()
        found_terms = set()

        for term in self.OCCUPATION_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                found_terms.add(term)

        return found_terms

    def load_sentences(self, file_paths: List[Path]) -> List[Dict]:
        """Load sentences from multiple files"""
        all_sentences = []

        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    text = row.get('text', '').strip()

                    # Quality filter
                    if not self.is_high_quality(text):
                        continue

                    # Extract occupation terms
                    terms = self.extract_occupation_terms(text)
                    if not terms:
                        continue

                    # Store with metadata
                    all_sentences.append({
                        'text': text,
                        'source': row.get('source', 'unknown'),
                        'file': row.get('file', ''),
                        'occupation_terms': list(terms)
                    })

        return all_sentences

    def stratified_sample(
        self,
        sentences: List[Dict],
        target_size: int = 1500,
        max_per_term: int = 200
    ) -> List[Dict]:
        """Stratified sampling by occupation term"""

        # Bucket sentences by occupation term
        for sentence in sentences:
            for term in sentence['occupation_terms']:
                self.occupation_buckets[term].append(sentence)

        print(f"\n📊 Occupation term distribution:")
        for term in sorted(self.occupation_buckets.keys(),
                          key=lambda t: len(self.occupation_buckets[t]),
                          reverse=True):
            count = len(self.occupation_buckets[term])
            print(f"  {term}: {count:,} sentences")

        # Sample from each bucket
        sampled = []
        seen_texts = set()

        # Calculate samples per term
        num_terms = len(self.occupation_buckets)
        samples_per_term = min(max_per_term, target_size // num_terms)

        print(f"\n🎯 Target: {target_size} samples, ~{samples_per_term} per term")

        for term, bucket in self.occupation_buckets.items():
            # Sample from this bucket
            sample_size = min(samples_per_term, len(bucket))
            term_sample = random.sample(bucket, sample_size)

            # Deduplicate
            for sentence in term_sample:
                text = sentence['text']
                if text not in seen_texts:
                    sampled.append(sentence)
                    seen_texts.add(text)

        # Fill remaining quota with random samples
        if len(sampled) < target_size:
            remaining = target_size - len(sampled)
            candidates = [s for s in sentences if s['text'] not in seen_texts]
            if candidates:
                additional = random.sample(
                    candidates,
                    min(remaining, len(candidates))
                )
                sampled.extend(additional)

        # Shuffle final sample
        random.shuffle(sampled)

        return sampled[:target_size]

    def to_annotation_format(self, samples: List[Dict]) -> List[Dict]:
        """Convert to AI BRIDGE annotation schema"""
        annotation_ready = []

        for i, sample in enumerate(samples, 1):
            annotation_ready.append({
                'id': f'SW-NEWS-{i:05d}',
                'language': 'sw',
                'script': 'latin',
                'country': 'Kenya',
                'region_dialect': '',
                'source_type': 'web_public',
                'source_ref': sample['source'],
                'collection_date': '2025-12-03',
                'text': sample['text'],
                'translation': '',
                'domain': 'news',
                'topic': ','.join(sample['occupation_terms']),
                'theme': 'occupations',
                'sensitive_characteristic': 'gender',
                'target_gender': 'NEEDS_ANNOTATION',
                'bias_label': 'NEEDS_ANNOTATION',
                'stereotype_category': 'NEEDS_ANNOTATION',
                'explicitness': 'NEEDS_ANNOTATION',
                'bias_severity': '',
                'sentiment_toward_referent': '',
                'device': '',
                'safety_flag': 'safe',
                'pii_removed': 'false',
                'annotator_id': '',
                'qa_status': 'needs_review',
                'approver_id': '',
                'cohen_kappa': '',
                'notes': f'Occupation terms: {", ".join(sample["occupation_terms"])}',
                'eval_split': 'train'
            })

        return annotation_ready


def main():
    parser = argparse.ArgumentParser(
        description="Sample collected data for human annotation"
    )
    parser.add_argument(
        '--news-file',
        type=str,
        default='data/analysis/swahili_news_occupations.csv',
        help="News dataset CSV"
    )
    parser.add_argument(
        '--wiki-file',
        type=str,
        default='data/raw/wikipedia_sw_raw.csv',
        help="Wikipedia dataset CSV"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/annotation_sample.csv',
        help="Output annotation CSV"
    )
    parser.add_argument(
        '--target-size',
        type=int,
        default=1500,
        help="Target number of samples (default: 1500)"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    print("=" * 70)
    print("📝 ANNOTATION SAMPLER")
    print("=" * 70)

    # Initialize sampler
    sampler = AnnotationSampler()

    # Load sentences
    print("\n📥 Loading collected data...")
    file_paths = [Path(args.news_file)]
    if Path(args.wiki_file).exists():
        file_paths.append(Path(args.wiki_file))

    sentences = sampler.load_sentences(file_paths)
    print(f"✅ Loaded {len(sentences):,} high-quality sentences")

    # Stratified sampling
    print(f"\n🎲 Sampling {args.target_size} sentences...")
    samples = sampler.stratified_sample(sentences, args.target_size)
    print(f"✅ Sampled {len(samples):,} sentences")

    # Convert to annotation format
    print("\n📋 Converting to AI BRIDGE annotation schema...")
    annotation_data = sampler.to_annotation_format(samples)

    # Save to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = annotation_data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotation_data)

    print(f"💾 Saved to: {output_path}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 SAMPLING SUMMARY")
    print("=" * 70)
    print(f"  Total sentences sampled: {len(samples):,}")
    print(f"  Average length: {sum(len(s['text']) for s in samples) // len(samples)} chars")
    print(f"  Unique occupation terms: {len(sampler.occupation_buckets)}")
    print(f"  Output file: {output_path}")
    print("\n✅ Ready for human annotation!")
    print("\nNext steps:")
    print("1. Review sample quality: head -20 data/analysis/annotation_sample.csv")
    print("2. Recruit 3+ Swahili annotators (Upwork/Masakhane)")
    print("3. Double-annotate 30% for Cohen's Kappa ≥0.70")
    print("4. Build ground truth from annotated samples")
    print("=" * 70)


if __name__ == "__main__":
    main()
