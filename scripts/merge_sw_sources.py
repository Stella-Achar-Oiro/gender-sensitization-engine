"""
Merge real Swahili data sources into ground_truth_sw_v5.csv.

Sources processed:
1. data/analysis/annotation_sample.csv (1,500 rows from Swahili News)
2. data/analysis/masakhaner_example_sentences.csv (50 examples)
3. data/raw/masakhaner_swa_train.txt (6,593 sentences — mine all occupation ones)

Usage:
    python3 scripts/merge_sw_sources.py
"""

import csv
import re
import sys
from pathlib import Path
from collections import Counter

GROUND_TRUTH = "eval/ground_truth_sw_v5.csv"
OUTPUT = "eval/ground_truth_sw_v5.csv"  # Append in-place

CANONICAL_COLS = [
    "id", "language", "script", "country", "region_dialect", "source_type", "source_ref",
    "collection_date", "text", "domain", "topic", "theme", "sensitive_characteristic",
    "target_gender", "bias_label", "stereotype_category", "explicitness",
    "sentiment_toward_referent", "device", "safety_flag", "pii_removed",
    "annotator_id", "qa_status", "notes",
    # legacy
    "has_bias", "bias_category", "expected_correction"
]

SOURCE_URLS = {
    "swahili_news": "https://zenodo.org/record/5514203",
    "masakhaner_swa": "https://huggingface.co/datasets/masakhane/masakhaner",
    "masakhaner": "https://huggingface.co/datasets/masakhane/masakhaner",
    "wikipedia": "https://sw.wikipedia.org",
}

# Load lexicon terms for occupation matching
def load_lexicon(path="rules/lexicon_sw_v3.csv"):
    terms = set()
    try:
        with open(path) as f:
            for row in csv.DictReader(f):
                t = row.get("biased", "").strip().lower()
                if t:
                    terms.add(t)
    except FileNotFoundError:
        pass
    return terms

LEXICON_TERMS = load_lexicon()

# Gender markers in Swahili
GENDER_MARKERS = re.compile(
    r'\b(wa kiume|wa kike|mwanaume|mwanamke|mama|baba|dada|kaka|'
    r'yeye ni|binti|mwana|mtoto wa|mke|mume)\b',
    re.IGNORECASE
)

def has_occupation_term(text):
    text_lower = text.lower()
    for term in LEXICON_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
            return True
    return False

def infer_bias_label(text):
    """Infer bias_label from text content."""
    if GENDER_MARKERS.search(text):
        return "stereotype"
    if has_occupation_term(text):
        # occupation without gender marker = neutral (needs review)
        return "neutral"
    return "neutral"

def infer_domain(source):
    mapping = {
        "swahili_news": "media_and_online",
        "masakhaner_swa": "governance_civic",
        "masakhaner": "governance_civic",
        "wikipedia": "media_and_online",
    }
    return mapping.get(source, "media_and_online")

def make_row(idx, text, source_name, source_ref, collection_date, notes=""):
    bias_label = infer_bias_label(text)
    domain = infer_domain(source_name)
    topic_map = {
        "media_and_online": "media_representation",
        "governance_civic": "political_representation",
        "livelihoods_and_work": "occupation_roles",
    }
    return {
        "id": f"sw-{idx:05d}",
        "language": "sw",
        "script": "latin",
        "country": "Kenya",
        "region_dialect": "",
        "source_type": "media" if "news" in source_name else "web_public",
        "source_ref": source_ref,
        "collection_date": collection_date,
        "text": text.strip(),
        "domain": domain,
        "topic": topic_map.get(domain, "media_representation"),
        "theme": "stereotypes" if bias_label != "neutral" else "public_interest",
        "sensitive_characteristic": "gender",
        "target_gender": "unknown",
        "bias_label": bias_label,
        "stereotype_category": "profession" if bias_label == "stereotype" else "",
        "explicitness": "explicit" if bias_label == "stereotype" else "",
        "sentiment_toward_referent": "neutral",
        "device": "",
        "safety_flag": "safe",
        "pii_removed": "false",
        "annotator_id": "",
        "qa_status": "needs_review",
        "notes": notes,
        "has_bias": "true" if bias_label == "stereotype" else "false",
        "bias_category": "occupation" if bias_label == "stereotype" else "none",
        "expected_correction": "",
    }

def load_existing_texts(path):
    texts = set()
    try:
        with open(path) as f:
            for row in csv.DictReader(f):
                t = row.get("text", "").strip().lower()
                if t:
                    texts.add(t)
    except FileNotFoundError:
        pass
    return texts

