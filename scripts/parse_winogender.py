#!/usr/bin/env python3
"""
To whom it may concern,

This script will:
Extract sentences from the Winogender schemas JSON and write a normalized JSONL file
that matches the correction engine input schema:
  {"id": "...", "lang": "en", "text": "...", "source": "winogender", "meta": {...}}

Usage:
  # download the repo raw JSON first (or let ingest_data.py download it)
  python scripts/parse_winogender.py data/raw/schemas.jsonl data/raw/normalized/winogender.jsonl

If the Winogender file contains templates rather than concrete sentences the script
will attempt conservative extraction only — advanced template expansion is not automatic.
"""

import json
import sys
from pathlib import Path
import unicodedata
import re

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_sentences(winogender_obj):
    """
    Heuristically extract sentence-like strings from one Winogender entry.
    The Winogender repo stores entries with fields; I tried to find the most likely ones.(Common Keys: sentence, text, template, sent, sentences[])
    """
    candidates = []
    # Common keys that may contain full sentence strings
    for key in ("sentence", "text", "template", "sent"):
        if key in winogender_obj and isinstance(winogender_obj[key], str):
            candidates.append(winogender_obj[key])
    # Some entries have 'sentences' as an array
    if "sentences" in winogender_obj and isinstance(winogender_obj["sentences"], list):
        for s in winogender_obj["sentences"]:
            if isinstance(s, str):
                candidates.append(s)
    # As a fallback, collect any string fields > 20 chars that look like a sentence (ends with . ? !)
    if not candidates:
        for k,v in winogender_obj.items():
            if isinstance(v, str) and len(v) > 20 and re.search(r"[\.!?]$", v.strip()):
                candidates.append(v)
    return candidates

def main(input_path: str, output_path: str, lang: str = "en"):
    inp = Path(input_path)
    out = Path(output_path)
    if not inp.exists():
        print(f"[error] input file not found: {inp}")
        return

    raw = inp.read_text(encoding="utf-8", errors="ignore").strip()
    # Because Winogender is usually a JSON array
    try:
        j = json.loads(raw)
    except Exception as e:
        print("[error] failed to parse JSON:", e)
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as fo:
        for i, entry in enumerate(j):
            sents = extract_sentences(entry)
            for s in sents:
                s_norm = normalize_text(s)
                if not s_norm:
                    continue
                rec = {
                    "id": f"winogender_{i:06d}_{count%1000:03d}",
                    "lang": lang,
                    "text": s_norm,
                    "source": "winogender",
                    "meta": {"orig": entry}
                }
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1

    print(f"[done] extracted {count} sentences -> {out}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/parse_winogender.py <input_json> <output_jsonl> [lang]")
        print("Example: python scripts/parse_winogender.py data/raw/schemas.json data/raw/normalized/winogender.jsonl en")
        sys.exit(1)
    inp = sys.argv[1]
    outp = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    main(inp, outp, language)
