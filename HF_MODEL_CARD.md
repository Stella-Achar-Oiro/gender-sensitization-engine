---
language:
  - sw
  - en
  - fr
  - ki
license: apache-2.0
tags:
  - gender-bias
  - bias-detection
  - text-classification
  - multilingual
  - african-languages
  - swahili
  - kikuyu
  - french
  - east-africa
  - responsible-ai
datasets:
  - juakazike/gender-bias-multilingual
metrics:
  - f1
  - precision
  - recall
base_model:
  - microsoft/mdeberta-v3-base      # SW / EN / FR model
  - Davlan/afro-xlmr-large          # KI model
pipeline_tag: text-classification
---

# JuaKazi Multilingual Gender Bias Classifier — v1

## Model Overview

This release contains **two complementary models** for multilingual gender bias detection and correction, targeting East African language contexts:

| Model | Languages | Base | HF Hub |
|-------|-----------|------|--------|
| `multilingual-bias-classifier-v1` | Swahili · English · French | `microsoft/mdeberta-v3-base` | `juakazike/multilingual-bias-classifier-v1` |
| `ki-bias-classifier-v1` | Kikuyu (Gĩkũyũ) | `Davlan/afro-xlmr-large` + DAPT | `juakazike/ki-bias-classifier-v1` |

Both models are **binary classifiers** (biased / not biased) and function as the **Stage 2 ML fallback** in the JuaKazi gender sensitization engine. Stage 1 (rules-based lexicon matching) handles explicit, high-precision cases. These models handle implicit, contextual, and coreference-type bias that rules cannot reach.

---

## Project Context

The JuaKazi Gender Sensitization Engine is an NLP system for detecting and correcting gender bias in East African language content. It is built for the **AIBRIDGE programme** (Africa Initiative for Responsible AI and Gender-Responsive Development), targeting:

- Media content moderation (Kenya, Tanzania, Uganda, Rwanda)
- Governance and parliamentary transcript review
- Health and agriculture extension communication
- Education material screening

### Why these languages?

**Swahili (sw)** is the primary language of public media across East Africa (53M+ speakers in Kenya and Tanzania). Swahili has grammatical noun classes (ngeli) that interact with gender-marking in complex ways — existing multilingual bias models trained only on European languages miss these patterns.

**Kikuyu (ki)** is the largest Bantu language in Kenya (~8M speakers) and is heavily used in local governance and agricultural extension. It has received almost no NLP research attention.

**English (en) / French (fr)** are co-official languages used in formal media, government, and education across the region.

---

## Training Data

### SW — Swahili (67,290 rows)

The Swahili ground truth is the core dataset, built over 5 annotation sprints:

| Batch | Source | Rows | Annotators | Notes |
|-------|--------|------|------------|-------|
| `ann_sw_v2` | KBC, NTV, Citizen TV (radio transcripts) | 1,040 | AO-001 | Media news, 2022–2023 |
| `ann_sw_v3` | BBC Swahili, VOA Swahili, Deutsche Welle | 13,045 | AO-001, QA review | Includes counter-stereotypes |
| `ann_sw_auto_v1` | AfriSenti Twitter corpus | 50,275 | Auto + AO-001 QA | Social media; bias rate 0.8% |
| `ann_sw_kappa_v2` | CiviVox corpus (health, governance, agriculture, education) | 2,479 | Auto + manual QA | Non-media domains; κ=0.8537 |

**Inter-annotator agreement (IAA):** Cohen's Kappa κ = **0.8537** ("Almost Perfect" per Landis & Koch scale) computed on a 500-row overlap batch between annotator AO-001 and independent second-pass review. Above AIBRIDGE Bronze threshold (κ ≥ 0.61).

**Class distribution:** 1,151 biased (1.7%) / 65,844 not-biased. The 1.7% rate reflects genuine corpus bias prevalence — it is not an artifact. Main false positive sources: `Watoto wa Kike` (182 FPs) and `mtoto wa kike` (138 FPs) — genuinely ambiguous phrases retained with documented precision trade-off.

**Bias categories in training data:**

| Category | Count | % of biased |
|----------|-------|-------------|
| stereotype | 623 | 54% |
| occupational_bias | 198 | 17% |
| role_assignment | 156 | 14% |
| appearance_bias | 87 | 8% |
| personality_trait | 53 | 5% |
| social_norm | 34 | 3% |

