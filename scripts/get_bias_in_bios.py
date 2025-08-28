#!/usr/bin/env python3
"""
To whom it may concern,

This script will:
Export Bias-in-Bios (or similar occupation-biased biographies) from Hugging Face `datasets`
to a normalized JSONL that the correction engine can ingest.

Usage:
  python scripts/get_bias_in_bios.py data/raw/normalized/bias_in_bios.jsonl --split train --limit 500

Requirements:
  pip install datasets
"""

import argparse
import json
from pathlib import Path
from datasets import load_dataset

def main(output_jsonl: str, split: str = "train", limit: int = 1000, hf_id: str = "mila/bias_in_bios"):
    outp = Path(output_jsonl)
    outp.parent.mkdir(parents=True, exist_ok=True)
    print(f"[info] loading dataset '{hf_id}' split='{split}' (this may take a moment)...")
    ds = load_dataset(hf_id, split=split)
    print(f"[info] dataset loaded; total items in split: {len(ds)}")
    written = 0
    with outp.open("w", encoding="utf-8") as fo:
        for i, ex in enumerate(ds):
            if i >= limit:
                break
            # heuristics: locate text-like field
            text = ex.get("text") or ex.get("bio") or ex.get("description") or ex.get("full_text") or ""
            if not text:
                # try join fields if necessary
                for key in ex.keys():
                    v = ex.get(key)
                    if isinstance(v, str) and len(v) > 20:
                        text = v
                        break
            if not text or len(text.strip()) < 20:
                continue
            rec = {
                "id": f"biasinbios_{i:06d}",
                "lang": "en",
                "text": text.strip(),
                "source": "bias_in_bios",
                "meta": {"hf_id": hf_id, "occupation": ex.get("occupation") if "occupation" in ex else None}
            }
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print(f"[done] wrote {written} records -> {outp}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Output JSONL path")
    parser.add_argument("--split", default="train", help="Dataset split (train/validation/test)")
    parser.add_argument("--limit", type=int, default=1000, help="Max records to export")
    parser.add_argument("--hf", default="mila/bias_in_bios", help="Hugging Face dataset id")
    args = parser.parse_args()
    main(args.output, split=args.split, limit=args.limit, hf_id=args.hf)
