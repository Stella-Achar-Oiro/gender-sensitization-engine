#!/usr/bin/env python3
"""
Run AI annotations on Label Studio tasks and submit them.
Two models: rules (BiasDetector, sw-annotate style) and ml (ML classifier).
Run once with rules (e.g. admin token), once with ml (e.g. ann2 token) to get
two annotators for Cohen's κ.

Usage (from repo root):
  # Annotator 1 — rules (default): run with admin token
  python3 scripts/run_ai_annotations_label_studio.py --url http://localhost:8080 --token <admin-token> --project-id 1

  # Annotator 2 — ML: run with ann2 token (log in as ann2@juakazi.ai, get token from Account & settings)
  python3 scripts/run_ai_annotations_label_studio.py --model ml --url http://localhost:8080 --token <ann2-token> --project-id 1

  # Dry-run from CSV (no API): --csv path --dry-run [--limit N]
  python3 scripts/run_ai_annotations_label_studio.py --csv data/annotation_export/batch_for_annotator_B_kappa_overlap.csv --dry-run --limit 5

Requires: Label Studio running, project with tasks; token (unless --csv --dry-run).
"""
import argparse
import csv as csv_module
import json
import os
import sys
import urllib.request
import urllib.error

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from eval.bias_detector import BiasDetector
from eval.models import Language, Explicitness, StereotypeCategory

# ML classifier for second annotator (optional)
try:
    from eval.ml_classifier import classify as ml_classify
except Exception:
    ml_classify = None


# Map our stereotype_category to Label Studio minimal config choices
LS_CATEGORIES = {
    "profession": "occupational_stereotype",
    "occupation": "occupational_stereotype",
    "family_role": "family_role",
    "leadership": "leadership",
    "capability": "other",
    "appearance": "other",
    "personality": "other",
    "religion_culture": "other",
    "daily_life": "other",
    "education": "other",
    "proverb_idiom": "other",
    "none": "other",
}
LS_CATEGORY_DEROGATION = "derogation"


def _build_expected_correction(text: str, edits: list) -> str:
    """Build corrected sentence by applying each edit's from→to once."""
    if not edits:
        return ""
    out = text
    for e in edits:
        from_phrase = e.get("from") or ""
        to_phrase = e.get("to") or ""
        if from_phrase and from_phrase in out:
            out = out.replace(from_phrase, to_phrase, 1)
    return out if out != text else ""


def _map_category(result) -> str:
    """Map BiasDetectionResult to Label Studio stereotype_category value."""
    if result.bias_label and "derogation" in str(result.bias_label).lower():
        return LS_CATEGORY_DEROGATION
    cat = result.stereotype_category
    if cat is None:
        return "other"
    raw = (cat.value if hasattr(cat, "value") else str(cat)).lower()
    return LS_CATEGORIES.get(raw, "other")


def annotate_one(text: str) -> dict:
    """Run detector on one sentence; return dict of Label Studio field values."""
    detector = BiasDetector(enable_ml_fallback=False)
    result = detector.detect_bias(text.strip(), Language.SWAHILI)

    has_bias = result.has_bias_detected
    expected_correction = _build_expected_correction(text, result.detected_edits) if has_bias else ""

    if has_bias and result.explicitness:
        explicitness = result.explicitness.value if hasattr(result.explicitness, "value") else str(result.explicitness)
    else:
        explicitness = "explicit"  # placeholder when no bias

    # Confidence: high if we have clear edits, medium if only warn, low for borderline
    if has_bias and result.confidence and result.confidence >= 0.9:
        confidence = "high"
    elif has_bias:
        confidence = "medium"
    else:
        confidence = "high"  # no bias is usually high confidence

    return {
        "has_bias": "true" if has_bias else "false",
        "stereotype_category": _map_category(result),
        "explicitness": explicitness,
        "expected_correction": expected_correction,
        "annotator_confidence": confidence,
        "annotator_notes": "AI annotator (rules-based, sw-annotate style)",
    }


# Threshold for ML model: score >= this → has_bias=true
ML_BIAS_THRESHOLD = float(os.environ.get("JUAKAZI_ML_THRESHOLD", "0.75"))


