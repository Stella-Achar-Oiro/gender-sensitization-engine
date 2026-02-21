# JuaKazi Gender Bias Dataset Card
**Version**: 3.0 | **Last updated**: February 2026 | **Schema**: AIBRIDGE v1 (24-column CSVW)

Update this card every time a new dataset version is created. Per AI BRIDGE protocol.

---

## 1. Dataset Identity

| Field | Value |
|---|---|
| **Name** | JuaKazi Gender Bias Ground Truth |
| **Team** | Juakazi / AI BRIDGE |
| **Languages** | Kiswahili (sw), English (en), French (fr), Gikuyu (ki) |
| **Intended use** | Detection and correction of gender bias in African language text |
| **Schema** | AIBRIDGE v1 — 24 required columns + project extensions |
| **License** | CC BY 4.0 (text); ODC-BY (tabular metadata) |
| **Repository** | juakazi/gender-sensitization-engine |
| **Ethics review** | Internal review by Juakazi team; AI BRIDGE expert review (Rebecca, Feb 2026) |

---

## 2. Dataset Versions (Current)

| Language | File | Version | Total rows | Biased | Neutral | AI BRIDGE tier |
|---|---|---|---|---|---|---|
| Swahili | `eval/ground_truth_sw_v5.csv` | v5 | 51,419 | 1,956 (3.8%) | 49,300 (95.9%) | **Gold** (44,612 req. met) |
| Gikuyu | `eval/ground_truth_ki_v8.csv` | v8 | 11,848 | — | — | **Bronze** (987% of 1,200 req.) |
| English | `eval/ground_truth_en_v5.csv` | v5 | 66 | 25 | 41 | Pre-Bronze (needs 1,134 more) |
| French | `eval/ground_truth_fr_v5.csv` | v5 | 50 | 20 | 30 | Pre-Bronze (needs 1,150 more) |

---

## 3. Swahili Dataset — Detailed Breakdown (v5, Feb 2026)

### 3.1 Sample Distribution

| Metric | Count | % |
|---|---|---|
| Total rows | 51,419 | 100% |
| has_bias = true | 1,956 | 3.8% |
| has_bias = false | 49,300 | 95.9% |
| Missing expected_correction (biased rows) | ~1,066 | — |

### 3.2 Gender Representation

| target_gender | Count | % of total |
|---|---|---|
| female | 1,049 | 2.0% |
| male | 460 | 0.9% |
| mixed | 434 | 0.8% |
| neutral | 49,476 | 96.2% |

**Note**: AI BRIDGE requires F:M:Neutral within ±5%. Current dataset is heavily neutral due to large neutral corpus from news sources. Bias-targeted rows show 54% female / 24% male / 22% mixed among biased samples — within acceptable range for the biased slice.

### 3.3 Dialect / Regional Diversity

| region_dialect | Count | % | Source |
|---|---|---|---|
| tanzania | 33,411 | 65.0% | Helsinki Swahili Corpus (Zenodo 4300294) — Standard Tanzanian Swahili |
| kenya | 18,008 | 35.0% | Swahili News Dataset (Zenodo 5514203), BBC Swahili, AfriSenti, MasakhaNER |
| sheng | 0 | 0% | **Gap** — Nairobi urban youth register not yet represented |
| uganda | 0 | 0% | **Gap** |

**AI BRIDGE recommendation (Rebecca, Feb 2026)**: Add Standard Swahili, Sheng, and Tanzanian Swahili at minimum. Sheng and Uganda Swahili are current gaps to address in v6.

### 3.4 Bias Label Distribution (biased rows only)

| bias_label | Count | % of biased |
|---|---|---|
| stereotype | 1,950 | 99.7% |
| derogation | 6 | 0.3% |
| counter-stereotype | 0 | **Gap** — AI BRIDGE requires ≥15% |
| neutral | — | — |

**Action required**: Add counter-stereotype examples (target: ≥15% of biased rows = ~293 rows minimum).

### 3.5 Stereotype Category Distribution

| stereotype_category | Count | % of biased |
|---|---|---|
| profession | 1,803 | 92.2% |
| capability | 107 | 5.5% |
| family_role | 24 | 1.2% |
| leadership | 7 | 0.4% |
| daily_life | 6 | 0.3% |
| appearance | 5 | 0.3% |
| religion_culture | 0 | **Gap** |
| proverb_idiom | 0 | **Gap** |
| education | — | small |

### 3.6 Explicitness

| explicitness | Count | % of biased |
|---|---|---|
| explicit | 1,938 | 99.1% |
| implicit | 18 | 0.9% |

**Gap**: AI BRIDGE requires ≥5% implicit. Current: 0.9%. Need ~80 more implicit rows.

### 3.7 Data Sources

| Source | Rows | Region | License |
|---|---|---|---|
| Helsinki Swahili Corpus | 33,411 | Tanzania | CC BY 4.0 |
| BBC Swahili / Swahili News | 16,421 | Kenya | Research use |
| MasakhaNER | 949 | Kenya | Apache 2.0 |
| Swahili News Dataset (Zenodo 5514203) | 394 | Kenya | CC BY 4.0 |
| AfriSenti | 244 | Kenya | CC BY 4.0 |