def get_next_id(path):
    try:
        with open(path) as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return 64
        ids = [r.get("id","sw-00000") for r in rows]
        nums = []
        for i in ids:
            m = re.search(r'(\d+)$', i)
            if m:
                nums.append(int(m.group(1)))
        return max(nums) + 1 if nums else 64
    except FileNotFoundError:
        return 64

def mine_masakhaner_bio(path, existing_texts, start_idx):
    """Extract full sentences from BIO-tagged MasakhaNER file."""
    rows = []
    idx = start_idx
    source_ref = SOURCE_URLS["masakhaner_swa"]

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  ⚠️  {path} not found")
        return rows, idx

    # Sentences separated by blank lines
    sentence_blocks = content.strip().split("\n\n")
    for block in sentence_blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue
        tokens = []
        for line in lines:
            parts = line.split()
            if parts:
                tokens.append(parts[0])
        text = " ".join(tokens)
        if not text or len(text) < 20:
            continue
        if not has_occupation_term(text):
            continue
        if text.lower() in existing_texts:
            continue
        row = make_row(idx, text, "masakhaner_swa", source_ref, "2023-01-01",
                       "Source: MasakhaNER Swahili train set")
        rows.append(row)
        existing_texts.add(text.lower())
        idx += 1

    return rows, idx

def main():
    print("=== SWAHILI DATA MERGE ===\n")

    existing_texts = load_existing_texts(GROUND_TRUTH)
    start_idx = get_next_id(GROUND_TRUTH)
    print(f"Existing rows: {len(existing_texts)}, next ID: sw-{start_idx:05d}\n")

    all_new_rows = []
    stats = Counter()

    # --- Source 1: annotation_sample.csv (Swahili News) ---
    print("📰 Processing annotation_sample.csv (Swahili News)...")
    try:
        with open("data/analysis/annotation_sample.csv") as f:
            sample_rows = list(csv.DictReader(f))

        added = 0
        for r in sample_rows:
            text = r.get("text", "").strip()
            if not text or text.lower() in existing_texts:
                continue
            if not has_occupation_term(text):
                continue
            source_name = r.get("source_ref", "swahili_news")
            source_ref = SOURCE_URLS.get(source_name, "https://zenodo.org/record/5514203")
            idx = start_idx + len(all_new_rows)
            row = make_row(idx, text, source_name, source_ref,
                           r.get("collection_date", "2025-12-03"),
                           f"Occupation: {r.get('topic','')}. Source: Swahili News Dataset")
            all_new_rows.append(row)
            existing_texts.add(text.lower())
            added += 1
        print(f"  Added: {added} rows")
        stats["swahili_news"] = added
    except FileNotFoundError:
        print("  ⚠️  annotation_sample.csv not found")

    # --- Source 2: MasakhaNER BIO file ---
    print("\n🔬 Mining MasakhaNER BIO file...")
    maska_rows, new_idx = mine_masakhaner_bio(
        "data/raw/masakhaner_swa_train.txt",
        existing_texts,
        start_idx + len(all_new_rows)
    )
    all_new_rows.extend(maska_rows)
    stats["masakhaner"] = len(maska_rows)
    print(f"  Added: {len(maska_rows)} rows")

    # --- Deduplicate within new rows ---
    seen = set()
    deduped = []
    for r in all_new_rows:
        key = r["text"].lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    print(f"\n  Deduped: {len(all_new_rows)} → {len(deduped)} rows")
    all_new_rows = deduped

    # Re-assign sequential IDs after dedup
    base_idx = get_next_id(GROUND_TRUTH)
    for i, r in enumerate(all_new_rows):
        r["id"] = f"sw-{base_idx + i:05d}"

    # --- Append to ground truth ---
    with open(GROUND_TRUTH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_COLS, extrasaction="ignore")
        writer.writerows(all_new_rows)

    # --- Summary ---
    total_after = len(existing_texts) + len(all_new_rows)
    print(f"\n{'='*50}")
    print(f"MERGE COMPLETE")
    print(f"Rows added:     {len(all_new_rows)}")
    print(f"  - Swahili News:  {stats['swahili_news']}")
    print(f"  - MasakhaNER:    {stats['masakhaner']}")
    print(f"Total rows now: {total_after}")
    print(f"Gold tier target: 10,000")
    print(f"Progress:       {100*total_after/10000:.1f}%")
    print(f"Still needed:   {max(0, 10000 - total_after)}")

    bl = Counter(r["bias_label"] for r in all_new_rows)
    print(f"\nbias_label: {dict(bl)}")
    print(f"qa_status:  all=needs_review")

if __name__ == "__main__":
    main()
