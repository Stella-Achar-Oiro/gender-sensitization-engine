# AI BRIDGE — Model Card (Detection & Correction Layers)

| Field | Value |
|---|---|
| **Model Name / Version** | JuaKazi Gender Sensitization Engine v3.3 (May 2026) |
| **Layer** | Detection + Correction |
| **Team / Project** | JuaKazi / AI BRIDGE — Engine 2 |
| **Languages** | English (en), Swahili (sw), French (fr), Gikuyu (ki), Hausa (ha), Zulu (zu) |
| **Architecture** | Rules engine (primary) + AfroXLM-R fine-tuned ML fallback (Swahili only, Stage 2) |
| **Linked Datasets** | ground_truth_sw_v5.csv, ground_truth_en_v5.csv, ground_truth_fr_v5.csv, ground_truth_ki_v8.csv, ground_truth_ha_v1.csv, ground_truth_zu_v1.csv |
| **Date** | 2026-05-01 |
| **Reviewer** | Rebecca Ryakitimbo (AI BRIDGE) |

---

## Detection Layer Metrics

| Metric | Definition | Baseline | Current | Δ | Notes |
|---|---|---|---|---|---|
| Precision | Proportion of flagged instances that are truly biased | SW:0.958 \| EN/FR/KI: first eval | EN:1.000 \| SW:0.822 \| FR:1.000 \| KI:0.967 \| HA:1.000 \| ZU:1.000 | SW:−0.136 (honest GT expansion) \| HA/ZU: new | SW precision drop intentional — Watoto wa Kike (~320 FPs) are ambiguous advocacy vs prescriptive phrases. HA/ZU: precision-first lexicons, zero FPs. |
| Recall | Proportion of biased instances correctly identified | Not available (first systematic eval) | EN:1.000 \| SW:0.881 \| FR:0.941 \| KI:0.510 \| HA:0.022 \| ZU:0.577 | SW:+0.224 \| FR:+0.201 \| KI:+0.254 \| HA/ZU: new | KI Recall=0.510 — FNs driven by religious text. HA Recall=0.022 — lexicon covers surface-form terms only; implicit/contextual bias requires ML (planned). ZU Recall=0.577 — morphological suffix rules; compound constructions not yet covered. |
| F1 Score | Harmonic mean of Precision and Recall | SW:0.771 \| EN/FR/KI: first eval | EN:1.000 \| SW:0.851 \| FR:0.970 \| KI:0.667 \| HA:0.043 \| ZU:0.732 | SW:+0.080 \| FR:+0.148 \| KI:+0.266 \| HA/ZU: new | HA F1=0.043 expected at initial lexicon stage — recall improvement is the critical next step. |
| Bias Type Coverage | Bias categories covered by lexicon | Not available | SW: occupation F1=0.936, stereotype F1=0.858, pronoun_assumption F1=0.000 (GT gap). HA: occupation/role covered; leadership/religion/daily_life not yet. ZU: gender suffix patterns covered; compound constructions not yet. | — | SW pronoun_assumption=0.000 is a GT collection gap, not a missing category. |
| Annotation Agreement (HVI) | Inter-annotator agreement (Cohen's κ ≥ 0.61) | Single annotator (SW) | SW: κ=0.8537 (Almost Perfect — above AIBRIDGE Bronze ≥0.61). HA: StudyLabs annotation team (IAA not separately computed). ZU: derived from correction pairs. | κ computed Apr 2026 on 500-row overlap (ann_sw_kappa_v2) | EN/FR/KI/HA/ZU IAA not computed. SW HVI CLOSED. |

---

## Correction Layer Metrics

| Metric | Definition | Baseline | Current | Δ | Notes |
|---|---|---|---|---|---|
| Correction Quality Score | Rubric-based average per corrected sentence | 2.3 | EN:0.939 \| SW:0.823 \| FR:0.788 \| KI:0.529 \| HA:N/A \| ZU:N/A | — | KI score (0.529) below production threshold — morphological complexity. HA/ZU correction quality not yet formally evaluated. |
| Meaning Preservation | Semantic similarity post-correction (threshold ≥0.70) | 0.86 | EN:0.722 \| SW:0.967 \| FR:0.767 \| KI:0.881 \| HA/ZU: threshold enforced | — | All languages: semantic check rejects rewrites scoring below 0.70. HA/ZU systematic score not yet computed on held-out set. |
| Bias Removal Accuracy | % of flagged biases successfully resolved | 78% | EN:100% (27/27) \| SW:83% (857/1,033) \| FR:78.3% (18/23) \| KI:100% (296/296) \| HA: precision-first (low volume) \| ZU: suffix removal applied | — | SW: 379 over-corrections are the known Watoto wa Kike / mtoto wa kike FP cluster. Human review recommended before bulk use. |
| Human Validation Index (HVI) | Annotator validation of corrections | 0.79 | SW: κ=0.8537 — HVI CLOSED. Human correction-review cycle (≥200 validated corrections in Streamlit UI) still pending for full FI. | — | κ HVI requirement closed. Review cycle is the remaining open item. |
| Fairness Index (FI) | Composite fairness score | 70 | FI=70. HVI (κ) CLOSED. DP/EO/EOdds computed for EN/SW/FR/KI. HA/ZU DP/EO pending. MBE=0.825 (below 0.85 — KI gap). | — | FI will increase after: human review cycle (≥200 corrections), HA/ZU DP/EO computation, KI recall improvement. |

---

## Bias Severity Reduction (Before vs After Correction)

| Bias Type | Severity Before | Severity After | Δ Improvement | Verified |
|---|---|---|---|---|
| Role-based (SW/EN/FR/KI) | 3 | 1 | 2 | ✅ |
| Proverbial (SW) | 3 | 1 | 2 | ✅ |
| Morphological (EN/ZU) | 2 | 1 | 1 | ✅ |
| Adjectival (EN/FR) | 2 | 1 | 1 | ✅ |
| Contextual / Cultural (SW) | 3 | 2 | 1 | ✅ |
| Occupational (HA) | 2 | 1 | 1 | ✅ (warn-severity; surface-form terms only) |
| Gender suffix (ZU) | 2 | 1 | 1 | ✅ (morphological suffix removal) |

---

## Governance & Documentation Checklist

| Item | Status | Notes |
|---|---|---|
| Dataset Cards linked | ✅ | SW=67,290, EN=66, FR=165, KI=11,622, HA=10,054, ZU=2,000 |
| Bias audit logs updated | ✅ | JSONL audit log appended after each correction request via api/audit.py |
| Ethics verification complete | ⏳ | κ=0.8537 (SW HVI closed). FI=70. DP/EO/EOdds computed for EN/SW/FR/KI. HA/ZU DP/EO pending. WEFE/WEAT: not yet measured (no East African gendered word lists). TGBI: not yet measured (no SW/KI TGBI translation). Human correction-review cycle pending. |
| Reviewer cross-validation | ✅ | ann_sw_kappa_v2: 500-row overlap, κ=0.8537. HA: StudyLabs annotation team. |
| Machine-readable governance | ✅ | technical-documentation.yaml at repository root (SBD-T Layer 1) |

---

## Computed Fairness Index: 70

Closed: κ=0.8537, counter-stereotype 15.63%, implicit bias 5.01%, DP/EO/EOdds computed for EN/SW/FR/KI.  
Open: EN DP=0.593 (eval distribution issue, not model unfairness), MBE=0.825 (KI recall gap), HA/ZU DP/EO not yet computed, human correction-review cycle pending.

---

## Gender-Disaggregated Detection Metrics (May 2026)

| Language | Gender | Precision | Recall | F1 | Rows |
|---|---|---|---|---|---|
| Swahili | Female | 0.774 | 0.868 | 0.818 | 887 |
| Swahili | Male | 0.928 | 0.972 | 0.950 | 213 |
| Swahili | Neutral | 0.324 | 0.379 | 0.349 | 29 |
| Gikuyu | Female | 0.978 | 0.731 | 0.837 | 249 |
| Gikuyu | Male | 0.964 | 0.491 | 0.651 | 918 |
| Gikuyu | Neutral | 1.000 | 0.417 | 0.589 | 429 |
| Hausa | — | — | — | — | Not yet computed — target_gender breakdown audit pending |
| Zulu | — | — | — | — | Not yet computed — ZU GT is correction pairs, target_gender not annotated |

---

## Swahili Bias Category Breakdown (Rules Layer, May 2026)

| Category | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| occupation | 0.955 | 0.918 | 0.936 | 719 | 34 | 64 |
| stereotype | 1.000 | 0.751 | 0.858 | 25 | 0 | 83 |
| pronoun_assumption | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |

SW pronoun_assumption F1=0.000 — GT gap (all 57 SW pronoun_assumption rows are has_bias=False). EN and FR pronoun detection: F1=1.000. KI pronoun_assumption F1=0.491, pronoun_generic F1=0.613.

---

## Hausa Notes (May 2026 — initial coverage)

- Lexicon: 36 rules, precision-first design (P=1.000)
- Ground truth: 10,054 rows (1,012 bias, 9,042 neutral) — sourced from StudyLabs (annotator_id=studylabs-v1)
- Dominant bias categories: leadership (male-default), religion_culture, daily_life — these require implicit/contextual understanding that word-level rules cannot catch
- Recall improvement path: ML classifier fine-tuned on 10K HA GT (data available, training queued post-submission)
- StudyLabs detection F1=0.814 on HA — combined pipeline recall currently ~0.018 (HA correction is the bottleneck)

## Zulu Notes (May 2026 — initial coverage)

- Lexicon: 53 rules targeting gender morphological suffixes (wesifazane, owesifazane, kwezifazane, wesilisa)
- Context gating: `zu_neutral_profession` condition suppresses rules in celebratory/counter-stereotype contexts — achieves P=1.000
- Ground truth: 2,000 rows (1,978 bias) — derived from zulu_retraining correction pairs
- Recall improvement path: compound construction patterns, idiomatic expressions, native ZU speaker lexicon review

---

**Signed**: David Nene  
**Role**: Technical Lead, JuaKazi  
**Date**: 2026-05-01  
**Programme**: AI BRIDGE — Engine 2
