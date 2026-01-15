"""
Data loading utilities for bias evaluation framework.

This module handles all file I/O operations with proper error handling and validation.
Supports both legacy 4-field format and full AI BRIDGE 29-field schema.
Includes automatic lexicon validation on load.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import (
    GroundTruthSample, Language, BiasCategory, BiasLabel,
    StereotypeCategory, TargetGender, Explicitness, Sentiment,
    SafetyFlag, QAStatus
)
from .lexicon_validator import (
    LexiconValidator, ValidationReport, LexiconValidationError,
    validate_lexicon_on_load
)


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
        filename = f"ground_truth_{language.value}_v3.csv"
        return self.data_dir / filename
    
    def _parse_ground_truth_row(self, row: Dict[str, str]) -> GroundTruthSample:
        """
        Parse a single CSV row into a GroundTruthSample.

        Supports both legacy 4-field format and full AI BRIDGE schema.
        """
        # Core required fields
        text = row['text'].strip('"')
        has_bias = row['has_bias'].lower() == 'true'
        bias_category = BiasCategory(row['bias_category'])
        expected_correction = row.get('expected_correction', '')

        # Check if this is AI BRIDGE extended format
        is_extended = 'target_gender' in row or 'bias_label' in row

        if is_extended:
            return GroundTruthSample(
                text=text,
                has_bias=has_bias,
                bias_category=bias_category,
                expected_correction=expected_correction,
                # AI BRIDGE metadata fields
                id=row.get('id'),
                language=row.get('language'),
                script=row.get('script'),
                country=row.get('country'),
                region_dialect=row.get('region_dialect'),
                source_type=row.get('source_type'),
                source_ref=row.get('source_ref'),
                collection_date=row.get('collection_date'),
                translation=row.get('translation'),
                domain=row.get('domain'),
                topic=row.get('topic'),
                theme=row.get('theme'),
                sensitive_characteristic=row.get('sensitive_characteristic'),
                # AI BRIDGE bias annotation fields
                target_gender=self._parse_enum(row.get('target_gender'), TargetGender),
                bias_label=self._parse_enum(row.get('bias_label'), BiasLabel),
                stereotype_category=self._parse_enum(row.get('stereotype_category'), StereotypeCategory),
                explicitness=self._parse_enum(row.get('explicitness'), Explicitness),
                bias_severity=self._parse_int(row.get('bias_severity')),
                sentiment_toward_referent=self._parse_enum(row.get('sentiment_toward_referent'), Sentiment),
                device=row.get('device'),
                # Quality and safety fields
                safety_flag=self._parse_enum(row.get('safety_flag'), SafetyFlag),
                pii_removed=self._parse_bool(row.get('pii_removed')),
                annotator_id=row.get('annotator_id'),
                qa_status=self._parse_enum(row.get('qa_status'), QAStatus),
                approver_id=row.get('approver_id'),
                cohen_kappa=self._parse_float(row.get('cohen_kappa')),
                notes=row.get('notes'),
                eval_split=row.get('eval_split')
            )
        else:
            # Legacy 4-field format
            return GroundTruthSample(
                text=text,
                has_bias=has_bias,
                bias_category=bias_category,
                expected_correction=expected_correction
            )

    def _parse_enum(self, value: Optional[str], enum_class) -> Optional[Any]:
        """Parse a string value into an enum, returning None if invalid."""
        if not value or value.upper() in ('', 'NEEDS_ANNOTATION', 'N/A', 'NONE'):
            return None
        try:
            # Handle both value and name matching
            value_lower = value.lower().replace('_', '-')
            for member in enum_class:
                if member.value.lower() == value_lower or member.name.lower() == value_lower:
                    return member
            return None
        except (ValueError, KeyError):
            return None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse a string to int, returning None if invalid."""
        if not value or value in ('', 'N/A'):
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse a string to float, returning None if invalid."""
        if not value or value in ('', 'N/A'):
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _parse_bool(self, value: Optional[str]) -> Optional[bool]:
        """Parse a string to bool, returning None if invalid."""
        if not value or value in ('', 'N/A'):
            return None
        return value.lower() in ('true', '1', 'yes')


class RulesLoader:
    """Handles loading bias detection rules from CSV files with validation."""

    def __init__(self, rules_dir: Path = Path("rules"), validate: bool = True,
                 strict_validation: bool = False):
        """
        Initialize the rules loader.

        Args:
            rules_dir: Directory containing rule files
            validate: If True, validates lexicons before loading
            strict_validation: If True, warnings become errors during validation
        """
        self.rules_dir = rules_dir
        self.validate = validate
        self.strict_validation = strict_validation
        self._validator = LexiconValidator(strict_mode=strict_validation)
        self._validation_reports: Dict[str, ValidationReport] = {}

    def get_validation_report(self, language: Language) -> Optional[ValidationReport]:
        """Get the validation report for a language if available."""
        return self._validation_reports.get(language.value)

    def load_rules(self, language: Language) -> List[Dict[str, str]]:
        """
        Load bias detection rules for a specific language.

        Args:
            language: Language to load rules for

        Returns:
            List of rule dictionaries with AI BRIDGE extended fields

        Raises:
            DataLoadError: If rules cannot be loaded
            LexiconValidationError: If validation fails (when validate=True)
        """
        file_path = self._get_rules_path(language)

        # Validate lexicon before loading
        if self.validate:
            report = self._validator.validate_file(file_path)
            self._validation_reports[language.value] = report

            if not report.is_valid:
                # Log validation issues
                print(f"\n⚠️  Lexicon validation issues for {language.value}:")
                for issue in report.issues:
                    if issue.severity.value == "error":
                        print(f"   ❌ Row {issue.row_number}: {issue.message}")

                raise LexiconValidationError(report)

            elif report.warning_count > 0:
                print(f"\n⚠️  Lexicon warnings for {language.value}: {report.warning_count} warnings")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rules = []

                for row in reader:
                    # Include rules with biased term (neutral_primary can be empty for deletion patterns)
                    if row.get('biased'):
                        rule = {
                            'biased': row['biased'],
                            'neutral_primary': row.get('neutral_primary', ''),
                            'severity': row.get('severity', 'replace'),
                            'pos': row.get('pos', 'noun'),
                            'tags': row.get('tags', ''),
                            # AI BRIDGE extended fields
                            'bias_label': row.get('bias_label', 'stereotype'),
                            'stereotype_category': row.get('stereotype_category', 'profession'),
                            'explicitness': row.get('explicitness', 'explicit'),
                            # Language-specific fields
                            'ngeli': row.get('ngeli', ''),
                            'number': row.get('number', ''),
                            'requires_agreement': row.get('requires_agreement', 'false'),
                            'scope': row.get('scope', ''),
                            'register': row.get('register', 'formal'),
                        }
                        rules.append(rule)

                return rules

        except FileNotFoundError:
            raise DataLoadError(f"Rules file not found: {file_path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load rules from {file_path}: {e}") from e
    
    def _get_rules_path(self, language: Language) -> Path:
        """Get the file path for rules data."""
        filename = f"lexicon_{language.value}_v3.csv"
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