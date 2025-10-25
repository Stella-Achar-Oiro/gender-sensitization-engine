# JuaKazi Ground Truth Dataset Datasheet

## Dataset Overview

**Name**: JuaKazi Gender Bias Evaluation Dataset
**Version**: 1.0
**Creation Date**: October 2024
**Languages**: English (en), Swahili (sw)
**Total Samples**: 100 (50 per language)

## Provenance

**Source**: Manually curated test cases for bias detection evaluation
**Creation Method**: Expert annotation with planted bias examples
**Curators**: JuaKazi development team
**Quality Control**: Manual review of all labels and corrections

## Dataset Composition

### Sample Distribution
| Language | Total | Biased | Non-biased |
|----------|-------|--------|------------|
| English  | 50    | 25     | 25         |
| Swahili  | 50    | 25     | 25         |

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
**Cultural Context**: Swahili examples adapted for East African professional contexts
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
**Scale**: Small sample size (50 per language)
**Domain**: Professional/occupational bias focus
**Language Variety**: Standard English/Swahili only
**Temporal**: Static snapshot, no temporal bias evolution

## Contact & Support

**Maintainer**: JuaKazi development team
**Issues**: Report via project repository
**Updates**: Track via ENGINEERING_TASKS.md