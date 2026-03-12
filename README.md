# JuaKazi Gender Sensitization Engine

Multilingual gender bias detection and correction engine for East African languages. Targets Swahili, English, French, and Kikuyu. Rules-based detection with ML fallback, context-aware correction, and AIBRIDGE-compliant evaluation.

## Current Metrics (Mar 2026)

| Language | F1    | Precision | Recall | Ground Truth | Status |
|----------|-------|-----------|--------|--------------|--------|
| English  | 0.786 | 1.000     | 0.647  | 66 samples   | Production |
| Swahili  | 0.771 | 0.734     | 0.811  | 64,723 samples | Active development |
| French   | 0.750 | 1.000     | 0.600  | 50 samples   | Beta |
| Kikuyu   | 0.352 | 0.926     | 0.217  | 11,848 samples | Early stage |

SW precision (0.734) reflects honest signal from the ann_sw_v3 ground truth pass. Main FP drivers are `Watoto wa Kike` and `mtoto wa kike` — genuinely ambiguous phrases that appear in both advocacy and prescriptive contexts. This is documented and accepted.

## Quick Start

```bash
# Evaluation
make dev-eval                        # F1/Precision/Recall for all 4 languages
python3 run_evaluation.py            # same, direct

# Tests (must stay 5/5)
python3 tests/test_system.py

# Live demo
python3 demo_live.py

# API + web (local dev)
make run                             # FastAPI :8080 + Next.js :3001
make run-api                         # FastAPI only
make run-web                         # Next.js only (requires API running)

# Streamlit review UI
make dev-ui                          # :8501
```

## Architecture

Detection runs in three stages:

1. **Rules-based matching** — lexicons at `rules/lexicon_{lang}_v3.csv`, matched via `DetectorPatterns` (`eval/detector_patterns.py`).
2. **Context gating** — `ContextChecker` (`core/context_checker.py`) suppresses matches in quotes, biographical references, historical context, statistics, medical text, counter-stereotype framing, and more. The `avoid_when` field in lexicon CSVs uses pipe-separated `ContextCondition` enum values.
3. **ML fallback** — when rules find nothing, `ml_classifier.py` runs `juakazike/sw-bias-classifier-v1` (afro-xlmr-base fine-tuned on 51K Swahili rows). ML edits carry `severity=ml_fallback` and `needs_review=True`.

Correction API (`api/`):

```
api/main.py        # HTTP routing (FastAPI)
api/service.py     # Rewrite logic: rules -> semantic check -> ML fallback
api/rules_engine.py  # apply_rules_on_spans(), build_reason()
api/schemas.py     # RewriteRequest, RewriteResponse (Pydantic)
api/audit.py       # JSONL audit log
```

Frontends:

| Frontend | Path | Port | Purpose |
|----------|------|------|---------|
| Next.js web app | `apps/web/` | 3001 local / 3000 Docker | Public demo |
| Streamlit review UI | `ui/` | 8501 | Internal annotation review |

Shared core (`core/`):

```
core/context_checker.py        # ContextChecker, ContextCondition
core/rules_loader.py           # Lexicon CSV loading
core/semantic_preservation.py  # Composite score for rewrite quality
```

## Project Structure

```
api/                     # Correction API (FastAPI)
apps/web/                # Next.js frontend
core/                    # Shared detection logic
data/
  raw/                   # Source datasets, staged annotation batches
  analysis/              # Annotation samples and analysis outputs
docs/
  eval/                  # Model card, dataset card, eval protocol
eval/                    # Evaluation framework (BiasDetector, ground truth CSVs)
rules/                   # Lexicons (lexicon_{en,sw,fr,ki}_v3.csv)
scripts/                 # Data collection, annotation pipeline, kappa calculation
ui/                      # Streamlit review UI
config.py                # Central config (versions, thresholds, dialects)
run_evaluation.py        # Main eval runner
train_ml_model.py        # ML classifier training
```

## Lexicons

| Language | File | Entries | Notes |
|----------|------|---------|-------|
| English  | `rules/lexicon_en_v3.csv` | 515 | Production |
| Swahili  | `rules/lexicon_sw_v3.csv` | ~187 | Includes proverbs, Sheng, bride-price patterns |
| French   | `rules/lexicon_fr_v3.csv` | ~69 | Expanded Mar 2026 |
| Kikuyu   | `rules/lexicon_ki_v3.csv` | 1,209 | avoid_when enum fix pending |

`avoid_when` must be pipe-separated `ContextCondition` enum values: `quote`, `historical`, `proper_noun`, `biographical`, `statistical`, `medical`, `counter_stereotype`, `legal`, `artistic`, `organization`.

## ML Classifier

Model: `juakazike/sw-bias-classifier-v1`
- Base: afro-xlmr-base
- Fine-tuned on 51K Swahili rows, 3 epochs, T4 x2
- Val metrics: Precision=0.938, Recall=0.784, F1=0.854
- Activated via `JUAKAZI_ML_MODEL` env var in HF Space
- Stage 2 fallback only — never rewrites text, warn-only

## Requirements

Core evaluation and detection run with no dependencies (Python 3.12+ stdlib only):

```bash
python3 run_evaluation.py
python3 demo_live.py
python3 tests/test_system.py
```

Optional dependencies via `pyproject.toml`:

```bash
pip install -e ".[api]"   # FastAPI + pandas
pip install -e ".[ui]"    # Streamlit
pip install -e ".[ml]"    # Transformers, PyTorch, scikit-learn
pip install -e ".[dev]"   # pytest, black, ruff, mypy
```

## Hard Rules

1. `python3 tests/test_system.py` must stay 5/5 before any merge.
2. Run `python3 run_evaluation.py` before and after any lexicon or detector change.
3. `severity=replace` rules require Precision >= 1.000 for EN/FR. SW is 0.734 (documented exception).
4. `avoid_when` must use pipe-separated `ContextCondition` enum values — never prose.
5. Work in branches; squash-merge to main. Never commit directly to main.
6. Never push unless explicitly asked.

## Sprint Status (Mar 2026)

- Sprint 0-1: merged to main
- Sprint 2: IN PROGRESS — blocked on 2nd annotator recruitment (Cohen's Kappa required for AIBRIDGE Bronze)
- Sprint 3-4: not started (Sprint 4 web app can run in parallel with Sprint 3)

AIBRIDGE Bronze blockers:
- F1 >= 0.75 per language: EN (0.786), SW (0.771), FR (0.750) all pass; KI (0.352) does not
- Cohen's Kappa >= 0.70: unmeasured, requires 2nd Swahili native-speaker annotator
- Recruit via Masakhane Slack (Project Lead task)

## Documentation

- [Model Card](docs/eval/model_card.md)
- [Dataset Card](docs/eval/dataset_datasheet.md)
- [Evaluation Protocol](docs/eval/eval_protocol.md)
- [AIBRIDGE F1 Note](docs/SWAHILI_F1_NOTE.md)
- [Data Prompts](docs/DATA_PROMPTS.md)

## License

Open source. See project license for details.
