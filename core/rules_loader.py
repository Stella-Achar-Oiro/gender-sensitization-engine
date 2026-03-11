"""Single rule loader for lexicon CSV. Used by api and eval."""

import csv
from pathlib import Path
from typing import Optional

# Project root = parent of core/
_BASE = Path(__file__).resolve().parent.parent


def load_rules(lang: str, rules_dir: Optional[Path] = None) -> list[dict]:
    """
    Load lexicon rules for a language. Returns list of row dicts (all columns as str).

    Args:
        lang: Language code (en, sw, fr, ki).
        rules_dir: Directory containing lexicon_*_v3.csv. Defaults to project rules/.

    Returns:
        List of dicts with keys from CSV (biased, neutral_primary, severity, avoid_when, etc.).
    """
    from config import lexicon_filename

    rules_dir = rules_dir or (_BASE / "rules")
    path = rules_dir / lexicon_filename(lang)
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: str(v or "") for k, v in row.items()})
    return rows
