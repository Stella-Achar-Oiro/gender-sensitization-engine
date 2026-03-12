"""Compute Cohen's Kappa from two annotator CSV files.

Usage:
    python3 scripts/compute_kappa.py \\
        --annotator_a data/annotation_export/batch_for_annotator_A_reference.csv \\
        --annotator_b data/annotation_export/batch_for_annotator_B_kappa_overlap_RETURNED.csv \\
        --output eval/results/kappa_batch_024.json

Both CSVs must have columns: id, has_bias (and optionally target_gender,
stereotype_category, explicitness). Only rows whose `id` appears in BOTH
files are used for the kappa calculation (the overlap set).

Target: Cohen's Kappa >= 0.70 on has_bias to unlock AIBRIDGE Bronze IAA tier.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

try:
    from sklearn.metrics import cohen_kappa_score
except ImportError:
    print("ERROR: scikit-learn not installed. Run: pip install scikit-learn --break-system-packages")
    sys.exit(1)


def load_csv(path: str) -> dict[str, dict]:
    """Load CSV and return dict keyed by row id."""
    rows = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row_id = row.get("id", "").strip()
            if row_id:
                rows[row_id] = row
    return rows


def normalize_has_bias(val: str) -> int:
    """Convert has_bias string to 0/1."""
    v = val.strip().lower()
    if v in ("true", "yes", "1"):
        return 1
    if v in ("false", "no", "0"):
        return 0
    return -1  # invalid / missing


def compute_kappa(a_path: str, b_path: str, output_path: str | None = None) -> None:
    a_rows = load_csv(a_path)
    b_rows = load_csv(b_path)

    # Only overlap rows
    overlap_ids = sorted(set(a_rows.keys()) & set(b_rows.keys()))

    if len(overlap_ids) == 0:
        print("ERROR: No overlapping row IDs found between the two files.")
        print(f"  File A IDs (sample): {list(a_rows.keys())[:5]}")
        print(f"  File B IDs (sample): {list(b_rows.keys())[:5]}")
        sys.exit(1)

    print(f"Overlap rows: {len(overlap_ids)}")

    # Build label arrays
    a_labels, b_labels = [], []
    skipped = 0
    for row_id in overlap_ids:
        a_val = normalize_has_bias(a_rows[row_id].get("has_bias", ""))
        b_val = normalize_has_bias(b_rows[row_id].get("has_bias", ""))
        if a_val == -1 or b_val == -1:
            skipped += 1
            continue
        a_labels.append(a_val)
        b_labels.append(b_val)

    if skipped:
        print(f"Skipped {skipped} rows with missing/invalid has_bias values.")

    if len(a_labels) < 2:
        print("ERROR: Not enough valid rows to compute kappa.")
        sys.exit(1)

    # Cohen's Kappa on has_bias
    kappa = cohen_kappa_score(a_labels, b_labels)
    agreement_pct = sum(a == b for a, b in zip(a_labels, b_labels)) / len(a_labels)

    # Optional: compute kappa on other columns if present
    extra_kappas = {}
    for col in ("target_gender", "stereotype_category", "explicitness"):
        a_col, b_col = [], []
        for row_id in overlap_ids:
            a_v = a_rows[row_id].get(col, "").strip().lower()
            b_v = b_rows[row_id].get(col, "").strip().lower()
            if a_v and b_v:  # both present
                a_col.append(a_v)
                b_col.append(b_v)
        if len(a_col) >= 2:
            try:
                extra_kappas[col] = round(cohen_kappa_score(a_col, b_col), 4)
            except Exception:
                extra_kappas[col] = None

    # Report
    target = 0.70
    status = "✅ PASS" if kappa >= target else "❌ FAIL"
    print()
    print("=" * 60)
    print("COHEN'S KAPPA REPORT — JuaKazi Sprint 2")
    print("=" * 60)
    print(f"Rows evaluated:       {len(a_labels)}")
    print(f"Raw agreement:        {agreement_pct:.1%}")
    print()
    print(f"has_bias κ:           {kappa:.4f}   (target ≥ {target})  {status}")
    for col, k in extra_kappas.items():
        if k is not None:
            print(f"{col:25s} κ = {k:.4f}")
    print()
    print(f"AIBRIDGE Bronze IAA threshold (κ ≥ {target}): {status}")
    if kappa >= target:
        print()
        print("✅ Sprint 2 κ blocker is RESOLVED.")
        print("   Next: update CLAUDE.md §7 and §8 with κ value.")
        print("   Then: start Sprint 3.")
    else:
        print()
        print("   κ < 0.70 — run reconciliation session:")
        print("   1. Compare disagreements row by row with both annotators.")
        print("   2. Update docs/eval/schemas/ANNOTATION_GUIDELINES.md.")
        print("   3. Run a second 500-row batch after guideline clarification.")
    print()

    # Save JSON output
    result = {
        "run_date": __import__("datetime").date.today().isoformat(),
        "annotator_a_file": a_path,
        "annotator_b_file": b_path,
        "overlap_rows": len(a_labels),
        "raw_agreement": round(agreement_pct, 4),
        "kappa": {
            "has_bias": round(kappa, 4),
            **extra_kappas,
        },
        "aibridge_bronze_threshold": target,
        "aibridge_bronze_pass": kappa >= target,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"Results saved to {output_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute Cohen's Kappa from two annotator CSVs.")
    parser.add_argument("--annotator_a", required=True, help="CSV with annotator A labels")
    parser.add_argument("--annotator_b", required=True, help="CSV with annotator B labels (returned)")
    parser.add_argument("--output", default="eval/results/kappa_batch_024.json", help="Output JSON path")
    args = parser.parse_args()
    compute_kappa(args.annotator_a, args.annotator_b, args.output)


if __name__ == "__main__":
    main()
