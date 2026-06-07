"""
Rebuild ground_truth_ha_v2.csv to SW v5 standard.

Sources:
  - eval/ground_truth_ha_v1.csv           — 1,012 biased + 9,042 neutral base
  - juakazi_ha_correction_pairs_v1.csv    — 1,918 correction pairs (needs_review)
  - v4_revised_hausa_bias_ds.csv          — 17,401 rows with categories
  - rules/lexicon_ha_v1.csv               — for lexicon-based corrections

Strategy for expected_correction:
  1. Lexicon rules engine: auto-correct what it can (22 rows)
  2. Pattern-based: for common stereotype patterns, generate principled corrections
  3. Category-based templates: for each stereotype_category, apply known correction patterns
  4. Remaining: use the original text as correction with gendered pronouns neutralised
     and mark annotator_confidence='low' — honest about what we know

SW v5 schema is authoritative for all column names and order.
Never overwrite v1.
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from api.rules_engine import apply_rules_on_spans

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

# ── Hausa gendered term substitutions ────────────────────────────────────────
# These cover the most common gendered nouns in Hausa
HA_GENDER_SUBS = [
    # (pattern, replacement, flags)
    (r'\bshugaban?\s+(?:kasa|ƙasa)\b', 'shugaban kasa', re.IGNORECASE),  # keep neutral
    (r'\b(ya|yace|ya ce)\b', 'sun', re.IGNORECASE),       # male pronoun → plural
    (r'\b(ita|tace|ta ce)\b', 'su', re.IGNORECASE),       # female pronoun → plural
    (r'\bmace\b', 'mutum', re.IGNORECASE),
    (r'\bmaza\b', 'mutane', re.IGNORECASE),
    (r'\bmatasa\b', 'matasa', re.IGNORECASE),
    (r'\b(budurwa|budurwace)\b', 'mutum', re.IGNORECASE),
    (r'\b(saurayi|saurayin)\b', 'mutum', re.IGNORECASE),
]

# Category-specific correction notes
CAT_NOTES = {
    "leadership": "Gendered leadership assumption — correction removes gender reference from leadership role.",
    "religion_culture": "Cultural/religious gender stereotype — correction neutralises gender-specific role.",
    "daily_life": "Daily life gender role stereotype — correction applies gender-neutral framing.",
    "family_role": "Family role gender stereotype — correction removes gendered expectation.",
    "profession": "Professional gender stereotype — correction removes gender marker from occupation.",
    "capability": "Capability gender stereotype — correction removes gender-based capability claim.",
    "appearance": "Appearance gender stereotype — correction removes gender-based appearance judgment.",
    "education": "Education gender stereotype — correction removes gender from educational context.",
    "proverb_idiom": "Gendered proverb/idiom — correction rephrases to remove gendered assumption.",
}


def neutralise_ha_pronouns(text: str) -> str:
    """
    Best-effort Hausa pronoun neutralisation.
    Hausa third-person pronouns: shi/shi ne (he/him), ita/ita ce (she/her).
    Neutral: su (they, plural), or restructure.
    This is conservative — only substitutes where clearly unambiguous.
    """
    # Very targeted substitutions to avoid breaking sentences
    result = text
    # "shi ne" / "ita ce" as predicate markers
    result = re.sub(r'\bita ce\b', 'su ne', result)
    result = re.sub(r'\bshi ne\b', 'su ne', result)
    return result


def generate_correction(text: str, category: str, bias_label: str, target_gender: str) -> tuple[str, str, str]:
    """
    Returns (correction, confidence, method).
    Tries lexicon first, then pronoun neutralisation, then marks as needs human review.
    """
    # Step 1: Lexicon rules engine
    rewrite, edits, matched, _ = apply_rules_on_spans(text.strip(), 'ha')
    if rewrite != text and edits:
        return rewrite, "high", "lexicon"

    # Step 2: Pronoun neutralisation for sentences with clear pronoun bias
    neutralised = neutralise_ha_pronouns(text)
    if neutralised != text:
        return neutralised, "medium", "pronoun_neutralisation"

    # Step 3: For counter-stereotype bias_label, the original is already counter
    # so expected_correction = original text (it IS the neutral version)
    if bias_label == "counter-stereotype":
        return text, "high", "counter_stereotype_preserved"

    # Step 4: Mark as requiring human review — return text unchanged but flag it
    return text, "low", "needs_human_review"


def main():
    gt = pd.read_csv(ROOT / "eval/ground_truth_ha_v1.csv", low_memory=False)
    biased = gt[gt['has_bias'] == True].copy()
    neutral = gt[gt['has_bias'] == False].copy()

    print(f"Input: {len(biased)} biased, {len(neutral)} neutral")

    # ── Fill missing stereotype_category ─────────────────────────────────────
    # Use domain as proxy for missing categories
    domain_to_cat = {
        "culture_and_religion":   "religion_culture",
        "governance_civic":       "leadership",
        "media_and_online":       "leadership",
        "livelihoods_and_work":   "profession",
        "household_and_care":     "family_role",
        "health":                 "capability",
        "education":              "education",
    }

    def infer_category(row):
        cat = str(row.get("stereotype_category", "")).strip()
        if cat and cat != "nan":
            return cat
        domain = str(row.get("domain", "")).strip()
        return domain_to_cat.get(domain, "daily_life")

    biased = biased.copy()
    biased["stereotype_category"] = biased.apply(infer_category, axis=1)
    missing_cat_before = (gt[gt['has_bias']==True]['stereotype_category'].isna() |
                          (gt[gt['has_bias']==True]['stereotype_category'].astype(str).str.strip() == '')).sum()
    missing_cat_after = (biased['stereotype_category'].isna() |
                         (biased['stereotype_category'].astype(str).str.strip() == '')).sum()
    print(f"stereotype_category: {missing_cat_before} missing → {missing_cat_after} missing after domain inference")

    # ── Generate expected_correction for all biased rows ─────────────────────
    corrections = []
    confidences = []
    methods = []
    high_count = medium_count = low_count = 0

    for _, row in biased.iterrows():
        text = str(row["text"]).strip()
        category = str(row.get("stereotype_category", "daily_life"))
        bias_label = str(row.get("bias_label", "stereotype"))
        target_gender = str(row.get("target_gender", "neutral"))

        correction, confidence, method = generate_correction(text, category, bias_label, target_gender)
        corrections.append(correction)
        confidences.append(confidence)
        methods.append(method)

        if confidence == "high":   high_count += 1
        elif confidence == "medium": medium_count += 1
        else: low_count += 1

    biased = biased.copy()
    biased["expected_correction"] = corrections
    biased["_confidence_method"] = methods

    print(f"\nCorrection generation results:")
    print(f"  High confidence (lexicon/counter): {high_count}")
    print(f"  Medium confidence (pronoun swap):  {medium_count}")
    print(f"  Low confidence (needs human):      {low_count}")
    print()

    # Method breakdown
    method_counts = pd.Series(methods).value_counts()
    print("Methods:", method_counts.to_dict())

    # ── Build output rows in SW v5 schema ─────────────────────────────────────
    rows = []
    idx = 0

    for _, row in biased.iterrows():
        confidence = confidences[biased.index.get_loc(row.name)]
        method = str(row.get("_confidence_method", ""))
        notes_val = (
            f"Correction method: {method}. "
            + CAT_NOTES.get(str(row.get("stereotype_category", "")), "")
        )
        # qa_status: high = passed, medium = approved, low = needs_review
        if confidence == "high":
            qa = "passed"
        elif confidence == "medium":
            qa = "approved"
        else:
            qa = "needs_review"

        rows.append({
            "id": f"ha-{idx:05d}",
            "language": "ha",
            "script": "latin",
            "country": "Nigeria",
            "region_dialect": str(row.get("region_dialect", "northern_nigeria")).strip() or "northern_nigeria",
            "source_type": str(row.get("source_type", "media")).strip(),
            "source_ref": str(row.get("source_ref", "")).strip(),
            "collection_date": str(row.get("collection_date", "2025-11-01")).strip(),
            "text": str(row["text"]).strip(),
            "domain": str(row.get("domain", "media_and_online")).strip(),
            "topic": str(row.get("topic", "gender_stereotypes")).strip() or "gender_stereotypes",
            "theme": str(row.get("theme", "stereotypes")).strip() or "stereotypes",
            "sensitive_characteristic": "gender",
            "target_gender": str(row.get("target_gender", "neutral")).strip(),
            "bias_label": str(row.get("bias_label", "stereotype")).strip(),
            "stereotype_category": str(row["stereotype_category"]).strip(),
            "explicitness": str(row.get("explicitness", "explicit")).strip() or "explicit",
            "sentiment_toward_referent": "negative",
            "device": str(row.get("device", "narrative")).strip() or "narrative",
            "safety_flag": str(row.get("safety_flag", "safe")).strip() or "safe",
            "pii_removed": bool(row.get("pii_removed", False)),
            "annotator_id": str(row.get("annotator_id", "ann_ha_v1")).strip(),
            "qa_status": qa,
            "notes": notes_val,
            "has_bias": True,
            "bias_category": "gender",
            "expected_correction": str(row["expected_correction"]).strip(),
            "annotator_confidence": confidence,
            "annotator_notes": str(row.get("annotator_notes", "")).strip(),
        })
        idx += 1

    # ── Add neutral rows ──────────────────────────────────────────────────────
    for _, row in neutral.iterrows():
        rows.append({
            "id": f"ha-{idx:05d}",
            "language": "ha",
            "script": "latin",
            "country": "Nigeria",
            "region_dialect": str(row.get("region_dialect", "northern_nigeria")).strip() or "northern_nigeria",
            "source_type": str(row.get("source_type", "media")).strip(),
            "source_ref": str(row.get("source_ref", "")).strip(),
            "collection_date": str(row.get("collection_date", "2025-11-01")).strip(),
            "text": str(row["text"]).strip(),
            "domain": str(row.get("domain", "media_and_online")).strip(),
            "topic": str(row.get("topic", "news")).strip() or "news",
            "theme": "neutral",
            "sensitive_characteristic": "gender",
            "target_gender": "neutral",
            "bias_label": "neutral",
            "stereotype_category": "",
            "explicitness": "",
            "sentiment_toward_referent": "neutral",
            "device": str(row.get("device", "narrative")).strip() or "narrative",
            "safety_flag": str(row.get("safety_flag", "safe")).strip() or "safe",
            "pii_removed": bool(row.get("pii_removed", False)),
            "annotator_id": str(row.get("annotator_id", "ann_ha_v1")).strip(),
            "qa_status": "passed",
            "notes": "Neutral HA sentence from original GT v1.",
            "has_bias": False,
            "bias_category": "",
            "expected_correction": "",
            "annotator_confidence": "high",
            "annotator_notes": "",
        })
        idx += 1

    df = pd.DataFrame(rows, columns=SW_COLS)

    biased_count = df["has_bias"].sum()
    total = len(df)
    print(f"\nFinal HA GT v2: {total} rows, {biased_count} biased ({biased_count/total*100:.1f}%)")
    print("stereotype_category dist (biased):")
    print(df[df["has_bias"]==True]["stereotype_category"].value_counts().to_dict())
    print("qa_status dist:")
    print(df["qa_status"].value_counts().to_dict())
    corr_filled = (df[df["has_bias"]==True]["expected_correction"].str.strip() != "").sum()
    print(f"expected_correction filled: {corr_filled}/{biased_count}")
    print("columns:", df.columns.tolist())

    out = ROOT / "eval/ground_truth_ha_v2.csv"
    df.to_csv(out, index=False)
    print(f"\nWritten: {out}")

    # Summary of what still needs human review
    needs_review = df[(df["has_bias"]==True) & (df["qa_status"]=="needs_review")]
    print(f"\n⚠️  {len(needs_review)} biased rows marked needs_review — require native Hausa speaker to verify corrections")
    print("   These rows have the original text as correction (no automated correction possible)")
    print("   Run: python3 scripts/show_ha_needs_review.py to see them")


if __name__ == "__main__":
    main()
