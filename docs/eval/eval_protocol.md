# JuaKazi Evaluation Protocol

## Overview

Standardized evaluation framework for gender bias detection performance measurement across English, Swahili, French, and Gikuyu languages.

## Metrics Definitions

### Primary Metrics

**Precision**: `TP / (TP + FP)`
- True Positives: Correctly identified biased text
- False Positives: Non-biased text incorrectly flagged

**Recall**: `TP / (TP + FN)`  
- True Positives: Correctly identified biased text
- False Negatives: Biased text missed by detector

**F1-Score**: `2 * (Precision * Recall) / (Precision + Recall)`
- Harmonic mean balancing precision and recall

### Reporting Structure

**Overall Performance**: Aggregate metrics across all test samples
**Per-Category**: Metrics broken down by bias type (occupation, pronoun_assumption, etc.)
**Per-Language**: Separate evaluation for English, Swahili, French, and Gikuyu

## Ground Truth Data

**Location**: `eval/ground_truth_{lang}.csv` where lang = en, sw, fr, ki
**Format**: CSV with columns: text, has_bias, bias_category, expected_correction
**Size**: 216 total test samples across 4 languages

| Language | Test Samples | Biased | Neutral | Status |
|----------|-------------|--------|---------|--------|
| English  | 67 samples  | 42     | 25      | Production |
| Swahili  | 64 samples  | 33     | 31      | Foundation |
| French   | 50 samples  | 35     | 15      | Beta |
| Gikuyu   | 35 samples  | 18     | 17      | Beta |

## Evaluation Procedure

### Step 1: Environment Setup
```bash
cd /path/to/gender-sensitization-engine
```

### Step 2: Run Evaluation
```bash
python3 run_evaluation.py
```

### Step 3: Review Results
- Console output shows overall F1 scores
- Detailed CSV report saved to `eval/results/f1_report_TIMESTAMP.csv`

## Output Format

### Console Output (Nov 20, 2025)
```
Running bias detection evaluation...
Evaluating en...
EN Results:
  Overall F1: 0.764
  Precision: 1.000
  Recall: 0.618

Evaluating sw...
SW Results:
  Overall F1: 0.681
  Precision: 1.000
  Recall: 0.516

Evaluating fr...
FR Results:
  Overall F1: 0.627
  Precision: 1.000
  Recall: 0.457

Evaluating ki...
KI Results:
  Overall F1: 0.714
  Precision: 1.000
  Recall: 0.556

Report saved to: eval/results/f1_report_20251120_215337.csv
```

**Key Achievement:** All 4 languages achieve perfect precision (1.000) - zero false positives.

### Correction Evaluation
Run pre→post bias removal analysis:
```bash
python3 eval/correction_evaluator.py
```

Output includes:
- Detection rate (% of biased samples detected)
- Bias removal rate (% of detected biases successfully corrected)
- Quality metrics (meaning preservation, over-corrections)
- Example corrections with before/after text

### CSV Report Structure
| Language | Category | Precision | Recall | F1_Score | TP | FP | FN | TN |
|----------|----------|-----------|--------|----------|----|----|----|----|
| en       | OVERALL  | 1.000     | 0.120  | 0.214    | 3  | 0  | 22 | 25 |
| en       | occupation| 1.000     | 0.150  | 0.261    | 2  | 0  | 11 | 0  |

## Reproducibility Requirements

### Dependencies
- Python 3.x (standard library only)
- No external packages required for evaluation

### File Dependencies
- `eval/ground_truth_en.csv` - English test cases (67 samples)
- `eval/ground_truth_sw.csv` - Swahili test cases (64 samples)
- `eval/ground_truth_fr.csv` - French test cases (50 samples)
- `eval/ground_truth_ki.csv` - Gikuyu test cases (35 samples)
- `rules/lexicon_en_v2.csv` - English bias rules (514 entries)
- `rules/lexicon_sw_v2.csv` - Swahili bias rules (15 terms)
- `rules/lexicon_fr_v2.csv` - French bias rules (51 terms)
- `rules/lexicon_ki_v2.csv` - Gikuyu bias rules (22 terms)

### Expected Runtime
- Total execution: <30 seconds
- Per-language evaluation: <15 seconds

## Quality Assurance

### Validation Checks
- Ground truth files exist and are readable
- All required columns present in datasets
- No missing or malformed labels
- Consistent category naming across languages

### Error Handling
- Missing rule files: Returns empty results with warning
- Malformed CSV: Skips invalid rows, continues evaluation
- Empty datasets: Reports zero metrics with explanation

## Interpretation Guidelines

### Performance Benchmarks
- **Perfect Precision (1.000)**: Achieved across all 4 languages - zero false positives
- **Moderate Recall (0.45-0.62)**: Varies by lexicon maturity
- **F1 Target (>0.60)**: English (0.764), Gikuyu (0.714), Swahili (0.681), French (0.627)

### Common Issues
- **Perfect Precision, Low Recall**: Rule coverage gaps
- **Low Precision**: Rules too broad, catching non-biased text
- **Zero F1**: No rule matches found, check rule file paths

## Failure Analysis

### Manual Review Process
1. Identify false negatives from evaluation output
2. Examine missed bias cases for pattern recognition
3. Determine if new rules needed or existing rules insufficient
4. Document findings for rule expansion

### Systematic Improvement
- Track failure patterns across evaluation runs
- Prioritize rule additions based on frequency of missed cases
- Re-evaluate after rule updates to measure improvement

## Version Control

**Evaluation Scripts**: Track changes to `eval/run_evaluation.py`
**Ground Truth**: Version control test datasets for consistency
**Results**: Archive evaluation reports with timestamps
**Documentation**: Update protocol as methodology evolves