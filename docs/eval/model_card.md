# JuaKazi Gender Sensitization Engine — Model Card

**Version**: 3.2 | **Last updated**: April 2026
**Submission**: AI BRIDGE programme — Detection + Correction layers
**Reviewer**: Rebecca Ryakitimbo (AI BRIDGE)
**Live demo**: https://huggingface.co/spaces/juakazike/gender-sensitization-engine

Per AI BRIDGE protocol, this card is the authoritative source of truth for model behaviour, limitations, and update history. Update it every time lexicons change, run_evaluation.py produces new metrics, or the ML model is retrained.

---

## 1. Model Description

### What it does

The JuaKazi Gender Sensitization Engine detects and corrects gender-biased language in East African text. Given an input sentence, it identifies spans that contain gender bias, explains why they are flagged, and proposes a neutral rewrite. The system targets overt bias (explicit stereotypes, role assignment, derogatory terms) as well as occupational and morphological patterns.

### Languages

English (en), Swahili (sw), French (fr), Gikuyu/Kikuyu (ki)

### Two-layer architecture

```
Input text
  |
  v
+-------------------------------------------------------------+
|  Layer 1 -- Rules-based lexicon detector (PRIMARY)         |
|                                                             |
|  BiasDetector.detect_bias()                                 |
|    +-- DEROGATION_PATTERNS  (hardcoded, highest priority)   |
|    +-- COUNTER_STEREOTYPE_PATTERNS  (detect + preserve)     |
|    +-- Lexicon rules  (lexicon_{lang}_v3.csv)               |
|          +-- ContextChecker  (10 condition gates)           |
|          |     quote | historical | proper_noun |           |
|          |     biographical | statistical | medical |       |
|          |     counter_stereotype | legal | artistic |      |
|          |     organization                                 |
|          +-- severity=replace -> correction applied         |
|          +-- severity=warn   -> advisory flag only          |
+-------------------------------------------------------------+
  |  no match found?
  v
+-------------------------------------------------------------+
|  Layer 2 -- ML fallback (Swahili only, Stage 2)             |
|                                                             |
|  juakazike/sw-bias-classifier-v3                            |
|  afro-xlmr-base, fine-tuned on 66,995 SW rows              |
|  -> severity=ml_fallback, needs_review=True                 |
|  -> never auto-corrects; flags for human review only        |
+-------------------------------------------------------------+
  |
  v
POST /rewrite -> { original_text, rewrite, edits, confidence,
                   source, semantic_score, reason }
```

Key design decisions:

- Layer 1 handles EN, SW, FR, KI. Layer 2 is Swahili-only.
- severity=replace triggers automatic correction; severity=warn is advisory and never flips has_bias_detected.
- Context gating (avoid_when in lexicon CSVs) suppresses rules in biographical, statistical, historical, and counter-stereotype contexts to reduce false positives.
- Case is preserved in all rewrites (Chairman -> Chairperson, not chairperson).
- Separate lexicons per language — no cross-lingual transfer.
- Swahili noun-class agreement (ngeli) is tracked by eval/ngeli_tracker.py to keep replacements grammatically valid.

### Lexicons (Apr 2026)

| Language | File                      | Entries |
|----------|---------------------------|---------|
| English  | rules/lexicon_en_v3.csv   | 68      |
| Swahili  | rules/lexicon_sw_v3.csv   | 267     |
| French   | rules/lexicon_fr_v3.csv   | 101     |
| Gikuyu   | rules/lexicon_ki_v3.csv   | 1,247   |

---

## 2. Intended Use

**Intended use:** Flag and neutralise gender-biased language in written East African text for content moderation, editorial review, and inclusive writing assistance.

**Primary users:** Journalists, content platforms, NGOs, government communication teams, and educational publishers operating in East Africa.

**Not intended for:**

- Real-time speech transcription or audio analysis
- Personal messaging surveillance
- Automated mass-moderation without a human reviewer in the loop
- Languages outside the four supported
- Detecting non-gender forms of bias (racial, ethnic, disability, age)

