# Kikuyu v6 Dataset - With Bible Corpus

**Date**: 2026-02-05
**Version**: v6
**Total Samples**: 5,507 (+307 from v5)
**Schema**: 27 fields (AI BRIDGE compliant)
**License**: CC BY 4.0

---

## What's New in v6

✅ **Added 307 Bible verses** with occupation terms and gender context
✅ **Increased sample count** from 5,200 to 5,507 (+5.9%)
✅ **Progress to Gold tier**: 55.1% (10,000 target)
✅ **New data source**: Bible corpus (Biblica® 2013, CC BY-SA 4.0)

---

## Source Distribution

| Source | Samples | % | URL | Status |
|--------|---------|---|-----|--------|
| **Scripted Templates** | 4,458 | 81.0% | [generate_test_templates.py](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/main/scripts/data_collection/generate_test_templates.py) | ✅ Fully annotated |
| **Bible** | 307 | 5.6% | https://eBible.org/Scriptures/kik_readaloud.zip | ⚠️ Awaiting annotation |
| **Synthetic** | 302 | 5.5% | [ground_truth_ki_v4.csv](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/main/eval/ground_truth_ki_v4.csv) | ✅ Fully annotated |
| **News** | 182 | 3.3% | https://nation.africa/kenya/news/politics | ✅ Annotated |
| **Government** | 61 | 1.1% | https://nation.africa/kenya/news/politics | ✅ Annotated |
| **Corporate** | 52 | 0.9% | https://www.businessdailyafrica.com | ✅ Annotated |
| **Education** | 41 | 0.7% | https://ki.wikipedia.org/wiki/ | ✅ Annotated |
| **Healthcare** | 26 | 0.5% | https://www.health.go.ke | ✅ Annotated |
| **Social Media** | 18 | 0.3% | https://x.com | ✅ Annotated |
| **Agriculture** | 17 | 0.3% | https://www.kalro.org | ✅ Annotated |
| **Legal** | 14 | 0.3% | https://www.judiciary.go.ke | ✅ Annotated |
| **Job Listing** | 7 | 0.1% | https://www.brightermonday.co.ke | ✅ Annotated |
| **Financial** | 7 | 0.1% | https://www.centralbank.go.ke | ✅ Annotated |
| **Domestic** | 4 | 0.1% | [ground_truth_ki_v4.csv](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/main/eval/ground_truth_ki_v4.csv) | ✅ Annotated |
| **Technology** | 3 | 0.1% | [ground_truth_ki_v4.csv](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/main/eval/ground_truth_ki_v4.csv) | ✅ Annotated |
| **Health** | 3 | 0.1% | https://www.health.go.ke | ✅ Annotated |
| **Sports** | 2 | 0.0% | https://nation.africa/kenya/sports | ✅ Annotated |
| **Arts** | 2 | 0.0% | https://nation.africa/kenya/life-and-style | ✅ Annotated |
| **Law** | 1 | 0.0% | https://www.judiciary.go.ke | ✅ Annotated |

**Total**: 5,507 samples across 19 source types

---

## Bible Corpus Details

**Translation**: Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre (2013)
**Download**: https://eBible.org/Scriptures/kik_readaloud.zip
**License**: Creative Commons Attribution-ShareAlike 4.0
**Extraction**: 2026-02-05

### Selection Criteria

From 794 extracted Bible verses, selected **307 high-priority verses**:
- ✅ All verses with occupation terms AND gender context (pronouns/gender markers)
- ✅ Covers all 66 Bible books (Genesis to Revelation)
- ✅ Multiple occupation types: priests (mũthĩnjĩri), leaders (mũtongoria), teachers (mũrutani), shepherds (mũrĩithi), managers (mũrũgamĩrĩri)

### Top Occupation Terms in Bible Samples

| Term | Count | Translation |
|------|-------|-------------|
| mũthĩnjĩri | 167 | priest/minister |
| mũtongoria | 51 | leader |
| mũrutani | 29 | teacher |
| mũrĩithi | 23 | shepherd |
| mũrũgamĩrĩri | 18 | manager/overseer |

### Sample Bible Verses

**Genesis 4:3** (farmer + shepherd + gender pronouns):
```
Thuutha ũcio agĩciara Habili, mũrũ wa nyina. 
Habili aarĩ mũrĩithi wa mbũri nake Kaini aarĩ mũrĩmi.
```
- Occupation terms: mũrĩithi (shepherd), mũrĩmi (farmer)
- Gender context: pronouns present
- Verse reference: GEN_4_3

