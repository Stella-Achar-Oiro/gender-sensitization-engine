#!/Users/stellaoiro/open-chat-studio/.venv/bin/python3
"""
Generate Hausa correction pairs using Claude Batch API.

Reads 2,169 stereotype rows from v3_revised_hausa_bias_ds.csv, submits them
as a batch job, polls until done, then writes juakazi_ha_correction_pairs_v1.csv.

Cost estimate: ~$0.81 (Haiku 4.5 batch, 50% discount)

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 scripts/generate_ha_correction_pairs.py          # submit + poll + collect
    python3 scripts/generate_ha_correction_pairs.py --poll <batch_id>
    python3 scripts/generate_ha_correction_pairs.py --collect <batch_id>
"""

import anthropic
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "v3_revised_hausa_bias_ds.csv"
OUTPUT_CSV = ROOT / "juakazi_ha_correction_pairs_v1.csv"
STATE_FILE = ROOT / ".ha_batch_id"

MODEL = "claude-haiku-4-5"

SYSTEM = """You are a Hausa gender bias correction specialist. Your task is to rewrite biased Hausa sentences to remove gender stereotypes while preserving the original meaning and natural Hausa expression.

Rules:
1. Remove male-default assumptions in professional roles (e.g., replace gendered role assumptions with neutral ones)
2. Remove sentences that imply women are less capable in professional settings
3. Replace gender-specific terms with neutral alternatives when the gender is not relevant
4. Keep the sentence natural and fluent Hausa — do not over-translate
5. If the sentence is too short or lacks context for a meaningful correction, write a neutral version that removes the bias
6. Return ONLY the corrected Hausa sentence, nothing else — no explanation, no prefix"""

def load_stereotype_rows():
    with open(INPUT_CSV) as f:
        return [r for r in csv.DictReader(f) if r.get("bias_label", "") == "stereotype"]

def build_requests(rows):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    requests = []
    for r in rows:
        text = r["text"].strip()
        if not text:
            continue
        requests.append(Request(
            custom_id=r["id"],
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=512,
                system=SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"Rewrite this biased Hausa sentence to remove gender bias:\n\n{text}"
                }]
            )
        ))
    return requests

def submit_batch(client, rows):
    requests = build_requests(rows)
    print(f"Submitting {len(requests)} requests...")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch ID: {batch.id}")
    STATE_FILE.write_text(batch.id)
    print(f"Saved to {STATE_FILE}")
    return batch.id

def poll_batch(client, batch_id):
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(f"  Status: {batch.processing_status} | processing={counts.processing} succeeded={counts.succeeded} errored={counts.errored}")
        if batch.processing_status == "ended":
            return batch
        time.sleep(30)

def collect_results(client, batch_id, rows):
    row_map = {r["id"]: r for r in rows}
    pairs = []
    errors = 0

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            msg = result.result.message
            corrected = next((b.text.strip() for b in msg.content if b.type == "text"), "")
            original_row = row_map.get(result.custom_id, {})
            original_text = original_row.get("text", "").strip()

            if corrected and corrected != original_text:
                pairs.append({
                    "id": result.custom_id,
                    "original_text": original_text,
                    "corrected_text": corrected,
                    "stereotype_category": original_row.get("stereotype_category", ""),
                    "explicitness": original_row.get("explicitness", ""),
                    "domain": original_row.get("domain", ""),
                    "source": "claude-haiku-draft",
                    "qa_status": "needs_review",
                })
        else:
            errors += 1

    print(f"Collected {len(pairs)} pairs ({errors} errors/unchanged)")
    return pairs

def write_output(pairs):
    if not pairs:
        print("No pairs to write.")
        return

    fieldnames = ["id", "original_text", "corrected_text", "stereotype_category",
                  "explicitness", "domain", "source", "qa_status"]
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(pairs)
    print(f"Written {len(pairs)} pairs to {OUTPUT_CSV}")

def main():
    client = anthropic.Anthropic()
    rows = load_stereotype_rows()
    print(f"Loaded {len(rows)} stereotype rows")

    # --poll <batch_id> or --collect <batch_id>
    if len(sys.argv) >= 3 and sys.argv[1] == "--poll":
        batch_id = sys.argv[2]
        poll_batch(client, batch_id)
        return

    if len(sys.argv) >= 3 and sys.argv[1] == "--collect":
        batch_id = sys.argv[2]
        pairs = collect_results(client, batch_id, rows)
        write_output(pairs)
        return

    # Full run: submit → poll → collect
    batch_id = submit_batch(client, rows)
    print("Polling (every 30s)...")
    poll_batch(client, batch_id)
    pairs = collect_results(client, batch_id, rows)
    write_output(pairs)

if __name__ == "__main__":
    main()
