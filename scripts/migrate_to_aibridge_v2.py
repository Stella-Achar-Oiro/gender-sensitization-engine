"""
Migrate legacy ground truth CSVs to canonical AIBRIDGE schema.

Usage:
    python3 scripts/migrate_to_aibridge_v2.py <input.csv> <output.csv> <lang>

Example:
    python3 scripts/migrate_to_aibridge_v2.py eval/ground_truth_fr_v4.csv eval/ground_truth_fr_v5.csv fr
"""

import csv
import sys
from datetime import date

CANONICAL_COLS = [
    "id", "language", "script", "country", "region_dialect", "source_type", "source_ref",
    "collection_date", "text", "domain", "topic", "theme", "sensitive_characteristic",
    "target_gender", "bias_label", "stereotype_category", "explicitness",
    "sentiment_toward_referent", "device", "safety_flag", "pii_removed",
    "annotator_id", "qa_status", "notes"
]

RENAME_MAP = {
    "sample_id": "id",
    "regional_variant": "region_dialect",
    "data_source": "source_type",
    "source_url": "source_ref",
    "sentiment": "sentiment_toward_referent",
    "validation_status": "qa_status",
    "protected_attribute": "sensitive_characteristic",
}

SOURCE_TYPE_REMAP = {
    "bible": "web_public",
    "scripted": "community",
    "news": "media",
    "wikipedia": "web_public",
    "government": "web_public",
    "corporate": "web_public",
    "education": "web_public",
    # Kikuyu-specific sources
    "anv_kenya": "community",
    "waxal_tts": "community",
    "flores200": "web_public",
    "kikuyu_kiswahili_translation": "community",
    "digigreen_asr": "community",
    "digigreen_cgiar_translation": "community",
}

QA_STATUS_REMAP = {
    "validated": "passed",
    "NEEDS_ANNOTATION": "needs_review",
    "": "needs_review",
}

SAFETY_FLAG_REMAP = {
    "none": "safe",
    "safe": "safe",
    "sensitive": "sensitive",
    "reject": "reject",
    "": "safe",
}

DOMAIN_REMAP = {
    # Kikuyu-specific → canonical
    "speech_corpus": "media_and_online",
    "translation_benchmark": "media_and_online",
    "translation_corpus": "media_and_online",
    "religious_text": "culture_and_religion",
    "agriculture": "livelihoods_and_work",
}

LANG_DEFAULTS = {
    "fr": {"script": "latin", "country": "Kenya"},
    "en": {"script": "latin", "country": "Kenya"},
    "sw": {"script": "latin", "country": "Kenya"},
    "ki": {"script": "latin", "country": "Kenya"},
}

# bias_category → bias_label
BIAS_LABEL_MAP = {
    "occupation": "stereotype",
    "pronoun_assumption": "stereotype",
    "pronoun_generic": "stereotype",
    "honorific": "stereotype",
    "morphology": "stereotype",
    "none": "neutral",
    "": "neutral",
}

# bias_category → stereotype_category
STEREOTYPE_CAT_MAP = {
    "occupation": "profession",
    "pronoun_assumption": "family_role",
    "pronoun_generic": "daily_life",
    "honorific": "profession",
    "morphology": "daily_life",
    "none": "",
    "": "",
}

# bias_category → domain
DOMAIN_MAP = {
    "occupation": "livelihoods_and_work",
    "pronoun_assumption": "household_and_care",
    "pronoun_generic": "household_and_care",
    "honorific": "governance_civic",
    "morphology": "media_and_online",
    "none": "media_and_online",
    "": "media_and_online",
}

# domain → topic
TOPIC_MAP = {
    "livelihoods_and_work": "occupation_roles",
    "household_and_care": "domestic_roles",
    "governance_civic": "political_representation",
    "media_and_online": "media_representation",
    "culture_and_religion": "traditional_roles",
    "education": "academic_roles",
    "health": "healthcare_roles",
}


def infer_bias_label(row):
    """Infer bias_label from has_bias + bias_category."""
    if row.get("bias_label"):
        return row["bias_label"]
    has_bias = str(row.get("has_bias", "false")).strip().lower()
    bias_cat = row.get("bias_category", "").strip().lower()
    if has_bias == "true":
        return BIAS_LABEL_MAP.get(bias_cat, "stereotype")
    return "neutral"


def infer_stereotype_category(row, bias_label):
    """Infer stereotype_category — blank if neutral."""
    if bias_label == "neutral":
        return ""
    existing = row.get("stereotype_category", "").strip()
    if existing:
        return existing
    bias_cat = row.get("bias_category", "").strip().lower()
    return STEREOTYPE_CAT_MAP.get(bias_cat, "")


def infer_explicitness(row, bias_label):
    """explicit/implicit for biased, blank for neutral."""
    if bias_label == "neutral":
        return ""
    existing = row.get("explicitness", "").strip()
    return existing if existing else "explicit"