def annotate_one_ml(text: str) -> dict:
    """Second annotator: ML classifier only. No expected_correction or fine-grained category."""
    if ml_classify is None:
        raise RuntimeError("ML classifier not available (eval.ml_classifier)")
    score = ml_classify(text.strip(), Language.SWAHILI)
    has_bias = score >= ML_BIAS_THRESHOLD
    if score >= 0.9:
        confidence = "high"
    elif score >= ML_BIAS_THRESHOLD:
        confidence = "medium"
    else:
        confidence = "high"  # no bias
    return {
        "has_bias": "true" if has_bias else "false",
        "stereotype_category": "other",  # ML does not predict category
        "explicitness": "implicit" if has_bias else "explicit",
        "expected_correction": "",  # ML is warn-only, no correction
        "annotator_confidence": confidence,
        "annotator_notes": "AI annotator (ML classifier)",
    }


def build_result_payload(ann: dict) -> list:
    """Build Label Studio result array for minimal config (Choices + TextArea)."""
    to_name = "text"
    out = [
        {"from_name": "has_bias", "to_name": to_name, "type": "choices", "value": {"choices": [ann["has_bias"]]}},
        {"from_name": "stereotype_category", "to_name": to_name, "type": "choices", "value": {"choices": [ann["stereotype_category"]]}},
        {"from_name": "explicitness", "to_name": to_name, "type": "choices", "value": {"choices": [ann["explicitness"]]}},
        {"from_name": "expected_correction", "to_name": to_name, "type": "textarea", "value": {"text": [ann["expected_correction"]]}},
        {"from_name": "annotator_confidence", "to_name": to_name, "type": "choices", "value": {"choices": [ann["annotator_confidence"]]}},
        {"from_name": "annotator_notes", "to_name": to_name, "type": "textarea", "value": {"text": [ann["annotator_notes"]]}},
    ]
    return out


