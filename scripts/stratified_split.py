#!/usr/bin/env python3
"""
Stratified train/val split with BIAS oversampling for classifier training.

Loads ground truth CSV, splits 80/20 by has_bias, oversamples biased samples
in the train set to ~25% (recommended for imbalanced bias detection).
Writes train/val CSV splits and a summary JSON.

Usage:
    python scripts/stratified_split.py --language sw
    python scripts/stratified_split.py --language sw --out-dir data/splits
    python scripts/stratified_split.py --language sw --val-ratio 0.2 --bias-ratio 0.25

Requires: ground truth CSV in eval/ (e.g. eval/ground_truth_sw_v5.csv).
Output: eval/results/splits/{lang}_train.csv, {lang}_val.csv, {lang}_split_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

# Project root for config import when run as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def load_ground_truth_rows(data_dir: Path, lang: str, gt_filename: str) -> list[dict]:
    """Load ground truth CSV into list of row dicts; preserve all columns."""
    path = data_dir / gt_filename
    if not path.exists():
        raise FileNotFoundError(f"Ground truth not found: {path}")
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            row = {k: (v or "").strip().strip('"') for k, v in row.items()}
            rows.append(row)
    return rows, list(fieldnames)


def get_has_bias(row: dict) -> bool:
    return (row.get("has_bias") or "").lower() == "true"


def stratified_split_indices(
    n: int,
    has_bias_list: list[bool],
    val_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[list[int], list[int]]:
    """Return (train_indices, val_indices) stratified by has_bias."""
    rng = random.Random(seed)
    biased_idx = [i for i in range(n) if has_bias_list[i]]
    neutral_idx = [i for i in range(n) if not has_bias_list[i]]
    rng.shuffle(biased_idx)
    rng.shuffle(neutral_idx)
    n_val_biased = max(1, int(len(biased_idx) * val_ratio))
    n_val_neutral = max(1, int(len(neutral_idx) * val_ratio))
    val_idx = biased_idx[-n_val_biased:] + neutral_idx[-n_val_neutral:]
    train_idx = biased_idx[:-n_val_biased] + neutral_idx[:-n_val_neutral]
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return train_idx, val_idx


def oversample_to_bias_ratio(
    train_indices: list[int],
    has_bias_list: list[bool],
    target_bias_ratio: float = 0.25,
    seed: int = 42,
) -> list[int]:
    """Oversample biased samples in train so biased fraction ≈ target_bias_ratio."""
    rng = random.Random(seed)
    train_biased = [i for i in train_indices if has_bias_list[i]]
    train_neutral = [i for i in train_indices if not has_bias_list[i]]
    n_neutral = len(train_neutral)
    # target: n_biased / (n_biased + n_neutral) = target_bias_ratio
    # => n_biased = target_bias_ratio * n_neutral / (1 - target_bias_ratio)
    target_biased = int(n_neutral * target_bias_ratio / (1 - target_bias_ratio))
    if not train_biased or target_biased <= len(train_biased):
        return train_indices
    extra = target_biased - len(train_biased)
    added = rng.choices(train_biased, k=extra)
    out = train_indices + added
    rng.shuffle(out)
    return out


def main() -> None:
    from config import ground_truth_filename

    parser = argparse.ArgumentParser(
        description="Stratified train/val split with BIAS oversampling for ML training."
    )
    parser.add_argument(
        "--language",
        "-l",
        default="sw",
        choices=("en", "sw", "fr", "ki"),
        help="Language code (default: sw)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("eval"),
        help="Directory containing ground truth CSV (default: eval)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("eval/results/splits"),
        help="Output directory for train/val CSVs (default: eval/results/splits)",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Validation fraction (default: 0.2)",
    )
    parser.add_argument(
        "--bias-ratio",
        type=float,
        default=0.25,
        help="Target biased fraction in train after oversampling (default: 0.25)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    gt_filename = ground_truth_filename(args.language)
    rows, fieldnames = load_ground_truth_rows(data_dir, args.language, gt_filename)
    if not rows:
        raise SystemExit("No rows loaded")

    has_bias_list = [get_has_bias(r) for r in rows]
    n = len(rows)
    n_biased = sum(has_bias_list)

    train_idx, val_idx = stratified_split_indices(
        n, has_bias_list, val_ratio=args.val_ratio, seed=args.seed
    )
    train_idx = oversample_to_bias_ratio(
        train_idx, has_bias_list, target_bias_ratio=args.bias_ratio, seed=args.seed
    )

    train_rows = [rows[i] for i in train_idx]
    val_rows = [rows[i] for i in val_idx]
    n_train_biased = sum(1 for i in train_idx if has_bias_list[i])
    n_val_biased = sum(1 for i in val_idx if has_bias_list[i])

    train_path = out_dir / f"{args.language}_train.csv"
    val_path = out_dir / f"{args.language}_val.csv"
    summary_path = out_dir / f"{args.language}_split_summary.json"

    for path, subset in [(train_path, train_rows), (val_path, val_rows)]:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(subset)
        print(f"Wrote {path} ({len(subset)} rows)")

    summary = {
        "language": args.language,
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "target_bias_ratio_train": args.bias_ratio,
        "total_samples": n,
        "total_biased": n_biased,
        "train_size": len(train_idx),
        "train_biased": n_train_biased,
        "train_biased_ratio": round(n_train_biased / len(train_idx), 4) if train_idx else 0,
        "val_size": len(val_idx),
        "val_biased": n_val_biased,
        "val_biased_ratio": round(n_val_biased / len(val_idx), 4) if val_idx else 0,
        "paths": {"train": str(train_path), "val": str(val_path)},
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {summary_path}")
    print(
        f"Train: {len(train_idx)} rows, {n_train_biased} biased ({100 * n_train_biased / len(train_idx):.1f}%)"
    )
    print(
        f"Val:   {len(val_idx)} rows, {n_val_biased} biased ({100 * n_val_biased / len(val_idx):.1f}%)"
    )


if __name__ == "__main__":
    main()
