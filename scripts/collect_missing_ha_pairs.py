#!/Users/stellaoiro/open-chat-studio/.venv/bin/python3
"""
Collect missing HA correction pairs from batch results, deduplicate, rewrite clean CSV.
"""

import anthropic
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "v3_revised_hausa_bias_ds.csv"
OUTPUT_CSV = ROOT / "juakazi_ha_correction_pairs_v1.csv"
BATCH_ID = "msgbatch_01XQUw9rDUnegpGEh6b1e3QP"

FIELDNAMES = ["id", "original_text", "corrected_text", "stereotype_category",
              "explicitness", "domain", "source", "qa_status"]


def load_stereotype_rows():
    with open(INPUT_CSV) as f:
        return {r["id"]: r for r in csv.DictReader(f) if r.get("bias_label", "") == "stereotype"}


def main():
    client = anthropic.Anthropic()
    row_map = load_stereotype_rows()

    # Load existing pairs, dedup by id (keep first occurrence)
    existing = {}
    with open(OUTPUT_CSV) as f:
        for r in csv.DictReader(f):
            if r["id"] not in existing:
                existing[r["id"]] = r

    done_ids = set(existing.keys())
    missing_ids = set(row_map.keys()) - done_ids
    print(f"Existing unique pairs: {len(done_ids)}, Missing: {len(missing_ids)}")

    added = 0
    for result in client.messages.batches.results(BATCH_ID):
        if result.custom_id not in missing_ids:
            continue
        if result.result.type != "succeeded":
            continue
        msg = result.result.message
        corrected = next((b.text.strip() for b in msg.content if b.type == "text"), "")
        original_row = row_map.get(result.custom_id, {})
        original_text = original_row.get("text", "").strip()
        if corrected and corrected != original_text:
            existing[result.custom_id] = {
                "id": result.custom_id,
                "original_text": original_text,
                "corrected_text": corrected,
                "stereotype_category": original_row.get("stereotype_category", ""),
                "explicitness": original_row.get("explicitness", ""),
                "domain": original_row.get("domain", ""),
                "source": "claude-haiku-draft",
                "qa_status": "needs_review",
            }
            added += 1

    # Rewrite clean deduplicated file
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(existing.values())

    print(f"Added {added} from batch. Final total: {len(existing)} pairs written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