def fetch_json(url: str, token: str) -> dict | list:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def post_annotation(url: str, token: str, task_id: int, result: list) -> dict:
    """POST one annotation to Label Studio. Uses token's user as completed_by."""
    # Get current user so we can set completed_by (optional; server may use token user)
    try:
        me = fetch_json(f"{url.rstrip('/')}/api/current-user", token)
        user_id = me.get("id") or me.get("pk")
    except Exception:
        user_id = None

    payload = {"result": result}
    if user_id is not None:
        payload["completed_by"] = user_id

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/tasks/{task_id}/annotations/",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    p = argparse.ArgumentParser(description="Run AI annotations on Label Studio tasks")
    p.add_argument("--url", default=os.environ.get("LS_URL", "http://localhost:8080"), help="Label Studio URL")
    p.add_argument("--token", default=os.environ.get("LS_TOKEN"), required=False, help="API token (or LS_TOKEN or --token-file)")
    p.add_argument("--token-file", default=os.environ.get("LS_TOKEN_FILE"), help="Path to file containing token (one line). Default env: LS_TOKEN_FILE")
    p.add_argument("--project-id", default=os.environ.get("LS_PROJECT_ID", "1"), help="Project ID")
    p.add_argument("--model", choices=("rules", "ml"), default="rules", help="Annotator model: rules (BiasDetector) or ml (ML classifier). Use rules first, then ml with ann2 token for κ.")
    p.add_argument("--csv", default=None, help="Path to CSV with id,text columns (for --dry-run without API)")
    p.add_argument("--dry-run", action="store_true", help="Only print what would be submitted")
    p.add_argument("--limit", type=int, default=None, help="Max tasks to annotate (default: all)")
    args = p.parse_args()

    url = None
    token = None
    if args.csv and args.dry_run:
        # Dry-run from CSV only — no token needed
        csv_path = os.path.join(repo_root, args.csv) if not os.path.isabs(args.csv) else args.csv
        if not os.path.isfile(csv_path):
            print(f"Error: CSV not found: {csv_path}", file=sys.stderr)
            sys.exit(1)
        tasks = []
        with open(csv_path, encoding="utf-8") as f:
            for row in csv_module.DictReader(f):
                tasks.append({"id": row.get("id", ""), "data": {"text": row.get("text", ""), "id": row.get("id", "")}})
        if args.limit:
            tasks = tasks[: args.limit]
        print(f"Dry-run from CSV: {len(tasks)} row(s)")
    else:
        token = args.token
        if not token and args.token_file:
            path = os.path.join(repo_root, args.token_file) if not os.path.isabs(args.token_file) else args.token_file
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    token = f.read().strip()
        if not token and args.model == "ml":
            ann2_path = os.environ.get("LS_TOKEN_ANN2_FILE")
            if ann2_path and not os.path.isabs(ann2_path):
                ann2_path = os.path.join(repo_root, ann2_path)
            if not ann2_path:
                ann2_path = os.path.join(repo_root, ".label_studio_data", "ann2_token.txt")
            if os.path.isfile(ann2_path):
                with open(ann2_path, encoding="utf-8") as f:
                    token = f.read().strip()
        if not token:
            admin_path = os.path.join(repo_root, ".label_studio_data", "admin_token.txt")
            if os.path.isfile(admin_path):
                with open(admin_path, encoding="utf-8") as f:
                    token = f.read().strip()
        if not token:
            hint = "For --model ml you can use .label_studio_data/ann2_token.txt (ann2's token). " if args.model == "ml" else ""
            print(f"Error: set --token, LS_TOKEN, or create .label_studio_data/admin_token.txt (one line) or use --token-file. {hint}", file=sys.stderr)
            sys.exit(1)
        url = args.url.rstrip("/")
        project_id = args.project_id
        tasks_url = f"{url}/api/projects/{project_id}/tasks?page_size=500"
        try:
            data = fetch_json(tasks_url, token)
        except urllib.error.HTTPError as e:
            print(f"Error fetching tasks: {e.code} {e.read().decode()}", file=sys.stderr)
            sys.exit(1)
        tasks = data if isinstance(data, list) else data.get("tasks", data.get("results", []))
        if not tasks:
            print("No tasks found.")
            return
    if args.limit:
        tasks = tasks[: args.limit]

    annotate_fn = annotate_one if args.model == "rules" else annotate_one_ml
    if args.model == "ml" and ml_classify is None:
        print("Error: --model ml requires eval.ml_classifier (transformers). Install or set JUAKAZI_ML_MODEL.", file=sys.stderr)
        sys.exit(1)

    print(f"Annotating with model={args.model} ({len(tasks)} task(s))...")
    if args.dry_run:
        print("(dry-run: no POSTs)")

    # Skip only when task already has 2 annotations (full); allow adding second annotator
    max_ann = 2
    done = 0
    skipped = 0
    for task in tasks:
        task_id = task.get("id")
        if len(task.get("annotations") or []) >= max_ann:
            skipped += 1
            continue
        text = (task.get("data") or {}).get("text", "")
        if not text:
            print(f"  Skip task {task_id}: no text", file=sys.stderr)
            continue

        try:
            ann = annotate_fn(text)
        except Exception as e:
            print(f"  Task {task_id} annotate error: {e}", file=sys.stderr)
            continue
        result = build_result_payload(ann)

        if args.dry_run:
            print(f"  Task {task_id}: has_bias={ann['has_bias']} category={ann['stereotype_category']}")
            done += 1
            continue

        if not url or not token:
            done += 1
            continue
        try:
            post_annotation(url, token, task_id, result)
            done += 1
            if done % 50 == 0:
                print(f"  Submitted {done}...")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  Task {task_id} failed: {e.code} {body}", file=sys.stderr)

    if skipped:
        print(f"Skipped {skipped} task(s) (already annotated).")
    if args.dry_run:
        print(f"Done. Would submit {done} annotation(s).")
    else:
        print(f"Done. Submitted {done} annotation(s).")
    if not args.dry_run and done > 0:
        print("For Cohen's κ you need a second annotator (human or different model). Export with:")
        print("  python3 scripts/export_label_studio_annotations.py --url ... --token ... --project-id ... --output ...")


if __name__ == "__main__":
    main()