**Deployment guidance:** Layer 2 (ML fallback) outputs needs_review=True on every edit it produces. These must be reviewed by a human before being used to modify published content. Layer 1 corrections are higher confidence but should still be reviewed before bulk application.

---

## 3. Training Data

### Datasets

| File                                              | Language | Rows   | Purpose                                |
|---------------------------------------------------|----------|--------|----------------------------------------|
| eval/ground_truth_sw_v5.csv                       | Swahili  | 66,995 | Rules eval + ML training               |
| eval/ground_truth_ki_v8.csv                       | Kikuyu   | 11,622 | Rules eval                             |
| eval/ground_truth_en_v5.csv                       | English  | 66     | Rules eval (held-out, not for training)|
| eval/ground_truth_fr_v5.csv                       | French   | 165    | Rules eval                             |
| data/annotation_export/en_ml_training_v1.csv      | English  | 2,828  | ML training only                       |

The English ML training set combines WinoBias (1,584 rows), WinoGender (720 rows), and CrowS-Pairs (524 rows). These are real published benchmark datasets, not synthetic data.

### Swahili sources

| Source corpus                     | Description                          | Region   |
|-----------------------------------|--------------------------------------|----------|
| Helsinki Corpus of Swahili        | Tanzanian news, formal SW            | Tanzania |
| BBC Swahili / swahili_news (HF)   | Kenyan broadcast news                | Kenya    |
| AfriSenti                         | Social media (Twitter/X)             | Mixed    |
| MasakhaNER                        | Named entity corpus, neutral-class   | Mixed    |
| Wikipedia SW                      | Encyclopedia text                    | Mixed    |
| C4-SW                             | Web-crawled Swahili                  | Mixed    |

### Dialect distribution (Swahili)

| region_dialect       | Rows   | Share  |
|----------------------|--------|--------|
| Tanzania             | 34,594 | 51.6%  |
| Kenya                | 32,401 | 48.4%  |
| Sheng content        | 49     | 0.1%   |

Note on Sheng: 49 rows contain Sheng-language content as topic or text. Sheng as a distinct dialect tag in the annotation schema is a gap for future collection sprints — these 49 rows are not a representative sample of Sheng and should not be treated as such.

### Data quality properties (Swahili ground truth)

| Property                           | Value                                              | AIBRIDGE requirement |
|------------------------------------|---------------------------------------------------|----------------------|
| Counter-stereotype rows            | 15.63%                                            | >=15% -- met         |
| Implicit bias rows                 | 5.01%                                             | >=5% -- met          |
| PII scrubbed                       | 110 rows (emails -> [EMAIL], phones -> [PHONE])   | --                   |
| Inter-annotator agreement (kappa)  | 0.8537 (Almost Perfect) -- COMPLETE               | >=0.61 (Bronze) met  |
| Duplicate texts removed            | 207 rows                                          | --                   |
| Empty texts removed                | 1 row                                             | --                   |

### Inter-annotator agreement

Cohen's Kappa kappa=0.8537 was computed on a 500-row Swahili overlap batch between primary annotator (AO-001) and second-pass annotator (ann_sw_kappa_v2). This exceeds the AIBRIDGE Bronze threshold (kappa>=0.61) and falls in the Almost Perfect band (kappa>=0.81) per Landis and Koch (1977). The Human Validation Index requirement is closed.

Full annotated overlap file: data/annotation_export/batch_for_annotator_B_kappa_overlap_ANNOTATED_v2.csv

English and French IAA has not been computed (single annotator, small evaluation sets). This is acknowledged as a limitation.

### Schema (key columns)

| Column              | Description                                                                                          |
|---------------------|------------------------------------------------------------------------------------------------------|
| text                | The sentence to classify                                                                             |
| has_bias            | True = biased, False = neutral                                                                       |
| bias_label          | neutral, stereotype, occupational_bias, role_assignment, appearance_bias, personality_trait,         |
|                     | social_norm, counter-stereotype, annotation_error                                                    |
| explicitness        | explicit or implicit                                                                                 |
| target_gender       | female, male, both, unspecified                                                                      |
| annotator_id        | Annotator identifier                                                                                 |
| expected_correction | Suggested neutral rewrite (where available)                                                          |

