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

Detects and rewrites gender-biased language in **Swahili, English, French, Gikuyu, Hausa, and Zulu**. Supports single-sentence and batch API input.

## Current metrics (May 2026)

| Language | F1 | Precision | Recall | Samples |
|---|---|---|---|---|
| English | 1.000 | 1.000 | 1.000 | 66 |
| Swahili | 0.851 | 0.822 | 0.881 | 67,290 |
| French | 0.970 | 1.000 | 0.941 | 165 |
| Gikuyu | 0.667 | 0.967 | 0.510 | 11,622 |
| Hausa | 0.043 | 1.000 | 0.022 | 10,054 |
| Zulu | 0.732 | 1.000 | 0.577 | 2,000 |

Hausa: precision-first initial lexicon (36 rules); recall requires ML classifier (planned). Zulu: morphological suffix rules with context gating for zero false positives.

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
- **Context gating**: 11 suppression conditions (biographical, quote, statistical, counter-stereotype, Zulu neutral profession, etc.)
- **Integration**: `caller` field allows upstream partners (StudyLabs/AIBRIDGE) to skip redundant re-detection

## Lexicons (May 2026)

| Language | File | Rules |
|---|---|---|
| English | rules/lexicon_en_v3.csv | 77 |
| Swahili | rules/lexicon_sw_v3.csv | 437 (incl. 69 Sheng/informal terms) |
| French | rules/lexicon_fr_v3.csv | 117 |
| Gikuyu | rules/lexicon_ki_v3.csv | 1,288 |
| Hausa | rules/lexicon_ha_v1.csv | 36 |
| Zulu | rules/lexicon_zu_v1.csv | 53 |

## API

```bash
POST /rewrite
{ "id": "1", "lang": "sw", "text": "Daktari wa kiume alifika" }
# Optional: "caller": "studylabs" skips Stage 0 re-detection
# Supported lang codes: en, sw, fr, ki, ha, zu
```

Returns: `{ original_text, rewrite, edits, confidence, source, reason, semantic_score }`

Batch endpoint: `POST /rewrite/batch` (up to 100 sentences)

## Dataset

| Language | Ground truth rows | Bias rows | Source |
|---|---|---|---|
| Swahili | 67,290 | ~1,600 | Helsinki Corpus, BBC SW, AfriSenti, MasakhaNER |
| Gikuyu | 11,622 | ~1,200 | Wikipedia KI, annotated |
| Hausa | 10,054 | 1,012 | StudyLabs dataset (annotator_id=studylabs-v1) |
| Zulu | 2,000 | 1,978 | zulu_retraining correction pairs |

Inter-annotator agreement (Cohen's κ): 0.8537 (Almost Perfect — AIBRIDGE Bronze threshold ≥ 0.61)

## Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000   # API
python3 demo_live.py                         # CLI demo
python3 run_evaluation.py                    # Run evaluation (all 6 languages)
```

## AI BRIDGE submission

Team: JuaKazi | Updated: May 2026 | Schema: AIBRIDGE v1 (24-column CSVW)