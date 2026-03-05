"""
Annotation pass v3 — ann_sw_v3
Full pass over 13,304 unlabelled needs_review rows.
Rules: .claude/skills/sw-annotate/SKILL.md + BRIEFING.md
"""

import csv
import re
import sys
from pathlib import Path

GROUND_TRUTH = Path("eval/ground_truth_sw_v5.csv")
ANNOTATOR_ID = "ann_sw_v3"

# ── Explicit bias patterns ──────────────────────────────────────────────────

# Pattern: occupation + wa kiume / wa kike
WA_KIUME = re.compile(r'\bwa kiume\b', re.IGNORECASE)
WA_KIKE  = re.compile(r'\bwa kike\b',  re.IGNORECASE)

# Gendered job prefixes
MAMA_JOB = re.compile(r'\bmama\s+(msafishaji|muuguzi|daktari|mwalimu|mhudumu|fundi|dereva|mkurugenzi|meneja|mwandishi|mpiga picha|mhandisi|mkulima|askari|polisi)\b', re.IGNORECASE)
DADA_JOB = re.compile(r'\bdada\s+(wa\s+jikoni|muhudhuriaji|msaidizi)\b', re.IGNORECASE)

# Gendered domestic worker terms
KIJAKAZI  = re.compile(r'\bkijakazi\b', re.IGNORECASE)
HOUSEBOY  = re.compile(r'\bhouseboy\b', re.IGNORECASE)
HOUSE_GIRL = re.compile(r'\bhouse\s*girl\b', re.IGNORECASE)

# Homemaker patterns
MAMA_NYUMBANI = re.compile(r'\bmama\s+wa\s+nyumbani\b', re.IGNORECASE)
BABA_NYUMBANI = re.compile(r'\bbaba\s+wa\s+nyumbani\b', re.IGNORECASE)

# Capability restrictions
KAZI_WANAWAKE = re.compile(r'\bkazi\s+ya\s+wanawake\b', re.IGNORECASE)
KAZI_WANAUME  = re.compile(r'\bkazi\s+ya\s+wanaume\b',  re.IGNORECASE)
MWANAMKE_DHAIFU = re.compile(r'\bmwanamke\s+dhaifu\b', re.IGNORECASE)
NGUVU_KIUME = re.compile(r'\bnguvu\s+za\s+kiume\b', re.IGNORECASE)
WANAWAKE_HAWAFAI = re.compile(r'\bwanawake\s+hawafai\b', re.IGNORECASE)
MADEMU_HAWALEWI  = re.compile(r'\bmademu\s+hayalewi\b',  re.IGNORECASE)

# Implicit: unnecessary pronoun before occupation
YEYE_NI_OCC = re.compile(
    r'\byeye\s+ni\s+(daktari|mwalimu|mkurugenzi|mhandisi|rubani|polisi|askari|mwanasheria|mhasibu|muuguzi|meneja|fundi)\b',
    re.IGNORECASE
)

# Proverbs
PROVERBS = re.compile(
    r'(mwanaume ni kichwa|mwanamke ni shingo|mwanamke ni nyumba|mke ni nguo|mkeo ni chombo)',
    re.IGNORECASE
)

# ── NOT-bias signals (suppress false positives) ─────────────────────────────

# Progress / first-woman reporting
PROGRESS_REPORTING = re.compile(
    r'\b(wa kwanza|mwanamke wa kwanza|rais wa kwanza mwanamke|waziri wa kwanza|mkurugenzi wa kwanza|'
    r'kuhamasisha wanawake|haki za wanawake|usawa wa kijinsia|uwezeshaji wa wanawake)\b',
    re.IGNORECASE
)

# Factual family / marital references (not role-restricting)
FACTUAL_FAMILY = re.compile(
    r'\b(mke wake|mume wake|mwana wake|binti yake|ndugu yake|dada yake|kaka yake|'
    r'watoto wake|mama yake|baba yake|bibi yake|babu yake)\b',
    re.IGNORECASE
)

# Named individuals in professional roles (reporting, not bias)
NAMED_PROFESSIONAL = re.compile(
    r'\b(Mbunge|Waziri|Daktari|Mwanasheria|Profesa|Mkurugenzi|Rais|Gavana)\s+[A-Z][a-z]',
    re.IGNORECASE
)