---

## 4. Evaluation Results

All metrics from run_evaluation.py, April 2026. Reproduce with: python3 run_evaluation.py

### 4.1 Detection — overall (rules-based, all languages)

| Language | F1    | Precision | Recall | Eval samples |
|----------|-------|-----------|--------|--------------|
| English  | 1.000 | 1.000     | 1.000  | 66           |
| Swahili  | 0.840 | 0.807     | 0.876  | 66,995       |
| French   | 0.970 | 1.000     | 0.941  | 165          |
| Gikuyu   | 0.667 | 0.967     | 0.510  | 11,622       |

### 4.2 Swahili — gender-disaggregated

| Target gender       | Precision | Recall | F1    | Rows |
|---------------------|-----------|--------|-------|------|
| Female              | 0.774     | 0.868  | 0.818 | 887  |
| Male                | 0.928     | 0.972  | 0.950 | 213  |
| Neutral/unspecified | 0.324     | 0.379  | 0.349 | 29   |

The 13.2 point gap between female F1 (0.818) and male F1 (0.950) reflects lower precision on female-targeted bias. The main FP cluster — Watoto wa Kike and mtoto wa kike — is disproportionately female-targeted. See section 5.1.

### 4.3 Gikuyu — gender-disaggregated

| Target gender       | Precision | Recall | F1    | Rows |
|---------------------|-----------|--------|-------|------|
| Female              | 0.978     | 0.731  | 0.837 | 249  |
| Male                | 0.964     | 0.491  | 0.651 | 918  |
| Neutral/unspecified | 1.000     | 0.417  | 0.589 | 429  |

Kikuyu shows the reverse pattern from Swahili: precision is high across all genders but recall is low. Male recall (0.491) is worse than female (0.731). The majority of male-targeted KI biased rows involve religious and traditional-leadership text not yet covered by the lexicon.

### 4.4 Swahili — bias category breakdown

| Bias category       | Precision | Recall | F1    | TP  | FP | FN |
|---------------------|-----------|--------|-------|-----|----|----|
| occupation          | 0.955     | 0.918  | 0.936 | 719 | 34 | 64 |
| stereotype          | 1.000     | 0.751  | 0.858 | 25  | 0  | 83 |
| pronoun_assumption  | 0.000     | 0.000  | 0.000 | 0   | 0  | 0  |

SW pronoun_assumption F1=0.000: The 57 SW ground truth rows tagged pronoun_assumption are all has_bias=False — they are neutral sentences used as pronoun context, not positive bias examples. There is nothing for the rule layer to detect. This is a ground truth gap (no positive SW pronoun bias examples collected), not a missing lexicon category. EN and FR pronoun detection is fully implemented and scores F1=1.000 in both languages. KI pronoun_assumption F1=0.491, KI pronoun_generic F1=0.613.

stereotype Recall=0.751: 83 stereotyping sentences are missed (FN=83). These are likely implicit or proverb-form bias that word-level rules cannot match.

### 4.5 ML classifier — Swahili Stage 2 fallback

Metrics from Richard Kadey's external benchmark (test.csv, 9,709 rows, 172 BIAS labels). Base: afro-xlmr-base. Fine-tuned on 66,995 SW rows, 3 epochs, T4 GPU.

| Version | HF ID                              | Test F1 | Test Precision | Test Recall | Status         |
|---------|------------------------------------|---------|----------------|-------------|----------------|
| v1      | juakazike/sw-bias-classifier-v1    | 0.854   | 0.938          | 0.784       | Superseded     |
| v2      | juakazike/sw-bias-classifier-v2    | 0.493   | 0.330          | 0.976       | Invalid        |
| v3      | juakazike/sw-bias-classifier-v3    | 0.871   | 0.810          | 0.942       | Deployed       |

v2 failure: pos_weight approximately 58x caused extreme recall-bias. BIAS Precision collapsed to 0.330 with 333 false positives on the external evaluation. v3 fix: pos_weight hard-capped at 10; neutral_ratio=40 (40K neutral rows exposed, up from 4K); annotation_error rows excluded from training.