### EN — English (2,828 rows — ML training; 66 rows — held-out eval)

The English **training** set combines three well-established coreference-bias benchmarks. These were selected because they contain **real sentences** (not synthetically generated) with documented human annotations:

| Source | Rows | Bias type | Annotation rule |
|--------|------|-----------|-----------------|
| WinoBias (Zhao et al., 2018) | 1,584 | Occupational pronoun coreference | Source label (`bias_label == 'stereotype'`) |
| WinoGender (Rudinger et al., 2018) | 720 | Occupation + pronoun + BLS gender map | Male-dominated occupation + male pronoun = biased |
| CrowS-Pairs (Nangia et al., 2020) | 524 | Gender role statements | Pattern rules for explicit gender role language |

**WinoGender annotation detail:** Uses US Bureau of Labor Statistics (BLS) majority-gender occupation data. If an occupation is ≥60% male-dominated and the pronoun is male (or ≥60% female-dominated and pronoun is female), the sentence is labeled biased (reinforcing occupational gender stereotype). Gender-neutral pronouns ("they/their") are always labeled neutral.

The English **held-out eval set** (66 rows, rules-based evaluation only) remains entirely separate — no overlap with training data was verified before training.

### FR — French (165 rows)

| Source | Rows | Notes |
|--------|------|-------|
| Original annotation | 50 | Collected 2024, Quebec + African French |
| Wikipedia FR (Feb 2025) | 115 | Gender-role articles, occupation descriptions |

French eval F1 improved from 0.793 to 0.822 (+3.7pp) after adding 115 Wikipedia rows. The Wikipedia rows target the recall gap on occupational bias in formal written French.

### KI — Kikuyu (11,622 rows)

| Source | Rows | Notes |
|--------|------|-------|
| `auto_waxal` | 2,011 | WaXal corpus (Wolof/cross-lingual transfer, validated) |
| `auto_flores` | 2,006 | FLORES+ Kikuyu subset |
| `ann_002` | 1,723 | Human annotator |
| Other batches | 5,882 | Mixed sources |

**KI challenge:** 79% of biased KI rows are **implicit bias** — the same terms appear in both biased and not-biased contexts depending on discourse. Rules-based F1 on KI is 0.401 (Recall 0.256) because lexicon matching fails on implicit patterns. The KI ML model targets this gap directly.

---

## Model Architecture

### SW/EN/FR: `multilingual-bias-classifier-v1`

- **Base:** `microsoft/mdeberta-v3-base` (125M params, 100 languages)
- **Task head:** 2-class classification (neutral / biased)
- **Why mDeBERTa?** DeBERTa's disentangled attention mechanism separates position and content representations, improving performance on nuanced classification tasks. 2025 benchmarks on African language text classification show mDeBERTa-v3-base achieving 0.803 macro-F1 vs AfroXLMR-large at 0.532.
- **Training:** Joint training on all three languages. Cross-lingual transfer helps low-resource French (only 165 rows) benefit from SW and EN signal.
- **Class imbalance:** `BCEWithLogitsLoss(pos_weight=X)` where X = min(n_neutral/n_biased, 10). The hard cap of 10× prevents the recall-only optimisation that caused v2's 33% precision problem (pos_weight ~58× in v2).
- **Layer freezing:** Bottom 4 transformer layers frozen during fine-tuning to preserve multilingual representations and reduce VRAM usage on T4 GPU.
- **Decision threshold:** Per-language optimal thresholds (stored in `juakazi_metadata.json`). Default 0.5 if not specified.

### KI: `ki-bias-classifier-v1`

- **Base:** `Davlan/afro-xlmr-large` (560M params, 17 African languages incl. Gikuyu)
- **DAPT (optional):** Domain-Adaptive Pre-Training on raw Gikuyu Wikipedia + Bible text (MLM, 15% mask rate, 2 epochs). DAPT adapts internal representations to Gikuyu domain vocabulary before fine-tuning. Expected improvement: +5–30% F1 based on AfroXLMR-Social paper results.
- **Task head:** 2-class classification
- **Class imbalance:** `pos_weight = min(n_neutral/n_biased, 8)` — gentler cap for KI (11.3% bias rate vs SW 1.7%)
- **Optimisation target:** `metric_for_best_model = f1_bias` (BIAS class F1, not macro) — prioritises improving low recall

---

## Performance

