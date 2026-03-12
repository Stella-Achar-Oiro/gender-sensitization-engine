#!/usr/bin/env bash
# Restart Label Studio with legacy API tokens enabled so DB tokens work for the annotation script.
# Run from repo root: bash scripts/restart_label_studio_legacy_tokens.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LS_DATA="$REPO_ROOT/.label_studio_data"
LS_PORT=8080
VENV="$REPO_ROOT/.ls_venv"

if [ ! -f "$VENV/bin/label-studio" ]; then
  echo "Run setup first: bash scripts/setup_label_studio.sh"
  exit 1
fi

echo "Stopping Label Studio on port $LS_PORT..."
OLD_PID=$(lsof -t -i ":$LS_PORT" 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then kill $OLD_PID 2>/dev/null || true; fi
sleep 3

echo "Starting Label Studio with legacy API tokens enabled..."
cd "$REPO_ROOT"
export LABEL_STUDIO_BASE_DATA_DIR="$LS_DATA"
export DJANGO_DB=sqlite
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN=true
  "$VENV/bin/label-studio" start \
    --port $LS_PORT \
    --host 0.0.0.0 \
    --no-browser \
    --enable-legacy-api-token \
    > "$LS_DATA/label_studio.log" 2>&1 &

for i in $(seq 1 30); do
  sleep 2
  if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$LS_PORT/health" 2>/dev/null | grep -q 200; then
    echo "Label Studio ready at http://localhost:$LS_PORT"
    exit 0
  fi
done
echo "Timeout waiting for Label Studio. Check $LS_DATA/label_studio.log"
exit 1
