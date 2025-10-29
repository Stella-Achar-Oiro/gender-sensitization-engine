#!/usr/bin/env python3
"""

1) Download known hosted raw files (MasakhaNER Swahili train/dev/test).
2) Accept arbitrary local file paths or URLs (CSV/JSON/TXT/CoNLL).
3) Parse/normalize into JSONL records suitable for the correction engine.
4) Call local /rewrite/batch API to process chunks and save processed outputs.

Usage examples:
  python scripts/ingest_data.py --download-masakhaner
  python scripts/ingest_data.py --input-url https://raw.githubusercontent.com/.../some.csv --lang en
  python scripts/ingest_data.py --call-api
"""

import argparse
import csv
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Dict, Any
import requests

# -----------------------
# CONFIG
# -----------------------
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
NORM_DIR = RAW_DIR / "normalized"
PROC_DIR = DATA_DIR / "processed"
NORM_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

# MasakhaNER (Swahili) GitHub raw URLs (train/dev/test). Adjust if repository moves.
MASAKHANER_BASE = "https://raw.githubusercontent.com/masakhane-io/masakhane-ner/main/MasakhaNER2.0/data/swa"
MASAKHANER_FILES = {
    "train": f"{MASAKHANER_BASE}/train.txt",
    "dev": f"{MASAKHANER_BASE}/dev.txt",
    "test": f"{MASAKHANER_BASE}/test.txt"
}

# Default API (local) for batch rewrite
DEFAULT_API_BATCH = "http://127.0.0.1:8000/rewrite/batch"

