"""Base classes for data collection.

This module provides the foundation for all data collectors,
replacing the scattered collection scripts with a unified interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class CollectionConfig:
    """Configuration for data collection."""
    language: str
    max_items: int
    output_file: Path
    cache_dir: Path = Path("data/cache")
    source_name: str = ""

    def __post_init__(self):
        """Validate and initialize configuration."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if self.max_items < 1:
            raise ValueError("max_items must be >= 1")

        if not self.language:
            raise ValueError("language cannot be empty")


@dataclass
class CollectedSample:
    """A single collected data sample."""
    text: str
    source: str
    metadata: Dict = field(default_factory=dict)
    language: str = ""
    collection_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate sample."""
        if not self.text or not self.text.strip():
            raise ValueError("text cannot be empty")

        if not self.source:
            raise ValueError("source cannot be empty")


@dataclass
class CollectionResult:
    """Result from a data collection operation."""
    success: bool
    samples_collected: int
    output_file: Optional[Path]
    error_message: str = ""
    lineage: Dict = field(default_factory=dict)

    def summary(self) -> str:
        """Return human-readable summary."""
        if self.success:
            return f"Successfully collected {self.samples_collected} samples → {self.output_file}"
        else:
            return f"Collection failed: {self.error_message}"


class DataCollector(ABC):
    """
    Abstract base class for data collectors.

    All collectors must implement:
    - collect(): Gather data from source
    - get_lineage(): Return provenance information
    """

    def __init__(self, config: CollectionConfig):
        """
        Initialize collector.

        Args:
            config: Collection configuration
        """
        self.config = config

    @abstractmethod
    def collect(self) -> List[CollectedSample]:
        """
        Collect data from source.

        Returns:
            List of collected samples

        Raises:
            Exception: If collection fails
        """
        pass

    @abstractmethod
    def get_lineage(self) -> Dict:
        """
        Return data lineage information.

        Returns:
            Dictionary with provenance metadata
        """
        pass

    def save_samples(self, samples: List[CollectedSample]) -> CollectionResult:
        """
        Save collected samples to CSV file.

        Args:
            samples: List of samples to save

        Returns:
            CollectionResult with status and metadata
        """
        try:
            import csv

            if not samples:
                return CollectionResult(
                    success=True,
                    samples_collected=0,
                    output_file=self.config.output_file,
                    lineage=self.get_lineage()
                )

            # Ensure output directory exists
            self.config.output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to CSV
            with open(self.config.output_file, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['text', 'source', 'language', 'collection_date', 'metadata']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for sample in samples:
                    writer.writerow({
                        'text': sample.text,
                        'source': sample.source,
                        'language': sample.language,
                        'collection_date': sample.collection_date,
                        'metadata': str(sample.metadata)
                    })

            return CollectionResult(
                success=True,
                samples_collected=len(samples),
                output_file=self.config.output_file,
                lineage=self.get_lineage()
            )

        except Exception as e:
            return CollectionResult(
                success=False,
                samples_collected=0,
                output_file=None,
                error_message=str(e)
            )