To switch the deployed ML model: set JUAKAZI_ML_MODEL=juakazike/sw-bias-classifier-v3 (this is the default if not set).

### 4.6 Correction layer metrics

| Metric                  | English          | Swahili          | French           | Gikuyu           |
|-------------------------|------------------|------------------|------------------|------------------|
| Correction Quality      | 0.939            | 0.823            | 0.788            | 0.529            |
| Meaning Preservation    | 0.722 (Good)     | 0.967 (Excellent)| 0.767 (Good)     | 0.881 (Excellent)|
| Bias Removal Accuracy   | 100% (27/27)     | 83% (857/1,033)  | 78.3% (18/23)    | 100% (296/296)   |

Swahili: 379 over-corrections flagged out of 1,033 correction attempts. These are the Watoto wa Kike / mtoto wa kike FP cluster (section 5.1), not random errors. Human review is recommended before bulk production use.

Gikuyu: Correction Quality Score of 0.529 is below production threshold. Treat KI correction outputs as beta.

### 4.7 Bias severity reduction (rule-based corrections)

| Bias type            | Severity before | Severity after | Verified |
|----------------------|-----------------|----------------|----------|
| Role-based           | 3               | 1              | Yes      |
| Proverbial           | 3               | 1              | Yes      |
| Morphological        | 2               | 1              | Yes      |
| Adjectival           | 2               | 1              | Yes      |
| Contextual/Cultural  | 3               | 2              | Yes      |

---

## 5. Limitations and Known Gaps

All items below were flagged by Rebecca Ryakitimbo in her review. They are documented here because they are real constraints, not because they indicate the system is broken.

### 5.1 Swahili precision (0.807) — two known FP clusters

The two largest false positive drivers:

- Watoto wa Kike ("girl children / female children"): 182 false positives. Factual in health and education advocacy contexts; stereotyping in prescriptive media. The lexicon fires on both. This precision hit is intentional and accepted — removing the rule would collapse recall on prescriptive cases.
- mtoto wa kike ("female child"): 138 false positives. Same ambiguity pattern.

These 320 FPs represent a deliberate trade-off: they are the cost of maintaining recall=0.876 in Swahili. The long-term fix is richer avoid_when context gating, not rule removal.

### 5.2 Swahili pronoun_assumption: F1=0.000 — ground truth gap, not a lexicon gap

Pronoun bias detection is fully implemented for EN (F1=1.000), FR (F1=1.000), and KI (pronoun_assumption F1=0.491, pronoun_generic F1=0.613). The SW zero is caused by the ground truth, not the rule layer: all 57 SW rows tagged pronoun_assumption have has_bias=False. They represent neutral pronoun-context sentences, not biased ones. Because there are no positive SW pronoun bias examples in the ground truth, the rule layer correctly returns zero detections and scores F1=0.000. The gap is in data collection, not in coverage implementation. Positive SW pronoun bias examples are targeted for the next annotation sprint.

### 5.3 Gikuyu recall (0.510) — high-risk gap

Gikuyu recall is 0.510. Approximately half of biased rows are missed. Primary drivers:

- Religious text patterns: mũthĩnjĩri-Ngai and related Bible passages appear in both devotional (neutral) and gender-prescriptive contexts. The lexicon does not yet have sufficient context discrimination for these.
- Implicit bias prevalence: 79% of KI biased rows are implicit bias, which word-level rules cannot address.

This is a high-risk failure mode: biased content passes through undetected. KI outputs should be treated as beta coverage with mandatory human review.

### 5.4 Sheng dialect coverage

49 rows contain Sheng-language content. Sheng as a distinct, properly collected dialect is not represented. System performance on Sheng text is unknown and likely poor. Documented as a collection gap for future sprints.

### 5.5 Small evaluation sets for EN and FR

English evaluation: 66 rows. French evaluation: 165 rows. Both single-annotator, no IAA computed. EN F1=1.000 and FR F1=0.970 should be read as indicative of rule coverage on the curated set, not as production benchmarks.

