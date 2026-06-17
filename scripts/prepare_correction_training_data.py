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

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from api.rules_engine import apply_rules_on_spans

OUT_PATH = ROOT / "data" / "training_data_correction_v3.csv"
STATS_PATH = ROOT / "data" / "training_data_correction_v3_stats.txt"


def _clean(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


_ANNOTATION_NOISE = re.compile(
    r'This sentence|If you meant|corrected version|The bias would|'
    r'already neutral|neutral—|\(This|\bNote:\b|\bNOTE:\b|Corrected version|'
    r'\[needs_review|Consider:|reinforcing gendered|traditionally coded',
    re.IGNORECASE,
)


def _is_valid_pair(inp: str, tgt: str, max_words: int = 40, min_overlap: float = 0.70) -> bool:
    inp, tgt = _clean(inp), _clean(tgt)
    if not inp or not tgt:
        return False
    if inp == tgt:
        return False
    if len(inp) < 5 or len(tgt) < 5:
        return False
    if _ANNOTATION_NOISE.search(tgt):
        return False
    # Drop list-literal artifacts from old annotation pipeline
    if inp.startswith("['") or tgt.startswith("['"):
        return False
    inp_words = set(inp.split())
    tgt_words = set(tgt.split())
    overlap = len(inp_words & tgt_words) / max(len(inp_words), 1)
    if overlap < min_overlap:
        return False
    if len(inp.split()) > max_words:
        return False
    return True


def _lexicon_example_pairs(lang: str) -> list[dict]:
    """Generate pairs from lexicon example_biased/example_neutral columns."""
    try:
        lex = pd.read_csv(ROOT / f"rules/lexicon_{lang}_v3.csv")
    except Exception:
        return []
    pairs = []
    for _, r in lex.iterrows():
        inp = _clean(str(r.get("example_biased", "") or ""))
        tgt = _clean(str(r.get("example_neutral", "") or ""))
        if _is_valid_pair(inp, tgt):
            pairs.append({
                "language": lang,
                "input_text": inp,
                "target_text": tgt,
                "source": f"{lang}_lexicon_examples",
                "stereotype_category": str(r.get("stereotype_category", "") or ""),
            })
    return pairs


def _load_v1_pairs(lang: str, source_tag: str) -> list[dict]:
    """
    Pull clean pairs from the old training_data_correction.csv (v1) that
    aren't already covered by the primary per-language sources.
    Applies standard quality filters: noise, overlap, length, list artifacts.
    """
    v1_path = ROOT / "data" / "training_data_correction.csv"
    if not v1_path.exists():
        return []
    v1 = pd.read_csv(v1_path)
    g = v1[v1["language"] == lang].copy()
    rows = []
    for _, r in g.iterrows():
        inp = _clean(str(r.get("input_text", "") or ""))
        tgt = _clean(str(r.get("target_text", "") or ""))
        # Drop list-literal artifacts from old annotation pipeline
        if inp.startswith("['") or tgt.startswith("['"):
            continue
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": lang,
                "input_text": inp,
                "target_text": tgt,
                "source": source_tag,
                "stereotype_category": str(r.get("stereotype_category", "") or ""),
            })
    return rows