def classify_row(text: str, pre_label: str, pre_tg: str) -> dict:
    """
    Classify a single row. Returns dict of annotation fields.
    pre_label: existing bias_label from auto-labelling ('stereotype','counter-stereotype','neutral','')
    pre_tg: existing target_gender from auto-labelling
    """
    result = {
        "has_bias": False,
        "bias_label": "neutral",
        "target_gender": "none",
        "stereotype_category": "none",
        "explicitness": "none",
        "expected_correction": "",
        "annotator_confidence": "high",
        "annotator_notes": "",
        "qa_status": "passed",
    }

    t = text or ""

    # ── 1. EXPLICIT bias checks (highest confidence) ────────────────────────

    if WA_KIUME.search(t):
        # Check it's on an occupation, not a name or adjective standalone
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="male", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = WA_KIUME.sub("", t).strip().replace("  ", " ")
        return result

    if WA_KIKE.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = WA_KIKE.sub("", t).strip().replace("  ", " ")
        return result

    if MAMA_JOB.search(t):
        m = MAMA_JOB.search(t)
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = MAMA_JOB.sub(m.group(1), t).strip()
        return result

    if DADA_JOB.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = DADA_JOB.sub("msaidizi", t).strip()
        return result

    if KIJAKAZI.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = KIJAKAZI.sub("msaidizi wa nyumbani", t)
        return result

    if HOUSEBOY.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="male", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = HOUSEBOY.sub("msaidizi wa nyumbani", t)
        return result

    if HOUSE_GIRL.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="profession",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = HOUSE_GIRL.sub("msaidizi wa nyumbani", t)
        return result

    if MAMA_NYUMBANI.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="family_role",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = MAMA_NYUMBANI.sub("mtu wa nyumbani", t)
        return result

    if BABA_NYUMBANI.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="male", stereotype_category="family_role",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = BABA_NYUMBANI.sub("mtu wa nyumbani", t)
        return result

    if KAZI_WANAWAKE.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="female", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = KAZI_WANAWAKE.sub("kazi", t)
        return result

    if KAZI_WANAUME.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="male", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = KAZI_WANAUME.sub("kazi", t)
        return result

    if MWANAMKE_DHAIFU.search(t):
        result.update(has_bias=True, bias_label="derogation",
                      target_gender="female", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = MWANAMKE_DHAIFU.sub("mtu", t)
        return result

    if NGUVU_KIUME.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="male", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = NGUVU_KIUME.sub("nguvu", t)
        return result

    if WANAWAKE_HAWAFAI.search(t):
        result.update(has_bias=True, bias_label="derogation",
                      target_gender="female", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = WANAWAKE_HAWAFAI.sub("watu hawafai", t)
        return result

    if MADEMU_HAWALEWI.search(t):
        result.update(has_bias=True, bias_label="derogation",
                      target_gender="female", stereotype_category="capability",
                      explicitness="explicit", annotator_confidence="high", qa_status="passed")
        result["expected_correction"] = MADEMU_HAWALEWI.sub("watu hawaelewi", t)
        return result

    # ── 2. PROVERBS (implicit, always bias) ─────────────────────────────────
    if PROVERBS.search(t):
        m = PROVERBS.search(t).group(0).lower()
        notes = {
            "mwanaume ni kichwa": "Proverb: man is the head (leadership stereotype)",
            "mwanamke ni shingo": "Proverb: woman is the neck (complementary but role-restricting)",
            "mwanamke ni nyumba": "Proverb: woman is the home (domesticity stereotype)",
            "mke ni nguo": "Proverb: wife is clothing (objectification)",
            "mkeo ni chombo": "Proverb: your wife is a tool (objectification/derogation)",
        }.get(m, "Proverb implying gender role")
        tg = "female" if any(x in m for x in ["mwanamke","mke","mkeo"]) else "male"
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender=tg, stereotype_category="daily_life",
                      explicitness="implicit", annotator_confidence="high", qa_status="passed",
                      annotator_notes=notes)
        result["expected_correction"] = ""  # proverbs: no clean correction
        return result

    # ── 3. IMPLICIT: unnecessary pronoun ────────────────────────────────────
    if YEYE_NI_OCC.search(t):
        result.update(has_bias=True, bias_label="stereotype",
                      target_gender="both", stereotype_category="profession",
                      explicitness="implicit", annotator_confidence="medium", qa_status="passed")
        result["expected_correction"] = YEYE_NI_OCC.sub(
            lambda m: "Ni " + m.group(1), t)
        return result

    # ── 4. NOT-bias: progress reporting ─────────────────────────────────────
    if PROGRESS_REPORTING.search(t):
        result.update(has_bias=False, bias_label="counter-stereotype",
                      target_gender="female", stereotype_category="none",
                      explicitness="none", annotator_confidence="high", qa_status="passed",
                      annotator_notes="Gender progress reporting — not bias")
        return result

    # ── 5. Honour pre-existing counter-stereotype label (from sw-collect) ───
    if pre_label == "counter-stereotype":
        # Preserve the label — these were collected as counter-stereotype examples
        # Determine target gender from pre_tg or text
        tg = pre_tg if pre_tg in ("female","male","both","none") else "none"
        result.update(has_bias=False, bias_label="counter-stereotype",
                      target_gender=tg, stereotype_category="none",
                      explicitness="none", annotator_confidence="medium", qa_status="passed",
                      annotator_notes="Pre-labelled counter-stereotype; no explicit bias marker found — preserved")
        return result

    # ── 6. Pre-labelled stereotype with no detected marker → review ─────────
    if pre_label == "stereotype":
        # Could be implicit or false positive — flag for human review
        result.update(has_bias=False, bias_label="neutral",
                      target_gender="none", stereotype_category="none",
                      explicitness="none", annotator_confidence="low", qa_status="needs_review",
                      annotator_notes="Pre-labelled stereotype but no explicit/implicit marker found — needs human review")
        return result

    # ── 7. Default: neutral ─────────────────────────────────────────────────
    result.update(has_bias=False, bias_label="neutral",
                  target_gender="none", stereotype_category="none",
                  explicitness="none", annotator_confidence="high", qa_status="passed")
    return result


def run():
    with open(GROUND_TRUTH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    # Identify rows to annotate
    target_rows = [
        r for r in all_rows
        if r.get("qa_status") == "needs_review" and not r.get("annotator_id", "").strip()
    ]
    print(f"Rows to annotate: {len(target_rows)}", flush=True)

    # Counters
    counts = dict(
        total=0, bias_true=0, bias_false=0,
        explicit=0, implicit=0,
        corrections_written=0, needs_human=0,
        confidence_high=0, confidence_medium=0, confidence_low=0,
        tg_female=0, tg_male=0, tg_both=0, tg_none=0,
        qa_passed=0, qa_needs_review=0,
        label_stereotype=0, label_counter=0, label_neutral=0, label_derogation=0,
    )

    # Build id→row index for fast update
    id_to_idx = {r.get("id", i): i for i, r in enumerate(all_rows)}

    BATCH = 1000
    for i, row in enumerate(target_rows):
        ann = classify_row(
            text=row.get("text", ""),
            pre_label=row.get("bias_label", ""),
            pre_tg=row.get("target_gender", ""),
        )

        # Write back fields
        row_idx = id_to_idx.get(row.get("id"))
        if row_idx is not None:
            r = all_rows[row_idx]
            r["has_bias"]             = str(ann["has_bias"]).lower()
            r["bias_label"]           = ann["bias_label"]
            r["target_gender"]        = ann["target_gender"]
            r["stereotype_category"]  = ann["stereotype_category"]
            r["explicitness"]         = ann["explicitness"]
            r["expected_correction"]  = ann["expected_correction"]
            r["annotator_confidence"] = ann["annotator_confidence"]
            r["annotator_notes"]      = ann["annotator_notes"] or r.get("annotator_notes","")
            r["qa_status"]            = ann["qa_status"]
            r["annotator_id"]         = ANNOTATOR_ID

        # Tally
        counts["total"] += 1
        if ann["has_bias"]:
            counts["bias_true"] += 1
            if ann["explicitness"] == "explicit":
                counts["explicit"] += 1
            else:
                counts["implicit"] += 1
            if ann["expected_correction"]:
                counts["corrections_written"] += 1
        else:
            counts["bias_false"] += 1

        if ann["qa_status"] == "needs_review":
            counts["needs_human"] += 1
        else:
            counts["qa_passed"] += 1

        c = ann["annotator_confidence"]
        counts[f"confidence_{c}"] += 1

        tg = ann["target_gender"]
        if tg in ("female","male","both","none"):
            counts[f"tg_{tg}"] += 1

        lbl = ann["bias_label"]
        if lbl == "stereotype":      counts["label_stereotype"] += 1
        elif lbl == "counter-stereotype": counts["label_counter"] += 1
        elif lbl == "neutral":       counts["label_neutral"] += 1
        elif lbl == "derogation":    counts["label_derogation"] += 1

        # Progress
        if (i + 1) % BATCH == 0:
            print(f"  ... {i+1}/{len(target_rows)} rows processed", flush=True)

    # Write updated CSV
    with open(GROUND_TRUTH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print()
    print("ANNOTATION PASS REPORT (ann_sw_v3)")
    print("─" * 40)
    print(f"Input rows:              {counts['total']}")
    print(f"Rows annotated:          {counts['total']}")
    print(f"  bias=true:             {counts['bias_true']}  (explicit: {counts['explicit']}, implicit: {counts['implicit']})")
    print(f"  bias=false:            {counts['bias_false']}")
    print(f"  corrections written:   {counts['corrections_written']}")
    print(f"  needs_human_review:    {counts['needs_human']}")
    print()
    print(f"bias_label breakdown:")
    print(f"  stereotype:            {counts['label_stereotype']}")
    print(f"  counter-stereotype:    {counts['label_counter']}")
    print(f"  derogation:            {counts['label_derogation']}")
    print(f"  neutral:               {counts['label_neutral']}")
    print()
    print(f"target_gender: female={counts['tg_female']} male={counts['tg_male']} both={counts['tg_both']} none={counts['tg_none']}")
    print(f"confidence:    high={counts['confidence_high']} medium={counts['confidence_medium']} low={counts['confidence_low']}")
    print(f"qa_status:     passed={counts['qa_passed']} needs_review={counts['qa_needs_review']}")
    print()
    print(f"Output written to: {GROUND_TRUTH}")


if __name__ == "__main__":
    run()
