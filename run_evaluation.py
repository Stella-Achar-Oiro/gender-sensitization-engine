#!/usr/bin/env python3
"""
Main entry point for bias detection evaluation.

  python run_evaluation.py                  # F1, Precision, Recall per language
  python run_evaluation.py --fairness       # + AIBRIDGE fairness (DP, EO, MBE)
  python run_evaluation.py --tag v0.8-desc  # save snapshot to model_registry.json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

REGISTRY_PATH = project_root / "eval" / "results" / "model_registry.json"


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=project_root, text=True
        ).strip()
    except Exception:
        return None


def _lexicon_size(lang: str) -> int:
    try:
        import csv
        path = project_root / "rules" / f"lexicon_{lang}_v3.csv"
        with open(path, newline="", encoding="utf-8") as f:
            return sum(1 for _ in csv.reader(f)) - 1
    except Exception:
        return 0


def _ground_truth_size(lang: str) -> int:
    try:
        import csv
        path = project_root / "eval"
        # find the file matching ground_truth_{lang}_v*.csv
        candidates = sorted(path.glob(f"ground_truth_{lang}_v*.csv"))
        if not candidates:
            return 0
        with open(candidates[-1], newline="", encoding="utf-8") as f:
            return sum(1 for _ in csv.reader(f)) - 1
    except Exception:
        return 0


def _save_to_registry(tag: str, results: list) -> None:
    registry = {"versions": []}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            registry = json.load(f)

    existing_tags = {v["tag"] for v in registry["versions"]}
    if tag in existing_tags:
        print(f"Warning: tag '{tag}' already exists in registry — skipping save.")
        return

    langs = ["en", "sw", "fr", "ki"]
    metrics_map = {}
    for r in results:
        lang = r.language.value if hasattr(r.language, "value") else str(r.language)
        m = r.overall_metrics
        metrics_map[lang] = {
            "f1": round(m.f1_score, 3),
            "precision": round(m.precision, 3),
            "recall": round(m.recall, 3),
        }

    entry = {
        "tag": tag,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "notes": "",
        "lexicon_sizes": {lang: _lexicon_size(lang) for lang in langs},
        "ground_truth_sizes": {lang: _ground_truth_size(lang) for lang in langs},
        "metrics": metrics_map,
    }
    registry["versions"].append(entry)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    print(f"Snapshot saved to registry as '{tag}'")


def main():
    parser = argparse.ArgumentParser(
        description="Run bias detection evaluation (F1/precision/recall)."
    )
    parser.add_argument("--fairness", action="store_true",
                        help="Include AIBRIDGE fairness metrics (DP, EO, MBE).")
    parser.add_argument("--tag", metavar="TAG",
                        help="Save a named snapshot to eval/results/model_registry.json")
    args = parser.parse_args()

    if args.fairness:
        from run_aibridge_evaluation import main as fairness_main
        fairness_main()
        return

    from eval.evaluator import BiasEvaluationOrchestrator
    orchestrator = BiasEvaluationOrchestrator()
    results = orchestrator.run_evaluation()

    if args.tag:
        _save_to_registry(args.tag, results)


if __name__ == "__main__":
    main()
