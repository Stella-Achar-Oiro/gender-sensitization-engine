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

## Current metrics (Mar 2026)

| Language | F1 | Precision | Recall | Samples |
|---|---|---|---|---|
| English | 0.885 | 1.000 | 0.794 | 66 |
| Swahili | 0.816 | 0.733 | 0.920 | 64,723 |
| French | 0.793 | 1.000 | 0.657 | 50 |
| Gikuyu | 0.352 | 0.926 | 0.217 | 11,848 |

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

- SW ground truth: 64,723 rows — Gold tier (sample count)
- KI ground truth: 11,848 rows — Bronze tier (sample count)
- All real text, no synthetic data. Sources: Helsinki Corpus, BBC Swahili, Wikipedia SW, AfriSenti, MasakhaNER
- Inter-annotator agreement (Cohen's κ): in progress

## Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000   # API
python3 demo_live.py                         # CLI demo
python3 -m eval.evaluator                    # Run evaluation
```

## AI BRIDGE submission

Team: JuaKazi | Submission: Mar 2026 | Schema: AIBRIDGE v1 (24-column CSVW)