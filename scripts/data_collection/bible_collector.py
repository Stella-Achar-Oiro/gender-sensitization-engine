"""Bible data collector for Kikuyu verses with occupation terms."""
import csv
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set

from .base_collector import DataCollector, CollectedSample, CollectionConfig


class BibleCollector(DataCollector):
    """
    Collect data from Kikuyu Bible verses.

    Extracts verses containing occupation terms and/or gender contexts
    from Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013).
    """

    # Kikuyu occupation terms
    OCCUPATION_TERMS = [
        "mũrutani", "mũruti", "daktari", "mũrũgamĩrĩri", "mũthaki",
        "mũigũ", "mũrĩmi", "mũrĩithi", "mũcungĩ", "mũthondeki",
        "mũteti", "mũthuurĩ", "mũcamanĩri", "mũtongoria", "mũthĩnjĩri",
        "mũigĩ", "mũguĩ", "mũgurĩ", "mũthembi", "mũheani",
    ]

    # Gender terms
    GENDER_TERMS = [
        "mũrũme", "mũtumia", "mũirĩtu", "kĩhĩĩ", "andũ-a-nja",
        "arũme", "athuri",
    ]

    # Pronouns
    PRONOUN_TERMS = [
        "yeye", "we", "ũcio", "ĩyo",
    ]

    # Book code mappings
    BOOK_NAMES = {
        'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus',
        'NUM': 'Numbers', 'DEU': 'Deuteronomy', 'JOS': 'Joshua',
        'JDG': 'Judges', 'RUT': 'Ruth', '1SA': '1 Samuel',
        '2SA': '2 Samuel', '1KI': '1 Kings', '2KI': '2 Kings',
        'PSA': 'Psalms', 'PRO': 'Proverbs', 'JOB': 'Job',
        'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke',
        'JHN': 'John', 'ACT': 'Acts', 'ROM': 'Romans',
        '1CO': '1 Corinthians', '2CO': '2 Corinthians',
    }

    def __init__(self, config: CollectionConfig, bible_dir: str = "data/raw/kikuyu_bible"):
        super().__init__(config)
        if config.language != "ki":
            raise ValueError("BibleCollector only supports Kikuyu (ki)")

        self.bible_dir = Path(bible_dir)

    def _parse_filename(self, filename: str) -> Tuple[str, str, str]:
        """Parse book and chapter from filename."""
        parts = filename.replace('.txt', '').split('_')
        if len(parts) >= 4:
            book_code = parts[2]
            chapter = parts[3]
            book_name = self.BOOK_NAMES.get(book_code, book_code)
            return book_name, chapter.lstrip('0'), book_code
        return "Unknown", "0", "UNK"

    def _contains_terms(self, text: str, terms: List[str]) -> Tuple[bool, List[str]]:
        """Check if text contains any terms."""
        found = []
        text_lower = text.lower()

        for term in terms:
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found.append(term)

        return len(found) > 0, found

    def collect(self) -> List[CollectedSample]:
        """
        Collect verses from Kikuyu Bible.

        Returns:
            List of CollectedSample objects
        """
        if not self.bible_dir.exists():
            print(f"Warning: Bible directory not found at {self.bible_dir}")
            print("Download from: https://eBible.org/Scriptures/kik_readaloud.zip")
            return []

        text_files = sorted(self.bible_dir.glob("kik_*_read.txt"))
        if not text_files:
            print(f"Warning: No Bible text files found in {self.bible_dir}")
            return []

        samples = []
        all_gender_terms = self.GENDER_TERMS + self.PRONOUN_TERMS

        for text_file in text_files:
            if len(samples) >= self.config.max_items:
                break

            book_name, chapter, book_code = self._parse_filename(text_file.name)

            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception:
                continue

            verse_num = 0
            for line in lines:
                line = line.strip()
                if not line or len(line) < 10:
                    continue

                verse_num += 1

                # Check for occupation and gender terms
                has_occupation, occ_terms = self._contains_terms(line, self.OCCUPATION_TERMS)
                has_gender, gender_terms = self._contains_terms(line, all_gender_terms)

                # Only include verses with occupation terms
                if has_occupation:
                    verse_id = f"{book_code}_{chapter}_{verse_num}"

                    sample = CollectedSample(
                        text=line,
                        source="kikuyu_bible",
                        language=self.config.language,
                        metadata={
                            'verse_id': verse_id,
                            'book': book_name,
                            'chapter': chapter,
                            'verse': str(verse_num),
                            'occupation_terms': ','.join(occ_terms),
                            'gender_terms': ','.join(gender_terms),
                            'has_gender_context': has_gender,
                            'source_url': 'https://eBible.org/Scriptures/kik_readaloud.zip',
                            'license': 'CC BY-SA 4.0',
                            'translation': 'Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013)'
                        }
                    )
                    samples.append(sample)

                    if len(samples) >= self.config.max_items:
                        break

        return samples

    def get_lineage(self) -> Dict:
        """Get data lineage information."""
        return {
            "source": "Kikuyu Bible",
            "language": self.config.language,
            "translation": "Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013)",
            "license": "CC BY-SA 4.0",
            "source_url": "https://eBible.org/Scriptures/kik_readaloud.zip",
            "collector": "BibleCollector",
            "occupation_terms": len(self.OCCUPATION_TERMS),
            "gender_terms": len(self.GENDER_TERMS)
        }
