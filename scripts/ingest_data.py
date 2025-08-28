# scripts/ingest_data.py
import requests, json, time
from datasets import load_dataset
from pathlib import Path

API_URL = "http://127.0.0.1:8000/rewrite/batch"
OUT = Path("data/processed/rewrites")
OUT.mkdir(parents=True, exist_ok=True)

def process_dataset(dataset_name: str, split="train", lang="en", sample=200, out_fname=None):
    try:
        ds = load_dataset(dataset_name, split=split)
    except Exception as e:
        print("Error loading", dataset_name, e)
        return
    # sample
    samples = ds.select(range(min(len(ds), sample)))
    items = []
    for i, rec in enumerate(samples):
        text = rec.get("text") or rec.get("sentence") or rec.get("translation") or str(rec)
        items.append({"id": f"{dataset_name}_{i}", "lang": lang, "text": text})
    # call batch API in chunks of 20
    results = []
    for i in range(0, len(items), 20):
        chunk = items[i:i+20]
        r = requests.post(API_URL, json=chunk, timeout=60)
        if r.status_code == 200:
            results.extend(r.json())
        else:
            print("API error", r.status_code, r.text)
            time.sleep(1)
    # save
    out_file = OUT / (out_fname or f"{dataset_name}_{lang}_rewrites.jsonl")
    with open(out_file, "w", encoding="utf-8") as f:
        for res in results:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
    print(f"Saved {len(results)} results to {out_file}")

if __name__ == "__main__":
    # small example: FLORES dev (if available)
    # process_dataset("facebook/flores", split="dev", lang="en", sample=50, out_fname="flores_dev_en.jsonl")
    # MasakhaNER sample (can be large); use a small selection
    process_dataset("masakhane/masakhaner", split="train", lang="sw", sample=100, out_fname="masakhaner_sw_rewrites.jsonl")
