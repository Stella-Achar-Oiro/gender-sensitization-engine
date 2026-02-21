# JuaKazi Gender Sensitization Engine

Gender bias detection and correction system for African languages with comprehensive F1 evaluation framework.

## Supported Languages

### Production & Foundation
- **English** (F1: 0.786, Precision: 1.000, Recall: 0.647) - Production-ready
- **Swahili** (F1: 0.708, Precision: 1.000, Recall: 0.548) - Foundation

### Beta (Pending Native Speaker Validation)
- **French** (F1: 0.571, Precision: 1.000, Recall: 0.400) - Initial validation complete
- **Gikuyu** (F1: 0.643, Precision: 1.000, Recall: 0.473) - Expanded dataset (5,254 samples)

**Perfect Precision**: All 4 languages achieve 1.000 precision (zero false positives)

**Latest Update (Jan 2026):** Major Kikuyu expansion with 5,200+ lexicon entries and 5,254 ground truth samples. AI BRIDGE compliance features added.

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

### Detection Performance (Jan 2026)
| Language | F1 Score | Precision | Recall | Lexicon Size | Ground Truth | Status |
|----------|----------|-----------|--------|--------------|--------------|--------|
| English  | 0.786    | 1.000     | 0.647  | 515 entries (v3) | 67 samples | Production |
| Swahili  | 0.708    | 1.000     | 0.548  | 151 entries (v3) | 64 samples | Foundation |
| French   | 0.571    | 1.000     | 0.400  | 51 entries (v3) | 51 samples | Beta |
| Gikuyu   | 0.643    | 1.000     | 0.473  | 1,209 entries (v3) | 5,254 samples (v4) | Beta |

### Correction Effectiveness
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 64.7%         | **100.0%**        | Production-ready |
| Swahili  | 54.8%         | Improving         | Expanding |
| French   | 40.0%         | Pending           | Needs validation |
| Gikuyu   | 47.3%         | In Progress       | Large-scale validation |

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
│   ├── lexicon_en_v3.csv  # English (515 entries)
│   ├── lexicon_sw_v3.csv  # Swahili (151 entries)
│   ├── lexicon_fr_v3.csv  # French (51 entries)
│   ├── lexicon_ki_v3.csv  # Gikuyu (1,209 entries)
│   └── lexicon_ki_v2.csv  # Gikuyu baseline (111 entries)
├── scripts/                  # Utilities and generation tools
│   ├── generate_ki_lexicon_v3.py    # Kikuyu lexicon generator (data-driven)
│   ├── generate_kikuyu_lexicon_ai.py # AI-based lexicon generation
│   └── data_collection/      # Data collection tools
│       ├── download_datasets.py  # WinoBias, WinoGender, CrowS-Pairs
│       ├── extract_wikipedia.py  # Wikipedia corpus extraction
│       └── common_utils.py       # Shared utilities
├── data/                   # Training and evaluation datasets
│   ├── Kikuyu/             # Kikuyu transcripts (33MB+)
│   ├── raw/                # Original benchmark datasets
│   ├── clean/              # Processed datasets for team access
│   ├── swahili_corpus/     # Swahili training data
│   └── analysis/           # Analysis outputs
└── docs/                   # Documentation
    ├── approach_card.md    # Technical methodology
    ├── dataset_datasheet.md # Ground truth documentation
    └── eval_protocol.md    # Evaluation procedures
```

**Data Pipeline:**
- `data/raw/` - Original datasets (WinoBias, WinoGender, CrowS-Pairs, Wikipedia extracts)
- `data/clean/` - Processed datasets ready for evaluation and model training
- Use `scripts/data_collection/` tools to regenerate or update datasets

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
- **AI BRIDGE Compliant**: Fairness metrics (DP, EO) for bias detection
- **Large-Scale Kikuyu Dataset**: 5,254 annotated samples with 1,209 lexicon entries
- **Context-Aware Correction**: Enhanced semantic preservation
- **Culturally Adapted**: Language-specific lexicons with regional context
- **Systematic Evaluation**: Comprehensive F1 framework with failure analysis

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
- **5,436 ground truth samples** (EN: 67, SW: 64, FR: 51, KI: 5,254)
- **Perfect precision** maintained across all languages
- **Major Kikuyu expansion**: 22 → 1,209 lexicon entries, 34 → 5,254 samples
- **AI BRIDGE compliance**: Fairness metrics integrated
- **Cross-language framework** proven scalable

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

Open source - see project license for details.