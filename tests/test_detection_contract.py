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


# ── Frozen test sets (Phase A): held-out data that must never enter training ──

FROZEN_LANGS = ("sw", "ha", "zu", "ki", "fr", "en")
FROZEN_LABELS = {"neutral", "stereotype", "counter-stereotype", "derogation"}


def test_find_leaks_catches_exact_and_near_duplicates():
    from eval.frozen_eval import find_leaks

    test_texts = ["Owesifazane akakwazi ukuba ngumphathi wenkampani enkulu."]
    pool = [
        "owesifazane akakwazi ukuba ngumphathi wenkampani enkulu",           # same, punctuation/case
        "Owesifazane akakwazi ukuba ngumphathi wenkampani enkulu kakhulu.",  # one word added
        "Indoda kufanele ibe yinhloko yomuzi njalo.",                        # unrelated
    ]
    assert find_leaks(test_texts, pool) == {pool[0], pool[1]}


@pytest.mark.parametrize("lang", FROZEN_LANGS)
def test_frozen_test_set_is_well_formed(lang):
    from eval.frozen_eval import load_frozen

    rows = load_frozen(lang)
    assert len(rows) >= 60, f"{lang}: frozen test set too small ({len(rows)})"
    assert {r["bias_label"] for r in rows} <= FROZEN_LABELS
    texts = [r["text"] for r in rows]
    assert len(set(texts)) == len(texts), f"{lang}: duplicate sentences in frozen test set"
    assert all(r["seen_by_classifier_v2"] in ("true", "false") for r in rows)


def test_next_training_data_has_no_frozen_leaks():
    """The next training file must not contain frozen test sentences or near-duplicates of them."""
    import csv as _csv
    from eval.frozen_eval import find_leaks, load_frozen

    path = ROOT / "data" / "training_data_multilingual_v3.csv"
    if not path.exists():
        pytest.skip("data/training_data_multilingual_v3.csv not built (run scripts/rebuild_training_data.py)")
    by_lang: dict = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            by_lang.setdefault(r["language"], []).append(r["text"])
    for lang in FROZEN_LANGS:
        leaks = find_leaks([r["text"] for r in load_frozen(lang)], by_lang.get(lang, []))
        assert not leaks, f"{lang}: {len(leaks)} training rows leak from the frozen test set"


def test_next_training_data_does_not_label_counter_stereotypes_as_biased():
    """
    Project decision (2026-11-14): only stereotype and derogation count as biased.
    A counter-stereotype ("women can lead too") is not bias and must not be trained as one.
    """
    import csv as _csv

    path = ROOT / "data" / "training_data_multilingual_v3.csv"
    if not path.exists():
        pytest.skip("data/training_data_multilingual_v3.csv not built (run scripts/rebuild_training_data.py)")
    wrong: dict = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            biased = r["has_bias"].strip().lower() == "true"
            if biased != (r["bias_label"] in ("stereotype", "derogation")):
                key = (r["language"], r["bias_label"], r["has_bias"])
                wrong[key] = wrong.get(key, 0) + 1
    assert not wrong, f"rows whose has_bias disagrees with the decision: {wrong}"
