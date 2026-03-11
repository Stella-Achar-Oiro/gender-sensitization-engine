#!/usr/bin/env python3
"""
Main entry point for bias detection evaluation.

  python run_evaluation.py           # F1, Precision, Recall per language
  python run_evaluation.py --fairness  # + AIBRIDGE fairness (DP, EO, MBE)
"""
import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description="Run bias detection evaluation (F1/precision/recall)."
    )
    parser.add_argument(
        "--fairness",
        action="store_true",
        help="Include AIBRIDGE fairness metrics (DP, EO, MBE).",
    )
    args = parser.parse_args()
    if args.fairness:
        from run_aibridge_evaluation import main as fairness_main
        fairness_main()
    else:
        from eval.evaluator import main as eval_main
        eval_main()


if __name__ == "__main__":
    main()