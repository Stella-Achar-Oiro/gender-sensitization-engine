# Weekly Metrics Log

## Week of October 28, 2025 (LATEST - Post Ground Truth Enhancement)

### Overall Performance Summary
| Language | Overall F1 | Precision | Recall | Status |
|----------|------------|-----------|--------|---------|
| English  | 0.764      | 1.000     | 0.618  | Good |
| Swahili  | 0.681      | 1.000     | 0.516  | Moderate |
| Hausa    | 0.780      | 1.000     | 0.640  | Good |
| Igbo     | 0.684      | 1.000     | 0.520  | Moderate |
| Yoruba   | 0.936      | 1.000     | 0.880  | Excellent |

**Note:** F1 scores decreased slightly (English: -0.046, Swahili: -0.069) due to enhanced ground truth with more diverse, challenging test cases. This represents more honest evaluation.

### Correction Effectiveness (NEW - Pre→Post Analysis)
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Excellent |
| Swahili  | 51.6%         | 12.5%             | Urgent Work Needed |
| Hausa    | 64.0%         | 68.8%             | Moderate |
| Igbo     | 52.0%         | 69.2%             | Moderate |
| Yoruba   | 88.0%         | 77.3%             | Good |

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
1. **Perfect Precision Maintained**: All languages achieve 1.000 precision - zero false positives
2. **English Correction Excellence**: 100% bias removal rate (all detected biases neutralized)
3. **Swahili Needs Urgent Attention**: 12.5% removal rate indicates major lexicon gaps
4. **Ground Truth Quality**: Enhanced with diverse samples, reduced repetitive patterns
5. **Honest Metrics**: Slightly lower F1 scores reflect more challenging evaluation
6. **Category Gaps**: pronoun_generic still missing in English/Swahili

### Action Items for Next Week
1. **URGENT:** Expand Swahili correction lexicon (12.5% → target 60%+)
2. Add pronoun_generic rules for English and Swahili
3. Continue recall improvement while maintaining perfect precision
4. Validate African language corrections with native speakers
5. Target: +0.1 F1 improvement per language + correction rate improvements