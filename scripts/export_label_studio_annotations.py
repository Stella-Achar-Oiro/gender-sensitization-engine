"""
Export Label Studio annotations → AIBRIDGE-ready CSV + Cohen's Kappa.

Usage:
    python3 scripts/export_label_studio_annotations.py \
        --url http://localhost:8080 \
        --token <your-admin-token> \
        --project-id 1 \
        --output eval/results/kappa_label_studio.json

Or set env vars: LS_URL, LS_TOKEN, LS_PROJECT_ID
"""
import argparse
import csv
import json
import os
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path


def fetch_json(url: str, token: str) -> dict | list:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def export_annotations(url: str, token: str, project_id: str, output_path: str) -> None:
    print(f"Fetching annotations from project {project_id}...")

    # Get all tasks with annotations
    tasks_url = f"{url}/api/projects/{project_id}/tasks?page_size=500"
    try:
        tasks = fetch_json(tasks_url, token)
    except urllib.error.HTTPError as e:
        print(f"Error fetching tasks: {e.code} {e.read().decode()}")
        sys.exit(1)

    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", tasks.get("results", []))

    print(f"Tasks found: {len(tasks)}")

    # Group annotations by task (for IAA)
    per_task: dict[str, list[dict]] = defaultdict(list)
    for task in tasks:
        task_id = task.get("id")
        text_id = task.get("data", {}).get("id", str(task_id))
        text = task.get("data", {}).get("text", "")
        annotations = task.get("annotations", [])
        for ann in annotations:
            annotator_id = ann.get("completed_by", {})
            if isinstance(annotator_id, dict):
                annotator_email = annotator_id.get("email", "unknown")
            else:
                annotator_email = str(annotator_id)

            result_map = {}
            for r in ann.get("result", []):
                name = r.get("from_name", "")
                value = r.get("value", {})
                if "choices" in value:
                    result_map[name] = value["choices"][0] if value["choices"] else ""
                elif "text" in value:
                    result_map[name] = value["text"][0] if value["text"] else ""

            per_task[text_id].append({
                "text_id": text_id,
                "text": text,
                "annotator_email": annotator_email,
                "has_bias": result_map.get("has_bias", ""),
                "stereotype_category": result_map.get("stereotype_category", ""),
                "explicitness": result_map.get("explicitness", ""),
                "expected_correction": result_map.get("expected_correction", ""),
                "annotator_confidence": result_map.get("annotator_confidence", ""),
                "annotator_notes": result_map.get("annotator_notes", ""),
            })

    # Count coverage
    tasks_with_2 = sum(1 for v in per_task.values() if len(v) >= 2)
    tasks_with_1 = sum(1 for v in per_task.values() if len(v) == 1)
    print(f"Tasks with 2 annotations: {tasks_with_2}")
    print(f"Tasks with 1 annotation:  {tasks_with_1}")
    print(f"Tasks with 0 annotations: {len(tasks) - tasks_with_2 - tasks_with_1}")

    # Compute Cohen's Kappa on tasks with 2 annotations
    def _cohen_kappa_binary(y1: list, y2: list) -> float:
        n = len(y1)
        if n == 0:
            return 0.0
        p_o = sum(a == b for a, b in zip(y1, y2)) / n
        p_yes_1 = sum(y1) / n
        p_yes_2 = sum(y2) / n
        p_e = p_yes_1 * p_yes_2 + (1 - p_yes_1) * (1 - p_yes_2)
        if p_e >= 1.0:
            return 0.0
        return (p_o - p_e) / (1.0 - p_e)

    kappa_result = None
    if tasks_with_2 > 0:
        ann_a, ann_b = [], []
        for annotations in per_task.values():
            if len(annotations) >= 2:
                a = 1 if annotations[0]["has_bias"].lower() in ("true", "yes", "1") else 0
                b = 1 if annotations[1]["has_bias"].lower() in ("true", "yes", "1") else 0
                ann_a.append(a)
                ann_b.append(b)

        kappa = _cohen_kappa_binary(ann_a, ann_b)
        agree = sum(a == b for a, b in zip(ann_a, ann_b)) / len(ann_a)
        kappa_result = {
            "has_bias_kappa": round(kappa, 4),
            "raw_agreement": round(agree, 4),
            "rows_evaluated": len(ann_a),
            "aibridge_bronze_pass": kappa >= 0.70,
        }
        status = "✅ PASS" if kappa >= 0.70 else "❌ FAIL"
        print()
        print("=" * 50)
        print(f"COHEN'S KAPPA: {kappa:.4f}  {status}")
        print(f"Raw agreement: {agree:.1%} over {len(ann_a)} rows")
        print(f"AIBRIDGE Bronze (κ ≥ 0.70): {status}")
        print("=" * 50)
    elif tasks_with_2 == 0:
        print("\nNo tasks with 2 annotations yet — annotate more rows first.")

    # Export flat CSV per annotator
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Separate by annotator
    by_annotator: dict[str, list] = defaultdict(list)
    for annotations in per_task.values():
        for ann in annotations:
            by_annotator[ann["annotator_email"]].append(ann)

    for email, rows in by_annotator.items():
        safe_name = email.replace("@", "_").replace(".", "_")
        csv_path = out_dir / f"ls_annotations_{safe_name}.csv"
        fieldnames = ["text_id", "text", "annotator_email", "has_bias",
                      "stereotype_category", "explicitness", "expected_correction",
                      "annotator_confidence", "annotator_notes"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} rows → {csv_path}")

    # Save kappa JSON
    result = {
        "project_id": project_id,
        "tasks_total": len(tasks),
        "tasks_with_2_annotations": tasks_with_2,
        "kappa": kappa_result,
        "annotators": list(by_annotator.keys()),
    }
    Path(output_path).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nSummary saved → {output_path}")


def _resolve_token(token: str | None, token_file: str | None, repo_root: str) -> str | None:
    if token:
        return token
    path = token_file or os.environ.get("LS_TOKEN_FILE")
    if path and not os.path.isabs(path):
        path = os.path.join(repo_root, path)
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    default = os.path.join(repo_root, ".label_studio_data", "admin_token.txt")
    if os.path.isfile(default):
        with open(default, encoding="utf-8") as f:
            return f.read().strip()
    return None


def main():
    repo_root = str(Path(__file__).resolve().parent.parent)
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("LS_URL", "http://localhost:8080"))
    parser.add_argument("--token", default=os.environ.get("LS_TOKEN"), help="API token or use --token-file / .label_studio_data/admin_token.txt")
    parser.add_argument("--token-file", default=os.environ.get("LS_TOKEN_FILE"), help="Path to file with token (one line)")
    parser.add_argument("--project-id", type=str, default=os.environ.get("LS_PROJECT_ID", "1"),
                        help="Project ID (integer or UUID from Label Studio)")
    parser.add_argument("--output", default="eval/results/kappa_label_studio.json")
    args = parser.parse_args()
    token = _resolve_token(args.token, args.token_file, repo_root)
    if not token:
        parser.error("Set --token, LS_TOKEN, or create .label_studio_data/admin_token.txt (one line)")
    export_annotations(args.url, token, args.project_id, args.output)


if __name__ == "__main__":
    main()
