"""
Detection contract tests.

These tests define the MINIMUM acceptable detection performance per language.
HA/ZU/KI thresholds are met by the multilingual ML classifier (v1).
CI runs with JUAKAZI_ML_MODEL="" so HA/ZU/KI are xfail (lexicon-only can't meet threshold).
SW must always pass — lexicon alone meets the gate.

Run:
    pytest tests/test_detection_contract.py -v
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.bias_detector import BiasDetector
from eval.models import Language

# ── Thresholds (locked — do not change without updating PLAN.md) ────────────
THRESHOLDS = {
    "sw": {"f1": 0.85, "precision": 0.80, "recall": 0.85},
    "ha": {"f1": 0.70, "precision": 0.60, "recall": 0.75},
    "zu": {"f1": 0.68, "precision": 0.60, "recall": 0.65},
    "ki": {"f1": 0.70, "precision": 0.65, "recall": 0.65},
    "fr": {"f1": 0.75, "precision": 0.75, "recall": 0.70},
}

# ── Ground truth files ───────────────────────────────────────────────────────
GT_FILES = {
    "sw": "eval/ground_truth_sw_v5.csv",
    "ha": "eval/ground_truth_ha_v2.csv",
    "zu": "eval/ground_truth_zu_v2.csv",
    "ki": "eval/ground_truth_ki_v8.csv",
    "fr": "eval/ground_truth_fr_v5.csv",
}

LANG_ENUM = {
    "sw": Language.SWAHILI,
    "ha": Language.HAUSA,
    "zu": Language.ZULU,
    "ki": Language.GIKUYU,
    "fr": Language.FRENCH,
}

ROOT = Path(__file__).parent.parent
RULES_DIR = ROOT / "rules"


def _load_gt(lang_code: str, max_rows: int = 2000):
    """Load ground truth rows for a language. Cap at max_rows for speed."""
    path = ROOT / GT_FILES[lang_code]
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            has_bias = str(r.get("has_bias", "")).strip().lower()
            text = r.get("text", "").strip()
            if not text:
                continue
            rows.append({
                "text": text,
                "has_bias": has_bias in ("true", "1", "yes"),
            })
    # Stratified sample: keep balance when capping
    if len(rows) > max_rows:
        biased = [r for r in rows if r["has_bias"]]
        neutral = [r for r in rows if not r["has_bias"]]
        ratio = len(biased) / max(len(rows), 1)
        n_biased = min(len(biased), int(max_rows * ratio) + 1)
        n_neutral = min(len(neutral), max_rows - n_biased)
        rows = biased[:n_biased] + neutral[:n_neutral]
    return rows


def _evaluate(lang_code: str, max_rows: int = 2000):
    """Run detector on ground truth, return precision/recall/f1."""
    rows = _load_gt(lang_code, max_rows)
    lang = LANG_ENUM[lang_code]
    detector = BiasDetector(rules_dir=RULES_DIR, enable_ml_fallback=True)

    tp = fp = fn = tn = 0
    for row in rows:
        result = detector.detect_bias(row["text"], lang)
        predicted = result.has_bias_detected
        actual = row["has_bias"]
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "total": len(rows),
    }


def _assert_thresholds(lang_code: str, metrics: dict):
    t = THRESHOLDS[lang_code]
    errors = []
    if metrics["f1"] < t["f1"]:
        errors.append(f"F1 {metrics['f1']} < threshold {t['f1']}")
    if metrics["precision"] < t["precision"]:
        errors.append(f"Precision {metrics['precision']} < threshold {t['precision']}")
    if metrics["recall"] < t["recall"]:
        errors.append(f"Recall {metrics['recall']} < threshold {t['recall']}")
    if errors:
        pytest.fail(
            f"[{lang_code.upper()}] Detection below threshold:\n"
            + "\n".join(f"  - {e}" for e in errors)
            + f"\n  Metrics: {metrics}"
        )


# ── Tests ────────────────────────────────────────────────────────────────────

def test_sw_detection():
    """SW must always pass — this is the non-regression gate."""
    metrics = _evaluate("sw", max_rows=3000)
    print(f"\nSW metrics: {metrics}")
    _assert_thresholds("sw", metrics)


@pytest.mark.xfail(reason="HA lexicon-only F1~0.04 — requires multilingual-bias-classifier-v1", strict=False)
def test_ha_detection():
    """HA passes with ML classifier (F1=0.800). Lexicon-only fails — xfail in CI."""
    metrics = _evaluate("ha", max_rows=2000)
    print(f"\nHA metrics: {metrics}")
    _assert_thresholds("ha", metrics)


@pytest.mark.xfail(reason="ZU lexicon-only F1~0.73 precision=1.0 recall=0.58 — requires multilingual-bias-classifier-v1", strict=False)
def test_zu_detection():
    """ZU passes with ML classifier (F1=0.996). Lexicon recall too low — xfail in CI."""
    metrics = _evaluate("zu", max_rows=2000)
    print(f"\nZU metrics: {metrics}")
    _assert_thresholds("zu", metrics)


@pytest.mark.xfail(reason="KI lexicon-only F1~0.54 — requires multilingual-bias-classifier-v1", strict=False)
def test_ki_detection():
    """KI passes with ML classifier (F1=0.865). Lexicon-only fails — xfail in CI."""
    metrics = _evaluate("ki", max_rows=2000)
    print(f"\nKI metrics: {metrics}")
    _assert_thresholds("ki", metrics)


@pytest.mark.skipif(
    not (ROOT / GT_FILES["fr"]).exists(),
    reason="FR ground truth not in repo (gitignored large file)"
)
def test_fr_detection():
    """FR lexicon rules already meet threshold (F1=0.97). Phase 1b will improve recall further."""
    metrics = _evaluate("fr", max_rows=2000)
    print(f"\nFR metrics: {metrics}")
    _assert_thresholds("fr", metrics)
