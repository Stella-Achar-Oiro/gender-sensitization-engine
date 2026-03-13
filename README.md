---
title: JuaKazi Gender Sensitization Engine
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: "4.44.0"
python_version: "3.11"
app_file: gradio_app.py
pinned: false
---

# JuaKazi Gender Sensitization Engine

Multilingual gender bias detection and correction engine targeting East African languages. Supports Swahili, English, French, and Kikuyu. Three-tier detection pipeline: rules-based lexicon matching → context gating → ML fallback. AIBRIDGE-compliant evaluation.

---

## Current Metrics (Mar 2026)

### Rules-based system (production)

| Language | F1    | Precision | Recall | Ground Truth   | Status |
|----------|-------|-----------|--------|----------------|--------|
| English  | 0.885 | 1.000     | 0.794  | 66 samples     | Production |
| Swahili  | 0.816 | 0.735     | 0.918  | 64,723 samples | Active development |
| French   | 0.793 | 1.000     | 0.657  | 50 samples     | Beta |
| Kikuyu   | 0.368 | 0.916     | 0.231  | 11,848 samples | Early stage |

SW precision (0.735) reflects honest signal from ann_sw_v3 ground truth. Main FP drivers: `Watoto wa Kike` (182 FPs), `mtoto wa kike` (138 FPs) — genuinely ambiguous phrases in both advocacy and prescriptive contexts. Documented and accepted.

### ML classifier — sw-bias-classifier-v2 (Swahili only)

| Model | Train data | Val split | Val F1 | Precision | Recall |
|-------|-----------|-----------|--------|-----------|--------|
| sw-bias-classifier-v1 | 51,419 rows (gt_sw_v4) | ~15% | 0.854 | 0.938 | 0.784 |
| sw-bias-classifier-v2 | 64,723 rows (gt_sw_v5) | 15% → 1,211 rows | **0.953** | 0.940 | 0.960 |

v2 training config: base=`Davlan/afro-xlmr-base`, epochs=10, batch=16, lr=2e-5, TRAIN_SPLIT=0.85, NEUTRAL_RATIO=4, BIAS_TARGET=3000 (augmented), frozen_layers=6. Target ≥0.92 — **TARGET MET**.

