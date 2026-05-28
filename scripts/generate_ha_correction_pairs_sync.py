#!/Users/stellaoiro/open-chat-studio/.venv/bin/python3
"""
Generate Hausa correction pairs synchronously (no batch API).

Reads 2,169 stereotype rows from v3_revised_hausa_bias_ds.csv, calls Claude
directly for each row, writes juakazi_ha_correction_pairs_v1.csv.

Cost estimate: ~$1.62 (Haiku 4.5, standard pricing)
Runtime: ~15-25 minutes

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 scripts/generate_ha_correction_pairs_sync.py
"""

import anthropic
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "v3_revised_hausa_bias_ds.csv"
OUTPUT_CSV = ROOT / "juakazi_ha_correction_pairs_v1.csv"

MODEL = "claude-haiku-4-5"

SYSTEM = """You are a Hausa gender bias correction specialist. Your task is to rewrite biased Hausa sentences to remove gender stereotypes while preserving the original meaning and natural Hausa expression.

Rules:
1. Remove male-default assumptions in professional roles (e.g., replace gendered role assumptions with neutral ones)
2. Remove sentences that imply women are less capable in professional settings
3. Replace gender-specific terms with neutral alternatives when the gender is not relevant
4. Keep the sentence natural and fluent Hausa — do not over-translate
5. If the sentence is too short or lacks context for a meaningful correction, write a neutral version that removes the bias
6. Return ONLY the corrected Hausa sentence, nothing else — no explanation, no prefix"""

FIELDNAMES = ["id", "original_text", "corrected_text", "stereotype_category",
              "explicitness", "domain", "source", "qa_status"]


def load_stereotype_rows():
    with open(INPUT_CSV) as f:
        return [r for r in csv.DictReader(f) if r.get("bias_label", "") == "stereotype"]


def load_done_ids():
    if not OUTPUT_CSV.exists():
        return set()
    with open(OUTPUT_CSV) as f:
        return {r["id"] for r in csv.DictReader(f)}


def main():
    client = anthropic.Anthropic()
    rows = load_stereotype_rows()
    print(f"Loaded {len(rows)} stereotype rows")

    done_ids = load_done_ids()
    if done_ids:
        print(f"Resuming — {len(done_ids)} already done, skipping")

    remaining = [r for r in rows if r["id"] not in done_ids]
    print(f"Generating {len(remaining)} corrections...")

    # Open in append mode so we can resume if interrupted
    mode = "a" if done_ids else "w"
    with open(OUTPUT_CSV, mode, newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if mode == "w":
            w.writeheader()

        errors = 0
        for i, row in enumerate(remaining, 1):
            text = row["text"].strip()
            if not text:
                continue

            try:
                msg = client.messages.create(
                    model=MODEL,
                    max_tokens=512,
                    system=SYSTEM,
                    messages=[{
                        "role": "user",
                        "content": f"Rewrite this biased Hausa sentence to remove gender bias:\n\n{text}"
                    }]
                )
                corrected = next((b.text.strip() for b in msg.content if b.type == "text"), "")

                if corrected and corrected != text:
                    w.writerow({
                        "id": row["id"],
                        "original_text": text,
                        "corrected_text": corrected,
                        "stereotype_category": row.get("stereotype_category", ""),
                        "explicitness": row.get("explicitness", ""),
                        "domain": row.get("domain", ""),
                        "source": "claude-haiku-draft",
                        "qa_status": "needs_review",
                    })
                    f.flush()

                if i % 50 == 0:
                    print(f"  {i}/{len(remaining)} done ({errors} errors so far)")

            except Exception as e:
                errors += 1
                print(f"  Error on row {row['id']}: {e}", file=sys.stderr)
                time.sleep(2)

    print(f"Done. Written to {OUTPUT_CSV} ({errors} errors/skipped)")


if __name__ == "__main__":
    main()
