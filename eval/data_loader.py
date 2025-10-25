"""
Data loading utilities for bias evaluation framework.

This module handles all file I/O operations with proper error handling and validation.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

from .models_simple import GroundTruthSample, Language, BiasCategory


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


class GroundTruthLoader:
    """Handles loading and validation of ground truth datasets."""
    
    def __init__(self, data_dir: Path = Path("eval")):
        """
        Initialize the ground truth loader.
        
        Args:
            data_dir: Directory containing ground truth files
        """
        self.data_dir = data_dir
    
    def load_ground_truth(self, language: Language) -> List[GroundTruthSample]:
        """
        Load ground truth samples for a specific language.
        
        Args:
            language: Language to load ground truth for
            
        Returns:
            List of validated ground truth samples
            
        Raises:
            DataLoadError: If file cannot be loaded or data is invalid
        """
        file_path = self._get_ground_truth_path(language)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                samples = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        sample = self._parse_ground_truth_row(row)
                        samples.append(sample)
                    except Exception as e:
                        raise DataLoadError(
                            f"Invalid data in {file_path} at row {row_num}: {e}"
                        ) from e
                        
                return samples
                
        except FileNotFoundError:
            raise DataLoadError(f"Ground truth file not found: {file_path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load ground truth from {file_path}: {e}") from e
    
    def _get_ground_truth_path(self, language: Language) -> Path:
        """Get the file path for ground truth data."""
        filename = f"ground_truth_{language.value}.csv"
        return self.data_dir / filename
    
    def _parse_ground_truth_row(self, row: Dict[str, str]) -> GroundTruthSample:
        """Parse a single CSV row into a GroundTruthSample."""
        return GroundTruthSample(
            text=row['text'].strip('"'),  # Remove quotes if present
            has_bias=row['has_bias'].lower() == 'true',
            bias_category=BiasCategory(row['bias_category']),
            expected_correction=row['expected_correction']
        )


class RulesLoader:
    """Handles loading bias detection rules from CSV files."""
    
    def __init__(self, rules_dir: Path = Path("rules")):
        """
        Initialize the rules loader.
        
        Args:
            rules_dir: Directory containing rule files
        """
        self.rules_dir = rules_dir
    
    def load_rules(self, language: Language) -> List[Dict[str, str]]:
        """
        Load bias detection rules for a specific language.
        
        Args:
            language: Language to load rules for
            
        Returns:
            List of rule dictionaries
            
        Raises:
            DataLoadError: If rules cannot be loaded
        """
        file_path = self._get_rules_path(language)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rules = []
                
                for row in reader:
                    if row.get('biased') and row.get('neutral_primary'):
                        rules.append({
                            'biased': row['biased'],
                            'neutral_primary': row['neutral_primary'],
                            'severity': row.get('severity', 'replace')
                        })
                
                return rules
                
        except FileNotFoundError:
            raise DataLoadError(f"Rules file not found: {file_path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load rules from {file_path}: {e}") from e
    
    def _get_rules_path(self, language: Language) -> Path:
        """Get the file path for rules data."""
        filename = f"lexicon_{language.value}_v2.csv"
        return self.rules_dir / filename


class ResultsWriter:
    """Handles writing evaluation results to files."""
    
    def __init__(self, results_dir: Path = Path("eval/results")):
        """
        Initialize the results writer.
        
        Args:
            results_dir: Directory to write results to
        """
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def write_csv_report(self, results: List[Any], filename: str) -> Path:
        """
        Write evaluation results to CSV file.
        
        Args:
            results: List of result dictionaries
            filename: Name of output file
            
        Returns:
            Path to written file
            
        Raises:
            DataLoadError: If file cannot be written
        """
        file_path = self.results_dir / filename
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            
            return file_path
            
        except Exception as e:
            raise DataLoadError(f"Failed to write CSV report to {file_path}: {e}") from e
    
    def write_json_report(self, data: Dict[str, Any], filename: str) -> Path:
        """
        Write data to JSON file.
        
        Args:
            data: Data to write
            filename: Name of output file
            
        Returns:
            Path to written file
            
        Raises:
            DataLoadError: If file cannot be written
        """
        file_path = self.results_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return file_path
            
        except Exception as e:
            raise DataLoadError(f"Failed to write JSON report to {file_path}: {e}") from e