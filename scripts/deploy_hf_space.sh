#!/usr/bin/env bash
# Deploy the app to a Hugging Face Space.
#
#   scripts/deploy_hf_space.sh staging            # build + push to the staging Space
#   scripts/deploy_hf_space.sh live               # promote what staging is running
#   scripts/deploy_hf_space.sh staging --dry-run  # show what would change, push nothing
#
# The Spaces have their own git history (no common ancestor with main, and the
# ground-truth CSVs exceed HF's file size limit), so `git push hfspace main` cannot
# work. This script copies the runtime files from SOURCE_REF (default: main) onto
# the local branch deploy/multilingual-hfspace and pushes that branch.
#
# "live" refuses to run unless staging is healthy on the same commit and live has
# no variables or secrets that staging lacks (a stale secret crashed live once).
set -euo pipefail

TARGET="${1:-}"; DRY_RUN="${2:-}"
SOURCE_REF="${SOURCE_REF:-main}"
BRANCH="deploy/multilingual-hfspace"
OWNER="juakazike"
STAGING_SPACE="autotrain-advanced"
LIVE_SPACE="gender-sensitization-engine"
RUNTIME_PATHS=(api core eval rules config.py frontend requirements_docker.txt)

case "$TARGET" in
  staging) SPACE="$STAGING_SPACE" ;;
  live)    SPACE="$LIVE_SPACE" ;;
  *) echo "usage: $0 staging|live [--dry-run]" >&2; exit 2 ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel)"; cd "$REPO_ROOT"
TOKEN="${HF_TOKEN:-$(git remote get-url hfspace | sed -E 's#https://[^:]+:([^@]+)@.*#\1#')}"
api()  { curl -fsS -m 30 -H "Authorization: Bearer $TOKEN" "https://huggingface.co/api/spaces/$OWNER/$1"; }
stage_and_sha() { api "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('runtime') or {}).get('stage'), d.get('sha'))"; }
setting_names() { { api "$1/variables"; api "$1/secrets"; } | python3 -c "
import sys,json
names=set()
for line in sys.stdin.read().replace('}{','}\n{').splitlines():
    names |= set(json.loads(line))
print(' '.join(sorted(names)))"; }
wait_until_running() {  # space, sha
  for _ in $(seq 1 120); do
    read -r stage sha <<<"$(stage_and_sha "$1")"
    case "$stage" in
      RUNNING) [ "$sha" = "$2" ] && return 0 ;;
      *ERROR*|PAUSED) echo "Space $1 is in state $stage" >&2; return 1 ;;
    esac
    sleep 15
  done
  echo "Timed out waiting for $1" >&2; return 1
}

if [ "$TARGET" = "staging" ]; then
  WORKTREE="$(mktemp -d)"; trap 'git worktree remove --force "$WORKTREE" 2>/dev/null || true' EXIT
  git worktree add -q "$WORKTREE" "$BRANCH"
  (
    cd "$WORKTREE"
    git rm -r -q --ignore-unmatch "${RUNTIME_PATHS[@]}"
    git checkout -q "$SOURCE_REF" -- "${RUNTIME_PATHS[@]}"
    git rm -q --cached --ignore-unmatch 'eval/ground_truth_*.csv'; rm -f eval/ground_truth_*.csv
    git show "$SOURCE_REF:infra/docker/Dockerfile" > Dockerfile
    git show "$SOURCE_REF:README.md" | sed 's/^app_port: .*/app_port: 8000/' > README.md
    git add -A
    if git diff --cached --quiet; then
      echo "Deploy branch already matches $SOURCE_REF."
    else
      git diff --cached --stat | tail -15
      [ "$DRY_RUN" = "--dry-run" ] || git commit -q -m "deploy: sync with $SOURCE_REF @ $(git rev-parse --short "$SOURCE_REF")"
    fi
  )
  [ "$DRY_RUN" = "--dry-run" ] && { echo "Dry run: nothing committed or pushed."; exit 0; }
else
  read -r stage sha <<<"$(stage_and_sha "$STAGING_SPACE")"
  [ "$stage" = "RUNNING" ] && [ "$sha" = "$(git rev-parse "$BRANCH")" ] || {
    echo "Staging is not running the commit on $BRANCH (stage=$stage). Deploy to staging and verify it first." >&2; exit 1; }
  extra="$(comm -23 <(setting_names "$LIVE_SPACE" | tr ' ' '\n') <(setting_names "$STAGING_SPACE" | tr ' ' '\n') | tr '\n' ' ')"
  [ -z "${extra// }" ] || { echo "Live has variables/secrets that staging does not: $extra— remove them or add them to staging and re-test." >&2; exit 1; }
  [ "$DRY_RUN" = "--dry-run" ] && { echo "Dry run: checks passed, nothing pushed."; exit 0; }
fi

SHA="$(git rev-parse "$BRANCH")"
git push "https://$OWNER:$TOKEN@huggingface.co/spaces/$OWNER/$SPACE" "$BRANCH:refs/heads/main" 2>&1 | sed -E 's/hf_[A-Za-z0-9]+/<token>/g'
wait_until_running "$SPACE" "$SHA"
curl -fsS -m 30 "https://$OWNER-$SPACE.hf.space/health"; echo
echo "$TARGET is running $SHA"
