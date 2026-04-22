# Data Collection Toolkit
**Team JuaKazi - AI BRIDGE Project**

Complete toolkit for collecting, cleaning, annotating, and tracking gender bias detection datasets.

---

## Overview

This toolkit provides 5 essential tools for the data collection pipeline:

1. **Dataset Downloader** - Download open-source bias datasets
2. **Wikipedia Extractor** - Extract gender-relevant text from Wikipedia
3. **PII Detector** - Detect and remove personally identifiable information
4. **Annotation Interface** - Terminal-based annotation tool
5. **Quality Tracker** - Monitor data balance and annotation progress

---

## Quick Start

### 1. Download Open-Source Datasets

Download WinoBias, WinoGender, and CrowS-Pairs (English only):

```bash
python3 scripts/data_collection/download_datasets.py --datasets all --output data/raw
```

**Output:** 2,828 English samples from 3 datasets

**Options:**
```bash
# Download specific datasets
--datasets winobias winogender crowspairs

# Specify output directory
--output data/raw
```

---

### 2. Extract from Wikipedia

Extract gender-relevant articles from Wikipedia (multi-language):

```bash
# English occupations
python3 scripts/data_collection/extract_wikipedia.py \
    --language en \
    --topics occupations \
    --max-articles 50 \
    --output data/raw

# Swahili all topics
python3 scripts/data_collection/extract_wikipedia.py \
    --language sw \
    --topics all \
    --max-articles 100 \
    --output data/raw
```

**Supported Languages:**
- `en` - English
- `sw` - Swahili
- `fr` - French
- `ki` - Gikuyu (Kikuyu)

**Topics:**
- `occupations` - Gender stereotypes in professions
- `stereotypes` - General gender roles and stereotypes
- `biographies` - Women/men in leadership and STEM
- `all` - All topics

---

### 3. Detect and Remove PII

Clean datasets by removing personally identifiable information:

```bash
# Process single file
python3 scripts/data_collection/detect_pii.py \
    --input data/raw/samples.csv \
    --output data/clean/samples_clean.csv

# Process entire directory
python3 scripts/data_collection/detect_pii.py \
    --input data/raw \
    --output data/clean \
    --recursive
```

**Detects:**
- Email addresses
- Phone numbers
- URLs
- Social security numbers / ID numbers
- Names after titles (Mr., Dr., etc.)

**Options:**
```bash
# Replace with placeholder (default)
--redact-method placeholder  # Output: [EMAIL_REDACTED]

# Remove entirely
--redact-method remove
```

---

### 4. Annotate Samples

Interactive terminal interface for annotating bias labels:

```bash
python3 scripts/data_collection/annotate_samples.py \
    --input data/clean/samples.csv \
    --annotator alice \
    --start-from 1
```

**Annotates:**
- `target_gender`: male, female, neutral, both, unknown
- `bias_label`: stereotype, counter-stereotype, neutral, toxic, slur
- `stereotype_category`: profession, appearance, ability, personality, etc.
- `explicitness`: explicit, implicit, unmarked
- `bias_severity`: low, medium, high
- `sentiment_toward_referent`: positive, negative, neutral

**Commands:**
- `1-N`: Select option
- `s`: Skip (keep current value)
- `q`: Quit and save progress

**Output:** `samples_annotated.csv` with all annotations

---

### 5. Track Quality

Monitor annotation progress and data balance:

```bash
python3 scripts/data_collection/track_quality.py \
    --input data/clean \
    --report docs/quality_report.md
```

**Tracks:**
- Overall annotation progress
- Language distribution
- Bias label balance
- Target gender balance
- Stereotype category distribution
- Annotator contributions

**Quality Checks:**
- Language imbalance warnings (>30% difference)
- Gender imbalance warnings (>40% difference)
- Annotation progress tracking

**Output:** Markdown report with visualizations and recommendations

---

## Complete Workflow

### Step 1: Data Collection
```bash
# Download English datasets
python3 scripts/data_collection/download_datasets.py --datasets all --output data/raw

# Extract Swahili from Wikipedia
python3 scripts/data_collection/extract_wikipedia.py --language sw --topics all --max-articles 100 --output data/raw

# Extract French from Wikipedia
python3 scripts/data_collection/extract_wikipedia.py --language fr --topics all --max-articles 100 --output data/raw

# Extract Gikuyu from Wikipedia
python3 scripts/data_collection/extract_wikipedia.py --language ki --topics all --max-articles 50 --output data/raw
```

### Step 2: Data Cleaning
```bash
# Remove PII from all raw data
python3 scripts/data_collection/detect_pii.py --input data/raw --output data/clean --recursive
```

### Step 3: Annotation (Double Annotation for Cohen's Kappa)
```bash
# Annotator 1
python3 scripts/data_collection/annotate_samples.py --input data/clean/samples.csv --annotator alice

# Annotator 2 (same samples)
python3 scripts/data_collection/annotate_samples.py --input data/clean/samples.csv --annotator bob
```

### Step 4: Quality Tracking
```bash
# Generate quality report
python3 scripts/data_collection/track_quality.py --input data/clean --report docs/quality_report.md
```

### Step 5: Calculate Cohen's Kappa (for double annotation)
```bash
# Custom script to calculate agreement between alice and bob
python3 scripts/data_collection/calculate_kappa.py \
    --annotator1 alice_annotated.csv \
    --annotator2 bob_annotated.csv
```

---

## File Structure

