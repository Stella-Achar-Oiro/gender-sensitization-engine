#!/usr/bin/env python3
"""
Merge all Zulu training data sources into one file for training.

Sources:
  - IsiZulu_Ithute_Dataset_Final.csv  (9,570 biased rows)
  - eval/ground_truth_zu_v1.csv       (2,000 rows — mixed)
  - data/neutral_zu_v1.csv            (3,000 neutral rows)

Output: data/ground_truth_zu_merged_v1.csv
Schema: id, language, text, has_bias, bias_label, source

Usage:
    python3 scripts/merge_zu_training_data.py
"""

import csv
from pathlib import Path

ROOT   = Path(__file__).parent.parent
OUTPUT = ROOT / "data" / "ground_truth_zu_merged_v1.csv"
OUTPUT.parent.mkdir(exist_ok=True)

FIELDNAMES = ["id", "language", "text", "has_bias", "bias_label", "source"]


def main():
    all_rows   = []
    seen_texts = set()

    # ── Source 1: IsiZulu Ithute (biased rows) ────────────────────────────────
    path = ROOT / "IsiZulu_Ithute_Dataset_Final.csv"
    with open(path, encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f)):
            text = r.get("Zulu text", r.get("text", "")).strip()
            bl   = r.get("bias_label", "").lower().strip()
            if not text or text in seen_texts:
                continue
            if bl not in ("stereotype", "derogation"):
                continue
            seen_texts.add(text)
            all_rows.append({
                "id":         f"ZU-IT-{i:06d}",
                "language":   "zu",
                "text":       text,
                "has_bias":   "true",
                "bias_label": bl,
                "source":     "IsiZulu_Ithute",
            })

    print(f"IsiZulu Ithute: {len(all_rows)} biased rows loaded")

    # ── Source 2: Ground truth v1 ─────────────────────────────────────────────
    path = ROOT / "eval" / "ground_truth_zu_v1.csv"
    gt_added = 0
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                text = r.get("text", "").strip()
                hb   = str(r.get("has_bias", "")).strip().lower()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)
                is_biased = hb in ("true", "1", "yes")
                all_rows.append({
                    "id":         r.get("id", f"ZU-GT-{gt_added:06d}"),
                    "language":   "zu",
                    "text":       text,
                    "has_bias":   "true" if is_biased else "false",
                    "bias_label": "stereotype" if is_biased else "neutral",
                    "source":     "ground_truth_zu_v1",
                })
                gt_added += 1
    print(f"Ground truth v1: {gt_added} rows added")

    # ── Source 3: Generated neutral rows ─────────────────────────────────────
    path = ROOT / "data" / "neutral_zu_v1.csv"
    neutral_added = 0
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                text = r.get("text", "").strip()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)
                all_rows.append({
                    "id":         r.get("id", f"ZU-NEU-{neutral_added:06d}"),
                    "language":   "zu",
                    "text":       text,
                    "has_bias":   "false",
                    "bias_label": "neutral",
                    "source":     r.get("source_ref", "cc100/zu"),
                })
                neutral_added += 1
    print(f"Neutral rows: {neutral_added} rows added")

    # ── Summary ──────────────────────────────────────────────────────────────
    biased  = sum(1 for r in all_rows if r["has_bias"] == "true")
    neutral = sum(1 for r in all_rows if r["has_bias"] == "false")
    print(f"\nTotal: {len(all_rows):,} unique rows")
    print(f"  Biased:  {biased:,}")
    print(f"  Neutral: {neutral:,}")
    print(f"  Ratio:   {biased/max(neutral,1):.1f}:1 biased")

    # ── Write output ─────────────────────────────────────────────────────────
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWritten to {OUTPUT}")
    print("Upload this file to Drive at MyDrive/juakazi/ before running train_zu_bias_v1.ipynb")


if __name__ == "__main__":
    main()