### 5.6 ML fallback is Swahili-only and warn-only

Layer 2 covers Swahili only. EN, FR, and KI rely entirely on rules. Every ML edit carries severity=ml_fallback and needs_review=True. It never applies automatic corrections.

---

## 6. Fairness Metrics

### Closed requirements

Inter-annotator agreement: Cohen's kappa=0.8537 (Almost Perfect) computed via second annotator batch ann_sw_kappa_v2 on a 500-row overlap set. This closes the Human Validation Index requirement. The AIBRIDGE Bronze threshold (kappa>=0.61) is met.

AIBRIDGE dataset thresholds met:
- Counter-stereotype rows: 15.63% (requirement: >=15%)
- Implicit bias rows: 5.01% (requirement: >=5%)

### Fairness metrics (Apr 2026)

Per-language demographic parity, equal opportunity, and equalized odds. Computed over the held-out detection sets.

| Language | Demographic Parity | Equal Opportunity | Equalized Odds | Passes AIBRIDGE? |
|----------|--------------------|-------------------|----------------|------------------|
| English  | 0.593              | 0.000             | 0.000          | DP fails (>0.10) |
| Swahili  | 0.006              | 0.000             | 0.000          | All pass         |
| French   | 0.000              | 0.000             | 0.000          | All pass         |
| Gikuyu   | 0.000              | 0.000             | 0.000          | All pass         |

Mean Bias Error (MBE, all 4 languages): 0.825 — below the 0.85 target.

Notes on EN and MBE:
- EN Demographic Parity=0.593 is a data distribution issue, not model unfairness. The EN evaluation set has very few male-tagged rows relative to female-tagged rows, which inflates the parity gap. The EN detection rules are gender-symmetric.
- MBE=0.825 is pulled below the 0.85 target primarily by KI F1=0.667. As Gikuyu coverage improves, MBE will rise.

### What remains open

| Item                                        | Status         | Notes                                                                        |
|---------------------------------------------|----------------|------------------------------------------------------------------------------|
| Sheng dialect coverage                      | Open gap       | 49 rows of Sheng content; full dialect not represented                       |
| Gikuyu recall                               | Open gap       | Recall=0.510 driven by religious text patterns not yet in lexicon            |
| EN and FR IAA                               | Not computed   | Single annotator, small sets                                                 |
| Human review cycle (correction validation)  | Not started    | No human review sessions completed; Bias Removal Accuracy is system-computed |
| SW pronoun bias GT coverage                 | Collection gap | No positive SW pronoun bias examples in ground truth; future annotation sprint|
| MBE >=0.85                                  | Not yet met    | MBE=0.825; will improve as KI recall increases                               |
| WEFE/WEAT                                   | Not yet measured | Requires embedding extraction from afro-xlmr-base and East African gendered word lists — no standard word lists exist for SW/KI |
| TGBI                                        | Not yet measured | Requires a translated Gender Bias Inventory for Swahili/Gikuyu — no such translation exists for East African languages |

### Representation and balance metrics (SW, Apr 2026)

Computed from ground_truth_sw_v5.csv (66,995 rows). Swahili only; EN/FR/KI sets are too small for meaningful subgroup statistics.

| Metric                          | Target           | Actual                                                                                     | Status       |
|---------------------------------|------------------|--------------------------------------------------------------------------------------------|--------------|
| Gender representation ratio     | 45–55% balanced  | female=65.9% (887 biased rows), male=15.8% (213), mixed=12.1% (163), neutral=2.2% (29)   | Not met      |
| Role-based bias count           | <=5%             | 58.1% (783/1,347 biased rows have bias_category=occupation)                                | Not met      |
| Cultural/proverbial incidence   | <=2 per 1,000    | 1.33 per 1,000 (89 biased rows, stereotype_category in {family_role, daily_life})         | Met          |
| Regional diversity              | >=3 regions      | 2 tagged regions (TZ=51.6% 34,594 rows, KE=48.4% 32,401 rows); 49 rows Sheng content     | Not met      |
| Pronoun consistency rate        | >=95%            | EN: F1=1.000 (pronoun_assumption + pronoun_generic both implemented). FR: F1=1.000. KI: pronoun_assumption F1=0.491, pronoun_generic F1=0.613. SW: F1=0.000 — GT gap (no positive SW pronoun bias examples collected yet). | EN/FR met; KI partial; SW GT gap |

