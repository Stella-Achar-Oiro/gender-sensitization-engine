#!/usr/bin/env python3
"""
Push JuaKazi datasets to HuggingFace Hub.

Creates the dataset repo juakazike/gender-bias-multilingual and uploads:
  - ground_truth_sw_v5.csv      (Swahili, 66,995 rows)
  - ground_truth_ki_v8.csv      (Kikuyu, 11,622 rows)
  - ground_truth_en_v5.csv      (English eval, 66 rows)
  - en_ml_training_v1.csv       (English ML train, 2,828 rows)
  - ground_truth_fr_v5.csv      (French, 165 rows)
  - dataset_card.md             → uploaded as README.md

Usage (local):
    export HF_TOKEN=hf_xxx...
    python3 push_datasets_to_hf.py

Usage (Google Colab):
    from google.colab import userdata
    import os
    os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')
    exec(open('push_datasets_to_hf.py').read())
"""

import os
import sys
import shutil
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
REPO_ID   = "juakazike/gender-bias-multilingual"
REPO_TYPE = "dataset"

# File map: source path → destination filename in repo
# Paths are relative to this script's location (project root)
FILES = {
    "eval/ground_truth_sw_v5.csv":          "ground_truth_sw_v5.csv",
    "eval/ground_truth_ki_v8.csv":          "ground_truth_ki_v8.csv",
    "eval/ground_truth_en_v5.csv":          "ground_truth_en_v5.csv",
    "data/annotation_export/en_ml_training_v1.csv": "en_ml_training_v1.csv",
    "eval/ground_truth_fr_v5.csv":          "ground_truth_fr_v5.csv",
    "dataset_card.md":                      "README.md",
}

# ── Auth ───────────────────────────────────────────────────────────────────────
def get_token():
    token = os.environ.get("HF_TOKEN")
    if not token:
        # Try colab secrets if running in Colab
        try:
            from google.colab import userdata
            token = userdata.get("HF_TOKEN")
        except Exception:
            pass
    if not token:
        token = input("HuggingFace write token (hf_xxx...): ").strip()
    if not token.startswith("hf_"):
        print("Warning: token doesn't look like a HF token (should start with hf_)")
    return token


def main():
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    token = get_token()
    login(token=token)
    api = HfApi()

    # ── Locate project root ────────────────────────────────────────────────────
    root = Path(__file__).parent.resolve()
    print(f"Project root: {root}")

    # ── Validate all source files exist ───────────────────────────────────────
    print("\nValidating source files...")
    missing = []
    for src_rel, dest in FILES.items():
        src = root / src_rel
        if not src.exists():
            missing.append(str(src))
            print(f"  ✗ {src_rel}")
        else:
            size_kb = src.stat().st_size / 1024
            print(f"  ✓ {src_rel} ({size_kb:,.0f} KB) → {dest}")

    if missing:
        print(f"\n{len(missing)} file(s) missing. Aborting.")
        sys.exit(1)

    # ── Create repo (idempotent) ───────────────────────────────────────────────
    print(f"\nCreating/confirming dataset repo: {REPO_ID}")
    api.create_repo(
        repo_id   = REPO_ID,
        repo_type = REPO_TYPE,
        exist_ok  = True,
        private   = False,
    )
    print(f"  ✓ Repo ready: https://huggingface.co/datasets/{REPO_ID}")

    # ── Upload files one by one (with progress) ────────────────────────────────
    print("\nUploading files...")
    for src_rel, dest_name in FILES.items():
        src = root / src_rel
        size_mb = src.stat().st_size / 1e6
        print(f"  Uploading {dest_name} ({size_mb:.1f} MB)...", end=" ", flush=True)
        api.upload_file(
            path_or_fileobj = str(src),
            path_in_repo    = dest_name,
            repo_id         = REPO_ID,
            repo_type       = REPO_TYPE,
            commit_message  = f"Add {dest_name}",
        )
        print("✓")

    # ── Final verification ─────────────────────────────────────────────────────
    print("\nVerifying upload...")
    repo_files = api.list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE)
    expected   = set(FILES.values())
    uploaded   = set(f for f in repo_files if not f.startswith("."))

    missing_in_repo = expected - uploaded
    if missing_in_repo:
        print(f"Warning: these files were not found in repo: {missing_in_repo}")
    else:
        print(f"  ✓ All {len(expected)} files confirmed in repo")

    print(f"""
═══════════════════════════════════════════════════════════════
  DATASET PUSH COMPLETE
═══════════════════════════════════════════════════════════════
  Repo:  https://huggingface.co/datasets/{REPO_ID}
  Files: {len(expected)} uploaded

  Quick load test:
    from datasets import load_dataset
    ds = load_dataset("{REPO_ID}")

  Or with pandas:
    import pandas as pd
    sw = pd.read_csv("hf://datasets/{REPO_ID}/ground_truth_sw_v5.csv")
═══════════════════════════════════════════════════════════════
""")

    # ── Sanity check: row counts ───────────────────────────────────────────────
    print("Sanity check — row counts:")
    import pandas as pd
    expected_counts = {
        "ground_truth_sw_v5.csv":  66995,
        "ground_truth_ki_v8.csv":  11622,
        "ground_truth_en_v5.csv":  66,
        "en_ml_training_v1.csv":   2828,
        "ground_truth_fr_v5.csv":  165,
    }
    all_ok = True
    for src_rel, dest_name in FILES.items():
        if dest_name == "README.md":
            continue
        src = root / src_rel
        df = pd.read_csv(src, low_memory=False)
        expected_n = expected_counts.get(dest_name)
        ok = len(df) == expected_n
        if not ok:
            all_ok = False
        status = "✓" if ok else "✗"
        print(f"  {status} {dest_name}: {len(df):,} rows (expected {expected_n:,})")

    if all_ok:
        print("\nAll row counts match. Dataset is ready for use.")
    else:
        print("\nRow count mismatch detected — check source files before using for training.")


if __name__ == "__main__":
    main()