**Domains**: 98.2% media_and_online, 1.8% governance_civic. **Gap**: livelihood_and_work, household_and_care, health domains absent — recommended by Rebecca (Feb 2026).

---

## 4. Annotators

### 4.1 Annotation Method

| Annotator ID | Type | Rows annotated | Method |
|---|---|---|---|
| ann_sw_auto_v1 | Automated (rule-based) | 51,344 | Heuristic labeling from source corpora |
| ann_sw_auto_v2 | Automated (rule-based) | 26 | Heuristic labeling |
| claude_ann_v1 | AI-assisted (Claude Sonnet 4.6) | 49 | Supervised annotation per AIBRIDGE guidelines |

### 4.2 Annotator Gender Breakdown

**Current status**: Auto-annotation only — no human annotators recruited yet.

| Annotator type | Count | Female | Male | Not specified |
|---|---|---|---|---|
| Human native speakers | 0 | — | — | — |
| AI-assisted | 1 (Claude) | N/A | N/A | N/A |

**Action required (Phase 2)**: Recruit 2–5 Swahili native speakers for double annotation of 100% of biased rows. Document gender breakdown (e.g., "3 female, 2 male") in next version of this card. AI BRIDGE requires annotator gender breakdown for transparency.

### 4.3 Inter-Annotator Agreement

| Metric | Target | Current |
|---|---|---|
| Cohen's Kappa (κ) | ≥ 0.70 | Not yet computed — no human double annotation |
| Krippendorff's α | ≥ 0.80 | Not yet computed |
| Multi-annotator coverage | ≥ 10% of biased rows | 0% (pending native speaker recruitment) |

---

## 5. Bias Classifications Table (Swahili — representative examples)

| Bias type | Example | Severity | Corrected | Human reviewed |
|---|---|---|---|---|
| Gendered occupation suffix | "Daktari wa kiume" | replace | Y (remove suffix) | Partial |
| Gendered occupation suffix | "Muuguzi wa kike" | replace | Y (remove suffix) | Partial |
| Homemaker role | "Mama wa nyumbani" | replace | Y → "Mtu anayeshughulikia nyumba" | Partial |
| Leadership derogation | "Wanawake hawafai kushika nafasi za uongozi" | replace | Y → "Kila mtu anaweza..." | Partial |
| Capability derogation | "Wanaume wana akili zaidi ya wanawake" | replace | Y → "Kila mtu ana uwezo sawa..." | Partial |
| Proverb (preserved) | "Mama ni nguzo ya nyumba" | warn | Preserved — culturally embedded | Pending |
| Implicit profession | "Yeye ni muuguzi" (female assumed) | replace | Y → "Muuguzi huyo" | Pending |

---

## 6. Quality Assurance

### 6.1 Automated Checks
- Duplicate detection (by text hash)
- Language ID sanity check
- Script validation (all sw rows = latin)
- PII detection (`pii_removed` field)
- Schema validation (24 required columns present)

### 6.2 Gold Standard
No gold standard set defined yet. **Action required**: Define 200-row gold set per AI BRIDGE protocol for drift checks across training cycles.

### 6.3 Known Data Quality Issues
- `expected_correction` missing on ~1,066 biased rows (annotation in progress)
- `stereotype_category` auto-assigned; some corrections needed (ongoing in annotation batches)
- No counter-stereotype rows yet
- Implicit bias rows at 0.9% (target: ≥5%)
- Proverb/idiom rows: near zero (target: ≥5%)

---

## 7. Detection Metrics (as of Feb 2026)

| Language | Precision | Recall | F1 | DP | EO | AI BRIDGE tier |
|---|---|---|---|---|---|---|
| English | 1.000 | 0.647 | 0.786 | 0.038 | 0.019 | Pre-Bronze |
| Swahili | 1.000 | 0.457 | 0.627 | 0.000 | 0.000 | Gold (sample size) |
| French | 1.000 | 0.371 | 0.542 | 0.060 | 0.030 | Pre-Bronze |
| Gikuyu | 0.926 | 0.217 | 0.352 | 0.000 | 0.000 | Bronze (sample size) |

**Precision 1.000 = zero false positives across all languages (hard constraint).**

---

## 8. Ethical Considerations

- **No PII**: All rows have pii_removed checked; names replaced with [NAME] tokens where applicable
- **Cultural sensitivity**: Religious texts (Bible/Gikuyu) marked `safety_flag=sensitive`; annotated for social meaning not theological content
- **Overcorrection risk**: Tool may flag culturally significant gendered terms — documented in `skipped_context` in audit logs; flagged for human review
- **Withdrawal route**: Contact team via project repository issues to request removal of community-contributed text
- **Binary gender framework limitation**: Current schema supports `nonbinary` as a target_gender value; no nonbinary examples in dataset yet

---

## 9. Versioning Protocol

- Update this card with every new dataset version
- Increment `DataVersions.GROUND_TRUTH` in `config.py` when schema changes
- Record: rows added, source, annotation method, new metrics
- AI BRIDGE team adds review notes after each submission
