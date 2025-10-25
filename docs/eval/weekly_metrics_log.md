# Weekly Metrics Log

## Week of October 25, 2024

### Overall Performance Summary
| Language | Overall F1 | Precision | Recall | Status |
|----------|------------|-----------|--------|---------|
| English  | 0.810      | 1.000     | 0.680  | Good |
| Swahili  | 0.750      | 1.000     | 0.600  | Moderate |
| Hausa    | 0.780      | 1.000     | 0.640  | Moderate |
| Igbo     | 0.684      | 1.000     | 0.520  | Needs Work |
| Yoruba   | 0.936      | 1.000     | 0.880  | Excellent |

### Performance by Bias Category

#### English
| Category | Precision | Recall | F1 Score | Notes |
|----------|-----------|--------|----------|-------|
| occupation | 1.000 | 0.941 | 0.970 | Strong performance |
| pronoun_assumption | 1.000 | 0.200 | 0.333 | Low recall - expand rules |
| pronoun_generic | 0.000 | 0.000 | 0.000 | Missing coverage |

#### Swahili  
| Category | Precision | Recall | F1 Score | Notes |
|----------|-----------|--------|----------|-------|
| occupation | 1.000 | 0.824 | 0.903 | Good coverage |
| pronoun_assumption | 1.000 | 0.200 | 0.333 | Limited rules |
| pronoun_generic | 0.000 | 0.000 | 0.000 | No coverage |

#### Hausa
| Category | Precision | Recall | F1 Score | Notes |
|----------|-----------|--------|----------|-------|
| occupation | 1.000 | 0.550 | 0.710 | Moderate coverage |
| pronoun_generic | 1.000 | 1.000 | 1.000 | Perfect on limited samples |

#### Igbo
| Category | Precision | Recall | F1 Score | Notes |
|----------|-----------|--------|----------|-------|
| occupation | 1.000 | 0.450 | 0.621 | Low coverage |
| pronoun_generic | 1.000 | 0.800 | 0.889 | Good performance |

#### Yoruba
| Category | Precision | Recall | F1 Score | Notes |
|----------|-----------|--------|----------|-------|
| occupation | 1.000 | 0.850 | 0.919 | Excellent coverage |
| pronoun_generic | 1.000 | 1.000 | 1.000 | Perfect performance |

### Key Insights
1. **Perfect Precision**: All languages achieve 1.000 precision - no false positives
2. **Recall Gaps**: Main limitation is rule coverage, especially for pronoun categories
3. **Language Variation**: Yoruba performs best, Igbo needs most improvement
4. **Category Gaps**: pronoun_generic completely missing in English/Swahili

### Action Items for Next Week
1. Add pronoun_generic rules for English and Swahili
2. Expand occupation lexicons for Igbo and Hausa
3. Improve pronoun_assumption coverage across all languages
4. Target: +0.1 F1 improvement per language