def load_sw() -> pd.DataFrame:
    rows = []

    # Source 1: correction pairs file (filter: ≤40 words, ≥30% overlap)
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

    # Source 3: lexicon example pairs (short, minimal edits)
    rows.extend(_lexicon_example_pairs("sw"))

    # Source 4: v1 dataset pairs not already covered above
    rows.extend(_load_v1_pairs("sw", "sw_v1_extra"))

    # Source 5: Umunthu Dataset — 5,174 SW stereotype rows, no pre-made corrections,
    # generate via lexicon (wa kike/wa kiume removal, mwanamke→mtu etc.)
    umunthu = ROOT / "Umunthu Data - Swahili Annotated (3).csv"
    if umunthu.exists():
        u = pd.read_csv(umunthu)
        u_texts = u[u["bias_label"] == "stereotype"]["text"].dropna().tolist()
        rows.extend(_lexicon_pairs("sw", u_texts, "sw_umunthu"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def load_ha() -> pd.DataFrame:
    rows = []

    # Source 1: correction pairs v1 — approve the 1,520 tight pairs programmatically.
    # qa_status=needs_review but pairs are genuine minimal edits (mace→mutum, ta→ya).
    df = pd.read_csv(ROOT / "juakazi_ha_correction_pairs_v1.csv")
    for _, r in df.iterrows():
        inp, tgt = _clean(r["original_text"]), _clean(r["corrected_text"])
        # Strict filter: overlap ≥ 0.70 AND word diff ≤ 3 (minimal edit only)
        inp_w = set(inp.split())
        tgt_w = set(tgt.split())
        ov = len(inp_w & tgt_w) / max(len(inp_w), 1)
        wd = abs(len(inp.split()) - len(tgt.split()))
        if _is_valid_pair(inp, tgt) and ov >= 0.70 and wd <= 3:
            rows.append({
                "language": "ha", "input_text": inp, "target_text": tgt,
                "source": "ha_pairs_v1_approved",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    # Source 2: mine HA GT (10,054 approved rows) via lexicon to top up to ~2,000
    gt_ha = ROOT / "eval" / "ground_truth_ha_v1.csv"
    if gt_ha.exists():
        gt = pd.read_csv(gt_ha)
        ha_biased = gt[gt["bias_label"].str.lower().isin(["stereotype", "derogation", "biased"])]["text"].dropna().tolist() \
            if "bias_label" in gt.columns else gt["text"].dropna().tolist()
        rows.extend(_lexicon_pairs("ha", ha_biased, "ha_gt_lexicon"))

    # Source 3: lexicon example pairs
    rows.extend(_lexicon_example_pairs("ha"))

    return pd.DataFrame(rows).drop_duplicates(subset=["input_text"])


def load_zu() -> pd.DataFrame:
    rows = []

    # Source 1: correction pairs v1 — all 1,142 pass strict filter (overlap>=0.70, wdiff<=3)
    df = pd.read_csv(ROOT / "juakazi_zu_correction_pairs_v1.csv")
    for _, r in df.iterrows():
        inp, tgt = _clean(r["original_text"]), _clean(r["corrected_text"])
        if _is_valid_pair(inp, tgt):
            rows.append({
                "language": "zu", "input_text": inp, "target_text": tgt,
                "source": "zu_pairs_v1",
                "stereotype_category": r.get("stereotype_category", ""),
            })

    # Source 2: mine IsiZulu Ithute dataset (9,570 biased rows, all qa_status=passed)
    # via lexicon to generate minimal-edit pairs (drop wesifazane/wesilisa/wamadoda etc.)
    ithute = ROOT / "IsiZulu_Ithute_Dataset_Final.csv"
    if ithute.exists():
        it = pd.read_csv(ithute)
        zu_texts = it["Zulu text"].dropna().tolist() if "Zulu text" in it.columns else []
        rows.extend(_lexicon_pairs("zu", zu_texts, "zu_ithute_lexicon"))

    # Source 3: lexicon-generated from ZU GT biased rows
    gt_zu = ROOT / "eval" / "ground_truth_zu_v1.csv"
    if gt_zu.exists():
        gt = pd.read_csv(gt_zu)
        zu_texts = gt[gt["has_bias"] == True]["text"].dropna().tolist()
        rows.extend(_lexicon_pairs("zu", zu_texts, "zu_gt_lexicon"))

    # Source 4: lexicon example pairs
    rows.extend(_lexicon_example_pairs("zu"))

    df = pd.DataFrame(rows).drop_duplicates(subset=["input_text"])
    # Cap at 2,000 to keep ZU balanced with other languages — prioritise hand-curated pairs
    if len(df) > 2000:
        hand = df[df.source == "zu_pairs_v1"]
        rest = df[df.source != "zu_pairs_v1"].sample(
            n=min(2000 - len(hand), len(df) - len(hand)), random_state=42
        )
        df = pd.concat([hand, rest]).drop_duplicates(subset=["input_text"]).reset_index(drop=True)
    return df


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

    # Lexicon example pairs
    rows.extend(_lexicon_example_pairs("ki"))

    # v1 dataset extras (mũthamaki→mũtongoria single-word swaps, etc.)
    rows.extend(_load_v1_pairs("ki", "ki_v1_extra"))

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

    # Lexicon example pairs
    rows.extend(_lexicon_example_pairs("fr"))

    # v1 title-template pairs (directeur→directeur ou la directrice, etc.) — 344 unique pairs
    rows.extend(_load_v1_pairs("fr", "fr_v1_titles"))

    df = pd.DataFrame(rows).drop_duplicates(subset=["input_text"])
    # Fix grammatical gender agreement errors introduced by lexicon substitution:
    # "homme"/"femme" are masculine/feminine — "personne" is always feminine.
    df["target_text"] = (
        df["target_text"]
        .str.replace(r"\bun personne\b", "une personne", regex=True)
        .str.replace(r"\bcet personne\b", "cette personne", regex=True)
        .str.replace(r"\bUn personne\b", "Une personne", regex=True)
        .str.replace(r"\bCet personne\b", "Cette personne", regex=True)
    )
    # Drop "jeune homme" -> "jeune personne" pairs — grammatically broken and not bias
    bad_jeune = (
        df.input_text.str.contains("jeune homme", case=False, na=False)
        & df.target_text.str.contains("jeune personne", case=False, na=False)
    )
    df = df[~bad_jeune].reset_index(drop=True)
    return df


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

    # Lexicon example pairs
    rows.extend(_lexicon_example_pairs("en"))

    # Source 3: WinoBias — 3,162 high-quality occupation pronoun-swap pairs.
    # These are the single best EN source: consistent minimal edits (he/she → they),
    # short sentences, verified bias patterns across 40 occupation types.
    wb_path = ROOT / "data" / "clean" / "winobias_clean.csv"
    if wb_path.exists():
        wb = pd.read_csv(wb_path)
        # WinoBias is detection-only — no pre-made corrections.
        # Generate corrections via lexicon rules (pronoun neutralization).
        wb_texts = wb[wb["bias_label"] != "neutral"]["text"].dropna().tolist()
        rows.extend(_lexicon_pairs("en", wb_texts, "winobias"))

    # Source 4: v1 dataset extras (title expansion, generated pairs, templates)
    rows.extend(_load_v1_pairs("en", "en_v1_extra"))

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
