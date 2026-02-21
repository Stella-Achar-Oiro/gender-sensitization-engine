"""Audit log writer — appends every correction to rewrites.jsonl."""

import json
import uuid
from pathlib import Path
from datetime import datetime

AUDIT_FILE = Path(__file__).resolve().parent.parent / "audit_logs" / "rewrites.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)


def log(entry: dict) -> None:
    entry["audit_id"] = str(uuid.uuid4())
    entry["timestamp"] = datetime.utcnow().isoformat()
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
