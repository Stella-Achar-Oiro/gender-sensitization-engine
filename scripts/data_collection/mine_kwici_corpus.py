#!/usr/bin/env python3
"""
Mine Kwici Wikipedia Swahili Corpus for occupation sentences.

Corpus: Kwici Wiki-Corpus-Swahili
Source: https://github.com/Kwici/Wiki-Corpus-Swahili
Size: 151,000 sentences, 2.8M words
Quality: Clean Wikipedia extractions

This script:
1. Downloads Kwici corpus from GitHub
2. Extracts sentences containing occupation terms
3. Outputs real-world Swahili text from Wikipedia
"""

import argparse
import csv
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = lambda x, **kwargs: x  # Fallback: no progress bar


class KwiciCorpusMiner:
    """Mines Kwici Wikipedia Corpus for occupation sentences"""

    GITHUB_REPO = "https://github.com/Kwici/Wiki-Corpus-Swahili.git"

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repo_dir = self.output_dir / "kwici-corpus"
        self.occupation_terms: Set[str] = set()

    def clone_repo(self, force: bool = False):
        """Clone Kwici corpus repository"""
        if self.repo_dir.exists() and not force:
            print(f"✓ Repository already cloned: {self.repo_dir}")
            return

        print(f"📥 Cloning Kwici Wikipedia Corpus from GitHub...")
        print(f"   URL: {self.GITHUB_REPO}")

        try:
            subprocess.run(
                ['git', 'clone', self.GITHUB_REPO, str(self.repo_dir)],
                check=True,
                capture_output=True
            )
            print(f"✅ Cloned to: {self.repo_dir}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Clone failed: {e}")
            print("\nAlternative: Clone manually:")
            print(f"git clone {self.GITHUB_REPO} {self.repo_dir}")
            raise

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

    def get_corpus_files(self) -> List[Path]:
        """Find all corpus files"""
        # Look for text files in corpus directory
        txt_files = list(self.repo_dir.rglob("*.txt"))
        corpus_files = list(self.repo_dir.rglob("corpus*.txt"))
        sw_files = list(self.repo_dir.rglob("sw*.txt"))

        all_files = list(set(txt_files + corpus_files + sw_files))
        print(f"📄 Found {len(all_files)} corpus files")
        return all_files

    def contains_occupation(self, sentence: str) -> bool:
        """Check if sentence contains occupation term"""
        sentence_lower = sentence.lower()
        for term in self.occupation_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', sentence_lower):
                return True
        return False

    def mine_file(self, file_path: Path) -> List[Dict]:
        """Mine occupation sentences from a corpus file"""
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Quality filters
                    if len(line) < 20 or len(line) > 500:
                        continue
                    if not re.search(r'\w', line):
                        continue

                    # Check for occupation
                    if self.contains_occupation(line):
                        results.append({
                            'text': line,
                            'source': 'kwici_wikipedia',
                            'file': str(file_path.name),
                            'line': line_num
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
        description="Mine Kwici Wikipedia Corpus"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help="Directory to clone corpus"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/analysis/kwici_occupations.csv',
        help="Output file for mined sentences"
    )
    parser.add_argument(
        '--force-clone',
        action='store_true',
        help="Force re-clone even if directory exists"
    )
    parser.add_argument(
        '--skip-clone',
        action='store_true',
        help="Skip cloning, use existing files"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📖 KWICI WIKIPEDIA CORPUS MINER")
    print("=" * 70)

    miner = KwiciCorpusMiner(args.output_dir)

    # Clone repository
    if not args.skip_clone:
        miner.clone_repo(force=args.force_clone)

    # Load occupations
    miner.load_occupations()

    # Find corpus files
    files = miner.get_corpus_files()

    if not files:
        print("❌ No corpus files found. Check repository.")
        return

    # Mine sentences
    results = miner.mine_all(files)

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['text', 'source', 'file', 'line']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Saved to: {output_path}")
    print("\n" + "=" * 70)
    print("✅ Mining complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
