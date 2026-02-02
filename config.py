"""Project-wide configuration helpers.

Centralizes data version tags so file naming stays consistent.
"""
from __future__ import annotations


class DataVersions:
    """Active version identifiers for dataset artifacts."""

    LEXICON: str = "v3"
    GROUND_TRUTH: str = "v4"


def lexicon_filename(language_code: str, version: str | None = None) -> str:
    """Build the lexicon filename for a given language code."""
    current_version = version or DataVersions.LEXICON
    return f"lexicon_{language_code}_{current_version}.csv"


def ground_truth_filename(language_code: str, version: str | None = None) -> str:
    """Build the ground truth filename for a given language code."""
    current_version = version or DataVersions.GROUND_TRUTH
    return f"ground_truth_{language_code}_{current_version}.csv"


def lexicon_glob_pattern(version: str | None = None) -> str:
    """Return a glob pattern that matches lexicons for the active version."""
    current_version = version or DataVersions.LEXICON
    return f"lexicon_*_{current_version}.csv"
