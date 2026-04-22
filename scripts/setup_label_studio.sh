#!/bin/bash
# ============================================================
# JuaKazi Label Studio Setup — one-shot script
# Installs Label Studio, starts it, creates the project,
# imports 250-row kappa dataset, and creates 2 annotator accounts.
#
# Run from the repo root:
#   bash scripts/setup_label_studio.sh
#
# After it completes, open: http://localhost:8080
#   Admin login:       admin@juakazi.ai / juakazi2026
#   Annotator 1:       ann1@juakazi.ai  / annotator1pass
#   Annotator 2:       ann2@juakazi.ai  / annotator2pass
# ============================================================

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LS_DATA="$REPO_ROOT/.label_studio_data"
LS_PORT=8080
LS_URL="http://localhost:$LS_PORT"
ADMIN_EMAIL="admin@juakazi.ai"
ADMIN_PASS="juakazi2026"
ANN1_EMAIL="ann1@juakazi.ai"
ANN1_PASS="annotator1pass"
ANN2_EMAIL="ann2@juakazi.ai"
ANN2_PASS="annotator2pass"
VENV="$REPO_ROOT/.ls_venv"
KAPPA_CSV="$REPO_ROOT/data/annotation_export/batch_for_annotator_B_kappa_overlap.csv"
XML_CONFIG="$REPO_ROOT/scripts/label_studio_config.xml"

echo "================================================"
echo " JuaKazi Label Studio Setup"
echo "================================================"

# Prefer Python 3.11 or 3.12 (Label Studio 1.22 breaks on 3.14: find_loader removed)
PYTHON="python3"
for p in python3.11 python3.12 python3.10; do
  if command -v "$p" >/dev/null 2>&1; then
    PYTHON="$p"
    break
  fi
done
echo "[0] Using: $($PYTHON --version)"

# Stop any existing Label Studio on our port so re-runs work
if command -v lsof >/dev/null 2>&1; then
  OLD_PID=$(lsof -t -i ":$LS_PORT" 2>/dev/null || true)
  if [ -n "$OLD_PID" ]; then
    echo "Stopping existing process on port $LS_PORT (PID $OLD_PID)..."
    kill "$OLD_PID" 2>/dev/null || true
    sleep 2
  fi
fi

# ── 1. Create venv and install Label Studio ──────────────────
if [ ! -f "$VENV/bin/label-studio" ]; then
  echo "[1/6] Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
  echo "[1/6] Installing Label Studio (this takes ~3 min)..."
  "$VENV/bin/pip" install "label-studio==1.22.0" -q
  echo "[1/6] Done."
else
  echo "[1/6] Label Studio already installed."
fi

# ── 2. Start Label Studio ────────────────────────────────────
mkdir -p "$LS_DATA"
echo "[2/6] Starting Label Studio on port $LS_PORT..."

LABEL_STUDIO_BASE_DATA_DIR="$LS_DATA" \
DJANGO_DB=sqlite \
LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true \
LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN=true \
  "$VENV/bin/label-studio" start \
    --port $LS_PORT \
    --host 0.0.0.0 \
    --no-browser \
    --username "$ADMIN_EMAIL" \
    --password "$ADMIN_PASS" \
    > "$LS_DATA/label_studio.log" 2>&1 &

LS_PID=$!
echo "[2/6] PID: $LS_PID — waiting for startup..."

# Wait for the server to be ready (up to 60s)
for i in $(seq 1 30); do
  sleep 2
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LS_URL/health" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    echo "[2/6] Server ready."
    break
  fi
  if [ $i -eq 30 ]; then
    echo "ERROR: Server did not start within 60s."
    echo "Last log lines:"
    tail -20 "$LS_DATA/label_studio.log"
    exit 1
  fi
done

# ── 3. Get admin token (Label Studio has no login API; token is in DB) ──
echo "[3/6] Getting admin token..."
ADMIN_TOKEN=$(sqlite3 "$LS_DATA/label_studio.sqlite3" "SELECT key FROM authtoken_token WHERE user_id=(SELECT id FROM htx_user WHERE email='$ADMIN_EMAIL');" 2>/dev/null | head -1)
if [ -z "$ADMIN_TOKEN" ]; then
  echo "ERROR: No token in DB. Check $LS_DATA/label_studio.log"
  exit 1
