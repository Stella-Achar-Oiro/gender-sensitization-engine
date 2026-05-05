# AI BRIDGE — Gender & Fairness Dataset Card

## Dataset Overview

| Field | Value |
|---|---|
| **Dataset Name** | JuaKazi Gender Bias Ground Truth v5 (May 2026) |
| **Team / Project** | JuaKazi / AI BRIDGE — Engine 2 |
| **Language(s)** | Swahili (sw), English (en), French (fr), Gikuyu (ki), Hausa (ha), Zulu (zu) |
| **Domain / Type** | Media and online (79%), governance/civic (8%), health (5%), agriculture (4%), education (4%) — non-media batch added Apr 2026 |
| **Intended Use** | Detection and correction of gender bias in African language text |
| **Collection Dates** | 2024-06 to 2026-04 |
| **Regional Diversity** | Tanzania 51.6% (34,594 rows), Kenya 48.4% (32,401 rows), Sheng: 49 rows (SW); Northern Nigeria (HA); South Africa (ZU); global (EN/FR) |
| **Sources** | Helsinki Corpus (Tanzanian SW), BBC Swahili / swahili_news (Kenyan SW), AfriSenti, MasakhaNER, Wikipedia SW, C4-SW; StudyLabs dataset (HA, annotator_id=studylabs-v1); zulu_retraining correction pairs (ZU) |
| **Annotators** | SW: 1 human (AO-001, native Swahili speaker, F, Kenya); auto-annotation (ann_sw_v2, ann_sw_v3); 2nd annotator (ann_sw_kappa_v2, 500-row overlap). κ=0.8537. HA: StudyLabs annotation team (studylabs-v1). ZU: derived from correction pairs. |
| **Ethics Reviewer** | Rebecca Ryakitimbo (AI BRIDGE, Feb 2026) |

---

## Dataset Size

| Language | Total rows | Bias rows | Neutral rows | GT file |
|---|---|---|---|---|
| Swahili | 67,290 | ~1,600 | ~65,690 | ground_truth_sw_v5.csv |
| Gikuyu | 11,622 | ~1,200 | ~10,422 | ground_truth_ki_v8.csv |
| English | 66 | ~30 | ~36 | ground_truth_en_v5.csv |
| French | 165 | ~30 | ~135 | ground_truth_fr_v5.csv |
| Hausa | 10,054 | 1,012 | 9,042 | ground_truth_ha_v1.csv |
| Zulu | 2,000 | 1,978 | 22 | ground_truth_zu_v1.csv |
| **Total** | **91,197** | | | |

Counter-stereotype rows: 15.63% (≥15% AIBRIDGE requirement — met).  
Implicit bias rows: 5.01% (≥5% AIBRIDGE requirement — met).  
PII scrubbed: 110 rows (emails/phone numbers replaced with [EMAIL]/[PHONE]).

---

## Representation & Gender Balance Metrics

| Metric | Target | Actual | Status |
|---|---|---|---|
| Gender representation ratio | 45–55% balanced | female=65.9% (887 bias rows), male=15.8% (213), mixed=12.1% (163), neutral=2.2% (29) | Not met — SW corpus skews toward female-targeted bias, reflecting source media. Gap documented; future collection should target male-targeted and neutral-gender examples. |
| Role-based bias count | ≤5% | 58.1% (783/1,347 bias rows have bias_category=occupation) | Not met — reflects online media corpus where occupational gender framing is prevalent. Not a data error; documented. |
| Pronoun consistency rate | ≥95% | EN: F1=1.000 ✅. FR: F1=1.000 ✅. KI: pronoun_assumption F1=0.491 / pronoun_generic F1=0.613 (partial). SW: F1=0.000 — ground truth gap: all 57 SW pronoun_assumption rows are has_bias=False, no positive SW pronoun bias examples collected. | EN/FR met. KI partial. SW is a GT collection gap — category is implemented, examples not yet in ground truth. |
| Cultural/proverbial bias incidence | ≤2 per 1,000 | 1.33 per 1,000 — met. (89 rows with stereotype_category in {family_role, daily_life} / 66,995 total × 1,000) | Met ✅ |
| Regional diversity | ≥3 regions | Tanzania 51.6% (34,594), Kenya 48.4% (32,401). Sheng: 49 rows — not a distinct tag. EN/FR: global. | Not met — 2 tagged SW regions. Ugandan/diaspora SW is a future collection target. |

---

## Bias Classification Summary

| Bias Type | Example | Language | Severity (1–3) | Corrected | Reviewer |
|---|---|---|---|---|---|
| Role-based | *Daktari wa kiume* → *Daktari* | SW | 3 | Y | AO-001 |
| Proverbial | *mwanamke ni shamba la baba* | SW | 3 | N (context gate) | AO-001 |
| Morphological | *waitress* → *server* | EN | 2 | Y | AO-001 |
| Morphological (suffix) | *owesifazane* → gender-neutral | ZU | 2 | Y | studylabs-v1 |
| Adjectival | gender-marked descriptors | EN/FR | 1 | Y | AO-001 |
| Occupational | *budurwa* (young woman framed as role) | HA | 2 | Y (warn) | studylabs-v1 |
| Contextual / Derogatory | *malaya wewe* (derogation) | SW | 3 | N (context gate) | AO-001 |
| Leadership/Religion | implicit male-default leadership framing | HA | 3 | N (recall gap) | studylabs-v1 |

---

## Fairness & Evaluation Metrics