### Rules-based layer (Layer 1 — not these models)

The rules-based lexicon system is the **primary** detection layer. These models are the **fallback** that only runs when rules find nothing.

| Language | F1 | Precision | Recall | Eval samples |
|----------|----|-----------|--------|--------------|
| Swahili | 0.851 | 0.822 | 0.881 | 67,290 |
| English | 1.000 | 1.000 | 1.000 | 66 |
| French | 0.970 | 1.000 | 0.941 | 165 |
| Kikuyu | 0.667 | 0.967 | 0.510 | 11,622 |

### ML models (Layer 2 — these models)

Metrics are reported after training. See `juakazi_metadata.json` in each model repository for exact per-run numbers.

**Targets for v1:**

| Language | F1 target | Precision target | Recall target |
|----------|-----------|-----------------|---------------|
| SW (ML fallback) | ≥ 0.70 macro | ≥ 0.60 | ≥ 0.85 |
| EN (ML fallback) | ≥ 0.70 macro | ≥ 0.75 | ≥ 0.70 |
| FR (ML fallback) | ≥ 0.70 macro | ≥ 0.75 | ≥ 0.70 |
| KI (ML primary) | ≥ 0.55 macro | ≥ 0.60 | ≥ 0.55 |

### Gender-disaggregated metrics (AIBRIDGE requirement)

| Group | Recall (rules layer, SW) | Notes |
|-------|--------------------------|-------|
| Female-targeted bias | 0.884 | 8.7pp gap vs male |
| Male-targeted bias | 0.975 | — |
| Appearance bias | 0.219 | Lowest category |
| Personality trait | 0.190 | Second lowest |

The ML model is trained to close the female recall gap and improve appearance/personality categories. Post-training disaggregated metrics are tracked in evaluation runs.

---

## Training Details

### Hyperparameters — SW/EN/FR model

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `base_model` | `microsoft/mdeberta-v3-base` | Best multilingual classification (2025 benchmarks) |
| `max_length` | 128 tokens | Covers 95th percentile of all languages |
| `batch_size` | 32 (train) / 64 (eval) | T4 16GB constraint |
| `gradient_accumulation_steps` | 2 | Effective batch = 64 |
| `epochs` | 4 | With early stopping via `load_best_model_at_end` |
| `learning_rate` | 2e-5 | Standard for DeBERTa fine-tuning |
| `lr_scheduler` | cosine decay | Outperforms linear on classification tasks |
| `warmup_ratio` | 0.06 | ~half an epoch warmup |
| `weight_decay` | 0.01 | AdamW regularisation |
| `pos_weight` | computed, capped at 10× | Prevents recall-only optimisation |
| `frozen_layers` | bottom 4 | Preserve multilingual representations |
| `SW neutral_ratio` | 30:1 | Prevents SW from drowning EN/FR signal |
| `seed` | 42 | Reproducibility |

### Hyperparameters — KI model

| Parameter | Value |
|-----------|-------|
| `base_model` | `Davlan/afro-xlmr-large` |
| `DAPT_epochs` | 2 (MLM on Gikuyu text) |
| `max_length` | 128 tokens |
| `batch_size` | 16 (train) / 32 (eval) |
| `gradient_accumulation_steps` | 4 (effective batch = 64) |
| `epochs` | 5 |
| `learning_rate` | 1e-5 (lower for larger model) |
| `lr_scheduler` | cosine decay |
| `pos_weight` | computed, capped at 8× |
| `best_model_metric` | `f1_bias` (BIAS F1, not macro) |

---

## Intended Use

### Primary uses

- Detecting gender bias in Swahili, English, French, and Kikuyu text
- Content moderation for East African media and government communication
- Research on gender bias in low-resource African language NLP
- Integration as Stage 2 fallback in the JuaKazi gender sensitization engine

### How it fits in the JuaKazi pipeline

```
Input text
    │
    ▼
[Layer 1: Rules-based lexicon matching]
    │  match found?
    ├─ YES → apply correction (high precision)
    │
    └─ NO → [Layer 2: ML fallback — these models]
                │
                ▼
            Probability ≥ threshold?
                │
                ├─ YES → flag for human review (severity=warn)
                └─ NO  → pass (no bias detected)
```

The ML layer **never applies automatic corrections** — it only flags for review (`severity=warn`, `needs_review=True`). This preserves precision and keeps humans in the loop.

### Out-of-scope uses

