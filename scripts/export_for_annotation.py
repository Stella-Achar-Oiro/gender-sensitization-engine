"""Export rows for Claude annotation.

Usage:
    # Export 50 rows missing expected_correction (default)
    python3 scripts/export_for_annotation.py

    # Export a specific batch size, starting at offset
    python3 scripts/export_for_annotation.py --batch 100 --offset 0

    # Export overlapping 10% sample for Kappa (same rows for annotator 2)
    python3 scripts/export_for_annotation.py --kappa-set

Outputs a CSV to stdout — paste directly into the annotation prompt.
"""
import argparse
import csv
import sys
from pathlib import Path

GT_FILE = Path("eval/ground_truth_sw_v5.csv")
KAPPA_SEED_FILE = Path("data/analysis/kappa_overlap_ids.txt")


def load_rows() -> list[dict]:
    with GT_FILE.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def needs_annotation(row: dict) -> bool:
    return (
        row.get("has_bias", "").lower() == "true"
        and not row.get("expected_correction", "").strip()
    )


def export_csv(rows: list[dict]) -> None:
    if not rows:
        print("No rows to export.", file=sys.stderr)
        sys.exit(1)
    writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=50, help="Rows per batch")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N candidates")
    parser.add_argument("--kappa-set", action="store_true",
                        help="Export the fixed 10%% overlap set for inter-annotator Kappa")
    args = parser.parse_args()

    all_rows = load_rows()

    if args.kappa_set:
        if not KAPPA_SEED_FILE.exists():
            print(f"Kappa seed file not found: {KAPPA_SEED_FILE}", file=sys.stderr)
            print("Run with --batch first to generate the overlap set.", file=sys.stderr)
            sys.exit(1)
        ids = set(KAPPA_SEED_FILE.read_text().splitlines())
        batch = [r for r in all_rows if r["id"] in ids]
        print(f"Exporting {len(batch)} kappa-overlap rows.", file=sys.stderr)
        export_csv(batch)
        return

    candidates = [r for r in all_rows if needs_annotation(r)]
    total = len(candidates)
    batch = candidates[args.offset: args.offset + args.batch]

    print(
        f"Candidates: {total} | offset: {args.offset} | exporting: {len(batch)}",
        file=sys.stderr,
    )

    # Save kappa overlap set on first batch (first 10% of batch, min 5)
    if args.offset == 0 and not KAPPA_SEED_FILE.exists():
        KAPPA_SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
        overlap_n = max(5, len(batch) // 10)
        overlap_ids = [r["id"] for r in batch[:overlap_n]]
        KAPPA_SEED_FILE.write_text("\n".join(overlap_ids))
        print(
            f"Saved {overlap_n} kappa-overlap IDs to {KAPPA_SEED_FILE}",
            file=sys.stderr,
        )

    export_csv(batch)


if __name__ == "__main__":
    main()
