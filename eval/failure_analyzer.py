#!/usr/bin/env python3
"""
Error analysis vs ground truth.

- Simple lexical FN scan (legacy): ``python3 eval/failure_analyzer.py --simple``
- Full detector FP/FN export (matches run_evaluation.py): ``python3 eval/failure_analyzer.py --lang sw --export eval/results/sw_errors.csv``

Run from the project root so paths ``eval/`` and ``rules/`` resolve.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ground_truth_filename
from core.rules_loader import load_rules as load_rules_from_core


def load_rules(lang: str):
    """Load bias detection rules (list of lowercased biased terms). Uses core.rules_loader."""
    rules = load_rules_from_core(lang)
    return [r["biased"].lower() for r in rules if r.get("biased")]


def detect_bias_simple(text: str, lang: str) -> bool:
    """Simple bias detection using substring rule match (does not match eval metrics)."""
    rules = load_rules(lang)
    text_lower = text.lower()
    return any(rule in text_lower for rule in rules)


def analyze_failures_simple():
    """Print false negatives using simple substring match (fast, approximate)."""
    for lang in ["en", "sw", "fr", "ki"]:
        gt_path = PROJECT_ROOT / "eval" / ground_truth_filename(lang)
        if not gt_path.exists():
            continue
        print(f"\n=== {lang.upper()} (simple lexical FN) ===")
        samples = []
        with open(gt_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(
                    {
                        "text": row["text"].strip().strip('"'),
                        "expected": row["has_bias"].lower() == "true",
                    }
                )
        false_negatives = [
            s["text"] for s in samples if s["expected"] and not detect_bias_simple(s["text"], lang)
        ]
        print(f"False Negatives: {len(false_negatives)}")
        for i, text in enumerate(false_negatives[:5], 1):
            print(f'{i}. "{text[:200]}{"…" if len(text) > 200 else ""}"')
        if len(false_negatives) > 5:
            print(f"... and {len(false_negatives) - 5} more")


def export_detector_errors(
    lang: str,
    out_path: Path,
    *,
    limit: int | None = None,
    enable_ml: bool = False,
) -> tuple[int, int, int]:
    """
    Export FP/FN rows using BiasDetector (same has_bias_detected semantics as run_evaluation).

    Returns (fp_count, fn_count, rows_written).
    """
    from eval.bias_detector import BiasDetector
    from eval.data_loader import GroundTruthLoader
    from eval.models import Language

    lang_enum = {
        "en": Language.ENGLISH,
        "sw": Language.SWAHILI,
        "fr": Language.FRENCH,
        "ki": Language.GIKUYU,
    }.get(lang)
    if not lang_enum:
        raise SystemExit(f"Unsupported --lang {lang!r} (use en|sw|fr|ki)")

    loader = GroundTruthLoader(PROJECT_ROOT / "eval")
    ground_truth = loader.load_ground_truth(lang_enum)
    rules_dir = PROJECT_ROOT / "rules"
    detector = BiasDetector(rules_dir, enable_ml_fallback=enable_ml)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fp = fn = 0
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "kind",
                "text",
                "has_bias_gt",
                "has_bias_pred",
                "matched_from",
                "bias_category",
            ],
        )
        w.writeheader()
        for sample in ground_truth:
            if limit is not None and n >= limit:
                break
            n += 1
            pred = detector.detect_bias(sample.text, lang_enum)
            predicted = pred.has_bias_detected
            expected = sample.has_bias
            if predicted == expected:
                continue
            if predicted and not expected:
                kind = "FP"
                fp += 1
            else:
                kind = "FN"
                fn += 1
            matched = ""
            if pred.detected_edits:
                matched = str(pred.detected_edits[0].get("from", ""))
            w.writerow(
                {
                    "kind": kind,
                    "text": sample.text,
                    "has_bias_gt": expected,
                    "has_bias_pred": predicted,
                    "matched_from": matched,
                    "bias_category": sample.bias_category.value if sample.bias_category else "",
                }
            )
    return fp, fn, fp + fn


def main() -> None:
    parser = argparse.ArgumentParser(description="Ground truth error analysis")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Fast lexical FN estimate only (legacy behaviour)",
    )
    parser.add_argument("--lang", default="sw", help="Language code for --export (default sw)")
    parser.add_argument(
        "--export",
        metavar="CSV",
        help="Write FP/FN rows to CSV (uses full BiasDetector; matches eval)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only first N ground-truth rows (for quick iteration)",
    )
    parser.add_argument(
        "--ml",
        action="store_true",
        help="Enable ML fallback when exporting (usually unchanged for F1; replace-only detection)",
    )
    args = parser.parse_args()

    if args.simple:
        analyze_failures_simple()
        return

    if args.export:
        fp, fn, total = export_detector_errors(
            args.lang,
            Path(args.export),
            limit=args.limit,
            enable_ml=args.ml,
        )
        print(f"Wrote {total} error rows ({fp} FP, {fn} FN) → {args.export}")
        return

    parser.print_help()
    print(
        "\nExample:\n"
        "  python3 eval/failure_analyzer.py --lang sw --export eval/results/sw_fp_fn.csv\n"
        "  python3 eval/failure_analyzer.py --lang sw --export eval/results/sw_sample.csv --limit 5000"
    )


if __name__ == "__main__":
    main()
