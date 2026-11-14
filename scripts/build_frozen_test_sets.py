"""
Build the frozen test sets: eval/frozen_test_{lang}_v1.csv

Run once:  python3 scripts/build_frozen_test_sets.py
It refuses to overwrite an existing frozen file — a frozen set is never edited
in place; create v2 instead (same rule as ground truth).

Where the rows come from:
  HA  rows of Hausa_balanced_bias_2k.csv that classifier v2 never saw
  FR  eval/ground_truth_fr_v5.csv plus the unseen rows of the annotated file
  EN  eval/ground_truth_en_v5.csv
  SW, ZU, KI  no unseen data exists, so a stratified sample is carved out of the
      ground truth. Classifier v2 was trained on these rows (seen_by_classifier_v2
      = true): they are a valid test only for models trained after today, and
      scripts/rebuild_training_data.py now removes them from training.

Every row starts with native_review empty. A native speaker fills it with
"agree" or the corrected label; until then the labels are candidates.
"""
import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.frozen_eval import LABELS, frozen_path, normalize  # noqa: E402

SEED = 20261114
PER_LABEL = 125          # target rows per label for the carved-out languages
OUT_COLS = ["id", "language", "text", "bias_label", "expected_correction", "source_file",
            "source_id", "label_origin", "seen_by_classifier_v2", "native_review", "reviewer_id"]
# Labels used in the ground truth for specific kinds of stereotype
LABEL_ALIASES = {"capability": "stereotype", "appearance_stereotype": "stereotype"}
QA_RANK = {"gold": 0, "approved": 1, "human-annotated": 1, "human-reviewed": 1, "passed": 2}

csv.field_size_limit(10**9)


def read(path: str) -> list[dict]:
    with open(ROOT / path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def label_of(row: dict) -> str | None:
    label = (row.get("bias_label") or "").strip().lower()
    label = LABEL_ALIASES.get(label, label)
    if label not in LABELS:
        has_bias = (row.get("has_bias") or "").strip().lower()
        label = {"true": "stereotype", "false": "neutral"}.get(has_bias) if not label else None
    return label


def to_row(row: dict, lang: str, source_file: str, seen: bool) -> dict | None:
    text, label = (row.get("text") or "").strip(), label_of(row)
    if not text or label is None:
        return None
    expected = (row.get("expected_correction") or "").strip()
    return {
        "language": lang, "text": text, "bias_label": label,
        "expected_correction": expected if label != "neutral" else "",
        "source_file": source_file,
        "source_id": row.get("id") or row.get("sentence_id") or "",
        "label_origin": f"{(row.get('qa_status') or '').strip()}|{(row.get('annotator_id') or '').strip()}",
        "seen_by_classifier_v2": "true" if seen else "false",
        "native_review": "", "reviewer_id": "",
    }


def dedupe(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = normalize(r["text"])
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


def carve(lang: str, source_file: str, rng: random.Random) -> list[dict]:
    """Stratified sample from a ground-truth file, best-reviewed rows first."""
    by_label = defaultdict(list)
    for raw in read(source_file):
        row = to_row(raw, lang, source_file, seen=True)
        if row and 4 <= len(row["text"].split()) <= 60:
            rank = QA_RANK.get((raw.get("qa_status") or "").strip().lower(), 3)
            by_label[row["bias_label"]].append((rank, rng.random(), row))
    picked = []
    for label in LABELS:
        picked += [r for _, _, r in sorted(by_label[label], key=lambda t: t[:2])[:PER_LABEL]]
    return dedupe(picked)


def main() -> None:
    rng = random.Random(SEED)
    training = defaultdict(set)
    for r in read("data/training_data_multilingual.csv"):
        training[r["language"]].add(normalize(r["text"]))

    def unseen(path: str, lang: str) -> list[dict]:
        rows = [to_row(r, lang, path, seen=False) for r in read(path)
                if normalize(r.get("text", "")) not in training[lang]]
        return [r for r in rows if r]

    sets = {
        "ha": dedupe(unseen("Hausa_balanced_bias_2k.csv", "ha")),
        "fr": dedupe(unseen("eval/ground_truth_fr_v5.csv", "fr")
                     + unseen("French Annotated - final (1).csv", "fr")),
        "en": dedupe(unseen("eval/ground_truth_en_v5.csv", "en")),
        "sw": carve("sw", "eval/ground_truth_sw_v5.csv", rng),
        "zu": carve("zu", "eval/ground_truth_zu_v2.csv", rng),
        "ki": carve("ki", "eval/ground_truth_ki_v8.csv", rng),
    }
    for lang, rows in sets.items():
        path = frozen_path(lang)
        if path.exists():
            print(f"{lang}: {path.name} already exists — not overwriting")
            continue
        for i, r in enumerate(rows, 1):
            r["id"] = f"frozen-{lang}-{i:04d}"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=OUT_COLS)
            w.writeheader()
            w.writerows(rows)
        seen = sum(r["seen_by_classifier_v2"] == "true" for r in rows)
        with_ref = sum(bool(r["expected_correction"]) for r in rows)
        print(f"{lang}: {len(rows):>5} rows  seen_by_v2={seen:>4}  with expected_correction={with_ref:>4}  "
              f"{dict(Counter(r['bias_label'] for r in rows))}")


if __name__ == "__main__":
    main()
