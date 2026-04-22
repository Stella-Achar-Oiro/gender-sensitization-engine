import json
from pathlib import Path

REVIEWS = Path("audit_logs/reviews.jsonl")
approved = 0
total = 0

if REVIEWS.exists():
    for line in REVIEWS.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            total += 1
            if r["action"] in ("approve", "approve_with_edit"):
                approved += 1
        except:
            pass

print(f"Total reviews: {total}")
print(f"Approved: {approved}")
print(f"Acceptance rate: {approved/total:.3f}" if total else "Acceptance rate: N/A")
