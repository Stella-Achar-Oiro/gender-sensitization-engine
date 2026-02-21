"""Project-wide configuration helpers.

Centralizes data version tags so file naming stays consistent.
"""
from __future__ import annotations


class DataVersions:
    """Active version identifiers for dataset artifacts."""

    LEXICON: str = "v3"
    GROUND_TRUTH: str = "v5"  # default for en, sw, fr

    # Per-language overrides (Kikuyu is ahead of the default version)
    GROUND_TRUTH_BY_LANG: dict = {
        "ki": "v8",
    }


class RegionDialects:
    """Known region/dialect tags for data collection and audit logging.

    Used in:
    - API request: region_dialect field
    - Ground truth CSV: regional_variant column (AIBRIDGE schema)
    - Audit logs: region_dialect field

    Add new tags here as new dialects/regions are covered.
    """
    KENYA = "kenya"
    TANZANIA = "tanzania"
    UGANDA = "uganda"
    SHENG = "sheng"          # Nairobi urban youth mix (SW+EN)
    COASTAL_SW = "coastal"   # Mombasa/Zanzibar coastal Swahili
    UNKNOWN = "unknown"

    ALL: list = [KENYA, TANZANIA, UGANDA, SHENG, COASTAL_SW, UNKNOWN]


def lexicon_filename(language_code: str, version: str | None = None) -> str:
    """Build the lexicon filename for a given language code."""
    current_version = version or DataVersions.LEXICON
    return f"lexicon_{language_code}_{current_version}.csv"


def ground_truth_filename(language_code: str, version: str | None = None) -> str:
    """Build the ground truth filename for a given language code."""
    if version is None:
        version = DataVersions.GROUND_TRUTH_BY_LANG.get(
            language_code, DataVersions.GROUND_TRUTH
        )
    return f"ground_truth_{language_code}_{version}.csv"


def lexicon_glob_pattern(version: str | None = None) -> str:
    """Return a glob pattern that matches lexicons for the active version."""
    current_version = version or DataVersions.LEXICON
    return f"lexicon_*_{current_version}.csv"