HuggingFace models: [`juakazike/sw-bias-classifier-v1`](https://huggingface.co/juakazike/sw-bias-classifier-v1) · [`juakazike/sw-bias-classifier-v2`](https://huggingface.co/juakazike/sw-bias-classifier-v2)

---

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

# Docker (CI parity)
make build && make test              # build + run all tests in Docker
make up                              # API :8000 + Streamlit :8501
```

---

## Architecture

### Detection pipeline (3 stages)

1. **Rules-based matching** — lexicons at `rules/lexicon_{lang}_v3.csv`, matched via `DetectorPatterns` (`eval/detector_patterns.py`). Swahili noun-class agreement tracked by `NgeliTracker`.
2. **Context gating** — `ContextChecker` (`core/context_checker.py`) suppresses matches in quotes, biographical references, historical context, statistics, medical text, counter-stereotype framing, legal, artistic, and organizational contexts. `avoid_when` in lexicon CSVs uses pipe-separated `ContextCondition` enum values.
3. **ML fallback** — when rules find nothing, `ml_classifier.py` runs `juakazike/sw-bias-classifier-v2` (afro-xlmr-base fine-tuned on 64,723 Swahili rows, Val F1=0.953). ML edits carry `severity=ml_fallback` and `needs_review=True`.

### Correction API (`api/`)

```
api/main.py          # HTTP routing only (FastAPI)
api/service.py       # Rewrite logic: rules → semantic check → Stage 2.5 LLM → ML fallback
api/disambiguator.py # Stage 2.5: Llama 3.1 8B via HF router for borderline SW warn cases
api/rules_engine.py  # apply_rules_on_spans(), build_reason()
api/ml_rewriter.py   # MT5-small seq2seq rewriter (ML fallback)
api/schemas.py       # RewriteRequest, RewriteResponse (Pydantic)
api/audit.py         # JSONL audit log
```

**Rewrite decision flow** (`api/service.py`):
1. `apply_rules_on_spans()` → produces edits
2. Semantic gate: if composite score < `JUAKAZI_SEMANTIC_THRESHOLD` (default 0.70) → revert (`source=preserved`)
3. Stage 2.5: if warn-only SW match → `disambiguate()` via Llama 3.1 8B → promote to replace or suppress
4. If no rules matched → ML rewriter fallback; same semantic gate applies

### Frontends

| Frontend | Path | Port | Purpose |
|----------|------|------|---------|
| Gradio demo | `gradio_app.py` | 7860 / HF Spaces | Public demo — model selector, detection, correction, version history |
| Next.js web app | `apps/web/` | 3001 local / 3000 Docker | Public demo, proxies `/api/*` to FastAPI |
| Streamlit review UI | `ui/` | 8501 | Internal annotation review |

The Gradio demo includes a **Model** dropdown with 4 options (Rules-based, sw-bias-classifier-v2, HF LLM, Ollama) each showing their own metrics. The **Model Versions** tab shows the full F1 progression with a trend chart.

### Shared core (`core/`)

```
core/context_checker.py        # ContextChecker, ContextCondition enum
core/rules_loader.py           # Lexicon CSV loading
core/semantic_preservation.py  # Composite score for rewrite quality
```

---

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
  results/
    model_registry.json  # Full version history with metrics for all releases
rules/                   # Lexicons (lexicon_{en,sw,fr,ki}_v3.csv)
scripts/                 # Data collection, annotation pipeline, training notebooks
  train_sw_bias_v2.ipynb # sw-bias-classifier-v2 training (Colab, T4)
ui/                      # Streamlit review UI
config.py                # Central config (versions, thresholds, dialects)
gradio_app.py            # HF Spaces entry point
run_evaluation.py        # Main eval runner
```

---

## Lexicons

| Language | File | Entries | Notes |
|----------|------|---------|-------|
| English  | `rules/lexicon_en_v3.csv` | 515 | Production, P=1.000 |
| Swahili  | `rules/lexicon_sw_v3.csv` | 187 | Proverbs, Sheng, bride-price, religious framing |
| French   | `rules/lexicon_fr_v3.csv` | 69  | Expanded Mar 2026, P=1.000 |
| Kikuyu   | `rules/lexicon_ki_v3.csv` | 1,209 | Early stage |

`avoid_when` must use pipe-separated `ContextCondition` enum values: `quote`, `historical`, `proper_noun`, `biographical`, `statistical`, `medical`, `counter_stereotype`, `legal`, `artistic`, `organization`. Never prose.

---

## ML Classifier

### sw-bias-classifier-v2 (current)

- **Base model**: `Davlan/afro-xlmr-base`
- **Training data**: `ground_truth_sw_v5.csv` — 64,723 Swahili rows
- **Train/val split**: 85/15 → train ~7,260 rows (with augmentation), val 1,211 rows
- **Augmentation**: synonym swaps for gender terms; bias class augmented to 3,000 rows; neutral sampled at 4:1 ratio
- **Training**: 10 epochs, batch=16, lr=2e-5, warmup=10%, weight_decay=0.01, 6 frozen encoder layers
- **Val results**: NEUTRAL P=0.98 R=0.97 F1=0.97 · BIAS P=0.94 R=0.96 F1=0.95 · **Overall F1=0.953**
- **HuggingFace**: `juakazike/sw-bias-classifier-v2`
- **Role**: Stage 3 ML fallback — fires only when rules find nothing; edits are `severity=ml_fallback`, `needs_review=True`

### sw-bias-classifier-v1 (previous)

- **Training data**: 51,419 rows (gt_sw_v4), 3 epochs, T4 x2
- **Val F1**: 0.854 (P=0.938, R=0.784)
- **HuggingFace**: `juakazike/sw-bias-classifier-v1`

### Testing the classifier on HF

```python
from transformers import pipeline

clf = pipeline("text-classification", model="juakazike/sw-bias-classifier-v2")
clf("Mwanamke ni nyumba.")          # → BIAS
clf("Mwanamke mhandisi alitengeneza daraja.")  # → NEUTRAL (counter-stereotype)
clf("Daktari wa kiume alipima mgonjwa.")       # → borderline
```

Or use the Inference widget on the HF model page directly.

---

## Ground Truth

| Language | File | Rows | Notes |
|----------|------|------|-------|
| Swahili  | `eval/ground_truth_sw_v5.csv` | 64,723 | ann_sw_v3 AI pass + human batch_024 + 170 FN corrections |
| English  | `eval/ground_truth_en_v5.csv` | 66 | |
| French   | `eval/ground_truth_fr_v5.csv` | 50 | |
| Kikuyu   | `eval/ground_truth_ki_v8.csv` | 11,848 | |

SW dataset composition: 15.63% counter-stereotype, 5.01% implicit/proverb, region_dialect tagged (tanzania=33,411 · kenya=18,008).

---

## Version History

Full history in `eval/results/model_registry.json`. Key milestones:

| Tag | SW F1 | Notes |
|-----|-------|-------|
| v0.1-baseline | 0.681 | EN+SW only, small ground truth |
| v0.5-sw-groundtruth-v3 | 0.708 | ann_sw_v3 pass, 64,723 rows |
| v0.7-fr-bronze | 0.773 | FR Bronze, SW proverbs/Sheng added |
| v0.8-gt-corrections | **0.816** | 170 FN corrections, LLM Stage 2.5 |
| sw-classifier-v1 | 0.854 | ML on 51K rows |
| sw-classifier-v2 | **0.953** | ML on 64K rows · TARGET MET |

---

## Requirements

Core evaluation and detection run with no extra dependencies:

```bash
python3 run_evaluation.py
python3 demo_live.py
python3 tests/test_system.py
```

Optional dependencies:

```bash
pip install -e ".[api]"   # FastAPI + pandas
pip install -e ".[ui]"    # Streamlit
pip install -e ".[ml]"    # Transformers, PyTorch, scikit-learn
pip install -e ".[dev]"   # pytest, black, ruff, mypy
```

---

## Hard Rules

1. `python3 tests/test_system.py` must stay 5/5 before any merge.
2. Run `python3 run_evaluation.py` before and after any lexicon or detector change.
3. `severity=replace` rules require Precision ≥ 1.000 for EN/FR. SW is 0.735 (documented exception).
4. `avoid_when` must use pipe-separated `ContextCondition` enum values — never prose.
5. Work in branches; squash-merge to main. Never commit directly to main.
6. Never push unless explicitly asked.

---

## Sprint Status (Mar 2026)

- **Sprint 0–1**: ✅ merged to main
- **Sprint 2**: 🔴 IN PROGRESS — blocked on 2nd annotator recruitment (Cohen's Kappa required for AIBRIDGE Bronze)
- **Sprint 3–4**: 🟡 not started (Sprint 4 web app can run in parallel with Sprint 3)

**AIBRIDGE Bronze blockers:**
- F1 ≥ 0.75: EN (0.885) ✅ · SW (0.816) ✅ · FR (0.793) ✅ · KI (0.368) ❌
- Cohen's Kappa ≥ 0.70: unmeasured — requires 2nd Swahili native-speaker annotator (recruit via Masakhane Slack)

---

## Documentation

- [Model Card](docs/eval/model_card.md)
- [Dataset Card](docs/eval/dataset_datasheet.md)
- [Evaluation Protocol](docs/eval/eval_protocol.md)
- [AIBRIDGE F1 Note](docs/SWAHILI_F1_NOTE.md)

---

## License

Open source. See project license for details.
