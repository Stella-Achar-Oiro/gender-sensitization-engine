"""Audit log I/O — load rewrites, save review decisions, load stats."""

import csv
import json
import uuid
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
REWRITES = BASE / "audit_logs" / "rewrites.jsonl"
RULES_DIR = BASE / "rules"
RESULTS_DIR = BASE / "eval" / "results"
REVIEWS = BASE / "audit_logs" / "reviews.jsonl"
REVIEWS.parent.mkdir(parents=True, exist_ok=True)


def load_rewrites() -> list:
    if not REWRITES.exists():
        return []
    items = []
    for line in REWRITES.read_text(encoding="utf-8").splitlines():
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return list(reversed(items))


def save_review(
    audit_id: str,
    action: str,
    reviewer: str,
    comment: str = "",
    edited_rewrite: str = None,
    chosen_candidate: str = None,
    flagged_reason: str = None,
) -> None:
    review = {
        "review_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "audit_id": audit_id,
        "action": action,
        "reviewer": reviewer,
        "comment": comment,
    }
    if edited_rewrite:
        review["edited_rewrite"] = edited_rewrite
    if chosen_candidate:
        review["chosen_candidate"] = chosen_candidate
    if flagged_reason:
        review["flagged_reason"] = flagged_reason
    with open(REVIEWS, "a", encoding="utf-8") as f:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")


def load_stats() -> dict:
    """Return latest F1 metrics per language + lexicon sizes."""
    # Latest F1 report
    reports = sorted(RESULTS_DIR.glob("f1_report_*.csv"))
    metrics: dict[str, dict] = {}
    if reports:
        for row in csv.DictReader(reports[-1].open(encoding="utf-8")):
            if row["Category"] == "OVERALL":
                lang = row["Language"].lower()
                metrics[lang] = {
                    "precision": float(row["Precision"]),
                    "recall": float(row["Recall"]),
                    "f1": float(row["F1_Score"]),
                }

    # Lexicon sizes
    lexicon_sizes: dict[str, int] = {}
    for f in RULES_DIR.glob("lexicon_*_v3.csv"):
        lang = f.stem.split("_")[1]
        with f.open(encoding="utf-8") as fh:
            lexicon_sizes[lang] = sum(1 for _ in csv.reader(fh)) - 1  # exclude header

    return {"metrics": metrics, "lexicon_sizes": lexicon_sizes}
