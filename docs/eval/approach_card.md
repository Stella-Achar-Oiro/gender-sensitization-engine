# JuaKazi Gender Bias Detection Approach Card

## Problem Framing

**Objective**: Detect and correct gender bias in African language text (English, Swahili, Hausa, Igbo, Yoruba) with focus on occupational and linguistic bias patterns.

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

### Cross-Language Strategy
**Per-language lexicons** with shared evaluation framework
- English: 515 occupational/pronoun rules
- Swahili: 15 culturally-adapted rules
- Hausa: 22 culturally-adapted rules
- Igbo: 20 culturally-adapted rules
- Yoruba: 20 culturally-adapted rules
- Independent rule sets to preserve linguistic accuracy

**Trade-off Rationale**: Language-specific rules over shared model to maintain semantic precision and cultural context.

## Current Performance

### Detection Results (Oct 28, 2025 - Enhanced Ground Truth)
| Language | Precision | Recall | F1 Score | Status |
|----------|-----------|--------|----------|---------|
| English  | 1.000     | 0.618  | 0.764    | Good |
| Swahili  | 1.000     | 0.516  | 0.681    | Moderate |
| Hausa    | 1.000     | 0.640  | 0.780    | Good |
| Igbo     | 1.000     | 0.520  | 0.684    | Moderate |
| Yoruba   | 1.000     | 0.880  | 0.936    | Excellent |

### Correction Effectiveness (Pre→Post Comparison)
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Effective |
| Swahili  | 51.6%         | 12.5%             | Needs Work |
| Hausa    | 64.0%         | 68.8%             | Moderate |
| Igbo     | 52.0%         | 69.2%             | Moderate |
| Yoruba   | 88.0%         | 77.3%             | Effective |

**Key Finding:** English achieves 100% bias removal rate - all detected biases successfully neutralized. Yoruba strong at 77.3%. Swahili requires significant lexicon expansion (12.5% removal rate indicates gaps).

### Analysis
**Strengths**:
- Perfect precision (1.000) - zero false positives across all languages
- English correction: 100% bias removal (all detected→neutralized)
- Yoruba: Excellent detection (88%) and correction (77.3%)
- No over-corrections detected (preserves non-biased text)

**Limitations**:
- Recall gaps indicate lexicon coverage needs expansion
- Swahili correction needs improvement (12.5% removal rate)
- African language test sets may need more complexity
- Generic pronoun category shows zero detection in English/Swahili

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

## Evaluation Protocol

**Metrics**: Precision, Recall, F1-score per language and bias category
**Ground Truth**: 50 manually labeled test cases per language (250 total across 5 languages)
**Reproducibility**: `python eval/run_evaluation.py`

**Failure Analysis**: Track false negatives to identify rule gaps
**Improvement Path**: Iterative lexicon expansion based on failure cases
**Baseline Comparison**: Simple keyword detector achieves F1 0.438-1.000; our approach shows +0.312 improvement for Swahili, mixed results for other African languages
**Ablation Studies**: Component analysis shows lexicon expansion drives gains in English/Swahili; African languages may benefit from simpler approaches