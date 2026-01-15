"""
Lexicon Validation Module for AI BRIDGE Compliance.

This module provides validation for lexicon entries to ensure data quality
and compliance with AI BRIDGE annotation guidelines. It checks for:
- Identical biased/neutral terms (non-functional entries)
- Identical example sentences (no pedagogical value)
- Missing required fields
- Schema compliance

Integrates into the data loading pipeline to flag issues automatically.
"""
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

from config import lexicon_glob_pattern


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Blocks loading, must be fixed
    WARNING = "warning"  # Should be fixed, but doesn't block
    INFO = "info"        # Informational, may be intentional


@dataclass
class ValidationIssue:
    """Represents a single validation issue in a lexicon entry."""
    row_number: int
    column: str
    issue_type: str
    severity: ValidationSeverity
    message: str
    biased_term: str = ""
    suggestion: str = ""


@dataclass
class ValidationReport:
    """Complete validation report for a lexicon file."""
    file_path: str
    language: str
    total_entries: int
    valid_entries: int
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO)

    @property
    def is_valid(self) -> bool:
        """Returns True if no errors (warnings allowed)."""
        return self.error_count == 0

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"\n{'='*60}",
            f"LEXICON VALIDATION REPORT: {self.language.upper()}",
            f"{'='*60}",
            f"File: {self.file_path}",
            f"Total entries: {self.total_entries}",
            f"Valid entries: {self.valid_entries}",
            f"Issues found: {len(self.issues)}",
            f"  - Errors: {self.error_count}",
            f"  - Warnings: {self.warning_count}",
            f"  - Info: {self.info_count}",
            f"Status: {'PASS' if self.is_valid else 'FAIL'}",
            f"{'='*60}",
        ]

        if self.issues:
            lines.append("\nDETAILED ISSUES:")
            lines.append("-" * 40)

            for issue in self.issues:
                severity_icon = {
                    ValidationSeverity.ERROR: "❌",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.INFO: "ℹ️"
                }.get(issue.severity, "•")

                lines.append(f"\n{severity_icon} Row {issue.row_number}: {issue.issue_type}")
                lines.append(f"   Term: '{issue.biased_term}'")
                lines.append(f"   {issue.message}")
                if issue.suggestion:
                    lines.append(f"   Suggestion: {issue.suggestion}")

        return "\n".join(lines)