Notes on gaps:
- Gender representation skew (65.9% female) reflects source media corpus, not a labeling error. SW online news disproportionately frames gender bias around female subjects. Future collection should actively seek male-targeted and neutral-gender bias examples.
- Occupation bias at 58.1% reflects the same corpus skew. Occupational gender framing dominates SW online media. This is documented, not hidden.
- Regional diversity: only TZ and KE are represented as dialect tags. A third region (e.g., Ugandan SW or diaspora SW) is a future collection target.
- SW pronoun GT gap: the 57 SW pronoun_assumption rows are all has_bias=False. No positive SW pronoun bias examples exist in the ground truth. This is a collection gap, not an unimplemented category.

### Current Fairness Index

FI=70. Closed items: inter-annotator agreement (kappa=0.8537), counter-stereotype threshold (15.63%), implicit bias threshold (5.01%), per-language DP/EO/EOdds computed. Open items: EN demographic parity gap (data distribution, not model unfairness), MBE=0.825 below 0.85 target (driven by KI F1), human correction-review cycle not yet completed, SW pronoun bias ground truth gap.

---

## 7. Ethical Considerations

### Gikuyu cultural validation gap

Gikuyu annotations were largely auto-generated with human QA. Religious and traditional-leadership text — the primary source of false negatives in KI — requires native Kikuyu speakers with appropriate cultural context to adjudicate correctly. This validation has not been completed. KI corrections should not be applied without native speaker review.

### Sheng coverage gap

Sheng (Nairobi urban youth Swahili) is not represented as a collected dialect. 49 rows contain Sheng content incidentally. Deploying this system on Sheng-dominant content without acknowledging this gap would be misleading.

### Over-correction cluster

The 379 Swahili over-corrections are not random. They are the Watoto wa Kike / mtoto wa kike FP cluster (section 5.1). This cluster is known, concentrated, and the first priority for context gating work in the next lexicon sprint.

### Annotator diversity

The annotator demographic breakdown (gender, region, L1 variety) has not been formally documented for all batches. AO-001 is a native Swahili speaker. ann_sw_kappa_v2 completed the 500-row overlap batch. Future batches should formally document annotator gender, country, and L1 Swahili variety.

### Data sources and consent

All sources are public corpora. No personal data was collected. 110 rows with PII (emails, phone numbers) have been scrubbed.

### Binary gender framework

The system uses binary gender labeling (female / male / neutral). Non-binary, intersectional, and disability-related bias are not captured. This reflects current annotation capacity.

### Deployment warnings

1. Do not use Layer 2 (ML) outputs to automatically modify published content. needs_review=True is enforced in the API response for all ML edits.
2. Swahili over-correction rate is approximately 37% of correction attempts. Bulk automated rewriting without review is not safe.
3. Kikuyu correction quality (0.529) is below production threshold.
4. Swahili pronoun bias: F1=0.000 because the SW ground truth contains no positive pronoun bias examples (all 57 SW pronoun_assumption rows are has_bias=False). EN/FR pronoun detection is fully implemented (F1=1.000). KI pronoun detection is partial (pronoun_assumption F1=0.491, pronoun_generic F1=0.613).
5. Gikuyu requires native speaker validation before production deployment.

---

## 8. How to Use

### API

```bash
# Start the API at port 8080
make run-api

# POST /rewrite
curl -X POST http://localhost:8080/rewrite \
  -H "Content-Type: application/json" \
  -d '{"id": "test-001", "lang": "sw", "text": "Mwanamke ni jiko la nyumbani."}'
```

Response shape:

```json
{
  "id": "test-001",
  "original_text": "Mwanamke ni jiko la nyumbani.",
  "rewrite": "Mtu anaweza kusaidia kazi za nyumbani.",
  "edits": [...],
  "confidence": 0.92,
  "source": "rules",
  "semantic_score": 0.71,
  "reason": "flagged because it assigns a domestic role to women exclusively"
}
```

