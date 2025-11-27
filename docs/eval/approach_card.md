# JuaKazi Gender Bias Detection Approach Card

## Problem Framing

**Objective**: Detect and correct gender bias in African language text (JuaKazi languages: English, Swahili, French, Gikuyu) with focus on occupational and linguistic bias patterns.

**Target Bias Categories**:
- Occupational terms (chairman → chairperson)
- Generic pronouns (his records → their records) 
- Gendered assumptions (she is a nurse → they are a nurse)
- Morphological gender markers (waitress → server)

**Scope**: Text-level bias detection and neutralization for content moderation and inclusive writing assistance.

## Methodology

### Detection Architecture
**Primary Engine**: Rules-based lexicon matching
- Curated bias terms per language (varying coverage)
- Regex pattern matching with word boundaries
- Case-insensitive detection with case preservation

**Fallback Engine**: ML-based correction (mT5-small)
- Activated when zero rule matches found
- Generates alternative phrasings for complex bias cases

### Rule Structure
```
biased_term → neutral_primary
chairman → chairperson
policeman → police officer
```

**Linguistic Features**:
- Word boundary detection (`\b` regex)
- Case preservation (Chairman → Chairperson)
- Severity levels (replace, warn)

### Cross-Language Strategy (JuaKazi)
**Per-language lexicons** with shared evaluation framework
- English: 515 occupational/pronoun rules
- Swahili: 15 culturally-adapted rules
- French: TBD (in development)
- Gikuyu: TBD (in development)
- Independent rule sets to preserve linguistic accuracy

**Trade-off Rationale**: Language-specific rules over shared model to maintain semantic precision and cultural context.

## Current Performance

### Detection Results (JuaKazi Languages)
| Language | Precision | Recall | F1 Score | Status |
|----------|-----------|--------|----------|---------|
| English  | 1.000     | 0.618  | 0.764    | Good |
| Swahili  | 1.000     | 0.516  | 0.681    | Moderate |
| French   | TBD       | TBD    | TBD      | In Progress |
| Gikuyu   | TBD       | TBD    | TBD      | In Progress |

### Correction Effectiveness (Pre→Post Comparison)
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Effective |
| Swahili  | 51.6%         | 12.5%             | Needs Work |
| French   | TBD           | TBD               | In Progress |
| Gikuyu   | TBD           | TBD               | In Progress |

**Key Finding:** English achieves 100% bias removal rate - all detected biases successfully neutralized. Swahili requires significant lexicon expansion (12.5% removal rate indicates gaps). French and Gikuyu data collection and evaluation in progress.

### Analysis
**Strengths**:
- Perfect precision (1.000) - zero false positives across evaluated languages
- English correction: 100% bias removal (all detected→neutralized)
- No over-corrections detected (preserves non-biased text)

**Limitations**:
- Recall gaps indicate lexicon coverage needs expansion
- Swahili correction needs improvement (12.5% removal rate)
- JuaKazi language test sets may need more complexity
- Generic pronoun category shows zero detection in English/Swahili
- French and Gikuyu lexicons and evaluations in development

**Priority Actions**:
1. Expand Swahili correction lexicon urgently
2. Add generic pronoun rules for English/Swahili
3. Improve recall while maintaining perfect precision
4. Validate correction naturalness with native speakers

## Assumptions & Constraints

**Linguistic Assumptions**:
- Bias primarily manifests in occupational terms and pronouns
- Word-level replacement preserves semantic meaning
- Context-independent detection sufficient for most cases

**Technical Constraints**:
- Rules-based approach limits to explicit term matching
- No syntactic or contextual analysis
- Manual lexicon curation required for coverage expansion

**Ethical Considerations**:
- Neutralization may lose cultural/historical context
- Binary gender assumptions in current rule set
- Focus on professional contexts over personal identity

## Data Collection Methodology (JuaKazi Team)

### Team Assignment
**Languages**: Gikuyu (ki), French (fr), English (en), Swahili (sw)
**Strategy**: 100% online sourcing from open-source datasets and Wikipedia

### Collection Approach
1. **Download bias datasets**: WinoBias (MIT), WinoGender (CC BY 4.0), CrowS-Pairs (CC BY-SA 4.0)
2. **Extract from Wikipedia**: Gender-relevant articles across 4 languages
3. **PII detection**: Automated removal of personally identifiable information
4. **Schema conversion**: Map all data to 40-field AI BRIDGE standard
5. **Quality assurance**: Double annotation for Cohen's Kappa ≥ 0.70

### Data Collection Toolkit
**5 Python scripts** (1,637 LOC, zero external dependencies):
- `download_datasets.py`: Download open-source bias datasets
- `extract_wikipedia.py`: Extract from Wikipedia (multi-language)
- `detect_pii.py`: PII detection and removal
- `annotate_samples.py`: Terminal annotation interface
- `track_quality.py`: Quality tracking dashboard

### Collection Results
**Total Collected**: 3,011 samples
- English: 2,838 samples (236% of Bronze target)
- French: 135 samples
- Swahili: 37 samples
- Gikuyu: 1 sample (limited online availability)

**Data Quality**:
- Schema compliance: 100% (40 fields)
- PII detection rate: 0.3% (all redacted)
- Pre-labeled: 1,584 samples (52.6%)
- Bias balance: 50% stereotype / 50% counter-stereotype

See `docs/eval/DATA_COLLECTION_REPORT.md` for complete details.

---

## Evaluation Protocol

**Metrics**: Precision, Recall, F1-score per language and bias category
**Ground Truth**: 50 manually labeled test cases per language (250 total across 5 languages)
**Reproducibility**: `python eval/run_evaluation.py`

**Failure Analysis**: Track false negatives to identify rule gaps
**Improvement Path**: Iterative lexicon expansion based on failure cases
**Baseline Comparison**: Simple keyword detector achieves F1 0.438-1.000; our approach shows +0.312 improvement for Swahili, mixed results for other African languages
**Ablation Studies**: Component analysis shows lexicon expansion drives gains in English/Swahili; African languages may benefit from simpler approaches