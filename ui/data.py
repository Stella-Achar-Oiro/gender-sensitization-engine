"""Audit log I/O — load rewrites, save review decisions."""

import json
import uuid
from pathlib import Path
from datetime import datetime

REWRITES = Path("../audit_logs/rewrites.jsonl")
REVIEWS = Path("../audit_logs/reviews.jsonl")
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