### Environment variables

| Variable                   | Default                              | Description                                   |
|----------------------------|--------------------------------------|-----------------------------------------------|
| JUAKAZI_ML_MODEL           | juakazike/sw-bias-classifier-v3      | HF model ID for Stage 2 ML fallback           |
| JUAKAZI_ML_THRESHOLD       | 0.56                                 | Confidence threshold for ML detections        |
| JUAKAZI_SEMANTIC_THRESHOLD | 0.70                                 | Minimum semantic similarity for corrections   |

### HuggingFace Space

Live demo: https://huggingface.co/spaces/juakazike/gender-sensitization-engine

### Evaluation

```bash
python3 run_evaluation.py              # full detection eval, all 4 languages
python3 run_evaluation.py --fairness   # with AIBRIDGE fairness metrics
python3 tests/test_system.py           # smoke tests, 5/5 must pass before merge
```

---

## 9. Citation and Team

```bibtex
@software{juakazi_bias_engine_2026,
  title   = {JuaKazi Gender Sensitization Engine},
  author  = {{JuaKazi Team}},
  year    = {2026},
  url     = {https://huggingface.co/spaces/juakazike/gender-sensitization-engine},
  note    = {Multilingual gender bias detection and correction for East African languages.
             Submitted to the AI BRIDGE programme, April 2026.}
}
```

JuaKazi Team — AI BRIDGE submission, April 2026.

---

## 10. Version History

| Card version | Date     | Key changes                                                                                                                                                                                                                                             | SW F1 | SW ML deployed |
|-------------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|----------------|
| 1.0         | Oct 2024 | Initial card                                                                                                                                                                                                                                            | 0.681  | None           |
| 2.0         | Feb 2026 | Modular API, region_dialect, HITL UI                                                                                                                                                                                                                    | 0.611  | v1 (0.854)     |
| 2.1         | Mar 2026 | ann_sw_v3 (13K rows), proverbs, Sheng terms                                                                                                                                                                                                             | 0.816  | v1             |
| 2.2         | Mar 2026 | ML v3 retrained; kappa=0.8537 established                                                                                                                                                                                                               | 0.816  | v3 (0.871)     |
| 2.3         | Mar 2026 | Ground truth 67,202 rows; FR expanded to 165                                                                                                                                                                                                            | 0.819  | v3             |
| 3.0         | Apr 2026 | Full rewrite; Apr 2026 metrics; gender-disaggregated added                                                                                                                                                                                              | 0.840  | v3             |
| 3.1         | Apr 2026 | Gender-disaggregated P/R/n, bias category table, dialect ratios, FI=70                                                                                                                                                                                  | 0.840  | v3             |
| 3.2         | Apr 2026 | Dialect numbers corrected (TZ=51.6% 34,594 rows, KE=48.4% 32,401 rows, Sheng 49 rows not zero). HVI closed (kappa=0.8537 complete). Fairness section updated: closed vs open items separated. No marketing language. No emojis. All facts verified. | 0.840  | v3 (0.871)     |
| 3.3         | Apr 2026 | Pronoun detection corrected: EN/FR F1=1.000, KI pronoun_assumption F1=0.491 / pronoun_generic F1=0.613; SW F1=0.000 is a GT gap not a missing category. Real DP/EO/EOdds/MBE fairness table added. Representation table pronoun row updated. All "not implemented" / "planned Sprint 5" language removed. | 0.840  | v3 (0.871)     |

---

## 11. Update Checklist

- [ ] Lexicon version incremented -- update section 1 entry counts and section 4 metrics
- [ ] run_evaluation.py new metrics -- paste into sections 4.1 through 4.4
- [ ] ML model retrained -- update section 4.5 and JUAKAZI_ML_MODEL default
- [ ] Human annotation batch completed -- update section 3 IAA
- [ ] Human review cycle completed -- update section 6 open items and FI
- [ ] New language added -- update sections 1, 3, 4
- [ ] New limitation discovered -- add to section 5
