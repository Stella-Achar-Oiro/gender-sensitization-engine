"""
Frozen test sets: held-out evaluation that training data must never touch.

Files:  eval/frozen_test_{lang}_v1.csv   (built by scripts/build_frozen_test_sets.py)
Run:    python3 run_evaluation.py --frozen            # detection, all languages
        python3 run_evaluation.py --frozen --correction   # also score the corrector

Why this exists: the per-language ground-truth files are almost entirely inside
the classifier's training data, so scores computed on them say nothing about
unseen text. Each frozen row records whether classifier v2 saw it during
training (`seen_by_classifier_v2`); a score on seen rows is only a valid test
for models trained after the frozen sets were created.

Labels keep the four classes (neutral / stereotype / counter-stereotype /
derogation). Project decision (2026-11-14): only stereotype and derogation are
biased; a counter-stereotype is not. So:
  strict     = stereotype + derogation                        <- the score that counts
  as_trained = stereotype + derogation + counter-stereotype   <- how classifier v2 was
               trained in HA/ZU/FR; kept only to explain v2's behaviour
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FROZEN_VERSION = "v1"
LANGS = ("sw", "ha", "zu", "ki", "fr", "en")
LABELS = ("neutral", "stereotype", "counter-stereotype", "derogation")
POSITIVE = {
    "strict": {"stereotype", "derogation"},
    "as_trained": {"stereotype", "derogation", "counter-stereotype"},
}
OUT_PATH = ROOT / "eval" / "metrics_frozen.json"

csv.field_size_limit(10**9)


def normalize(text: str) -> str:
    """Lowercase and collapse punctuation/whitespace, for duplicate matching."""
    return re.sub(r"\W+", " ", (text or "").lower()).strip()


def frozen_path(lang: str) -> Path:
    return ROOT / "eval" / f"frozen_test_{lang}_{FROZEN_VERSION}.csv"


def load_frozen(lang: str) -> list[dict]:
    with open(frozen_path(lang), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _shingles(norm: str, n: int = 3) -> set[str]:
    words = norm.split()
    if len(words) <= n:
        return {norm}
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def find_leaks(test_texts: list[str], pool_texts: list[str], threshold: float = 0.6) -> set[str]:
    """Return the pool texts that are exact or near duplicates of any test text.

    Near duplicate = Jaccard similarity of word 3-grams >= threshold. One changed
    or added word in a ten-word sentence gives about 0.6-0.8, which is the kind
    of templated variant that leaks a test sentence into training.
    """
    test_norm = {normalize(t) for t in test_texts}
    test_shingles = [(_shingles(t)) for t in test_norm]
    index: dict[str, list[int]] = defaultdict(list)
    for i, sh in enumerate(test_shingles):
        for s in sh:
            index[s].append(i)

    leaks: set[str] = set()
    for text in pool_texts:
        norm = normalize(text)
        if norm in test_norm:
            leaks.add(text)
            continue
        sh = _shingles(norm)
        shared = Counter(i for s in sh for i in index.get(s, ()))
        for i, inter in shared.items():
            if inter / (len(sh) + len(test_shingles[i]) - inter) >= threshold:
                leaks.add(text)
                break
    return leaks


# ── Detection ────────────────────────────────────────────────────────────────

def _prf(labels: list[str], flagged: list[bool], positive: set[str]) -> dict:
    y = [l in positive for l in labels]
    tp = sum(a and b for a, b in zip(y, flagged))
    fp = sum((not a) and b for a, b in zip(y, flagged))
    fn = sum(a and (not b) for a, b in zip(y, flagged))
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3),
            "tp": tp, "fp": fp, "fn": fn, "positives": sum(y)}


def evaluate_detection(lang: str) -> dict:
    """Score rules-only, classifier-only and the combined pipeline on one frozen set.

    The combined decision mirrors api/service.py: the text is flagged when the
    lexicon rules produce a replace/warn edit, or (when no rule replaced anything)
    the classifier score reaches JUAKAZI_ML_THRESHOLD.
    """
    from api.rules_engine import apply_rules_on_spans
    from eval.ml_classifier import classify
    from eval.models import Language

    lang_enum = {l.value: l for l in Language}[lang]
    threshold = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.56"))
    rows = load_frozen(lang)
    labels = [r["bias_label"] for r in rows]
    rules, ml, pipeline = [], [], []
    for r in rows:
        _, edits, _, _ = apply_rules_on_spans(r["text"], lang)
        rule_hit = any(e.get("severity") in ("replace", "warn") for e in edits)
        replaced = any(e.get("severity") == "replace" for e in edits)
        ml_hit = classify(r["text"], lang_enum) >= threshold
        rules.append(rule_hit)
        ml.append(ml_hit)
        pipeline.append(rule_hit or (ml_hit and not replaced))

    seen = sum(r["seen_by_classifier_v2"] == "true" for r in rows)
    result = {
        "rows": len(rows),
        "labels": dict(Counter(labels)),
        "seen_by_classifier_v2": seen,
        "labels_reviewed": sum(bool(r.get("native_review", "").strip()) for r in rows),
        "valid_test_for_classifier_v2": seen == 0,
        "ml_threshold": threshold,
        "flagged_by_label": {
            lab: f"{sum(f for l, f in zip(labels, pipeline) if l == lab)}/{labels.count(lab)}"
            for lab in LABELS if lab in labels
        },
    }
    for name, flags in (("pipeline", pipeline), ("rules_only", rules), ("classifier_only", ml)):
        result[name] = {d: _prf(labels, flags, pos) for d, pos in POSITIVE.items()}
    return result


# ── Correction ───────────────────────────────────────────────────────────────

def _chrf(hypothesis: str, reference: str, n: int = 4) -> float:
    """Character n-gram F-score (0-1), averaged over 1..n. No external dependency."""
    def grams(s: str, k: int) -> Counter:
        s = normalize(s)
        return Counter(s[i:i + k] for i in range(len(s) - k + 1))
    scores = []
    for k in range(1, n + 1):
        h, r = grams(hypothesis, k), grams(reference, k)
        if not h or not r:
            continue
        overlap = sum((h & r).values())
        p, rec = overlap / sum(h.values()), overlap / sum(r.values())
        scores.append(2 * p * rec / (p + rec) if p + rec else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def evaluate_correction(lang: str) -> dict | None:
    """Score the full correction path on frozen rows that carry an expected correction.

    Three questions, as in the text-detoxification shared tasks:
      bias removed  - does the classifier still flag the output?
      meaning kept  - chrF of the output against the input
      right answer  - chrF and exact match against the human reference
    """
    from api.service import rewrite_text
    from eval.ml_classifier import classify
    from eval.models import Language

    lang_enum = {l.value: l for l in Language}[lang]
    threshold = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.56"))
    rows = [r for r in load_frozen(lang)
            if r.get("expected_correction", "").strip()
            and normalize(r["expected_correction"]) != normalize(r["text"])]
    if not rows:
        return None

    by_source: Counter = Counter()
    exact = changed = still_flagged = 0
    to_ref, to_input = [], []
    for r in rows:
        response, _ = rewrite_text(id=r["id"], text=r["text"], lang=lang)
        out = response.rewrite
        by_source[response.source] += 1
        exact += normalize(out) == normalize(r["expected_correction"])
        was_changed = normalize(out) != normalize(r["text"])
        changed += was_changed
        if was_changed:
            still_flagged += classify(out, lang_enum) >= threshold
            to_input.append(_chrf(out, r["text"]))
        to_ref.append(_chrf(out, r["expected_correction"]))
    return {
        "pairs": len(rows),
        "source": dict(by_source),
        "changed": changed,
        "exact_match": exact,
        "chrf_vs_reference": round(sum(to_ref) / len(to_ref), 3),
        "chrf_vs_input_when_changed": round(sum(to_input) / len(to_input), 3) if to_input else None,
        "still_flagged_after_change": still_flagged,
    }


def main(correction: bool = False) -> dict:
    results = {"frozen_version": FROZEN_VERSION,
               "biased_definition": "strict (stereotype + derogation; counter-stereotype is not bias)",
               "classifier": os.environ.get("JUAKAZI_ML_MODEL") or "juakazike/multilingual-bias-classifier-v2",
               "detection": {}, "correction": {}}
    if not correction and OUT_PATH.exists():
        # A detection-only run keeps the corrector scores from the last full run.
        results["correction"] = json.loads(OUT_PATH.read_text(encoding="utf-8")).get("correction", {})
    print(f"{'lang':4} {'rows':>5} {'unseen':>6} | pipeline P/R/F1 (strict) | (as v2 was trained)  | flagged by label")
    for lang in LANGS:
        if not frozen_path(lang).exists():
            print(f"{lang:4} (no frozen test set)")
            continue
        d = evaluate_detection(lang)
        results["detection"][lang] = d
        s, a = d["pipeline"]["strict"], d["pipeline"]["as_trained"]
        unseen = "yes" if d["valid_test_for_classifier_v2"] else "NO"
        print(f"{lang:4} {d['rows']:>5} {unseen:>6} | {s['precision']:.3f} {s['recall']:.3f} {s['f1']:.3f}"
              f"      | {a['precision']:.3f} {a['recall']:.3f} {a['f1']:.3f}   | {d['flagged_by_label']}")
        if correction:
            c = evaluate_correction(lang)
            if c:
                results["correction"][lang] = c
    if correction:
        print("\nCorrection (rows with an expected correction):")
        for lang, c in results["correction"].items():
            print(f"{lang:4} pairs={c['pairs']:>4} changed={c['changed']:>4} exact={c['exact_match']:>4} "
                  f"chrF_ref={c['chrf_vs_reference']:.3f} still_flagged={c['still_flagged_after_change']} source={c['source']}")
    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWritten: {OUT_PATH.relative_to(ROOT)}")
    return results
