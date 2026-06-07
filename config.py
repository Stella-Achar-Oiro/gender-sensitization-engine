"""Project-wide configuration helpers.

Centralizes data version tags, rewrite thresholds, and confidence defaults.
Override via env: JUAKAZI_SEMANTIC_THRESHOLD (float, default 0.70).
"""
from __future__ import annotations

import os


class DataVersions:
    """Active version identifiers for dataset artifacts."""

    LEXICON: str = "v3"
    GROUND_TRUTH: str = "v5"  # default for en, sw, fr

    # Per-language lexicon file versions (Hausa/Zulu initial packs use v1 filenames)
    LEXICON_BY_LANG: dict = {
        "ha": "v2",
        "zu": "v2",
    }

    # Per-language overrides (Kikuyu is ahead of the default version)
    GROUND_TRUTH_BY_LANG: dict = {
        "ki": "v8",
        "ha": "v2",
        "zu": "v2",
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
    current_version = version or DataVersions.LEXICON_BY_LANG.get(
        language_code, DataVersions.LEXICON
    )
    return f"lexicon_{language_code}_{current_version}.csv"


def ground_truth_filename(language_code: str, version: str | None = None) -> str:
    """Build the ground truth filename for a given language code."""
    if version is None:
        version = DataVersions.GROUND_TRUTH_BY_LANG.get(
            language_code, DataVersions.GROUND_TRUTH
        )
    return f"ground_truth_{language_code}_{version}.csv"


def lexicon_glob_pattern(version: str | None = None) -> str:
    """Return a glob pattern that matches lexicon CSVs in rules/ (all active versions)."""
    if version is not None:
        return f"lexicon_*_{version}.csv"
    return "lexicon_*.csv"


# ---------------------------------------------------------------------------
# Rewrite / correction (API)
# ---------------------------------------------------------------------------

def get_semantic_threshold() -> float:
    """Semantic preservation threshold below which we keep original text. Default 0.70."""
    raw = os.environ.get("JUAKAZI_SEMANTIC_THRESHOLD", "0.70")
    try:
        return float(raw)
    except ValueError:
        return 0.70


# Confidence by rewrite source (for API response)
# "aibridge_preserved" = external AIBRIDGE classifier said no bias; text returned unchanged
REWRITE_CONFIDENCE_BY_SOURCE: dict[str, float] = {
    "rules": 0.85,
    "ml": 0.60,
    "preserved": 0.95,
    "disambiguated": 0.80,
    "aibridge_preserved": 0.90,
    "low_confidence": 0.30,
}
DEFAULT_REWRITE_CONFIDENCE: float = 0.85

# ---------------------------------------------------------------------------
# AIBRIDGE external Bias Detection API
# ---------------------------------------------------------------------------

AIBRIDGE_BASE_URL: str = os.getenv(
    "AIBRIDGE_BASE_URL",
    "https://aibridgebiasdetector-158985802014.us-central1.run.app",
)
AIBRIDGE_TIMEOUT: float = float(os.getenv("AIBRIDGE_TIMEOUT", "120.0"))  # 2 min covers cold start
AIBRIDGE_CONFIDENCE_THRESHOLD: float = float(os.getenv("AIBRIDGE_CONFIDENCE_THRESHOLD", "0.5"))
# Set AIBRIDGE_ENABLED=false to disable the external gate and use internal pipeline only
AIBRIDGE_ENABLED: bool = os.getenv("AIBRIDGE_ENABLED", "true").lower() == "true"