- Languages not in the training distribution (other African languages, European languages beyond EN/FR)
- Detecting hate speech, toxicity, or racial bias (different task — use a general toxicity classifier)
- Replacing human review in high-stakes decisions (journalism moderation, legal documents)
- Real-time high-throughput production at scale without a T4 GPU or equivalent

---

## Bias and Limitations

### Known precision trade-offs

**Swahili:** Precision 0.748 (below the 1.000 of English). The two main false positive drivers are:

- `Watoto wa Kike` ("Girl children / female children") — 182 FPs. This phrase is factual in health/education contexts but stereotyping in some media contexts. Accepted as an inherent ambiguity.
- `mtoto wa kike` ("female child") — 138 FPs. Same issue.

These are documented, not hidden. They are the honest cost of broad recall (0.917) in Swahili.

### Kikuyu recall limitation

Kikuyu rules-based recall is 0.256 (F1 0.401). Root cause: 79% of biased KI rows are implicit bias where the same phrases appear in both biased and not-biased contexts. The ML model targets this directly but may not fully close the gap in v1.

### Language variety coverage

All training data was collected in East African contexts:
- Swahili: Kenya/Tanzania (Standard Swahili; some Kenyan urban variations)
- Kikuyu: Central Kenya
- French: Written formal French (some Quebec data in early batches)
- English: East African English + global coreference benchmarks (WinoBias, WinoGender)

Performance may degrade on West African French, South African English, or Coastal Swahili dialects.

### Binary gender framework

The current model uses binary gender labeling (male/female). It does not capture:
- Non-binary or gender-nonconforming bias
- Intersectional bias (gender × ethnicity, gender × class)
- Disability-related gender bias

This reflects current annotation capacity, not an ideological position. Future versions will expand the framework.

### Model confidence vs. ground truth

The ML model is a fallback for cases where rules find nothing. This means it operates on the **hard cases** — texts that are ambiguous enough that no rule matched. Users should treat ML-flagged items as "possible bias — human review required," not as ground truth.

---

## Ethical Considerations

### Annotation transparency

- **SW Cohen's Kappa:** κ = 0.8537 (computed on 500-row overlap, full methodology in `data/annotation_export/batch_for_annotator_B_kappa_overlap_ANNOTATED_v2.csv`)
- **EN ML training data:** Automatically annotated using documented rules (BLS occupation map for WinoGender, source labels for WinoBias, pattern rules for CrowS-Pairs). Not human-annotated.
- **SW CiviVox batch (2,479 rows):** Auto-annotated using detector + manual QA. 29 biased rows confirmed (26 by detector, 3 by manual review). Bias rate 1.2%, consistent with corpus expectations.

### What we disclose that we don't know

- French recall is limited by small training set (165 rows). Cross-lingual transfer from SW/EN helps but does not substitute for more FR data.
- KI model performance is projected based on val set results. Production performance on unseen KI text is uncertain.
- Gender-disaggregated metrics for FR and KI are not yet computed (limited biased-row counts per subgroup).

### Feedback

This model is under active development. To report errors, false positives, or missed cases in any language, open an issue at [github.com/juakazike/gender-sensitization-engine](https://github.com/juakazike/gender-sensitization-engine).

---

## Citation

If you use this model or dataset in research, please cite:

```bibtex
@software{juakazi_bias_engine_2026,
  title  = {JuaKazi Gender Sensitization Engine},
  author = {{JuaKazi Team}},
  year   = {2026},
  url    = {https://huggingface.co/juakazike},
  note   = {Multilingual gender bias detection for East African languages.
            Supported by AIBRIDGE programme.}
}
```

---

## Model Card Authors

JuaKazi Team — April 2026

---

## Changelog

| Version | Date | Key changes |
|---------|------|-------------|
| v1 | Apr 2026 | First public release. mDeBERTa-v3-base for SW/EN/FR. AfroXLMR-large+DAPT for KI. Real training data only (WinoBias, WinoGender, CrowS-Pairs, Wikipedia FR). |
| (v2 — internal) | Mar 2026 | SW-only AfroXLMR-base model. BIAS precision 0.330. pos_weight ~58× caused recall-only optimisation. Deprecated. |
| (v3 — SW only) | Mar 2026 | SW AfroXLMR-base, pos_weight capped at 10. F1 improved. Not released publicly — superseded by v1 multilingual model. |