# -----------------------
# UTILITIES
# -----------------------
def download_file(url: str, out: Path, overwrite: bool = False) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not overwrite:
        print(f"[skip] already downloaded: {out}")
        return out
    print(f"[downloading] {url} -> {out}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(out, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return out

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    # Unicode normalize, collapse whitespace, strip
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def detect_file_format(path: Path, sample_lines: int = 50) -> str:
    """
    Returns: 'conll', 'plain', 'csv', 'json'
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    first = "\n".join(text.splitlines()[:sample_lines])
    # JSON detection
    stripped = first.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    # CSV heuristics (commas and headers)
    if "\n" in first and "," in first.splitlines()[0]:
        # treat as csv if header-like line contains 'text' or 'sentence' etc or many commas
        hdr = first.splitlines()[0].lower()
        if "text" in hdr or "sentence" in hdr or "translation" in hdr or len(hdr.split(",")) > 1:
            return "csv"
    # CoNLL detection: token + tag per line (tab or space separated) and blank lines
    lines = first.splitlines()
    token_tag_lines = sum(1 for ln in lines if len(ln.split()) >= 2)
    blank_lines = sum(1 for ln in lines if ln.strip() == "")
    if blank_lines and token_tag_lines > 0:
        return "conll"
    # default to plain
    return "plain"

# -----------------------
# PARSERS
# -----------------------
def parse_conll(path: Path) -> Iterable[str]:
    """
    Parse token-per-line CoNLL-like file into sentences (join tokens).
    We'll assume the token is the first column.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = []
        for line in f:
            line = line.strip()
            if not line:
                if tokens:
                    yield " ".join(tokens)
                    tokens = []
            else:
                parts = line.split()
                if len(parts) >= 1:
                    token = parts[0]
                    tokens.append(token)
        if tokens:
            yield " ".join(tokens)

def parse_plain(path: Path) -> Iterable[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s:
                yield s

def parse_csv(path: Path) -> Iterable[str]:
    # find a text-like column heuristically
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        # choose column
        cols = reader.fieldnames or []
        text_col = None
        for candidate in ("text", "sentence", "translation", "utterance", "content"):
            if candidate in cols:
                text_col = candidate
                break
        if text_col is None:
            # fallback: take first string-like column
            for c in cols:
                text_col = c
                break
        if text_col is None:
            return
        for i, row in enumerate(reader):
            t = row.get(text_col, "")
            if t:
                yield t

def parse_json(path: Path) -> Iterable[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    if raw.startswith("["):
        arr = json.loads(raw)
        for obj in arr:
            # pick likely text key
            for key in ("text", "sentence", "translation", "content"):
                if isinstance(obj.get(key, None), str):
                    yield obj[key]
                    break
    else:
        # newline-delimited JSON
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                for key in ("text", "sentence", "translation", "content"):
                    if isinstance(obj.get(key, None), str):
                        yield obj[key]
                        break
            except:
                continue

# -----------------------
# MAIN WORKFLOW
# -----------------------
def normalize_and_dump(sentences: Iterable[str], out_jsonl: Path, lang: str, source: str, start_id: int = 1):
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    i = start_id
    with open(out_jsonl, "w", encoding="utf-8") as fo:
        for s in sentences:
            s_norm = normalize_text(s)
            if not s_norm:
                continue
            rec = {
                "id": f"{source}_{i:06d}",
                "lang": lang,
                "text": s_norm,
                "source": source,
                "meta": {}
            }
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            i += 1
    return i - start_id  # number of records written

def call_batch_api_and_save(input_jsonl: Path, api_url: str = DEFAULT_API_BATCH, chunk_size: int = 20, out_jsonl: Path = None):
    out_jsonl = out_jsonl or (PROC_DIR / f"{input_jsonl.stem}_rewrites.jsonl")
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(input_jsonl, "r", encoding="utf-8") as fin, open(out_jsonl, "w", encoding="utf-8") as fout:
        buffer = []
        for line in fin:
            buffer.append(json.loads(line))
            if len(buffer) >= chunk_size:
                r = requests.post(api_url, json=buffer, timeout=120)
                r.raise_for_status()
                for obj in r.json():
                    fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                buffer = []
        # flush remainder
        if buffer:
            r = requests.post(api_url, json=buffer, timeout=120)
            r.raise_for_status()
            for obj in r.json():
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return out_jsonl

# -----------------------
# CLI
# -----------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-masakhaner", action="store_true", help="Download MasakhaNER Swahili raw files (train/dev/test)")
    parser.add_argument("--input-url", type=str, help="URL of a raw dataset (CSV/JSON/TXT/CoNLL)")
    parser.add_argument("--input-file", type=str, help="Local file path to parse")
    parser.add_argument("--lang", type=str, default="en", help="Language code for normalized output (default: en)")
    parser.add_argument("--out", type=str, help="Out JSONL path (optional)")
    parser.add_argument("--call-api", action="store_true", help="Call local rewrite batch API after normalization")
    parser.add_argument("--api-url", type=str, default=DEFAULT_API_BATCH, help="Batch API URL")
    args = parser.parse_args()

    record_count = 0

    if args.download_masakhaner:
        for split, url in MASAKHANER_FILES.items():
            out_local = RAW_DIR / f"masakhaner_swa_{split}.txt"
            try:
                download_file(url, out_local)
            except Exception as e:
                print("[error] failed download:", e)
                continue
            fmt = detect_file_format(out_local)
            print(f"[info] detected format {fmt} for {out_local}")
            if fmt == "conll":
                sentences = parse_conll(out_local)
            elif fmt == "plain":
                sentences = parse_plain(out_local)
            elif fmt == "csv":
                sentences = parse_csv(out_local)
            elif fmt == "json":
                sentences = parse_json(out_local)
            else:
                sentences = parse_plain(out_local)
            out_jsonl = NORM_DIR / f"masakhaner_swa_{split}.jsonl"
            written = normalize_and_dump(sentences, out_jsonl, lang="sw", source=f"masakhaner_{split}")
            print(f"[saved] {written} records -> {out_jsonl}")
            record_count += written
            # optionally call API
            if args.call_api:
                print("[info] calling batch API for", out_jsonl)
                out_processed = call_batch_api_and_save(out_jsonl, api_url=args.api_url)
                print("[saved processed] ->", out_processed)

    # single input (URL)
    if args.input_url:
        fname = args.input_url.split("/")[-1] or "input_download"
        out_local = RAW_DIR / fname
        try:
            download_file(args.input_url, out_local)
        except Exception as e:
            print("[error] download failed:", e); return
        fmt = detect_file_format(out_local)
        print(f"[info] detected format {fmt} for {out_local}")
        if fmt == "conll":
            sentences = parse_conll(out_local)
        elif fmt == "plain":
            sentences = parse_plain(out_local)
        elif fmt == "csv":
            sentences = parse_csv(out_local)
        elif fmt == "json":
            sentences = parse_json(out_local)
        else:
            sentences = parse_plain(out_local)
        out_jsonl = Path(args.out) if args.out else NORM_DIR / f"{fname}.jsonl"
        written = normalize_and_dump(sentences, out_jsonl, lang=args.lang, source=f"{fname}")
        print(f"[saved] {written} records -> {out_jsonl}")
        record_count += written
        if args.call_api:
            out_processed = call_batch_api_and_save(out_jsonl, api_url=args.api_url)
            print("[saved processed] ->", out_processed)

    # single local file
    if args.input_file:
        path = Path(args.input_file)
        if not path.exists():
            print("[error] input_file does not exist:", path); return
        fmt = detect_file_format(path)
        print(f"[info] detected format {fmt} for {path}")
        if fmt == "conll":
            sentences = parse_conll(path)
        elif fmt == "plain":
            sentences = parse_plain(path)
        elif fmt == "csv":
            sentences = parse_csv(path)
        elif fmt == "json":
            sentences = parse_json(path)
        else:
            sentences = parse_plain(path)
        out_jsonl = Path(args.out) if args.out else NORM_DIR / f"{path.stem}.jsonl"
        written = normalize_and_dump(sentences, out_jsonl, lang=args.lang, source=path.name)
        print(f"[saved] {written} records -> {out_jsonl}")
        record_count += written
        if args.call_api:
            out_processed = call_batch_api_and_save(out_jsonl, api_url=args.api_url)
            print("[saved processed] ->", out_processed)

    if record_count == 0:
        print("[info] no records processed. Use --download-masakhaner or --input-url/--input-file")
    else:
        print(f"[done] total records processed: {record_count}")

if __name__ == "__main__":
    main()