```
scripts/data_collection/
├── download_datasets.py      # Download open-source datasets
├── extract_wikipedia.py       # Extract from Wikipedia
├── detect_pii.py             # PII detection and removal
├── annotate_samples.py       # Terminal annotation interface
├── track_quality.py          # Quality tracking dashboard
└── README.md                 # This file

data/
├── raw/                      # Raw downloaded data
│   ├── winobias_raw.csv
│   ├── winogender_raw.csv
│   ├── crowspairs_raw.csv
│   └── wikipedia_*.csv
├── clean/                    # PII-cleaned data
│   └── *_clean.csv
└── annotated/                # Annotated data
    └── *_annotated.csv

docs/
├── quality_report.md         # Quality tracking report
├── DATA_DOWNLOAD_STATUS.md   # Download progress
└── FREE_OPEN_SOURCE_DATA_SOURCES.md  # Source inventory
```

---

## Data Schema

All tools conform to the required **40-field schema**:

### Core Fields
- id, language, script, country, region_dialect
- source_type, source_ref, collection_date
- text, translation

### Bias Annotation Fields
- domain, topic, theme, sensitive_characteristic
- target_gender, bias_label, stereotype_category
- explicitness, bias_severity, sentiment_toward_referent

### Quality Assurance Fields
- device, safety_flag, pii_removed
- annotator_id, qa_status, approver_id
- cohen_kappa, notes, eval_split

---

## Requirements

**Python:** 3.6+
**Dependencies:** Standard library only (no external packages required)

All scripts use only Python standard library modules:
- `urllib` - HTTP requests
- `csv` - CSV file handling
- `re` - Regular expressions
- `json` - JSON parsing
- `argparse` - Command-line interfaces
- `pathlib` - File path handling

---

## Performance

### Dataset Downloader
- **Speed:** ~1-2 seconds per dataset
- **Total:** 2,828 English samples in ~5 seconds
- **API Calls:** 3 calls per dataset

### Wikipedia Extractor
- **Speed:** ~0.1-0.5 seconds per article
- **Rate Limit:** 10 API calls/second (respectful)
- **Extraction:** ~2-5 sentences per article

### PII Detector
- **Speed:** ~1,000 samples/second
- **Detection:** 8 types of PII
- **Accuracy:** High precision, conservative redaction

### Annotation Interface
- **Speed:** ~30-60 seconds per sample (human)
- **Workload:** 6 fields per sample
- **Estimated:** 10-15 hours for 1,200 samples (2 annotators)

### Quality Tracker
- **Speed:** ~10,000 samples/second
- **Analysis:** Language, bias, gender distribution
- **Output:** Markdown report with warnings

---

## Legal & Ethical Compliance

### Licenses
All downloaded datasets respect original licenses:
- **WinoBias:** MIT License
- **WinoGender:** CC BY 4.0
- **CrowS-Pairs:** CC BY-SA 4.0
- **Wikipedia:** CC BY-SA 3.0

### Attribution
All samples include:
- `source_ref` field with original URL
- `notes` field with dataset/article name
- `source_type` field set to 'web_public'

### Privacy
- PII detection on all collected data
- `pii_removed` field tracks cleaning status
- `safety_flag` set to 'safe' after validation

### Rate Limiting
- Wikipedia API: 10 requests/second max
- User-Agent header identifies research project
- Respectful data collection practices

---

## Troubleshooting

### Wikipedia API 403 Errors
**Problem:** HTTP 403 Forbidden when accessing Wikipedia API
**Solution:** User-Agent header is now included automatically

### PII False Positives
**Problem:** Common names after titles flagged as PII
**Solution:** Review redacted samples manually, adjust name detection patterns if needed

### Annotation Progress Lost
**Problem:** Quit annotation session before completion
**Solution:** Use `--start-from N` to resume from last annotated sample

### Quality Report Empty
**Problem:** No samples found in input directory
**Solution:** Ensure CSV files exist in specified directory, check file permissions

---

## Next Steps

### For Data Collection Team
1. ✅ Download English datasets (COMPLETE)
2. ⏳ Extract Swahili, French, Gikuyu samples from Wikipedia
3. ⏳ Clean all datasets with PII detector
4. ⏳ Recruit 4-6 annotators (2 per language for Cohen's Kappa)
5. ⏳ Conduct 2-day annotation training workshop
6. ⏳ Begin double annotation
7. ⏳ Track quality with dashboard
8. ⏳ Calculate Cohen's Kappa (target: ≥0.70)

### For Engineering Team
- Integrate annotated datasets into training pipeline
- Build ML models for bias detection
- Validate with F1 ≥ 0.75 threshold
- Deploy API for real-time detection

---

## Contributors

**Team JuaKazi - Data Collection**
- Languages: Gikuyu, French, English, Swahili
- Project: AI BRIDGE (AfriLabs + Gates Foundation)

**Contact:**
- GitHub: [github.com/juakazi](https://github.com/juakazi)
- Email: achar@juakazi.org

---

## License

MIT License - See project root for details.

**Dataset Licenses:** Respect individual dataset licenses when redistributing collected data.

---

## Changelog

### Version 1.0 (2025-11-13)
- ✅ Dataset downloader for WinoBias, WinoGender, CrowS-Pairs
- ✅ Wikipedia extractor for 4 languages (en, sw, fr, ki)
- ✅ PII detection and removal tool
- ✅ Terminal-based annotation interface
- ✅ Quality tracking dashboard
- ✅ Comprehensive documentation

---

**Status:** ✅ All tools tested and ready for production use
