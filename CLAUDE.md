# JuaKazi — Claude Instructions

## The Goal
Production pipeline that detects AND corrects gender bias in 6 languages
(SW, HA, ZU, KI, EN, FR) using open-source African NLP models from HuggingFace.
Gates Foundation demo requires all 6 languages working end-to-end.

## ALWAYS follow PLAN.md
The full rebuild plan lives in PLAN.md. Read it before starting any task.
Every change must advance a phase in PLAN.md. No work outside the plan.

---

## Hard Rules — Never Break These

1. **Tests first.** No model wires into the pipeline without a passing acceptance test in
   `tests/test_detection_contract.py` or `tests/test_correction_contract.py`.

2. **No LLMs in the pipeline.** Detection and correction use open-source HuggingFace models
   only. No Claude, GPT, or any API-based LLM in the detection/correction flow.
   Claude (me) is for engineering work only — not for inference.

3. **SW must never regress.** Run `python3 run_evaluation.py --lang sw` before AND after
   every pipeline change. SW F1 must stay ≥ 0.85. If it drops → revert immediately.

4. **One phase at a time.** Do not start Phase N+1 until Phase N acceptance gate passes.
   Acceptance gate = pytest test passing + metrics logged to `eval/metrics.json`.

5. **Ground truth is read-only.** Never overwrite a ground truth CSV.
   Create a new version file (e.g., `ground_truth_zu_v2.csv`) instead.

6. **Train on clean data only.** For correction models: only `qa_status=approved` or
   `qa_status=gold` or `qa_status=passed` rows go into training.
   Exception: `zulu_retraining` file and KI GT (already validated).

7. **No new files unless strictly required.** Edit existing files.

8. **Never push to remote** unless explicitly asked.

9. **Always work in branches.** Never commit directly to main.

10. **Every training run updates `eval/metrics.json`.** No exceptions.

---

## Pipeline Architecture (what we are building)

```
Stage 1: ML Detector   → juakazike/{lang}-bias-classifier-v1
                          afro-xlmr-base (HA/ZU/SW/EN/FR)
                          afro-xlmr-large-76L (KI only)

Stage 2: Lexicon Rules → rules/lexicon_{lang}_v3.csv
                          fast word-level substitution, zero FP

Stage 3: ML Corrector  → juakazike/{lang}-bias-corrector-v1
                          castorini/afriteva_v2_base (HA/ZU/SW)
                          google/mt5-small (KI)
```

Detection and correction are separate models. Never conflate them.

---

## Training Data Sources (per language)

### Hausa (HA)
- `v4_revised_hausa_bias_ds.csv` — 17,401 rows (neutral+stereotype+derogation+counter) ← PRIMARY
- `study-labs-non-synthetics-qa-approved-sentences-2026-04-27T09-23-46-234Z.csv` — 10,178 rows
- `eval/ground_truth_ha_v1.csv` — 10,054 rows
- `twitter-hausa-bias-2026-04-29T17-14-06-511Z_classified.csv` — 1,608 rows (social media)
- Correction pairs: `juakazi_ha_correction_pairs_v1.csv` (1,918 rows — approved only)

### Zulu (ZU)
- `IsiZulu_Ithute_Dataset_Final.csv` — 9,570 rows (stereotype+derogation, all passed) ← PRIMARY
- `eval/ground_truth_zu_v1.csv` — 2,000 rows (biased only)
- `data/neutral_zu_generated_v1.csv` — generated neutral sentences (see Phase 0.5)
- Correction pairs: `zulu_retraining - zulu_retraining.csv.csv` (2,000 pairs, ready)
- Correction pairs: `juakazi_zu_correction_pairs_v1.csv` (1,142 pairs — approved only)

### Swahili (SW)
- `eval/ground_truth_sw_v5.csv` — 67,290 rows ← PRIMARY (do not modify)
- `Umunthu Data - Swahili Annotated (3).csv` — 10,741 rows (supplement)
- `sheng_gender_tweets_clean.csv` — 46 rows (Sheng lexicon only, not training)

### Kikuyu (KI)
- `eval/ground_truth_ki_v8.csv` — 11,622 rows (all have expected_correction) ← PRIMARY

### French (FR)
- `French Annotated - final (1).csv` — 10,996 rows (10,648 gold) ← PRIMARY
- `eval/ground_truth_fr_v5.csv` — 165 rows (supplement)

### English (EN)
- `eval/ground_truth_en_v5.csv` — 66 rows (low priority)

---

## Acceptance Thresholds

| Language | F1 | Recall | Precision |
|----------|----|--------|-----------|
| HA | ≥ 0.70 | ≥ 0.75 | ≥ 0.60 |
| ZU | ≥ 0.68 | ≥ 0.65 | ≥ 0.60 |
| KI | ≥ 0.70 | ≥ 0.65 | ≥ 0.65 |
| SW | ≥ 0.85 | ≥ 0.85 | ≥ 0.80 |
| FR | ≥ 0.75 | ≥ 0.70 | ≥ 0.75 |

---

## Current Metrics (as of 2026-05-28)

| Lang | F1 | Recall | Status |
|------|----|--------|--------|
| SW | 0.851 | 0.881 | ✅ production |
| EN | 1.000 | 1.000 | ⚠️ GT too small |
| FR | 0.970 | 0.941 | ⚠️ GT too small — now fixable with 10K rows |
| HA | 0.043 | 0.022 | ❌ needs classifier |
| ZU | 0.732 | 0.577 | ❌ needs classifier + neutral data |
| KI | 0.667 | 0.510 | ❌ wrong base model |

---

## Key File Locations

- Detection engine: `eval/bias_detector.py`
- ML classifier: `eval/ml_classifier.py`
- ML corrector: `eval/mt5_corrector.py`
- Lexicons: `rules/lexicon_{en,sw,fr,ki,ha,zu}_v*.csv`
- Ground truth: `eval/ground_truth_{lang}_v*.csv`
- API routing: `api/main.py`
- API service: `api/service.py` (stages 1→2→3)
- API rules: `api/rules_engine.py`
- Config: `config.py`
- Tests: `tests/`
- Training notebooks: `train_{lang}_bias_v1.ipynb`
- Metrics: `eval/metrics.json`
- This plan: `PLAN.md`
