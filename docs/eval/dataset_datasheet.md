# JuaKazi Gender Bias Dataset Datasheet

## Overview

This datasheet documents TWO complementary datasets used in the JuaKazi gender bias detection project:
1. **Evaluation Dataset**: Small, manually curated ground truth for F1 scoring
2. **Collection Dataset**: Large-scale online-sourced data for lexicon expansion and training

---

## Dataset 1: Evaluation Ground Truth

**Name**: JuaKazi Gender Bias Evaluation Dataset
**Version**: 1.0
**Creation Date**: October 2024
**Languages**: English (en), Swahili (sw), French (fr), Gikuyu (ki)
**Total Samples**: 50 English samples (initial evaluation set)
**Purpose**: F1 score calculation and model evaluation

### Provenance

**Source**: Manually curated test cases for bias detection evaluation
**Creation Method**: Expert annotation with planted bias examples
**Curators**: JuaKazi development team
**Quality Control**: Manual review of all labels and corrections

---

## Dataset 2: Open-Source Collection Dataset

**Name**: JuaKazi Bias Detection Training & Expansion Dataset
**Version**: 1.0
**Creation Date**: November 13, 2025
**Languages**: English (en) - with Swahili, French, Gikuyu in progress
**Total Samples**: 2,828 English samples collected
**Purpose**: Lexicon expansion, rule development, and training data augmentation

### JuaKazi Team Languages
Per AI BRIDGE assignment:
- **Gikuyu** (ki)
- **French** (fr)
- **English** (en)
- **Swahili** (sw)

### Provenance

**Source**: Open-source bias detection datasets and Wikipedia
**Collection Method**: Automated download and extraction using data collection toolkit
**Curators**: JuaKazi data collection team
**Quality Control**: PII detection and removal, schema validation, source attribution

### Data Sources

| Dataset | Samples | License | Source |
|---------|---------|---------|--------|
| **WinoBias** | 1,584 | MIT | https://github.com/uclanlp/corefBias |
| **WinoGender** | 720 | CC BY 4.0 | https://github.com/rudinger/winogender-schemas |
| **CrowS-Pairs** | 524 | CC BY-SA 4.0 | https://github.com/nyu-mll/crows-pairs |
| **Wikipedia (en)** | 10 (tested) | CC BY-SA 3.0 | en.wikipedia.org |
| **Total English** | **2,828** | | |

**In Progress**:
- Swahili: Wikipedia extraction (target: 300-500 samples)
- French: Wikipedia extraction (target: 300-500 samples)
- Gikuyu: Wikipedia extraction (target: 200-300 samples)

### Collection Methodology

**100% Online Sourcing Strategy**:
1. Download open-source bias datasets (WinoBias, WinoGender, CrowS-Pairs)
2. Extract gender-relevant articles from Wikipedia (4 languages)
3. PII detection and removal (automated)
4. Schema conversion to 40-field standard
5. Double annotation for quality assurance (Cohen's Kappa ≥ 0.70)

**Data Collection Toolkit**: 5 Python scripts (1,637 LOC, zero external dependencies)
- `download_datasets.py`: Download bias datasets
- `extract_wikipedia.py`: Extract from Wikipedia
- `detect_pii.py`: PII detection and removal
- `annotate_samples.py`: Terminal annotation interface
- `track_quality.py`: Quality tracking dashboard

### Schema Compliance

All collected samples conform to the **40-field AI BRIDGE schema**:
- ✅ Core fields: id, language, script, country, source_type, source_ref
- ✅ Bias annotation: target_gender, bias_label, stereotype_category, explicitness
- ✅ Quality assurance: annotator_id, qa_status, cohen_kappa, pii_removed

### Data Quality

**English Collection Dataset**:
- **Bias label balance**: 50% stereotype / 50% counter-stereotype (WinoBias)
- **Pre-labeled samples**: 1,584 (WinoBias)
- **Needs annotation**: 1,244 (WinoGender + CrowS-Pairs)
- **PII detection rate**: 0.3% (8 potential names found and redacted)
- **Schema compliance**: 100%

---

## Evaluation Dataset Composition (Original)

## Dataset Composition

### Sample Distribution
| Language | Total | Biased | Non-biased |
|----------|-------|--------|------------|
| English  | 50    | 25     | 25         |
| Swahili  | TBD   | TBD    | TBD        |
| French   | TBD   | TBD    | TBD        |
| Gikuyu   | TBD   | TBD    | TBD        |

### Bias Categories
- **occupation**: Gendered job titles (chairman, waitress)
- **pronoun_assumption**: Gender assumptions (she is a nurse)
- **pronoun_generic**: Generic masculine pronouns (his records)
- **none**: Non-biased control samples

## Data Schema

**File Format**: CSV with UTF-8 encoding
**Columns**:
- `text`: Input text sample
- `has_bias`: Boolean (true/false)
- `bias_category`: Category label or "none"
- `expected_correction`: Target neutral form

**Example**:
```csv
text,has_bias,bias_category,expected_correction
"The chairman will lead",true,occupation,chairperson
"The table is wooden",false,none,
```

## Ethical Considerations

**Bias Representation**: Focuses on occupational and linguistic bias, not identity-based discrimination
**Cultural Context**: African language examples adapted for regional professional contexts (East and Central Africa)
**Limitations**: Binary gender framework, professional domain focus
**Harm Mitigation**: No personal identifiers or sensitive content

## Intended Use

**Primary Purpose**: Evaluation of gender bias detection systems
**Appropriate Uses**:
- F1 score calculation for bias detection
- Precision/recall analysis by category
- Cross-language performance comparison

**Inappropriate Uses**:
- Training data for ML models (too small)
- Production bias detection (evaluation only)
- Cultural bias analysis beyond professional contexts

## Licensing & Distribution

**License**: Open source compatible (same as project)
**Distribution**: Internal evaluation use
**Attribution**: JuaKazi Gender Sensitization Engine project
**Restrictions**: Evaluation purposes only, not for commercial training

## Maintenance & Updates

**Update Frequency**: As needed based on evaluation gaps
**Version Control**: Git-tracked with project repository
**Quality Assurance**: Manual review of new samples
**Expansion Plan**: Add categories based on failure analysis

## Known Limitations

**Coverage**: Limited to 4 bias categories
**Scale**: Small sample size (50 English samples, other JuaKazi languages in progress)
**Domain**: Professional/occupational bias focus
**Language Variety**: Standard varieties only (English, Swahili, French, Gikuyu)
**Temporal**: Static snapshot, no temporal bias evolution

## Contact & Support

**Maintainer**: JuaKazi development team
**Issues**: Report via project repository
**Updates**: Track via Jira