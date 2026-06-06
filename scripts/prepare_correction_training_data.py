"""
Prepare unified correction training data for Stage 3 seq2seq corrector.

Output: data/training_data_correction.csv
Columns: language, input_text, target_text, source, stereotype_category

Input format for model: "correct bias {lang}: {input_text}"
Target: corrected/neutral text

Sources per language:
  SW  — juakazi_sw_correction_pairs_v1.csv (1,586 pairs)
       + eval/ground_truth_sw_v5.csv biased rows with expected_correction
  HA  — juakazi_ha_correction_pairs_v1.csv (1,918 pairs, needs_review accepted)
  ZU  — zulu_retraining - zulu_retraining.csv.csv (2,000 pairs)
       + juakazi_zu_correction_pairs_v1.csv (1,142 pairs)
  KI  — eval/ground_truth_ki_v8.csv biased rows with expected_correction (1,603)
  FR  — eval/ground_truth_fr_v5.csv biased rows with expected_correction (35)
       + lexicon-generated pairs from French Annotated gold rows
       + French Annotated gold biased rows via lexicon rules
  EN  — eval/ground_truth_en_v5.csv biased rows with expected_correction (34)
       + lexicon-generated pairs from EN ground truth
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.rules_engine import apply_rules_on_spans

OUT_PATH = ROOT / "data" / "training_data_correction.csv"
STATS_PATH = ROOT / "data" / "training_data_correction_stats.txt"


def _clean(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def _is_valid_pair(inp: str, tgt: str) -> bool:
    inp, tgt = _clean(inp), _clean(tgt)
    if not inp or not tgt:
        return False
    if inp == tgt:
        return False
    if len(inp) < 5 or len(tgt) < 5:
        return False
    return True


def load_sw() -> pd.DataFrame:
    rows = []

    # Source 1: correction pairs file
    df = pd.read_csv(ROOT / "juakazi_sw_correction_pairs_v1.csv")
    for _, r in df.iterrows():
        inp, tgt = _clean(r["original_text"]), _clean(r["expected_correction"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "sw", "input_text": inp, "target_text": tgt,
                "source": "sw_pairs_v1",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    # Source 2: ground truth expected_correction
    gt = pd.read_csv(ROOT / "eval" / "ground_truth_sw_v5.csv", low_memory=False)
    biased = gt[(gt["has_bias"] == True) & gt["expected_correction"].notna()]
    for _, r in biased.iterrows():
        inp, tgt = _clean(r["text"]), _clean(r["expected_correction"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "sw", "input_text": inp, "target_text": tgt,
                "source": "sw_gt_v5",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def load_ha() -> pd.DataFrame:
    rows = []
    df = pd.read_csv(ROOT / "juakazi_ha_correction_pairs_v1.csv")
    for _, r in df.iterrows():
        inp, tgt = _clean(r["original_text"]), _clean(r["corrected_text"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "ha", "input_text": inp, "target_text": tgt,
                "source": "ha_pairs_v1",
                "stereotype_category": r.get("stereotype_category", ""),
            })
    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def load_zu() -> pd.DataFrame:
    rows = []

    # Source 1: retraining file (instruction-tuning format, clean)
    rt = pd.read_csv(ROOT / "zulu_retraining - zulu_retraining.csv.csv")
    for _, r in rt.iterrows():
        inp, tgt = _clean(r["input"]), _clean(r["output"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "zu", "input_text": inp, "target_text": tgt,
                "source": "zu_retraining",
                "stereotype_category": r.get("category", ""),
            })

    # Source 2: correction pairs file
    df = pd.read_csv(ROOT / "juakazi_zu_correction_pairs_v1.csv")
    for _, r in df.iterrows():
        inp, tgt = _clean(r["original_text"]), _clean(r["corrected_text"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "zu", "input_text": inp, "target_text": tgt,
                "source": "zu_pairs_v1",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    # Source 3: lexicon-generated from ZU GT biased rows
    gt = pd.read_csv(ROOT / "eval" / "ground_truth_zu_v1.csv")
    zu_texts = gt[gt["has_bias"] == True]["text"].dropna().tolist()
    rows.extend(_lexicon_pairs("zu", zu_texts, "zu_gt_lexicon"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def load_ki() -> pd.DataFrame:
    rows = []
    gt = pd.read_csv(ROOT / "eval" / "ground_truth_ki_v8.csv")
    biased = gt[
        (gt["has_bias"] == True)
        & gt["expected_correction"].notna()
        & (gt["expected_correction"].astype(str).str.strip() != "")
    ]
    for _, r in biased.iterrows():
        inp, tgt = _clean(r["text"]), _clean(str(r["expected_correction"]))
        # Skip rows where correction is identical to input — those are placeholders
        if _is_valid_pair(inp, tgt) and inp != tgt:
            rows.append({
                "language": "ki", "input_text": inp, "target_text": tgt,
                "source": "ki_gt_v8",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    # Also generate pairs via lexicon for KI biased rows missing real corrections
    ki_texts = gt[gt["has_bias"] == True]["text"].dropna().tolist()
    rows.extend(_lexicon_pairs("ki", ki_texts, "ki_gt_lexicon"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def _lexicon_pairs(lang: str, texts: list[str], source_tag: str) -> list[dict]:
    """Generate correction pairs from a list of texts using lexicon rules."""
    pairs = []
    for text in texts:
        inp = _clean(text)
        if not inp:
            continue
        rewritten, edits, matched, _ = apply_rules_on_spans(inp, lang)
        if matched > 0 and rewritten != inp and _is_valid_pair(inp, rewritten):
            cat = edits[0].get("stereotype_category", "") if edits else ""
            pairs.append({
                "language": lang, "input_text": inp, "target_text": _clean(rewritten),
                "source": source_tag, "stereotype_category": cat,
            })
    return pairs


def load_fr() -> pd.DataFrame:
    rows = []

    # Source 1: ground truth expected_correction
    gt = pd.read_csv(ROOT / "eval" / "ground_truth_fr_v5.csv")
    biased = gt[
        (gt["has_bias"] == True)
        & gt["expected_correction"].notna()
        & (gt["expected_correction"].str.strip() != "")
    ]
    for _, r in biased.iterrows():
        inp, tgt = _clean(r["text"]), _clean(r["expected_correction"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "fr", "input_text": inp, "target_text": tgt,
                "source": "fr_gt_v5",
                "stereotype_category": r.get("stereotype_category", r.get("bias_category", "")),
            })

    # Source 2: lexicon-generated from French Annotated gold biased rows
    fa = pd.read_csv(ROOT / "French Annotated - final (1).csv")
    gold_biased = fa[
        (fa["bias_label"] != "neutral")
        & (fa["qa_status"] == "gold")
    ]["text"].dropna().tolist()
    rows.extend(_lexicon_pairs("fr", gold_biased, "fr_annotated_lexicon"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def _expand_partial_correction(original: str, correction: str) -> str:
    """
    Many EN/FR GT corrections are partial (just the replacement term).
    If the correction is shorter than 60% of the original and doesn't
    contain the original's subject, try to substitute it back into the sentence.
    """
    orig_words = original.lower().split()
    corr_words = correction.lower().split()
    # If correction looks like a full sentence, use as-is
    if len(corr_words) >= max(3, len(orig_words) * 0.5):
        return correction
    # Try lexicon substitution — correction is a replacement term, use full rewrite
    rewritten, _, matched, _ = apply_rules_on_spans(original, "en")
    if matched > 0 and rewritten != original:
        return rewritten
    # Fallback: use the correction as-is (partial target still teaches the model direction)
    return correction


def load_en() -> pd.DataFrame:
    rows = []

    # Source 1: ground truth — expand partial corrections to full sentences
    gt = pd.read_csv(ROOT / "eval" / "ground_truth_en_v5.csv")
    biased = gt[
        (gt["has_bias"] == True)
        & gt["expected_correction"].notna()
        & (gt["expected_correction"].str.strip() != "")
    ]
    for _, r in biased.iterrows():
        inp = _clean(r["text"])
        raw_tgt = _clean(r["expected_correction"])
        tgt = _expand_partial_correction(inp, raw_tgt)
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "en", "input_text": inp, "target_text": tgt,
                "source": "en_gt_v5",
                "stereotype_category": r.get("stereotype_category", r.get("bias_category", "")),
            })

    # Source 2: lexicon-generated from all EN biased rows
    en_texts = gt[gt["has_bias"] == True]["text"].dropna().tolist()
    rows.extend(_lexicon_pairs("en", en_texts, "en_gt_lexicon"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def main() -> None:
    print("Loading correction pairs per language...")

    loaders = [
        ("SW", load_sw),
        ("HA", load_ha),
        ("ZU", load_zu),
        ("KI", load_ki),
        ("FR", load_fr),
        ("EN", load_en),
    ]

    frames = []
    stats_lines = []

    for name, loader in loaders:
        df = loader()
        print(f"  {name}: {len(df):,} pairs")
        stats_lines.append(f"  {name}: {len(df):,} pairs")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["language", "input_text"])

    # Shuffle so languages are interleaved during training
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    OUT_PATH.parent.mkdir(exist_ok=True)
    combined.to_csv(OUT_PATH, index=False)

    total = len(combined)
    stats = [
        f"Total pairs: {total:,}",
        "",
        "By language:",
        *stats_lines,
        "",
        "By source:",
        *[f"  {s}: {n}" for s, n in combined["source"].value_counts().items()],
    ]
    stats_text = "\n".join(stats)
    STATS_PATH.write_text(stats_text)

    print(f"\n{'='*50}")
    print(stats_text)
    print(f"\nSaved to {OUT_PATH}")
    print(f"Stats:   {STATS_PATH}")


if __name__ == "__main__":
    main()
