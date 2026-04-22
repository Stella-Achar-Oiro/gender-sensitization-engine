#!/usr/bin/env bash
# Run both AI annotators (rules + ML) and export for Cohen's κ.
# Uses token files so you don't paste tokens each time.
#
# One-time setup:
#   1. Label Studio: http://localhost:8080 → log in as admin → Account & settings → copy API token.
#   2. echo "YOUR_ADMIN_TOKEN" > .label_studio_data/admin_token.txt
#   3. Log in as ann2@juakazi.ai → Account & settings → copy token.
#   4. echo "ANN2_TOKEN" > .label_studio_data/ann2_token.txt
#
# Then run (from repo root):
#   bash scripts/run_label_studio_ai_flow.sh
#
# Optional: LS_URL=http://... LS_PROJECT_ID=1 bash scripts/run_label_studio_ai_flow.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

LS_URL="${LS_URL:-http://localhost:8080}"
LS_PROJECT_ID="${LS_PROJECT_ID:-1}"
OUTPUT="${LS_KAPPA_OUTPUT:-eval/results/kappa_label_studio.json}"

ADMIN_TOKEN_FILE="$REPO_ROOT/.label_studio_data/admin_token.txt"
ANN2_TOKEN_FILE="$REPO_ROOT/.label_studio_data/ann2_token.txt"

if [[ ! -f "$ADMIN_TOKEN_FILE" ]]; then
  echo "Create $ADMIN_TOKEN_FILE with your admin API token (one line)."
  echo "  Label Studio → log in as admin → Account & settings → copy token."
  exit 1
fi

echo "=== 1. Annotator 1 (rules) ==="
python3 scripts/run_ai_annotations_label_studio.py \
  --url "$LS_URL" \
  --project-id "$LS_PROJECT_ID"

echo ""
echo "=== 2. Annotator 2 (ML) ==="
if [[ ! -f "$ANN2_TOKEN_FILE" ]]; then
  echo "Create $ANN2_TOKEN_FILE with ann2's API token to run the second annotator."
  echo "  Log in as ann2@juakazi.ai → Account & settings → copy token."
  echo "Skipping step 2. Export will only have one annotator."
else
  python3 scripts/run_ai_annotations_label_studio.py \
    --model ml \
    --url "$LS_URL" \
    --project-id "$LS_PROJECT_ID"
fi

echo ""
echo "=== 3. Export and κ ==="
mkdir -p "$(dirname "$OUTPUT")"
python3 scripts/export_label_studio_annotations.py \
  --url "$LS_URL" \
  --project-id "$LS_PROJECT_ID" \
  --output "$OUTPUT"

echo ""
echo "Done. Results: $OUTPUT"
