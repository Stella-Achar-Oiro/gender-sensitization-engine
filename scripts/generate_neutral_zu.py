#!/usr/bin/env python3
"""
Generate neutral Zulu sentences for classifier training.

Pulls from MasakhaNEWS Zulu split (non-gender topics) and Wikipedia Zulu.
Labels all rows as bias_label=neutral, has_bias=false.
Writes to data/neutral_zu_v1.csv.

Target: 3,000–5,000 neutral rows to balance IsiZulu_Ithute_Dataset_Final.csv

Usage:
    pip install datasets
    python3 scripts/generate_neutral_zu.py
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "data" / "neutral_zu_v1.csv"
OUTPUT.parent.mkdir(exist_ok=True)

FIELDNAMES = [
    "id", "language", "text", "domain", "source_ref",
    "bias_label", "has_bias", "qa_status"
]

# Topics safe to use as neutral (no gender framing in these domains)
SAFE_TOPICS = {
    "sports", "science/technology", "business/economy",
    "politics", "health", "entertainment", "weather",
    "agriculture", "environment"
}

# Gender-loaded keywords to filter out even from "neutral" sources
GENDER_KEYWORDS = [
    "wesifazane", "wesilisa", "owesifazane", "owesimame",
    "indoda", "umfazi", "intombazane", "umfana",
    "abafazi", "amadoda", "abesifazane", "abesilisa",
    "ubaba", "umama", "inkosikazi", "umyeni", "umlobokazi",
    "umakoti", "indodakazi", "indodana", "uyise", "unina",
]


WEB_NOISE = [
    "humushela", "translate", "google", "ukuze uvote", "ngemvume",
    "copyright", "http", "www.", ".com", ".org", "sawubona!",
    "isikhathi ukudala", "imizuzwana", "ngiyathanda lokhu",
    "bdsm", "anime", "bulili", "faka", "sign in", "login",
]


def is_gender_loaded(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in GENDER_KEYWORDS)


def is_web_noise(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in WEB_NOISE)


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\[.*?\]', '', text)  # remove wiki markup remnants
    return text


def pull_wikipedia_zu(target: int = 3000) -> list:
    """Pull neutral Zulu sentences from Wikipedia (20220301.zu)."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("datasets not installed. Run: pip install datasets")
        return []

    print("Loading Zulu Wikipedia (20220301.zu)...")
    try:
        ds = load_dataset("wikipedia", "20220301.zu",
                          trust_remote_code=True, split="train")
    except Exception as e:
        print(f"Wikipedia ZU load failed: {e}")
        return []

    rows = []
    seen = set()

    for item in ds:
        sentences = re.split(r'(?<=[.!?])\s+', item.get("text", ""))
        for sent in sentences:
            sent = clean_text(sent)
            if len(sent) < 30 or len(sent) > 300:
                continue
            if sent in seen:
                continue
            if is_gender_loaded(sent):
                continue
            seen.add(sent)
            rows.append({
                "id": f"ZU-NEU-WK-{len(rows):06d}",
                "language": "zu",
                "text": sent,
                "domain": "encyclopedia",
                "source_ref": "wikipedia/20220301.zu",
                "bias_label": "neutral",
                "has_bias": "false",
                "qa_status": "accepted",
            })
            if len(rows) >= target:
                break
        if len(rows) >= target:
            break

    print(f"Pulled {len(rows)} neutral rows from Wikipedia ZU")
    return rows


def pull_cc100_zu(target: int = 2000) -> list:
    """Pull neutral Zulu sentences from CC-100 corpus."""
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    print("Loading CC-100 Zulu...")
    try:
        ds = load_dataset("cc100", lang="zu", split="train",
                          streaming=True, trust_remote_code=True)
    except Exception as e:
        print(f"CC-100 ZU load failed: {e}")
        return []

    rows = []
    seen = set()

    for item in ds:
        text = clean_text(item.get("text", ""))
        if len(text) < 30 or len(text) > 300:
            continue
        if text in seen:
            continue
        if is_gender_loaded(text) or is_web_noise(text):
            continue
        seen.add(text)
        rows.append({
            "id": f"ZU-NEU-CC-{len(rows):06d}",
            "language": "zu",
            "text": text,
            "domain": "web",
            "source_ref": "cc100/zu",
            "bias_label": "neutral",
            "has_bias": "false",
            "qa_status": "accepted",
        })
        if len(rows) >= target:
            break

    print(f"Pulled {len(rows)} neutral rows from CC-100 ZU")
    return rows


def main():
    all_rows = []

    # Primary source: Wikipedia ZU
    wiki_rows = pull_wikipedia_zu(target=3000)
    all_rows.extend(wiki_rows)

    # Supplement with CC-100 if needed
    if len(all_rows) < 3000:
        needed = 3000 - len(all_rows)
        cc_rows = pull_cc100_zu(target=needed)
        all_rows.extend(cc_rows)

    if not all_rows:
        print("\nNo rows generated. Check that 'datasets' is installed:")
        print("  pip install datasets")
        print("\nThen re-run this script.")
        return

    # Write output
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\nWritten {len(all_rows)} neutral ZU rows to {OUTPUT}")
    print("Next step: merge with IsiZulu_Ithute_Dataset_Final.csv for Phase 2 training")
    print(f"Run: python3 scripts/merge_zu_training_data.py")


if __name__ == "__main__":
    main()
