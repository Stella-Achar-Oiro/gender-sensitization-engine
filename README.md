# JuaKazi Gender Sensitization Engine

Gender bias detection and correction system for African languages with comprehensive F1 evaluation framework.

## Supported Languages
- **English** (F1: 0.764, Correction: 100% bias removal)
- **Swahili** (F1: 0.681, Correction: 12.5% bias removal)
- **Hausa** (F1: 0.780, Correction: 68.8% bias removal)
- **Igbo** (F1: 0.684, Correction: 69.2% bias removal)
- **Yoruba** (F1: 0.936, Correction: 77.3% bias removal)

**Total Coverage**: 158M+ African language speakers

**Latest Update (Oct 28, 2025):** Enhanced ground truth with diverse test cases, added correction effectiveness evaluation

## Quick Start

### Run Full Evaluation
```bash
python3 run_evaluation.py
```

### Run Baseline Comparison
```bash
cd eval && python3 baseline_simple.py
```

### Run Correction Evaluation (Pre→Post)
```bash
python3 eval/correction_evaluator.py
```

### Test Individual Language
```bash
python3 -c "
from eval.bias_detector import BiasDetector
from eval.models import Language
detector = BiasDetector()
result = detector.detect_bias('The chairman will lead', Language.ENGLISH)
print('Has bias:', result.has_bias_detected)
print('Edits:', result.detected_edits)
"
```

## Performance Summary

### Detection Performance
| Language | F1 Score | Precision | Recall | Status |
|----------|----------|-----------|--------|---------|
| English  | 0.764    | 1.000     | 0.618  | Good |
| Swahili  | 0.681    | 1.000     | 0.516  | Moderate |
| Hausa    | 0.780    | 1.000     | 0.640  | Good |
| Igbo     | 0.684    | 1.000     | 0.520  | Moderate |
| Yoruba   | 0.936    | 1.000     | 0.880  | Excellent |

### Correction Effectiveness (Pre→Post Bias Removal)
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Excellent |
| Swahili  | 51.6%         | 12.5%             | Needs Work |
| Hausa    | 64.0%         | 68.8%             | Moderate |
| Igbo     | 52.0%         | 69.2%             | Moderate |
| Yoruba   | 88.0%         | 77.3%             | Good |

**Key Achievements**:
- Perfect precision (1.000) across all languages - zero false positives
- English: 100% bias removal rate (all detected biases successfully corrected)
- Enhanced ground truth with diverse, complex test cases

## Project Structure

```
├── eval/                    # Evaluation framework
│   ├── run_evaluation.py   # Main evaluation script
│   ├── correction_evaluator.py # Pre→post correction analysis
│   ├── ablation_study.py   # Component contribution analysis
│   ├── baseline_simple.py  # Baseline comparison
│   ├── ground_truth_*.csv  # Test datasets (50+ samples each)
│   └── results/            # Evaluation outputs
├── rules/                  # Bias detection lexicons
│   ├── lexicon_en_v2.csv  # English rules (515 terms)
│   ├── lexicon_sw_v2.csv  # Swahili rules (15 terms)
│   ├── lexicon_ha_v2.csv  # Hausa rules (22 terms)
│   ├── lexicon_ig_v2.csv  # Igbo rules (20 terms)
│   └── lexicon_yo_v2.csv  # Yoruba rules (20 terms)
└── docs/                   # Documentation
    ├── approach_card.md    # Technical methodology
    ├── dataset_datasheet.md # Ground truth documentation
    └── eval_protocol.md    # Evaluation procedures
```

## Requirements

- Python 3.x (standard library only)
- No external dependencies required

## Documentation

### Required Deliverables
- **[Approach Card](docs/eval/approach_card.md)** - Technical methodology + correction effectiveness
- **[Dataset Datasheet](docs/eval/dataset_datasheet.md)** - Ground truth documentation and ethics
- **[Evaluation Protocol](docs/eval/eval_protocol.md)** - Reproducible evaluation procedures
- **[Failure Case Log](docs/eval/failure_case_log.md)** - Systematic improvement tracking
- **[Weekly Metrics Log](docs/eval/weekly_metrics_log.md)** - Performance tracking by category
- **[Literature Review](docs/eval/literature_review_notes.md)** - Key insights from research

### Additional Analysis
- **[Ablation Study](docs/eval/ablation_results.md)** - Component contribution analysis
- **[Baseline Comparison](docs/eval/baseline_comparison.md)** - Baseline vs full approach

## Key Features

- **Zero False Positives**: Perfect precision across all languages
- **Culturally Adapted**: Language-specific lexicons with regional context
- **Systematic Evaluation**: Comprehensive F1 framework with failure analysis
- **Baseline Validated**: Outperforms simple keyword detection
- **Comprehensive Evaluation**: All languages evaluated with F1 > 0.5 threshold

## Usage Examples

### Detection
```python
from eval.bias_detector import BiasDetector
from eval.models import Language

detector = BiasDetector()

# English
result = detector.detect_bias("The chairman will lead", Language.ENGLISH)
print(result.has_bias_detected)  # True
print(result.detected_edits)     # [{'from': 'chairman', 'to': 'chair', 'severity': 'replace'}]

result = detector.detect_bias("The table is wooden", Language.ENGLISH)
print(result.has_bias_detected)  # False
```

### Correction
```python
# English
result = detector.correct_bias("The chairman will lead", Language.ENGLISH)
print(result.get('corrected_text'))  # Returns corrected version if available

# Note: Correction functionality depends on implementation
```

## Evaluation Results

Latest evaluation run shows consistent performance:
- **250 ground truth samples** (50 per language)
- **Perfect precision** maintained across all languages
- **Systematic improvement** process validated (Swahili: 0.077 → 0.750)
- **Cross-language framework** proven scalable

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

Open source - see project license for details.