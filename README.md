---
title: JuaKazi Gender Sensitization Engine
emoji: ⚖️
colorFrom: red
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# JuaKazi Gender Sensitization Engine

A multilingual gender bias detection and correction system for African language text, built for the AI BRIDGE programme.

## What it does

Detects and rewrites gender-biased language in **Swahili, English, French, and Gikuyu**. Supports single-sentence and batch API input.

## Current metrics (Apr 2026)

| Language | F1 | Precision | Recall | Samples |
|---|---|---|---|---|
| English | 1.000 | 1.000 | 1.000 | 66 |
| Swahili | 0.851 | 0.822 | 0.881 | 67,290 |
| French | 0.970 | 1.000 | 0.941 | 165 |
| Gikuyu | 0.667 | 0.967 | 0.510 | 11,622 |

## Live demo

[https://huggingface.co/spaces/juakazike/gender-sensitization-engine](https://huggingface.co/spaces/juakazike/gender-sensitization-engine)

## ML models

| Model | Base | Val F1 | Val Precision | Val Recall | Notes |
|---|---|---|---|---|---|
| [sw-bias-classifier-v1](https://huggingface.co/juakazike/sw-bias-classifier-v1) | afro-xlmr-base | 0.854 | 0.938 | 0.784 | Full fine-tune, 51K rows |
| [sw-bias-classifier-v2](https://huggingface.co/juakazike/sw-bias-classifier-v2) | afro-xlmr-base | 0.953 | 0.940 | 0.960 | Overfit on val — invalid |
| [sw-bias-classifier-v3](https://huggingface.co/juakazike/sw-bias-classifier-v3) | afro-xlmr-base | 0.871 | 0.810 | 0.942 | Current deployed model |

SW ML classifier is Stage 2 fallback only — runs when rules find nothing.

## Architecture

- **Detection**: Deterministic lexicon rules (primary) + AfroXLM-R fine-tuned ML fallback (Swahili only)
- **Correction**: Word-level substitution with semantic preservation check (threshold 0.70)
- **Languages**: Separate lexicons per language — no cross-lingual transfer
- **Context gating**: 10 suppression conditions (biographical, quote, statistical, counter-stereotype, etc.)

## API

```bash
POST /rewrite
{ "id": "1", "lang": "sw", "text": "Daktari wa kiume alifika" }
```

Returns: `{ original_text, rewrite, edits, confidence, source, reason }`

Batch endpoint: `POST /batch_rewrite` (up to 50 sentences)

## Dataset

- SW ground truth: 66,995 rows — Gold tier (sample count)
- KI ground truth: 11,622 rows — Bronze tier (sample count)
- All real text, no synthetic data. Sources: Helsinki Corpus, BBC Swahili, Wikipedia SW, AfriSenti, MasakhaNER
- Inter-annotator agreement (Cohen's κ): 0.8537 (Almost Perfect — AIBRIDGE Bronze threshold ≥ 0.61)

## Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000   # API
python3 demo_live.py                         # CLI demo
python3 -m eval.evaluator                    # Run evaluation
```

## AI BRIDGE submission

Team: JuaKazi | Updated: Apr 2026 | Schema: AIBRIDGE v1 (24-column CSVW)