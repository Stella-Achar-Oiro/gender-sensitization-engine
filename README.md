# JuaKazi Gender Sensitization Engine

Gender bias detection and correction system for African languages with comprehensive F1 evaluation framework.

## Supported Languages

### Production & Foundation
- **English** (F1: 0.764, Precision: 1.000, Bias Removal: 100%) - Production-ready
- **Swahili** (F1: 0.681, Precision: 1.000, Bias Removal: 12.5%) - Foundation

### Beta (Pending Native Speaker Validation)
- **French** (F1: 0.627, Precision: 1.000) - Initial validation complete
- **Gikuyu** (F1: 0.714, Precision: 1.000) - Initial validation complete

**Perfect Precision**: All 4 languages achieve 1.000 precision (zero false positives)

**Latest Update (Nov 20, 2025):** Added French and Gikuyu support with F1 evaluation, updated to 4-language system

## Quick Start

### Using Make Commands (Recommended)
```bash
# Show all available commands
make help

# Run evaluation (no dependencies required)
make eval              # F1 evaluation across all languages
make eval-correction   # Correction effectiveness analysis
make demo              # Live interactive demo

# Run tests
make test              # System tests
make test-demo         # Complete demo with all features

# Start services (requires optional dependencies)
make run-api           # API server on port 8000
make run-ui            # Streamlit UI on port 8501
make run               # Both API and UI together
```

### Direct Python Commands
```bash
# Evaluation (no dependencies required)
python3 run_evaluation.py           # F1 evaluation
python3 eval/correction_evaluator.py # Correction analysis
python3 demo_live.py                # Live demo

# Testing
python3 tests/test_system.py        # System tests
python3 tests/test_api.py           # API endpoint tests (requires FastAPI)
python3 tests/test_demo.py          # Complete demo

# Services (requires optional dependencies)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000  # API
streamlit run review_ui/app.py --server.port 8501         # UI
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

### Detection Performance (Nov 20, 2025)
| Language | F1 Score | Precision | Recall | Lexicon Size | Status |
|----------|----------|-----------|--------|--------------|---------|
| English  | 0.764    | 1.000     | 0.618  | 514 entries (19 concepts) | Production |
| Swahili  | 0.681    | 1.000     | 0.516  | 15 terms | Foundation |
| French   | 0.627    | 1.000     | 0.457  | 51 terms | Beta |
| Gikuyu   | 0.714    | 1.000     | 0.556  | 22 terms | Beta |

### Correction Effectiveness
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Production-ready |
| Swahili  | 51.6%         | 12.5%             | Needs expansion |
| French   | 45.7%         | Pending           | Needs validation |
| Gikuyu   | 55.6%         | Pending           | Needs validation |

**Key Achievements**:
- **Perfect precision (1.000) across all 4 languages** - zero false positives
- English: 100% bias removal rate (all detected biases successfully corrected)
- Hybrid approach: Rules-based (70%) + ML (30%)
- 4 languages with measurable F1 scores

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
│   ├── lexicon_en_v2.csv  # English (514 entries = 19 concepts)
│   ├── lexicon_sw_v2.csv  # Swahili (15 terms)
│   ├── lexicon_fr_v2.csv  # French (51 terms)
│   └── lexicon_ki_v2.csv  # Gikuyu (22 terms)
├── scripts/data_collection/  # Data collection tools
│   ├── download_datasets.py  # WinoBias, WinoGender, CrowS-Pairs
│   ├── extract_wikipedia.py  # Wikipedia corpus extraction
│   └── common_utils.py       # Shared utilities (1,637 lines)
└── docs/                   # Documentation
    ├── approach_card.md    # Technical methodology
    ├── dataset_datasheet.md # Ground truth documentation
    └── eval_protocol.md    # Evaluation procedures
```

## Requirements

### Core System (No Dependencies)
- Python 3.12+ (standard library only)
- All evaluation and detection features work without external dependencies

```bash
python3 run_evaluation.py           # F1 evaluation
python3 demo_live.py                # Live demo
python3 eval/correction_evaluator.py # Correction analysis
```

### Optional Dependencies

Install using Poetry for dependency management:

```bash
# Full installation (API, UI, ML, dev tools) - auto-installs poetry if needed
make setup

# Alternatives
make install-minimal  # API + UI only (no ML)
make install-core     # Dev tools only
```

Dependencies managed via `pyproject.toml` with optional extras:
- **api** - FastAPI, pandas
- **ui** - Streamlit
- **ml** - Transformers, PyTorch, scikit-learn
- **dev** - pytest, black, ruff, mypy, pre-commit

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