**Genesis 14:19** (priest + pronouns):
```
Nake Melikisedeki mũthamaki wa Salemu akĩrehe mĩgate na ndibei. 
We aarĩ mũthĩnjĩri wa Mũrungu Ũrĩa-ũrĩ-Igũrũ-Mũno.
```
- Occupation term: mũthĩnjĩri (priest)
- Gender context: "We" (he)
- Verse reference: GEN_14_19

---

## Annotation Status

### Fully Annotated (5,200 samples - 94.4%)
- All v5 samples have complete bias annotations
- Multi-annotator validation: 14.3% (744 samples)
- Cohen's Kappa: Available for multi-annotated samples

### Awaiting Annotation (307 samples - 5.6%)
- Bible verses added in v6
- Marked as `NEEDS_ANNOTATION` in bias fields
- `has_bias`, `bias_category`, `expected_correction`: To be determined
- `severity`, `explicitness`: To be assessed
- `annotator_id`: Currently "PENDING"

### Next Annotation Steps

1. **Manual Review** (Est. 10-15 hours):
   - Review 307 Bible verses for gender bias
   - Determine which verses contain implicit/explicit bias
   - Identify neutral corrections

2. **Annotation** (Est. 20-30 hours total):
   - Single annotator: ~5-6 minutes per sample
   - 307 samples × 6 min = ~30 hours

3. **Multi-Annotator Validation** (Optional, +10 hours):
   - Second annotator for 30% overlap (92 samples)
   - Calculate Cohen's Kappa
   - Reach Bronze tier multi-annotator requirement (10%)

---

## AI BRIDGE Compliance

| Metric | Requirement | Current | Status |
|--------|-------------|---------|--------|
| **Sample Size** | ≥1,200 (Bronze) | 5,507 | ✅ 459% |
| **Multi-Annotator** | ≥10% (Bronze) | 14.3% (744) | ✅ 143% |
| **F1 Score** | ≥0.75 (Bronze) | 0.999 | ✅ Gold |
| **Fairness (DP)** | ≤0.10 (Bronze) | 0.000 | ✅ Gold |
| **Fairness (EO)** | ≤0.05 (Bronze) | 0.000 | ✅ Gold |
| **Schema** | 24 fields | 27 fields | ✅ 113% |

**Overall**: v6 maintains Gold tier technical performance, pending annotation of new Bible samples

---

## Files

```
eval/
├── ground_truth_ki_v5.csv (5,200 samples, 2.23 MB) - Previous version
├── ground_truth_ki_v6.csv (5,507 samples, 2.72 MB) - NEW with Bible
└── ...

data/raw/
├── kikuyu_bible/ (1,190 chapter files)
├── kikuyu_bible_extracted.csv (794 verses, 244 KB)
└── ...

scripts/data_collection/
├── extract_bible_verses.py (extraction tool)
├── merge_bible_to_v5.py (merge tool)
└── annotate_samples.py (annotation interface)

docs/eval/
├── KIKUYU_V6_SUMMARY.md (this file)
├── KIKUYU_BIBLE_DOWNLOADED.md (download summary)
├── KIKUYU_BIBLE_EXTRACTION_COMPLETE.md (extraction summary)
└── ...
```

---

## Progress to Gold Tier (10,000 samples)

**Current**: 5,507 samples (55.1% to Gold)
**Still needed**: 4,493 samples

### Potential Additional Sources

1. **More Bible verses** (+487 available):
   - Occupation-only verses (without explicit gender context)
   - Would bring total to 5,994 (59.9% to Gold)

2. **Twitter** (+500-1,000):
   - Requires API setup
   - Estimated yield: 500-1,000 samples

3. **Google Waxal** (+500-1,500):
   - Speech transcriptions
   - Just launched Feb 2026

4. **Wikipedia expansion** (+200-500):
   - More articles
   - Biographies, occupations

**Estimated timeline to 10,000**: 8-12 weeks with multi-source collection

---

## Citation

```bibtex
@misc{juakazi2026kikuyu_v6,
  author = {{JuaKazi Team} and Nene, David and Oiro, Stella},
  title = {JuaKazi Kikuyu Gender Bias Detection Ground Truth v6},
  year = {2026},
  publisher = {GitLab},
  url = {https://gitlab.com/juakazike/gender-sensitization-engine},
  note = {5,507 samples including 307 Bible verses, AI BRIDGE compliant}
}
```

---

## Contact

**David Nene** (Primary Annotator): davienesh4@gmail.com
**Stella Oiro** (Project Lead)

**Repository**: https://gitlab.com/juakazike/gender-sensitization-engine
**Dataset File**: `eval/ground_truth_ki_v6.csv`

---

**Last Updated**: 2026-02-05
**Status**: Bible samples awaiting annotation, otherwise complete
**Next Action**: Annotate 307 Bible verses for bias detection
