"""Merge Claude annotation output back into the ground truth CSV.

Usage:
    python3 scripts/merge_annotations.py < /tmp/batch_002_annotated.json

The input JSON must be an array of objects with at least an "id" field plus
any fields to update. Only the fields present in each annotation object are
written — other columns in the CSV are preserved unchanged.

Updatable fields (subset of AIBRIDGE 24-column schema):
    has_bias, target_gender, bias_label, stereotype_category, explicitness,
    expected_correction, annotator_confidence, annotator_notes, qa_status,
    annotator_id, region_dialect, pii_removed, safety_flag

Typical annotation object shape:
    {
      "id": "sw-03295",
      "has_bias": "true",
      "target_gender": "female",
      "bias_label": "stereotype",
      "stereotype_category": "occupation",
      "explicitness": "explicit",
      "expected_correction": "wanafunzi wanaofeli ni wanafunzi wengi",
      "annotator_confidence": "high",
      "annotator_notes": "occupation stereotype; corrected to gender-neutral",
      "qa_status": "passed"
    }
"""
import csv
import json
import sys
from pathlib import Path

GT_FILE = Path("eval/ground_truth_sw_v5.csv")

UPDATABLE = {
    "has_bias", "target_gender", "bias_label", "stereotype_category",
    "explicitness", "expected_correction", "annotator_confidence",
    "annotator_notes", "qa_status", "annotator_id", "region_dialect",
    "pii_removed", "safety_flag",
}


def main() -> None:
    raw = sys.stdin.read().strip()
    # Strip markdown code fences if Claude wrapped the JSON
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            l for l in lines if not l.startswith("```")
        ).strip()

    annotations: list[dict] = json.loads(raw)
    ann_by_id = {a["id"]: a for a in annotations if "id" in a}

    rows = []
    with GT_FILE.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    updated = 0
    for row in rows:
        ann = ann_by_id.get(row["id"])
        if ann is None:
            continue
        for field in UPDATABLE:
            if field in ann and ann[field] is not None:
                row[field] = str(ann[field]).lower() if field == "has_bias" else str(ann[field])
        updated += 1

    with GT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {updated} / {len(ann_by_id)} annotation rows into {GT_FILE}",
          file=sys.stderr)

    # Remaining candidates after merge
    needs = sum(
        1 for r in rows
        if r.get("has_bias", "").lower() == "true"
        and not r.get("expected_correction", "").strip()
    )
    print(f"Remaining rows needing expected_correction: {needs}", file=sys.stderr)


if __name__ == "__main__":
    main()
