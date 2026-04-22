"""Eval report/file I/O helper — write results and reports to disk."""

import json
from pathlib import Path
from typing import Any


def write_results_json(results: dict[str, Any], output_path: Path) -> None:
    """Save evaluation results to a JSON file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"Results saved to {output_path}")
    except OSError as e:
        print(f"Error saving results to {output_path}: {e}")


def write_report_txt(report: str, output_path: Path) -> None:
    """Save a text report to a file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {output_path}")
    except OSError as e:
        print(f"Error saving report to {output_path}: {e}")
