# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Local dev (no Docker)
```bash
make run          # API (port 8080) + Next.js web (port 3001); Ctrl+C stops both
make run-api      # FastAPI only at :8080
make run-web      # Next.js only at :3001 (requires API running separately)
make dev-ui       # Streamlit review UI at :8501 (uses venv/bin/streamlit)
make dev-test     # pytest locally (skips slow tests)
make dev-eval     # python3 run_evaluation.py (F1/Precision/Recall per language)
```

### Docker (recommended for CI parity)
```bash
make build        # Build Docker image
make test         # Run all tests in Docker
make eval         # Run evaluation in Docker
make up           # API (:8000) + Streamlit UI (:8501)
make up-web       # API (:8000) + Next.js (:3000)
make down         # Stop all services
```

### Individual test runs
```bash
python3 -m pytest tests/ -v -k "not slow"    # all fast tests
python3 -m pytest tests/test_system.py -v    # 5-test smoke suite (must stay green)
python3 run_evaluation.py                    # F1 eval (all 4 languages)
python3 run_evaluation.py --fairness         # + AIBRIDGE fairness metrics
```

### Code quality
```bash
make format   # black + isort
make lint     # flake8
```

---

## Architecture

This is a **multilingual gender bias detection and correction engine** targeting East African languages (Swahili, Kikuyu, English, French). The system has three tiers:

### 1. Detection pipeline (`eval/`)

`BiasDetector` (`eval/bias_detector.py`) orchestrates three stages:
1. **Rules-based matching** — loads lexicons from `rules/lexicon_{lang}_v3.csv`, matches biased terms using `DetectorPatterns` (`eval/detector_patterns.py`).
2. **Context gating** — `ContextChecker` (`core/context_checker.py`, re-exported via `eval/context_checker.py`) decides whether to suppress a match. The `ContextCondition` enum defines all valid gate conditions: `quote`, `historical`, `proper_noun`, `biographical`, `statistical`, `medical`, `counter_stereotype`, `legal`, `artistic`, `organization`. The `avoid_when` field in lexicon CSVs must use **pipe-separated** enum values — no prose.
3. **ML fallback** — when rules find nothing, `ml_classifier.py` runs `juakazike/sw-bias-classifier-v1` (afro-xlmr-base fine-tuned on 51K Swahili rows). ML edits have `severity=ml_fallback` and `needs_review=True`.

Swahili noun-class agreement is tracked by `NgeliTracker` (`eval/ngeli_tracker.py`).

### 2. Correction API (`api/`)

```
api/main.py       # HTTP routing only (FastAPI); validates request, delegates
api/service.py    # Core rewrite logic: rules → semantic check → ML fallback
api/rules_engine.py  # apply_rules_on_spans(), build_reason() — closure-safe, module-level cache
api/schemas.py    # RewriteRequest, RewriteResponse (Pydantic)
api/audit.py      # Appends JSONL audit log after each request
```

**Rewrite decision flow** (`api/service.py`):
1. `apply_rules_on_spans()` → produces edits.
2. If the rewrite diverges semantically (composite score < `JUAKAZI_SEMANTIC_THRESHOLD`, default 0.70), revert to original (`source=preserved`).
3. If no rules matched, run ML rewriter (`api/ml_rewriter.py`); same semantic gate applies.
4. `build_reason()` produces the human-readable `reason` field.

### 3. Frontends

| Frontend | Path | Port | Purpose |
|---|---|---|---|
| Next.js web app | `apps/web/` | 3001 (local) / 3000 (Docker) | Public demo; proxies `/api/*` to FastAPI in dev |
| Streamlit review UI | `ui/` | 8501 | Internal annotation review |

Next.js dev proxy: in dev mode `next.config.ts` rewrites `/api/*` → `http://127.0.0.1:8080/*`, so the web app hits the local FastAPI without any `.env` setup.

### 4. Shared core (`core/`)

```
core/context_checker.py       # ContextChecker, ContextCondition — shared by eval and api
core/rules_loader.py          # Lexicon CSV loading
core/semantic_preservation.py # SemanticPreservationMetrics (composite score for rewrite quality)
```

### 5. Configuration (`config.py`)

Centralises:
- `DataVersions` — lexicon `v3`, ground truth `v5` (Kikuyu: `v8`).
- `RegionDialects` — valid `region_dialect` values for API requests and audit logs.
- `get_semantic_threshold()` — reads `JUAKAZI_SEMANTIC_THRESHOLD` env var.
- `REWRITE_CONFIDENCE_BY_SOURCE` — confidence scores per rewrite source.

Use `config.lexicon_filename(lang)` and `config.ground_truth_filename(lang)` to get the correct versioned paths.

---

## Hard rules — never break these

1. **Always keep `python3 tests/test_system.py` at 5/5 passing** before any merge.
2. **Always run `python3 run_evaluation.py` before and after any lexicon or detector change** to confirm no F1 regression.
3. **`severity=replace` rules require Precision ≥ 1.000 for EN/FR**. SW currently 0.734 (accepted — documented). Never add a replace rule without a before/after eval run.
4. **`avoid_when` must be pipe-separated `ContextCondition` enum values** (e.g. `biographical|historical`). Never use prose text.
5. **Work in branches; squash-merge to main.** Never commit directly to main. Start a new branch before any work.
6. **Never push unless explicitly asked.**
7. No new files unless strictly required. Edit existing files.
8. **HF Space deployment — use `hf-deploy` branch, remote `hfspace`.** The `hf-deploy` branch only contains `gradio_app.py`, `requirements.txt`, `rules/`, `eval/`, `core/`, `api/`, `config.py`. It does NOT have `run_evaluation.py`, `tests/`, or `apps/`. Always do lexicon/detector work on `main` first, then cherry-pick or merge into `hf-deploy`. If the Space gets stuck in "Restarting" loop: do a **Factory Reset** from HF Space Settings, then `git push hfspace hf-deploy --force`. The stuck-restart loop is caused by broken HF-side state, not our code. Token for `hfspace` remote: set via `git remote set-url hfspace https://juakazike:<TOKEN>@huggingface.co/spaces/juakazike/gender-sensitization-engine`.

---

## Current metrics (Mar 2026)

| Language | F1 | Precision | Recall | Samples |
|---|---|---|---|---|
| Swahili | 0.819 | 0.739 | 0.919 | 64,723 |
| English | 0.885 | 1.000 | 0.794 | 66 |
| French | 0.793 | 1.000 | 0.657 | 50 |
| Kikuyu | 0.368 | 0.916 | 0.231 | 11,848 |

SW precision drop (0.958 → 0.734) is intentional: reflects honest ground truth from ann_sw_v3. Main FP drivers: `Watoto wa Kike` (182 FPs), `mtoto wa kike` (138 FPs) — genuinely ambiguous phrases accepted as a known precision hit.

---

## Sprint status (Mar 2026)

- Sprint 0–1: ✅ merged to main
- Sprint 2: 🔴 IN PROGRESS — blocked on 2nd annotator recruitment (Cohen's Kappa unmeasured; required for AIBRIDGE Bronze)
- Sprint 3–4: 🟡 not started (Sprint 4 web app can run in parallel with Sprint 3)

AIBRIDGE blocker: Project Lead must recruit 2nd Swahili native-speaker annotator via Masakhane Slack for κ calculation.
