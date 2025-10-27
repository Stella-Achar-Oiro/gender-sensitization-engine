# JuaKazi Gender Sensitization Engine

Gender bias detection and correction system for African languages with comprehensive F1 evaluation framework.

## Supported Languages
- **English** (F1: 0.810)
- **Swahili** (F1: 0.750) 
- **Hausa** (F1: 0.780)
- **Igbo** (F1: 0.684)
- **Yoruba** (F1: 0.936)

**Total Coverage**: 158M+ African language speakers

## Quick Start

### Run Full Evaluation
```bash
python3 run_evaluation.py
```

### Run Baseline Comparison
```bash
cd eval && python3 baseline_simple.py
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

| Language | F1 Score | Precision | Recall | Status |
|----------|----------|-----------|--------|---------|
| English  | 0.810    | 1.000     | 0.680  | Production Ready |
| Swahili  | 0.750    | 1.000     | 0.600  | Production Ready |
| Hausa    | 0.780    | 1.000     | 0.640  | Production Ready |
| Igbo     | 0.684    | 1.000     | 0.520  | Production Ready |
| Yoruba   | 0.936    | 1.000     | 0.880  | Excellent |

**Key Achievement**: Perfect precision (1.000) across all languages - zero false positives

## Project Structure

```
├── eval/                    # Evaluation framework
│   ├── run_evaluation.py   # Main evaluation script
│   ├── baseline_simple.py  # Baseline comparison
│   ├── ground_truth_*.csv  # Test datasets (50 samples each)
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

- **[Approach Card](docs/approach_card.md)** - Technical methodology and performance analysis
- **[Dataset Datasheet](docs/dataset_datasheet.md)** - Ground truth documentation and ethics
- **[Evaluation Protocol](docs/eval_protocol.md)** - Reproducible evaluation procedures
- **[Failure Analysis](docs/failure_case_log.md)** - Systematic improvement tracking
- **[Weekly Metrics](docs/weekly_metrics_log.md)** - Performance monitoring

## Key Features

- **Zero False Positives**: Perfect precision across all languages
- **Culturally Adapted**: Language-specific lexicons with regional context
- **Systematic Evaluation**: Comprehensive F1 framework with failure analysis
- **Baseline Validated**: Outperforms simple keyword detection
- **Production Ready**: All languages exceed F1 > 0.5 threshold

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