fi
echo "[3/6] Token acquired."

AUTH="Authorization: Token $ADMIN_TOKEN"

# ── 4. Create the annotation project ────────────────────────
echo "[4/6] Creating JuaKazi annotation project..."
XML_CONTENT=$(cat "$XML_CONFIG")

PROJECT_ID=$(curl -s -X POST "$LS_URL/api/projects/" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d "{
    \"title\": \"JuaKazi — Swahili Kappa Overlap (250 rows)\",
    \"description\": \"250-row inter-annotator agreement set. Both annotators review every row independently. Kappa computed automatically.\",
    \"label_config\": $(python3 -c "import json,sys; print(json.dumps(open('$XML_CONFIG').read()))"),
    \"maximum_annotations\": 2,
    \"overlap_cohort_percentage\": 100
  }" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: Could not create project."
  exit 1
fi
echo "[4/6] Project created. ID: $PROJECT_ID"

# ── 5. Import the 250-row kappa dataset ─────────────────────
echo "[5/6] Importing 250-row dataset..."
python3 - <<PYEOF
import csv, json, urllib.request, urllib.error

url = "$LS_URL/api/projects/$PROJECT_ID/import"
auth_header = "$ADMIN_TOKEN"
kappa_csv = "$KAPPA_CSV"

tasks = []
with open(kappa_csv, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        task = {"data": {"id": row["id"], "text": row["text"]}}
        tasks.append(task)

body = json.dumps(tasks).encode("utf-8")
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Authorization", f"Token {auth_header}")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Imported {result.get('task_count', '?')} tasks.")
except urllib.error.HTTPError as e:
    print(f"Import error: {e.code} {e.read().decode()}")
PYEOF

# ── 6. Create annotator accounts ────────────────────────────
echo "[6/6] Creating annotator accounts..."
for email_pass in "$ANN1_EMAIL:$ANN1_PASS" "$ANN2_EMAIL:$ANN2_PASS"; do
  EMAIL="${email_pass%%:*}"
  PASS="${email_pass##*:}"
  RESULT=$(curl -s -X POST "$LS_URL/api/users/" \
    -H "Content-Type: application/json" \
    -H "$AUTH" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"first_name\":\"Annotator\",\"last_name\":\"$(echo $EMAIL | cut -d@ -f1)\"}")
  USER_ID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','ERROR: ' + str(d)))" 2>/dev/null)
  echo "  Created $EMAIL (id=$USER_ID)"

  # Add to project as annotator
  curl -s -X POST "$LS_URL/api/projects/$PROJECT_ID/members/" \
    -H "Content-Type: application/json" \
    -H "$AUTH" \
    -d "{\"user\": $USER_ID}" > /dev/null 2>&1 || true
done

# ── 7. Set annotator passwords (API does not set them) ─────────
echo "[7/7] Setting annotator passwords..."
LABEL_STUDIO_BASE_DATA_DIR="$LS_DATA" DJANGO_DB=sqlite \
  "$VENV/bin/python" "$REPO_ROOT/scripts/set_label_studio_passwords.py" 2>/dev/null || true

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "================================================"
echo " Label Studio is READY"
echo "================================================"
echo ""
echo "  URL:           $LS_URL"
echo "  Project ID:    $PROJECT_ID"
echo ""
echo "  Admin:         $ADMIN_EMAIL / $ADMIN_PASS"
echo "  Annotator 1:   $ANN1_EMAIL / annotator1pass"
echo "  Annotator 2:   $ANN2_EMAIL / annotator2pass"
echo ""
echo "  HOW TO ANNOTATE:"
echo "  1. Open $LS_URL in your browser"
echo "  2. Log in as Annotator 1 — label all 250 rows"
echo "  3. Log in as Annotator 2 — label the same 250 rows"
echo "  4. Admin dashboard shows Cohen's Kappa automatically"
echo ""
echo "  EXPORT WHEN DONE:"
echo "  python3 scripts/export_label_studio_annotations.py"
echo ""
echo "  To stop: kill $LS_PID"
echo "  Logs:    $LS_DATA/label_studio.log"
echo ""
echo "  Tip: Annotator 2 can be YOU reviewing rows you"
echo "  previously annotated as Annotator 1 — or send"
echo "  the link to any Swahili speaker."
echo ""