def infer_domain(row):
    existing = row.get("domain", "").strip()
    if existing:
        # Remap non-canonical domain values
        return DOMAIN_REMAP.get(existing, existing)
    bias_cat = row.get("bias_category", "").strip().lower()
    return DOMAIN_MAP.get(bias_cat, "media_and_online")


def infer_topic(domain):
    return TOPIC_MAP.get(domain, "media_representation")


def infer_theme(bias_label):
    return "stereotypes" if bias_label != "neutral" else "public_interest"


def migrate_row(row, idx, lang, existing_cols):
    """Migrate a single row to canonical schema."""
    # Apply column renames first
    for old, new in RENAME_MAP.items():
        if old in row and new not in row:
            row[new] = row.pop(old)

    lang_defaults = LANG_DEFAULTS.get(lang, {"script": "latin", "country": ""})

    bias_label = infer_bias_label(row)
    domain = infer_domain(row)

    new_row = {}

    # --- Canonical fields ---
    new_row["id"] = row.get("id") or f"{lang}-{idx:05d}"
    new_row["language"] = row.get("language") or lang
    new_row["script"] = row.get("script") or lang_defaults["script"]
    new_row["country"] = row.get("country") or lang_defaults["country"]
    new_row["region_dialect"] = row.get("region_dialect", "")
    source_type_raw = row.get("source_type", "community")
    new_row["source_type"] = SOURCE_TYPE_REMAP.get(source_type_raw, source_type_raw) or "community"
    new_row["source_ref"] = row.get("source_ref", "")
    new_row["collection_date"] = row.get("collection_date") or "2025-12-03"
    new_row["text"] = row.get("text", "")
    new_row["domain"] = domain
    new_row["topic"] = row.get("topic") or infer_topic(domain)
    new_row["theme"] = row.get("theme") or infer_theme(bias_label)
    new_row["sensitive_characteristic"] = row.get("sensitive_characteristic") or "gender"
    new_row["target_gender"] = row.get("target_gender") or "unknown"
    new_row["bias_label"] = bias_label
    new_row["stereotype_category"] = infer_stereotype_category(row, bias_label)
    new_row["explicitness"] = infer_explicitness(row, bias_label)
    new_row["sentiment_toward_referent"] = row.get("sentiment_toward_referent") or "neutral"
    new_row["device"] = row.get("device", "")
    safety_raw = row.get("safety_flag", "").strip()
    new_row["safety_flag"] = SAFETY_FLAG_REMAP.get(safety_raw, safety_raw) or "safe"
    new_row["pii_removed"] = row.get("pii_removed") or "false"
    new_row["annotator_id"] = row.get("annotator_id") or "ann_legacy"
    qa_raw = row.get("qa_status", "")
    new_row["qa_status"] = QA_STATUS_REMAP.get(qa_raw, qa_raw) or "needs_review"
    existing_notes = row.get("notes", "")
    migration_note = "Migrated from legacy schema v4"
    new_row["notes"] = f"{existing_notes} | {migration_note}".strip(" |") if existing_notes else migration_note

    # --- Legacy fields appended ---
    for col in existing_cols:
        if col not in CANONICAL_COLS and col not in RENAME_MAP:
            new_row[col] = row.get(col, "")

    return new_row


def migrate(input_path, output_path, lang):
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        existing_cols = list(reader.fieldnames)

    migrated = [migrate_row(dict(r), i + 1, lang, existing_cols) for i, r in enumerate(rows)]

    # Output columns: canonical + legacy extras
    legacy_extra = [c for c in existing_cols if c not in CANONICAL_COLS and c not in RENAME_MAP]
    out_cols = CANONICAL_COLS + legacy_extra

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(migrated)

    print(f"\n=== MIGRATION COMPLETE ===")
    print(f"Input:  {input_path} ({len(rows)} rows)")
    print(f"Output: {output_path} ({len(migrated)} rows)")
    print(f"Columns: {len(out_cols)} ({len(CANONICAL_COLS)} canonical + {len(legacy_extra)} legacy)")
    print(f"Legacy retained: {legacy_extra}")

    # Quick distribution
    from collections import Counter
    bl = Counter(r["bias_label"] for r in migrated)
    qs = Counter(r["qa_status"] for r in migrated)
    print(f"\nbias_label:  {dict(bl)}")
    print(f"qa_status:   {dict(qs)}")

    # Preview first 3 rows
    print("\n--- First 3 rows (canonical fields only) ---")
    for r in migrated[:3]:
        for k in CANONICAL_COLS:
            print(f"  {k}: {r.get(k,'')}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/migrate_to_aibridge_v2.py <input.csv> <output.csv> <lang>")
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2], sys.argv[3])
