"""News data collector for Swahili occupation sentences."""
import csv
import json
import re
import zipfile
from pathlib import Path
from typing import List, Dict, Set
import urllib.request

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = lambda x, **kwargs: x

from .base_collector import DataCollector, CollectedSample, CollectionConfig


class NewsCollector(DataCollector):
    """
    Collect data from Swahili News Dataset.

    Downloads and mines sentences containing occupation terms
    from 31,000+ news articles from Kenya (2015-2020).
    """

    ZENODO_URL = "https://zenodo.org/record/5514203/files/swahili-news.zip"

    def __init__(self, config: CollectionConfig, lexicon_path: str = "rules/lexicon_sw_v3.csv"):
        super().__init__(config)
        if config.language != "sw":
            raise ValueError("NewsCollector only supports Swahili (sw)")

        self.lexicon_path = Path(lexicon_path)
        self.occupation_terms: Set[str] = set()
        self._load_occupations()

        self.dataset_path = self.config.cache_dir / "swahili-news.zip"
        self.extracted_dir = self.config.cache_dir / "swahili-news"

    def _load_occupations(self):
        """Load occupation terms from lexicon."""
        if not self.lexicon_path.exists():
            print(f"Warning: Lexicon not found at {self.lexicon_path}")
            return

        with open(self.lexicon_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('language') == 'sw' and 'occupation' in row.get('tags', ''):
                    biased = row['biased'].lower()
                    neutral = row.get('neutral_primary', '').lower()

                    self.occupation_terms.add(biased)
                    if neutral and neutral != biased:
                        self.occupation_terms.add(neutral)

    def _download_dataset(self):
        """Download dataset from Zenodo if needed."""
        if self.dataset_path.exists():
            return

        print(f"Downloading Swahili News Dataset (~200MB)...")
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            if HAS_TQDM:
                with tqdm(unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                    def update_progress(block_num, block_size, total_size):
                        pbar.total = total_size
                        pbar.update(block_size)

                    urllib.request.urlretrieve(
                        self.ZENODO_URL,
                        self.dataset_path,
                        reporthook=update_progress
                    )
            else:
                urllib.request.urlretrieve(self.ZENODO_URL, self.dataset_path)

            print(f"Downloaded to: {self.dataset_path}")
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")

    def _extract_dataset(self):
        """Extract downloaded zip file."""
        if self.extracted_dir.exists():
            return

        print("Extracting dataset...")
        with zipfile.ZipFile(self.dataset_path, 'r') as zip_ref:
            zip_ref.extractall(self.extracted_dir)

    def _get_data_files(self) -> List[Path]:
        """Find all data files."""
        json_files = list(self.extracted_dir.rglob("*.json"))
        csv_files = list(self.extracted_dir.rglob("*.csv"))
        txt_files = list(self.extracted_dir.rglob("*.txt"))
        return json_files + csv_files + txt_files

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        sentences = re.split(r'[.!?]+', text)
        cleaned = []
        for sent in sentences:
            sent = sent.strip()
            if 20 <= len(sent) <= 500 and re.search(r'\w', sent):
                cleaned.append(sent)
        return cleaned

    def _contains_occupation(self, sentence: str) -> bool:
        """Check if sentence contains occupation term."""
        sentence_lower = sentence.lower()
        for term in self.occupation_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, sentence_lower):
                return True
        return False

    def _mine_file(self, file_path: Path) -> List[CollectedSample]:
        """Mine occupation sentences from a file."""
        samples = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    data = json.load(f)
                    if isinstance(data, list):
                        texts = [item.get('text', '') or item.get('content', '') for item in data]
                    elif isinstance(data, dict):
                        texts = [data.get('text', '') or data.get('content', '')]
                    else:
                        texts = []
                elif file_path.suffix == '.csv':
                    reader = csv.DictReader(f)
                    texts = [row.get('text', '') or row.get('content', '') for row in reader]
                else:
                    texts = [f.read()]

            for text in texts:
                if not text:
                    continue

                sentences = self._extract_sentences(text)
                for sentence in sentences:
                    if self._contains_occupation(sentence):
                        sample = CollectedSample(
                            text=sentence,
                            source="swahili_news",
                            language=self.config.language,
                            metadata={
                                'file': str(file_path.name),
                                'dataset': 'Swahili News Dataset (Zenodo)'
                            }
                        )
                        samples.append(sample)

                        if len(samples) >= self.config.max_items:
                            return samples

        except Exception:
            pass

        return samples

    def collect(self) -> List[CollectedSample]:
        """
        Collect samples from Swahili News Dataset.

        Returns:
            List of CollectedSample objects
        """
        if not self.occupation_terms:
            print("Warning: No occupation terms loaded, cannot mine sentences")
            return []

        # Download and extract if needed
        self._download_dataset()
        self._extract_dataset()

        # Get data files
        files = self._get_data_files()
        if not files:
            print("Warning: No data files found in extracted dataset")
            return []

        # Mine files
        all_samples = []
        for file_path in files:
            if len(all_samples) >= self.config.max_items:
                break

            samples = self._mine_file(file_path)
            all_samples.extend(samples)

        return all_samples[:self.config.max_items]

    def get_lineage(self) -> Dict:
        """Get data lineage information."""
        return {
            "source": "Swahili News Dataset",
            "language": self.config.language,
            "dataset_url": self.ZENODO_URL,
            "occupation_terms_count": len(self.occupation_terms),
            "collector": "NewsCollector",
            "coverage": "2015-2020 Kenya news articles"
        }