| Metric | Baseline | Current | Comment |
|---|---|---|---|
| WEFE / WEAT | — | Not yet measured | Requires word embeddings from afro-xlmr-base + East African gendered word lists. No standard word lists exist for SW/KI. Legitimate future work. |
| TGBI | — | Not yet measured | Requires a Gender Bias Inventory translated for Swahili/Gikuyu. No such translation exists for East African languages. Legitimate future work. |
| F1 per subgroup | — | SW: occupation F1=0.936, stereotype F1=0.858, pronoun_assumption F1=0.000. SW female F1=0.818, male F1=0.950. KI female F1=0.837, male F1=0.651. | Full per-subgroup breakdown in model card §4.2–4.4. |
| Fairness Index (FI) | — | FI=70 | Closed: κ=0.8537, counter-stereotype 15.63%, implicit 5.01%, DP/EO/EOdds computed. Open: EN DP=0.593 (eval set distribution, not model unfairness), MBE=0.825 (KI recall gap), human correction-review cycle pending. |
| Mean Bias Error (MBE) | — | 0.825 | Below 0.85 target — driven by KI F1=0.667. Will improve as KI recall increases. |

### Gender-Disaggregated F1 (May 2026)

| Language | Gender | Precision | Recall | F1 | Rows |
|---|---|---|---|---|---|
| Swahili | Female | 0.774 | 0.868 | 0.818 | 887 |
| Swahili | Male | 0.928 | 0.972 | 0.950 | 213 |
| Swahili | Neutral | 0.324 | 0.379 | 0.349 | 29 |
| Gikuyu | Female | 0.978 | 0.731 | 0.837 | 249 |
| Gikuyu | Male | 0.964 | 0.491 | 0.651 | 918 |
| Gikuyu | Neutral | 1.000 | 0.417 | 0.589 | 429 |

### Swahili Bias Category Breakdown (Rules, May 2026)

| Category | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| occupation | 0.955 | 0.918 | 0.936 | 719 | 34 | 64 |
| stereotype | 1.000 | 0.751 | 0.858 | 25 | 0 | 83 |
| pronoun_assumption | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |

pronoun_assumption F1=0.000 — ground truth gap (no positive SW pronoun_assumption examples collected). Category is implemented in the lexicon. Future annotation sprint targeted.

---

## Demographic Parity / Fairness (Per Language)

| Language | Demographic Parity | Equal Opportunity | Equalized Odds | AIBRIDGE pass? |
|---|---|---|---|---|
| English | 0.593 | 0.000 | 0.000 | DP fails — eval set distribution issue (very few male-tagged rows), not model unfairness |
| Swahili | 0.006 | 0.000 | 0.000 | All pass ✅ |
| French | 0.000 | 0.000 | 0.000 | All pass ✅ |
| Gikuyu | 0.000 | 0.000 | 0.000 | All pass ✅ |
| Hausa | — | — | — | Not yet computed — GT sourced from StudyLabs, DP/EO requires target_gender breakdown audit |
| Zulu | — | — | — | Not yet computed — ZU GT is correction pairs, target_gender not annotated |

---

## Ethics & Documentation Checklist

| Item | Status | Notes |
|---|---|---|
| Ethical approval & consent | ✅ | Ethics review completed by Rebecca Ryakitimbo, AI BRIDGE, Feb 2026 |
| Annotator demographic balance | ⏳ | AO-001 (F, native Swahili speaker, Kenya). ann_sw_kappa_v2: 2nd annotator, 500-row overlap, κ=0.8537. Full demographic documentation pending for all batches. |
| Licensing & provenance | ✅ | Helsinki Corpus (academic), BBC Swahili (news), Wikipedia SW (CC-BY-SA), AfriSenti (research), MasakhaNER (open) |
| Bias audit completed | ✅ | JSONL audit log per correction request. ann_sw_v3 + ann_sw_kappa_v2 audited. SW deduplication (207 rows removed), PII scrub (110 rows) completed Apr 2026. |
| Reviewer sign-off | ✅ | Rebecca Ryakitimbo (AI BRIDGE, Feb 2026) |

---

## Reviewer Notes

Dataset scale: SW=67,290 rows (Gold tier), KI=11,622, EN=66 (eval), FR=165, HA=10,054 (StudyLabs-sourced), ZU=2,000 (correction pairs). Total: 91,197 rows across 6 languages. SW dialect: TZ=51.6% (34,594), KE=48.4% (32,401), Sheng: 49 rows (incidental content, not a tagged dialect). Counter-stereotype: 15.63% (≥15% met, SW). Implicit bias: 5.01% (≥5% met, SW). PII scrubbed: 110 rows. Non-media domains added Apr 2026 (health, governance, agriculture, education — 2,479 rows). HVI (kappa) closed: κ=0.8537 (Almost Perfect, SW). HA precision-first initial coverage: 1,012 bias rows, dominant categories leadership/religion_culture/daily_life require ML for recall. ZU morphological coverage: 1,978 bias rows (gender suffix patterns). Known open gaps: distinct Sheng dialect coverage, SW pronoun_assumption GT gap, HA/ZU DP/EO not yet computed, WEFE/WEAT/TGBI pending tooling.

**Computed Fairness Index: 70**

FI closed items: κ=0.8537, counter-stereotype 15.63%, implicit bias 5.01%, DP/EO/EOdds computed for all 4 languages. FI open items: EN DP=0.593 (eval distribution issue), MBE=0.825 (KI recall gap), human correction-review cycle not yet completed. FI will increase once ≥200 validated human corrections are logged.

---

**Signed**: David Nene  
**Role**: Technical Lead, JuaKazi  
**Date**: 2026-05-01  
**Programme**: AI BRIDGE — Engine 2
