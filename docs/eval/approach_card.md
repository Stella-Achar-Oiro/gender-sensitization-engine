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

### Evaluation Results (Oct 25, 2024)
| Language | Precision | Recall | F1 Score |
|----------|-----------|--------|----------|
| English  | 1.000     | 0.680  | 0.810    |
| Swahili  | 1.000     | 0.600  | 0.750    |
| Hausa    | 1.000     | 0.640  | 0.780    |
| Igbo     | 1.000     | 0.520  | 0.684    |
| Yoruba   | 1.000     | 0.880  | 0.936    |

### Analysis
**Strengths**: Perfect precision (no false positives)
**Limitations**: Low recall indicates rule coverage gaps
**Priority**: Expand lexicon coverage for higher recall

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