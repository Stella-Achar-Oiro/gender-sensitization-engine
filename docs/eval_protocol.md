# JuaKazi Evaluation Protocol

## Overview

Standardized evaluation framework for gender bias detection performance measurement across English and Swahili languages.

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
**Per-Language**: Separate evaluation for English and Swahili

## Ground Truth Data

**Location**: `eval/ground_truth_{lang}.csv`
**Format**: CSV with columns: text, has_bias, bias_category, expected_correction
**Size**: 50 samples per language (25 biased, 25 non-biased)

## Evaluation Procedure

### Step 1: Environment Setup
```bash
cd /path/to/gender-sensitization-engine
```

### Step 2: Run Evaluation
```bash
python3 eval/run_evaluation.py
```

### Step 3: Review Results
- Console output shows overall F1 scores
- Detailed CSV report saved to `eval/results/f1_report_TIMESTAMP.csv`

## Output Format

### Console Output
```
Running bias detection evaluation...
Evaluating en...
EN Results:
  Overall F1: 0.214
  Precision: 1.000
  Recall: 0.120

Evaluating sw...
SW Results:
  Overall F1: 0.077
  Precision: 1.000
  Recall: 0.040

Report saved to: eval/results/f1_report_20241025_120518.csv
```

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
- `eval/ground_truth_en.csv` - English test cases
- `eval/ground_truth_sw.csv` - Swahili test cases  
- `rules/lexicon_en_v2.csv` - English bias rules
- `rules/lexicon_sw_v2.csv` - Swahili bias rules

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
- **High Precision (>0.9)**: Low false positive rate, conservative detection
- **Low Recall (<0.2)**: Missing many biased cases, needs rule expansion
- **Balanced F1 (>0.5)**: Good overall performance target

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