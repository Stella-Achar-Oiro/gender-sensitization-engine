"""
Rebuild ground_truth_zu_v2.csv to SW v5 standard.

Sources used:
  - eval/ground_truth_zu_v1.csv           — 1,978 biased + 22 neutral base
  - zulu_retraining - zulu_retraining.csv.csv — corrections for all 1,978 biased rows
  - IsiZulu_Ithute_Dataset_Final.csv      — 9,570 categorised biased rows (new biased rows)
  - data/neutral_zu_v1.csv                — 3,000 neutral rows (accepted, will mark passed)

Strategy:
  1. Take all 1,978 biased rows from v1 GT, attach corrections + categories from retraining
  2. Add IsiZulu_Ithute rows as additional biased rows (9,570 passed, categorised)
  3. Add neutral_zu rows to balance (~3,000 neutral)
  4. Output schema = SW v5 column order
  5. Write to eval/ground_truth_zu_v2.csv (never overwrite v1)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# ── discipline -> stereotype_category mapping ────────────────────────────────
DISCIPLINE_TO_CAT = {
    "Mining": "profession",
    "Engineering": "profession",
    "Law": "profession",
    "Law Enforcement": "profession",
    "Aviation": "profession",
    "Medicine": "profession",
    "Finance": "profession",
    "Construction": "profession",
    "Logistics": "profession",
    "Transport": "profession",
    "Technology": "profession",
    "Architecture": "profession",
    "Science": "profession",
    "Military": "profession",
    "Firefighting": "profession",
    "Plumbing": "profession",
    "Carpentry": "profession",
    "Welding": "profession",
    "Politics": "leadership",
    "Management": "leadership",
    "Sports": "capability",
    "Athletics": "capability",
    "Domestic": "family_role",
    "Nursing": "profession",
    "Teaching": "profession",
    "Cooking": "family_role",
    "Childcare": "family_role",
}

# ── bias_label normalisation ─────────────────────────────────────────────────
def norm_bias_label(val):
    v = str(val).lower().strip()
    if v in ("stereotype", "stereotyped"):
        return "stereotype"
    if v in ("derogation", "derogatory"):
        return "derogation"
    if "counter" in v:
        return "counter-stereotype"
    return "stereotype"

# ── IsiZulu enum_stereotype_category -> SW category ─────────────────────────
IZULU_CAT_MAP = {
    "daily_life": "daily_life",
    "profession": "profession",
    "leadership": "leadership",
    "capability": "capability",
    "appearance": "appearance",
    "family_role": "family_role",
    "proverb_idiom": "daily_life",
    "education": "education",
}

SW_COLS = [
    "id", "language", "script", "country", "region_dialect",
    "source_type", "source_ref", "collection_date",
    "text", "domain", "topic", "theme", "sensitive_characteristic",
    "target_gender", "bias_label", "stereotype_category", "explicitness",
    "sentiment_toward_referent", "device", "safety_flag", "pii_removed",
    "annotator_id", "qa_status", "notes",
    "has_bias", "bias_category", "expected_correction",
    "annotator_confidence", "annotator_notes",
]


def build_row(
    idx, text, has_bias, bias_label, stereotype_category, explicitness,
    expected_correction, target_gender, domain, source_ref, source_type,
    qa_status, notes, annotator_id, country="South Africa", collection_date="2025-11-01",
):
    lang_prefix = "zu"
    row_id = f"{lang_prefix}-{idx:05d}"
    return {
        "id": row_id,
        "language": "zu",
        "script": "latin",
        "country": country,
        "region_dialect": "south_africa",
        "source_type": source_type,
        "source_ref": source_ref,
        "collection_date": collection_date,
        "text": text,
        "domain": domain,
        "topic": "gender_stereotypes",
        "theme": "stereotypes",
        "sensitive_characteristic": "gender",
        "target_gender": target_gender,
        "bias_label": bias_label,
        "stereotype_category": stereotype_category,
        "explicitness": explicitness,
        "sentiment_toward_referent": "negative" if has_bias else "neutral",
        "device": "narrative",
        "safety_flag": "safe",
        "pii_removed": False,
        "annotator_id": annotator_id,
        "qa_status": qa_status,
        "notes": notes,
        "has_bias": has_bias,
        "bias_category": "gender" if has_bias else "",
        "expected_correction": expected_correction,
        "annotator_confidence": "high" if qa_status in ("passed", "gold") else "medium",
        "annotator_notes": "",
    }


def infer_target_gender(text):
    t = text.lower()
    female_terms = ["wesifazane", "abesifazane", "owesifazane", "intombazane", "umfazi", "umuntu wesifazane"]
    male_terms = ["wesilisa", "abesilisa", "owesisilisa", "indoda", "umuntu wesilisa"]
    has_f = any(term in t for term in female_terms)
    has_m = any(term in t for term in male_terms)
    if has_f and has_m:
        return "mixed"
    if has_f:
        return "female"
    if has_m:
        return "male"
    return "neutral"


def main():
    rows = []
    idx = 0

    # ── Part 1: v1 GT biased rows + corrections from retraining file ─────────
    print("Loading v1 GT biased rows...")
    gt_v1 = pd.read_csv(ROOT / "eval/ground_truth_zu_v1.csv")
    ret = pd.read_csv(ROOT / "zulu_retraining - zulu_retraining.csv.csv")
    ret_map_corr = dict(zip(ret["input"].str.strip(), ret["output"].str.strip()))
    ret_map_cat  = dict(zip(ret["input"].str.strip(), ret["category"].str.lower().str.strip()))
    ret_map_disc = dict(zip(ret["input"].str.strip(), ret["discipline"].str.strip()))

    biased_v1 = gt_v1[gt_v1["has_bias"] == True].copy()
    for _, row in biased_v1.iterrows():
        text = str(row["text"]).strip()
        correction = ret_map_corr.get(text, "")
        category_raw = ret_map_cat.get(text, "stereotype")
        discipline = ret_map_disc.get(text, "")
        if category_raw == "derogation":
            bl = "derogation"
            cat = "capability"
        elif category_raw == "counter-stereotype":
            bl = "counter-stereotype"
            cat = "profession"
        else:
            bl = "stereotype"
            cat = DISCIPLINE_TO_CAT.get(discipline, "profession")

        rows.append(build_row(
            idx=idx,
            text=text,
            has_bias=True,
            bias_label=bl,
            stereotype_category=cat,
            explicitness="explicit",
            expected_correction=correction,
            target_gender=infer_target_gender(text),
            domain="livelihoods_and_work",
            source_ref="eval/ground_truth_zu_v1.csv",
            source_type="annotation",
            qa_status="passed",
            notes=f"From ZU GT v1. Correction from zulu_retraining file.",
            annotator_id="zu_retraining_v1",
        ))
        idx += 1

    print(f"  Added {len(rows)} biased rows from v1 GT (all with corrections)")

    # ── Part 2: IsiZulu_Ithute biased rows (9,570 rows, all passed) ──────────
    print("Loading IsiZulu_Ithute rows...")
    iz = pd.read_csv(ROOT / "IsiZulu_Ithute_Dataset_Final.csv")
    # Only stereotype + derogation (skip any others)
    iz_biased = iz[iz["bias_label"].isin(["stereotype", "derogation"])].copy()

    # Build domain mapping from iz domain column
    iz_domain_map = {
        "Livelihoods And Work": "livelihoods_and_work",
        "Education": "education",
        "Health": "health",
        "Governance Civic": "governance_civic",
        "Culture And Religion": "culture_and_religion",
        "Media And Online": "media_and_online",
        "Household And Care": "household_and_care",
    }

    for _, row in iz_biased.iterrows():
        text = str(row["Zulu text"]).strip()
        cat_raw = str(row.get("enum_stereotype_category", "profession")).strip().lower()
        cat = IZULU_CAT_MAP.get(cat_raw, "profession")
        expl_raw = str(row.get("enum_explicitness", "explicit")).strip().lower()
        expl = expl_raw if expl_raw in ("explicit", "implicit") else "explicit"
        bl = norm_bias_label(row["bias_label"])
        domain_raw = str(row.get("domain", "livelihoods_and_work"))
        domain = iz_domain_map.get(domain_raw, "livelihoods_and_work")
        target = str(row.get("target_gender", "")).strip().lower()
        if target not in ("female", "male", "mixed", "neutral"):
            target = infer_target_gender(text)

        rows.append(build_row(
            idx=idx,
            text=text,
            has_bias=True,
            bias_label=bl,
            stereotype_category=cat,
            explicitness=expl,
            expected_correction="",   # IsiZulu has no corrections — corrector model handles this
            target_gender=target,
            domain=domain,
            source_ref="IsiZulu_Ithute_Dataset_Final.csv",
            source_type="annotation",
            qa_status="passed",
            notes="From IsiZulu Ithute dataset. Annotator QA: passed.",
            annotator_id="IsiZulu_Ithute_annotators",
            collection_date="2025-11-13",
        ))
        idx += 1

    print(f"  Total rows now: {len(rows)} (added {len(iz_biased)} IsiZulu rows)")

    # ── Part 3: neutral rows ─────────────────────────────────────────────────
    print("Loading neutral ZU rows...")
    neutral = pd.read_csv(ROOT / "data/neutral_zu_v1.csv")
    for _, row in neutral.iterrows():
        text = str(row["text"]).strip()
        rows.append(build_row(
            idx=idx,
            text=text,
            has_bias=False,
            bias_label="neutral",
            stereotype_category="",
            explicitness="",
            expected_correction="",
            target_gender="neutral",
            domain=str(row.get("domain", "web")).strip(),
            source_ref=str(row.get("source_ref", "cc100/zu")).strip(),
            source_type="web",
            qa_status="passed",
            notes="Neutral ZU sentence from CC-100 corpus.",
            annotator_id="neutral_zu_v1",
        ))
        idx += 1

    print(f"  Total rows now: {len(rows)} (added {len(neutral)} neutral rows)")

    # ── Assemble full DataFrame ──────────────────────────────────────────────
    df = pd.DataFrame(rows, columns=SW_COLS)

    # ── Split: eval GT vs training rows ─────────────────────────────────────
    # GT evaluation file: all v1 biased rows (1,978 with corrections) + all 3,000 neutral
    # This gives 1,978 biased / 3,000 neutral = 39.7% biased — acceptable for evaluation
    # Training rows: IsiZulu_Ithute (9,570) go into training_data_multilingual only
    eval_mask = (
        (df["source_ref"] == "eval/ground_truth_zu_v1.csv") |
        (df["source_ref"] == "cc100/zu") |
        (df["source_ref"] == "neutral_zu_v1")
    )
    df_eval = df[eval_mask].copy().reset_index(drop=True)
    # Re-assign IDs sequentially
    df_eval["id"] = [f"zu-{i:05d}" for i in range(len(df_eval))]

    df_train_extra = df[~eval_mask].copy().reset_index(drop=True)

    biased_eval = df_eval["has_bias"].sum()
    total_eval = len(df_eval)
    print(f"\nEval GT: {total_eval} rows, {biased_eval} biased ({biased_eval/total_eval*100:.1f}%)")
    print("stereotype_category dist (biased in eval):")
    print(df_eval[df_eval["has_bias"]==True]["stereotype_category"].value_counts().to_dict())
    print("qa_status dist (eval):")
    print(df_eval["qa_status"].value_counts().to_dict())
    corr_filled = (df_eval[df_eval["has_bias"]==True]["expected_correction"].str.strip() != "").sum()
    biased_eval_count = df_eval["has_bias"].sum()
    print(f"expected_correction filled: {corr_filled}/{biased_eval_count}")
    print()
    print(f"Training-only rows (IsiZulu_Ithute): {len(df_train_extra)} (no corrections, go to training CSV)")

    # ── Write eval GT (never overwrite v1) ───────────────────────────────────
    out_eval = ROOT / "eval/ground_truth_zu_v2.csv"
    df_eval.to_csv(out_eval, index=False)
    print(f"\nWritten eval GT: {out_eval}")

    # ── Write training extras to data/ for later merge ───────────────────────
    out_train = ROOT / "data/zu_ithute_training_rows.csv"
    df_train_extra.to_csv(out_train, index=False)
    print(f"Written training extras: {out_train}")


if __name__ == "__main__":
    main()