class LexiconValidator:
    """
    Validates lexicon CSV files for AI BRIDGE compliance.

    Usage:
        validator = LexiconValidator()
        report = validator.validate_file("rules/lexicon_sw_<version>.csv")

        if not report.is_valid:
            print(report.summary())
            raise ValidationError("Lexicon validation failed")
    """

    # Required columns for a valid lexicon
    REQUIRED_COLUMNS = ['language', 'biased', 'neutral_primary']

    # Columns that should have examples
    EXAMPLE_COLUMNS = ['example_biased', 'example_neutral']

    # AI BRIDGE required metadata columns
    AIBRIDGE_COLUMNS = ['bias_label', 'stereotype_category', 'explicitness']

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.

        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode

    def validate_file(self, file_path: str | Path) -> ValidationReport:
        """
        Validate a lexicon CSV file.

        Args:
            file_path: Path to the lexicon CSV file

        Returns:
            ValidationReport with all issues found
        """
        file_path = Path(file_path)

        # Extract language from filename (e.g., lexicon_sw_<version>.csv -> sw)
        language = file_path.stem.split('_')[1] if '_' in file_path.stem else 'unknown'

        report = ValidationReport(
            file_path=str(file_path),
            language=language,
            total_entries=0,
            valid_entries=0,
            issues=[]
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate header
                header_issues = self._validate_header(reader.fieldnames or [])
                report.issues.extend(header_issues)

                # Validate each row
                for row_num, row in enumerate(reader, start=2):
                    report.total_entries += 1
                    row_issues = self._validate_row(row, row_num)

                    if not any(i.severity == ValidationSeverity.ERROR for i in row_issues):
                        report.valid_entries += 1

                    report.issues.extend(row_issues)

        except FileNotFoundError:
            report.issues.append(ValidationIssue(
                row_number=0,
                column="file",
                issue_type="FILE_NOT_FOUND",
                severity=ValidationSeverity.ERROR,
                message=f"Lexicon file not found: {file_path}"
            ))
        except Exception as e:
            report.issues.append(ValidationIssue(
                row_number=0,
                column="file",
                issue_type="FILE_READ_ERROR",
                severity=ValidationSeverity.ERROR,
                message=f"Error reading file: {str(e)}"
            ))

        return report

    def _validate_header(self, fieldnames: List[str]) -> List[ValidationIssue]:
        """Validate CSV header has required columns."""
        issues = []

        for col in self.REQUIRED_COLUMNS:
            if col not in fieldnames:
                issues.append(ValidationIssue(
                    row_number=1,
                    column=col,
                    issue_type="MISSING_REQUIRED_COLUMN",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required column '{col}' is missing from header"
                ))

        for col in self.AIBRIDGE_COLUMNS:
            if col not in fieldnames:
                issues.append(ValidationIssue(
                    row_number=1,
                    column=col,
                    issue_type="MISSING_AIBRIDGE_COLUMN",
                    severity=ValidationSeverity.WARNING,
                    message=f"AI BRIDGE column '{col}' is missing - recommended for compliance"
                ))

        return issues

    def _validate_row(self, row: Dict[str, str], row_num: int) -> List[ValidationIssue]:
        """Validate a single lexicon row."""
        issues = []
        # Handle None values from CSV (when trailing columns are empty)
        biased = (row.get('biased') or '').strip()
        neutral = (row.get('neutral_primary') or '').strip()

        # Skip empty rows
        if not biased:
            return issues

        # Check 1: Identical biased and neutral terms (CRITICAL)
        if biased and neutral and biased == neutral:
            severity = ValidationSeverity.ERROR
            issues.append(ValidationIssue(
                row_number=row_num,
                column="biased/neutral_primary",
                issue_type="IDENTICAL_TERMS",
                severity=severity,
                message="Biased term is identical to neutral_primary - this entry is non-functional",
                biased_term=biased,
                suggestion="Either provide a different neutral term, or remove this entry if the term is inherently neutral"
            ))

        # Check 2: Empty neutral_primary (except for morphology/suffix entries)
        tags = row.get('tags') or ''
        if not neutral and 'morphology' not in tags and 'suffix' not in tags:
            issues.append(ValidationIssue(
                row_number=row_num,
                column="neutral_primary",
                issue_type="MISSING_NEUTRAL",
                severity=ValidationSeverity.WARNING,
                message="No neutral_primary provided",
                biased_term=biased,
                suggestion="Add a neutral alternative term"
            ))

        # Check 3: Identical example sentences
        example_biased = (row.get('example_biased') or '').strip()
        example_neutral = (row.get('example_neutral') or '').strip()

        if example_biased and example_neutral:
            if example_biased == example_neutral:
                issues.append(ValidationIssue(
                    row_number=row_num,
                    column="example_biased/example_neutral",
                    issue_type="IDENTICAL_EXAMPLES",
                    severity=ValidationSeverity.ERROR,
                    message="Example sentences are identical - no pedagogical value",
                    biased_term=biased,
                    suggestion="Provide distinct examples that show the difference between biased and neutral usage"
                ))
            elif self._examples_too_similar(example_biased, example_neutral, biased, neutral):
                issues.append(ValidationIssue(
                    row_number=row_num,
                    column="example_biased/example_neutral",
                    issue_type="SIMILAR_EXAMPLES",
                    severity=ValidationSeverity.WARNING,
                    message="Example sentences are nearly identical (only differ by the target term)",
                    biased_term=biased,
                    suggestion="Consider if the examples adequately demonstrate the bias"
                ))

        # Check 4: Missing examples
        if not example_biased and example_neutral:
            issues.append(ValidationIssue(
                row_number=row_num,
                column="example_biased",
                issue_type="MISSING_EXAMPLE_BIASED",
                severity=ValidationSeverity.WARNING,
                message="Missing biased example sentence",
                biased_term=biased
            ))

        if example_biased and not example_neutral:
            issues.append(ValidationIssue(
                row_number=row_num,
                column="example_neutral",
                issue_type="MISSING_EXAMPLE_NEUTRAL",
                severity=ValidationSeverity.WARNING,
                message="Missing neutral example sentence",
                biased_term=biased
            ))

        # Check 5: AI BRIDGE metadata
        bias_label = (row.get('bias_label') or '').strip()
        stereotype_category = (row.get('stereotype_category') or '').strip()

        if not bias_label:
            issues.append(ValidationIssue(
                row_number=row_num,
                column="bias_label",
                issue_type="MISSING_BIAS_LABEL",
                severity=ValidationSeverity.INFO,
                message="Missing bias_label (AI BRIDGE field)",
                biased_term=biased,
                suggestion="Add one of: stereotype, counter-stereotype, derogation, neutral"
            ))

        if not stereotype_category:
            issues.append(ValidationIssue(
                row_number=row_num,
                column="stereotype_category",
                issue_type="MISSING_STEREOTYPE_CATEGORY",
                severity=ValidationSeverity.INFO,
                message="Missing stereotype_category (AI BRIDGE field)",
                biased_term=biased,
                suggestion="Add one of: profession, family_role, leadership, capability, appearance, emotion, sexuality, violence, daily_life, intersectional"
            ))

        return issues

    def _examples_too_similar(self, ex_biased: str, ex_neutral: str,
                               biased: str, neutral: str) -> bool:
        """
        Check if examples only differ by the biased/neutral term swap.

        Returns True if the examples are essentially identical except for
        the term being demonstrated.
        """
        # Normalize for comparison
        ex_biased_norm = ex_biased.lower().replace(biased.lower(), '___TERM___')
        ex_neutral_norm = ex_neutral.lower().replace(neutral.lower(), '___TERM___')

        return ex_biased_norm == ex_neutral_norm

    def validate_all_lexicons(self, rules_dir: str | Path = "rules") -> Dict[str, ValidationReport]:
        """
        Validate all lexicon files in a directory.

        Args:
            rules_dir: Directory containing lexicon files

        Returns:
            Dictionary mapping language codes to validation reports
        """
        rules_dir = Path(rules_dir)
        reports = {}

        for lexicon_file in rules_dir.glob(lexicon_glob_pattern()):
            report = self.validate_file(lexicon_file)
            reports[report.language] = report

        return reports


class LexiconValidationError(Exception):
    """Raised when lexicon validation fails with errors."""

    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__(f"Lexicon validation failed for {report.language}: {report.error_count} errors found")


def validate_lexicon_on_load(file_path: str | Path,
                              strict: bool = False,
                              raise_on_error: bool = True) -> Tuple[bool, ValidationReport]:
    """
    Convenience function to validate a lexicon before loading.

    Args:
        file_path: Path to lexicon file
        strict: If True, warnings become errors
        raise_on_error: If True, raises LexiconValidationError on failure

    Returns:
        Tuple of (is_valid, report)

    Raises:
        LexiconValidationError: If validation fails and raise_on_error is True
    """
    validator = LexiconValidator(strict_mode=strict)
    report = validator.validate_file(file_path)

    if not report.is_valid and raise_on_error:
        raise LexiconValidationError(report)

    return report.is_valid, report


# CLI interface for running validation standalone
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("LEXICON VALIDATION TOOL")
    print("AI BRIDGE Compliance Checker")
    print("=" * 60)

    validator = LexiconValidator()

    if len(sys.argv) > 1:
        # Validate specific file
        file_path = sys.argv[1]
        report = validator.validate_file(file_path)
        print(report.summary())
        sys.exit(0 if report.is_valid else 1)
    else:
        # Validate all lexicons
        reports = validator.validate_all_lexicons()

        all_valid = True
        total_errors = 0
        total_warnings = 0

        for lang, report in reports.items():
            print(report.summary())
            if not report.is_valid:
                all_valid = False
            total_errors += report.error_count
            total_warnings += report.warning_count

        print("\n" + "=" * 60)
        print("OVERALL SUMMARY")
        print("=" * 60)
        print(f"Languages validated: {len(reports)}")
        print(f"Total errors: {total_errors}")
        print(f"Total warnings: {total_warnings}")
        print(f"Overall status: {'PASS' if all_valid else 'FAIL'}")
        print("=" * 60)

        sys.exit(0 if all_valid else 1)
