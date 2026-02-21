#!/usr/bin/env python3
"""
Download Kikuyu Bible Corpus from BibleNLP/Hugging Face

Downloads verse-aligned Kikuyu Bible text for gender bias detection dataset expansion.

Data Sources:
1. BibleNLP Corpus (Hugging Face): https://huggingface.co/datasets/bible-nlp/biblenlp-corpus
2. Christos-c Bible Corpus (GitHub): https://github.com/christos-c/bible-corpus
3. BibleTTS (Speech + Text): https://www.researchgate.net/publication/361901215_BibleTTS

License: CC-BY-SA (research and commercial friendly)
ISO 693-3 Language Code: kik (Kikuyu)

Usage:
    python3 scripts/data_collection/download_kikuyu_bible.py --output data/raw/kikuyu_bible.csv
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    from datasets import load_dataset
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    print("WARNING: huggingface datasets library not installed.")
    print("Install with: pip install datasets")


def download_from_huggingface(output_path: Path):
    """
    Download Kikuyu Bible from Hugging Face BibleNLP corpus.

    Note: The biblenlp-corpus dataset uses deprecated loading scripts.
    Use manual download or Christos-c corpus instead.
    """
    print("⚠️  BibleNLP corpus on Hugging Face uses deprecated loading scripts")
    print("\nRecommended alternatives:")
    print("\n1. Manual download from Hugging Face:")
    print("   - Visit: https://huggingface.co/datasets/bible-nlp/biblenlp-corpus")
    print("   - Download Parquet files for Kikuyu (kik)")
    print("   - Extract verse text")

    print("\n2. Use Christos-c Bible corpus (recommended):")
    print("   git clone https://github.com/christos-c/bible-corpus.git")
    print("   # Find Kikuyu files in bibles/ directory")

    print("\n3. Use eBible.org directly (RECOMMENDED - easiest):")
    print("   Translation: Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013)")
    print("   License: CC BY-SA 4.0")
    print("\n   Direct download links:")
    print("   - Plain Text: https://eBible.org/Scriptures/kik_readaloud.zip")
    print("   - USFM: https://eBible.org/Scriptures/kik_usfm.zip")
    print("   - HTML: https://eBible.org/Scriptures/kik_html.zip")
    print("\n   Quick download:")
    print("   curl -O https://eBible.org/Scriptures/kik_readaloud.zip")
    print("   unzip kik_readaloud.zip -d data/raw/kikuyu_bible/")

    return False


def download_from_christos_corpus(output_path: Path):
    """
    Download Kikuyu Bible from Christos-c corpus (GitHub).

    This requires manual download or git clone.
    Repository: https://github.com/christos-c/bible-corpus
    """
    print("=" * 60)
    print("Christos-c Bible Corpus - Manual Download")
    print("=" * 60)
    print("\nRepository: https://github.com/christos-c/bible-corpus")
    print("Website: https://christos-c.com/bible/")

    print("\n📋 Manual Download Steps:")
    print("\n1. Clone repository:")
    print("   git clone https://github.com/christos-c/bible-corpus.git")
    print("   cd bible-corpus")

    print("\n2. Find Kikuyu Bible files:")
    print("   # Look for files with Kikuyu/Gikuyu/kik language code")
    print("   find bibles/ -name '*kik*' -o -name '*gikuyu*'")

    print("\n3. Extract verse text:")
    print("   # Bible files are typically in XML or plain text format")
    print("   # Parse and extract verse content")

    print("\n4. Convert to CSV:")
    print("   # Create CSV with columns: verse_id, book, chapter, verse, text")

    print("\n📌 RECOMMENDED - Direct eBible.org Download:")
    print("\nTranslation: Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013)")
    print("License: Creative Commons Attribution-ShareAlike 4.0")
    print("\nDirect download links:")
    print("  • Plain Text (easiest): https://eBible.org/Scriptures/kik_readaloud.zip")
    print("  • USFM (structured): https://eBible.org/Scriptures/kik_usfm.zip")
    print("  • HTML (web format): https://eBible.org/Scriptures/kik_html.zip")
    print("\nQuick download command:")
    print("  curl -O https://eBible.org/Scriptures/kik_readaloud.zip")
    print("  unzip kik_readaloud.zip -d data/raw/kikuyu_bible/")
    print("\n💡 Plain text format is easiest to parse for gender bias detection")

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Kikuyu Bible corpus for bias detection"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/kikuyu_bible.csv"),
        help="Output CSV file path (default: data/raw/kikuyu_bible.csv)"
    )
    parser.add_argument(
        "--source",
        choices=["huggingface", "christos"],
        default="huggingface",
        help="Download source (default: huggingface)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Kikuyu Bible Corpus Download")
    print("=" * 60)

    if args.source == "huggingface":
        success = download_from_huggingface(args.output)
    else:
        success = download_from_christos_corpus(args.output)

    if success:
        print("\n✅ Download completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Review downloaded data: {args.output}")
        print(f"2. Extract samples with occupation/gender contexts")
        print(f"3. Annotate for bias detection using scripts/data_collection/annotate_samples.py")
    else:
        print("\n❌ Download failed. See error messages above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
