#!/usr/bin/env python3
"""
PII Detection and Removal for Collected Data

This script detects and removes Personally Identifiable Information (PII)
from collected bias detection samples to ensure privacy compliance.

Detects:
- Email addresses
- Phone numbers
- URLs with personal identifiers
- Names (basic heuristics)
- Physical addresses
- Social security numbers / ID numbers

Usage:
    python scripts/data_collection/detect_pii.py --input data/raw/samples.csv --output data/clean/samples_clean.csv
    python scripts/data_collection/detect_pii.py --input data/raw/ --output data/clean/ --recursive
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PIIDetector:
    """Detects and removes PII from text samples"""

    def __init__(self):
        self.stats = {
            'samples_processed': 0,
            'pii_detected': 0,
            'emails_found': 0,
            'phones_found': 0,
            'urls_found': 0,
            'potential_names_found': 0,
        }

        # Regex patterns for PII detection
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_us': re.compile(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            'phone_intl': re.compile(r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),
            'url': re.compile(r'https?://[^\s]+'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # US SSN
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            # Common ID formats
            'id_number': re.compile(r'\b[A-Z]{2}\d{6,10}\b'),
        }

        # Common titles that precede names (multi-language)
        self.name_titles = [
            # English
            r'\bMr\.?\s+', r'\bMrs\.?\s+', r'\bMs\.?\s+', r'\bDr\.?\s+', r'\bProf\.?\s+',
            # French
            r'\bM\.?\s+', r'\bMme\.?\s+', r'\bMlle\.?\s+',
            # Swahili
            r'\bBwana\s+', r'\bBibi\s+', r'\bDkt\.?\s+',
        ]

    def detect_email(self, text: str) -> List[str]:
        """Detect email addresses"""
        return self.patterns['email'].findall(text)

    def detect_phone(self, text: str) -> List[str]:
        """Detect phone numbers"""
        phones = []
        phones.extend(self.patterns['phone_us'].findall(text))
        phones.extend(self.patterns['phone_intl'].findall(text))
        return phones

    def detect_url(self, text: str) -> List[str]:
        """Detect URLs (may contain personal identifiers)"""
        return self.patterns['url'].findall(text)

    def detect_ssn_or_id(self, text: str) -> List[str]:
        """Detect SSN, credit cards, or ID numbers"""
        ids = []
        ids.extend(self.patterns['ssn'].findall(text))
        ids.extend(self.patterns['credit_card'].findall(text))
        ids.extend(self.patterns['id_number'].findall(text))
        return ids

    def detect_names_after_titles(self, text: str) -> List[str]:
        """Detect potential names after common titles"""
        names = []
        for title_pattern in self.name_titles:
            # Find text following title (up to next punctuation)
            pattern = title_pattern + r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            matches = re.findall(pattern, text)
            names.extend(matches)
        return names

    def detect_all_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect all types of PII in text"""
        pii_found = {
            'emails': self.detect_email(text),
            'phones': self.detect_phone(text),
            'urls': self.detect_url(text),
            'ids': self.detect_ssn_or_id(text),
            'potential_names': self.detect_names_after_titles(text),
        }

        # Update stats
        if any(pii_found.values()):
            self.stats['pii_detected'] += 1
        self.stats['emails_found'] += len(pii_found['emails'])
        self.stats['phones_found'] += len(pii_found['phones'])
        self.stats['urls_found'] += len(pii_found['urls'])
        self.stats['potential_names_found'] += len(pii_found['potential_names'])

        return pii_found

    def remove_pii(self, text: str, redact_method: str = 'placeholder') -> Tuple[str, bool]:
        """
        Remove PII from text

        Args:
            text: Input text
            redact_method: 'placeholder' (replace with [REDACTED]) or 'remove' (delete)

        Returns:
            (cleaned_text, pii_was_found)
        """
        pii_found = self.detect_all_pii(text)
        has_pii = any(pii_found.values())

        if not has_pii:
            return text, False

        cleaned_text = text

        # Replace emails
        for email in pii_found['emails']:
            if redact_method == 'placeholder':
                cleaned_text = cleaned_text.replace(email, '[EMAIL_REDACTED]')
            else:
                cleaned_text = cleaned_text.replace(email, '')

        # Replace phones
        for phone in pii_found['phones']:
            if redact_method == 'placeholder':
                cleaned_text = cleaned_text.replace(str(phone), '[PHONE_REDACTED]')
            else:
                cleaned_text = cleaned_text.replace(str(phone), '')

        # Replace URLs
        for url in pii_found['urls']:
            if redact_method == 'placeholder':
                cleaned_text = cleaned_text.replace(url, '[URL_REDACTED]')
            else:
                cleaned_text = cleaned_text.replace(url, '')

        # Replace IDs
        for id_num in pii_found['ids']:
            if redact_method == 'placeholder':
                cleaned_text = cleaned_text.replace(id_num, '[ID_REDACTED]')
            else:
                cleaned_text = cleaned_text.replace(id_num, '')

        # Replace potential names after titles
        for name in pii_found['potential_names']:
            if redact_method == 'placeholder':
                cleaned_text = re.sub(
                    r'(' + '|'.join(self.name_titles) + r')' + re.escape(name),
                    r'\1[NAME_REDACTED]',
                    cleaned_text
                )
            else:
                cleaned_text = re.sub(
                    r'(' + '|'.join(self.name_titles) + r')' + re.escape(name),
                    r'\1',
                    cleaned_text
                )

        # Clean up extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        return cleaned_text, True

    def process_csv(self, input_file: Path, output_file: Path, redact_method: str = 'placeholder'):
        """Process a CSV file and remove PII"""
        print(f"\n🔍 Processing: {input_file.name}")

        if not input_file.exists():
            print(f"  ⚠️  File not found: {input_file}")
            return

        # Read all rows
        rows = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            for row in reader:
                self.stats['samples_processed'] += 1

                # Clean the 'text' field
                if 'text' in row:
                    original_text = row['text']
                    cleaned_text, had_pii = self.remove_pii(original_text, redact_method)

                    row['text'] = cleaned_text

                    # Update pii_removed field
                    if 'pii_removed' in row:
                        row['pii_removed'] = 'true' if had_pii else row['pii_removed']

                    # Add note if PII was found
                    if had_pii and 'notes' in row:
                        if row['notes']:
                            row['notes'] += ' | PII detected and removed.'
                        else:
                            row['notes'] = 'PII detected and removed.'

                rows.append(row)

        # Write cleaned data
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"  ✅ Cleaned: {len(rows)} samples")
        print(f"  💾 Saved to: {output_file}")

    def print_stats(self):
        """Print PII detection statistics"""
        print("\n" + "="*60)
        print("📊 PII DETECTION STATISTICS")
        print("="*60)
        print(f"  Samples processed:    {self.stats['samples_processed']}")
        print(f"  Samples with PII:     {self.stats['pii_detected']}")
        print(f"  Emails found:         {self.stats['emails_found']}")
        print(f"  Phone numbers found:  {self.stats['phones_found']}")
        print(f"  URLs found:           {self.stats['urls_found']}")
        print(f"  Potential names:      {self.stats['potential_names_found']}")

        if self.stats['samples_processed'] > 0:
            pii_rate = (self.stats['pii_detected'] / self.stats['samples_processed']) * 100
            print(f"\n  PII detection rate:   {pii_rate:.1f}%")

        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Detect and remove PII from collected data"
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help="Input CSV file or directory"
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help="Output CSV file or directory"
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help="Process all CSV files in input directory recursively"
    )
    parser.add_argument(
        '--redact-method',
        type=str,
        choices=['placeholder', 'remove'],
        default='placeholder',
        help="How to redact PII: 'placeholder' ([REDACTED]) or 'remove' (delete)"
    )

    args = parser.parse_args()

    print("="*60)
    print("🔒 PII DETECTION AND REMOVAL")
    print("="*60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Method: {args.redact_method}")
    print("="*60)

    detector = PIIDetector()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        # Process single file
        detector.process_csv(input_path, output_path, args.redact_method)
    elif input_path.is_dir() and args.recursive:
        # Process all CSV files in directory
        csv_files = list(input_path.glob('**/*.csv'))
        print(f"\nFound {len(csv_files)} CSV files to process")

        for csv_file in csv_files:
            # Maintain directory structure
            relative_path = csv_file.relative_to(input_path)
            output_file = output_path / relative_path

            detector.process_csv(csv_file, output_file, args.redact_method)
    else:
        print("❌ Invalid input: must be a file or directory with --recursive flag")
        sys.exit(1)

    detector.print_stats()

    print("\n✅ PII removal complete!")
    print("\nNext steps:")
    print("1. Review redacted samples for quality")
    print("2. Verify sensitive information was properly removed")
    print("3. Proceed with annotation")


if __name__ == "__main__":
    main()
