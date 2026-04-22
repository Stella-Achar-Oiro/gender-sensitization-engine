#!/usr/bin/env python3
"""
Extract Relevant Verses from Kikuyu Bible for Gender Bias Detection

Extracts verses containing occupation terms and/or gender contexts from
the downloaded Kikuyu Bible corpus.

Usage:
    python3 scripts/data_collection/extract_bible_verses.py \\
        --input data/raw/kikuyu_bible/ \\
        --output data/raw/kikuyu_bible_extracted.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Kikuyu occupation terms to search for
OCCUPATION_TERMS = [
    # Common occupations
    "mũrutani",       # teacher
    "mũruti",         # teacher (variant)
    "daktari",        # doctor
    "mũrũgamĩrĩri",   # manager/leader
    "mũthaki",        # athlete/runner
    "mũigũ",          # builder/constructor
    "mũrĩmi",         # farmer
    "mũrĩithi",       # shepherd
    "mũcungĩ",        # herder
    "mũthondeki",     # developer/maker
    "mũteti",         # politician
    "mũthuurĩ",       # messenger
    "mũcamanĩri",     # helper/assistant
    "mũtongoria",     # leader
    "mũthĩnjĩri",     # priest/minister
    "mũigĩ",          # worker
    "mũguĩ",          # seller/trader
    "mũgurĩ",         # buyer
    "mũthembi",       # trusted one
    "mũheani",        # giver
]

# Gender-related terms
GENDER_TERMS = [
    "mũrũme",         # man/male
    "mũtumia",        # woman/female
    "mũirĩtu",        # girl
    "kĩhĩĩ",          # boy
    "andũ-a-nja",     # women (plural)
    "arũme",          # men (plural)
    "athuri",         # elders (male)
]

# Pronouns and gender markers
PRONOUN_TERMS = [
    "yeye",           # he/she
    "we",             # you (singular)
    "ũcio",           # that one (male)
    "ĩyo",            # that one (female)
]


def parse_filename(filename: str) -> Tuple[str, str, str]:
    """
    Parse book and chapter from filename.

    Format: kik_002_GEN_01_read.txt -> (Genesis, 1)
    """
    parts = filename.replace('.txt', '').split('_')
    if len(parts) >= 4:
        book_code = parts[2]  # GEN, EXO, etc.
        chapter = parts[3]    # 01, 02, etc.

        # Map common book codes to full names
        book_names = {
            'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus',
            'NUM': 'Numbers', 'DEU': 'Deuteronomy', 'JOS': 'Joshua',
            'JDG': 'Judges', 'RUT': 'Ruth', '1SA': '1 Samuel',
            '2SA': '2 Samuel', '1KI': '1 Kings', '2KI': '2 Kings',
            'PSA': 'Psalms', 'PRO': 'Proverbs', 'JOB': 'Job',
            'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke',
            'JHN': 'John', 'ACT': 'Acts', 'ROM': 'Romans',
            '1CO': '1 Corinthians', '2CO': '2 Corinthians',
        }

        book_name = book_names.get(book_code, book_code)
        return book_name, chapter.lstrip('0'), book_code

    return "Unknown", "0", "UNK"


def contains_terms(text: str, terms: List[str]) -> Tuple[bool, List[str]]:
    """Check if text contains any of the search terms."""
    found_terms = []
    text_lower = text.lower()

    for term in terms:
        # Use word boundary matching
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_terms.append(term)

    return len(found_terms) > 0, found_terms


def extract_verses(input_dir: Path, output_file: Path,
                   require_occupation: bool = True,
                   require_gender: bool = False):
    """
    Extract relevant verses from Bible text files.

    Args:
        input_dir: Directory containing Bible text files
        output_file: Output CSV file path
        require_occupation: Require occupation terms
        require_gender: Require gender terms
    """

    print(f"Extracting verses from: {input_dir}")
    print(f"Output file: {output_file}")
    print(f"Filters: occupation={require_occupation}, gender={require_gender}")

    # Find all text files
    text_files = sorted(input_dir.glob("kik_*_read.txt"))

    if not text_files:
        print(f"ERROR: No text files found in {input_dir}")
        return

    print(f"Found {len(text_files)} chapter files")

    # Extract verses
    extracted = []
    total_verses = 0

    for text_file in text_files:
        book_name, chapter, book_code = parse_filename(text_file.name)

        # Read file
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"ERROR reading {text_file}: {e}")
            continue

        # Process each line as a verse
        verse_num = 0
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue

            total_verses += 1
            verse_num += 1

            # Check for occupation terms
            has_occupation, occ_terms = contains_terms(line, OCCUPATION_TERMS)

            # Check for gender terms
            has_gender, gender_terms = contains_terms(line, GENDER_TERMS + PRONOUN_TERMS)

            # Apply filters
            include = True
            if require_occupation and not has_occupation:
                include = False
            if require_gender and not has_gender:
                include = False

            # If at least occupation term found, extract it
            if include and has_occupation:
                verse_id = f"{book_code}_{chapter}_{verse_num}"

                extracted.append({
                    'verse_id': verse_id,
                    'book': book_name,
                    'chapter': chapter,
                    'verse': str(verse_num),
                    'text': line,
                    'occupation_terms': ','.join(occ_terms),
                    'gender_terms': ','.join(gender_terms),
                    'has_gender_context': 'yes' if has_gender else 'no',
                    'data_source': 'bible',
                    'source_url': 'https://eBible.org/Scriptures/kik_readaloud.zip',
                    'collection_date': '2026-02-05',
                    'license': 'CC BY-SA 4.0'
                })

    # Write to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if extracted:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=extracted[0].keys())
            writer.writeheader()
            writer.writerows(extracted)

        print(f"\n✅ Extraction complete!")
        print(f"   Total verses processed: {total_verses:,}")
        print(f"   Verses extracted: {len(extracted):,}")
        print(f"   Percentage: {len(extracted)/total_verses*100:.2f}%")
        print(f"\n   Verses with occupation terms: {len(extracted)}")
        with_gender = sum(1 for v in extracted if v['has_gender_context'] == 'yes')
        print(f"   Verses with gender context: {with_gender}")
        print(f"   Percentage with gender: {with_gender/len(extracted)*100:.1f}%")

        # Print some statistics
        occ_counts = {}
        for verse in extracted:
            for term in verse['occupation_terms'].split(','):
                if term:
                    occ_counts[term] = occ_counts.get(term, 0) + 1

        print(f"\n   Top occupation terms found:")
        for term, count in sorted(occ_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"      {term}: {count}")

        print(f"\n📁 Output saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024:.2f} KB")
    else:
        print("\n⚠️  No verses found matching criteria")


def main():
    parser = argparse.ArgumentParser(
        description="Extract relevant verses from Kikuyu Bible for bias detection"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/kikuyu_bible"),
        help="Input directory with Bible text files (default: data/raw/kikuyu_bible)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/kikuyu_bible_extracted.csv"),
        help="Output CSV file (default: data/raw/kikuyu_bible_extracted.csv)"
    )
    parser.add_argument(
        "--require-gender",
        action="store_true",
        help="Only extract verses with both occupation AND gender terms"
    )
    parser.add_argument(
        "--all-terms",
        action="store_true",
        help="Extract all verses with occupation terms (ignore gender requirement)"
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input.exists():
        print(f"❌ ERROR: Input directory not found: {args.input}")
        print(f"\nExpected Bible files at: {args.input}")
        print(f"\nHave you downloaded the Bible? Run:")
        print(f"  curl -O https://eBible.org/Scriptures/kik_readaloud.zip")
        print(f"  unzip kik_readaloud.zip -d data/raw/kikuyu_bible/")
        return 1

    # Extract verses
    extract_verses(
        args.input,
        args.output,
        require_occupation=True,
        require_gender=args.require_gender
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
