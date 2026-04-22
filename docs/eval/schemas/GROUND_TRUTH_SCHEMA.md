# AI BRIDGE Ground Truth Schema

Extended schema for bias detection ground truth data, compliant with AI BRIDGE requirements.

This schema expands the current 4-field format to 24 fields for comprehensive evaluation and fairness tracking.

## Current Schema (4 fields)

```csv
text,has_bias,bias_category,expected_correction
"The chairman will lead the meeting",true,occupation,"The chairperson will lead the meeting"
```

## Extended AI BRIDGE Schema (24 fields)

### 1. Core Sample Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `sample_id` | string | Yes | Unique identifier | `sw_001`, `en_042` |
| `text` | string | Yes | Original text sample | `Mwalimu alipika chakula` |
| `language` | enum | Yes | Language code (en, sw, fr, ki) | `sw` |
| `has_bias` | boolean | Yes | Ground truth bias label | `true` |
| `bias_category` | enum | Yes | Category: occupation, pronoun_assumption, etc. | `occupation` |
| `expected_correction` | string | Conditional | Neutral rewrite (required if has_bias=true) | `Mwalimu alipika chakula` |

### 2. Annotation Metadata

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `annotator_id` | string | Yes | Anonymized annotator identifier | `ann_001` |
| `annotation_date` | ISO-8601 | Yes | Annotation timestamp | `2025-11-27T10:30:00Z` |
| `annotation_confidence` | float | Yes | Annotator confidence (0.0-1.0) | `0.95` |
| `annotation_time_seconds` | int | No | Time spent on annotation | `45` |
| `annotation_method` | enum | Yes | `manual`, `assisted`, `automated` | `manual` |

### 3. Multi-Annotator Agreement (HITL)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `annotator_2_label` | boolean | No | Second annotator's label (for Cohen's Kappa) | `true` |
| `annotator_3_label` | boolean | No | Third annotator's label (for Krippendorff's Alpha) | `false` |
| `consensus_method` | enum | Conditional | How disagreements resolved: `majority`, `expert`, `discussion` | `majority` |
| `inter_annotator_kappa` | float | No | Cohen's Kappa score for this sample | `0.85` |

### 4. Fairness & Demographic Context

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `demographic_group` | enum | Yes | Referent: `male`, `female`, `neutral`, `unknown` | `male` |
| `domain` | string | Yes | Context domain: `job_listing`, `news`, `education`, etc. | `job_listing` |
| `regional_variant` | string | Conditional | For Swahili: `kenya`, `tanzania`, `uganda` | `kenya` |

### 5. Bias Characteristics

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `severity` | enum | Conditional | `high`, `medium`, `low` (if has_bias=true) | `high` |
| `explicitness` | enum | Conditional | `explicit`, `implicit` (if has_bias=true) | `explicit` |
| `bias_source` | string | Conditional | Specific term causing bias | `mwalimu` |

### 6. Quality & Validation

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `validation_status` | enum | Yes | `validated`, `pending`, `disputed` | `validated` |
| `notes` | string | No | Free-text notes from annotator | `Regional variant - common in Nairobi` |
| `data_source` | string | Yes | Origin: `wikipedia`, `news`, `synthetic`, etc. | `wikipedia` |

## Full CSV Example

```csv
sample_id,text,language,has_bias,bias_category,expected_correction,annotator_id,annotation_date,annotation_confidence,annotation_time_seconds,annotation_method,annotator_2_label,annotator_3_label,consensus_method,inter_annotator_kappa,demographic_group,domain,regional_variant,severity,explicitness,bias_source,validation_status,notes,data_source
sw_001,"Mwalimu alipika chakula kwa familia yake",sw,true,occupation,"Mwalimu alipika chakula kwa familia yake",ann_001,2025-11-27T10:30:00Z,0.95,45,manual,true,true,majority,0.85,male,education,kenya,medium,implicit,mwalimu,validated,"Common occupation term with gendered assumption",wikipedia
en_042,"The chairman will lead the meeting",en,true,occupation,"The chairperson will lead the meeting",ann_002,2025-11-27T11:15:00Z,1.0,30,manual,true,true,unanimous,1.0,male,corporate,,high,explicit,chairman,validated,"Classic gendered title",synthetic
sw_002,"Yeye ni daktari mzuri",sw,false,,,ann_001,2025-11-27T10:32:00Z,0.90,20,manual,false,false,unanimous,1.0,neutral,healthcare,tanzania,,,yeye,validated,"Gender-neutral pronoun usage",news
```

## Enum Value Definitions

### `language`
- `en`: English
- `sw`: Swahili
- `fr`: French
- `ki`: Gikuyu

### `bias_category`
- `occupation`: Gendered occupational terms
- `pronoun_assumption`: Gendered pronoun assumptions
- `pronoun_generic`: Generic pronoun bias (e.g., "he" as universal)
- `honorific`: Gendered titles (Mr./Mrs./Ms.)
- `morphology`: Gender in word structure

### `annotation_method`
- `manual`: Human annotator from scratch
- `assisted`: Human with ML suggestions
- `automated`: Fully automated (requires validation)

### `consensus_method`
- `majority`: Majority vote among annotators
- `expert`: Expert annotator adjudication
- `discussion`: Annotators discussed and agreed
- `unanimous`: All annotators agreed initially

### `demographic_group`
- `male`: Male referent (he/his/him, mwanamume)
- `female`: Female referent (she/her, mwanamke)
- `neutral`: Neutral/non-binary (they/them, yeye without context)
- `unknown`: Cannot determine from text

### `domain`
- `job_listing`: Job postings and recruitment
- `news`: News articles
- `education`: Educational content
- `healthcare`: Medical/health contexts
- `corporate`: Business/corporate settings
- `government`: Political/governmental texts
- `social_media`: Social media content
- `synthetic`: Artificially created test cases

### `regional_variant` (Swahili-specific)
- `kenya`: Kenyan Swahili
- `tanzania`: Tanzanian Swahili
- `uganda`: Ugandan Swahili
- `standard`: Standard Swahili (non-regional)

### `severity` (if has_bias=true)
- `high`: Strongly gendered, requires immediate correction
- `medium`: Moderate bias, should be corrected
- `low`: Subtle bias, optional correction

### `explicitness` (if has_bias=true)
- `explicit`: Overtly gendered (chairman, he/she)
- `implicit`: Contextual bias (assumptions, stereotypes)

### `validation_status`
- `validated`: Reviewed and confirmed by expert
- `pending`: Awaiting validation
- `disputed`: Disagreement among annotators

## Migration from Current Schema

To migrate existing ground truth files:

```python
def migrate_to_aibridge_schema(old_csv_path: str, new_csv_path: str):
    """
    Migrate 4-field format to 24-field AI BRIDGE format.

    Fills missing fields with defaults:
    - sample_id: Generated as {lang}_{row_number:03d}
    - annotator_id: "migrated_legacy"
    - annotation_date: Migration timestamp
    - annotation_confidence: 1.0 (assumed high quality)
    - annotation_method: "manual"
    - demographic_group: Inferred from text
    - domain: "synthetic" (legacy default)
    - validation_status: "validated" (legacy assumed correct)
    - data_source: "legacy_migration"
    """
    pass  # Implementation in scripts/migrate_ground_truth.py
```

## Validation Rules

1. **Required Field Completeness**:
   - All "Required=Yes" fields must be non-empty
   - Conditional fields required when conditions met

2. **Data Type Validation**:
   - Booleans: `true`/`false` (lowercase)
   - Floats: 0.0 to 1.0 for confidence/scores
   - Enums: Must match defined values exactly
   - ISO-8601: `YYYY-MM-DDTHH:MM:SSZ` format

3. **Logical Consistency**:
   - If `has_bias=false`, then `expected_correction` must be empty
   - If `has_bias=true`, then `severity` and `explicitness` required
   - If `annotator_2_label` present, `consensus_method` required
   - `inter_annotator_kappa` range: -1.0 to 1.0 (but typically 0.0 to 1.0)

4. **HITL Requirements** (AI BRIDGE Bronze Tier):
   - Minimum 10% of samples must have `annotator_2_label`
   - `inter_annotator_kappa` must be ≥0.70 across dataset
   - `annotation_confidence` average must be ≥0.80

5. **Fairness Balance** (AI BRIDGE):
   - `demographic_group` distribution:
     - Male referent: 30-40% of samples
     - Female referent: 30-40% of samples
     - Neutral: 20-40% of samples
   - No single domain should exceed 50% of total samples

## Usage in Evaluation

The extended schema enables:

1. **HITL Metrics** ([eval/hitl_metrics.py](eval/hitl_metrics.py)):
   ```python
   from eval.hitl_metrics import HITLCalculator

   # Load ground truth with annotator_2_label, annotator_3_label
   multi_annotator_data = [
       gt['annotator_1_label'],  # Primary (has_bias)
       gt['annotator_2_label'],
       gt['annotator_3_label']
   ]

   calculator = HITLCalculator()
   metrics = calculator.calculate_hitl_metrics(
       model_predictions, ground_truth, multi_annotator_data
   )
   ```

2. **Fairness Metrics** ([eval/fairness_metrics.py](eval/fairness_metrics.py)):
   ```python
   from eval.fairness_metrics import FairnessCalculator, DemographicGroup

   # Extract demographic groups from ground truth
   groups = [DemographicGroup(row['demographic_group']) for row in ground_truth]

   calculator = FairnessCalculator()
   fairness = calculator.calculate_fairness_metrics(
       predictions, labels, groups, language_f1_scores
   )
   ```

3. **Enhanced Reporting**:
   - Per-domain performance breakdown
   - Regional variant analysis (Swahili)
   - Annotator agreement tracking
   - Confidence-weighted metrics

## Sample Size Requirements (AI BRIDGE Tiers)

| Tier | Minimum Samples | Multi-Annotator | Cohen's Kappa |
|------|----------------|-----------------|---------------|
| Bronze | 1,200 | 10% (120 samples) | ≥0.70 |
| Silver | 5,000 | 20% (1,000 samples) | ≥0.75 |
| Gold | 10,000+ | 30% (3,000+ samples) | ≥0.80 |

**Current Status**:
- English: 50 samples → Need 1,150 more (Bronze)
- Swahili: 63 samples → Need 1,137 more (Bronze)
- French: 50 samples → Need 1,150 more (Bronze)
- Gikuyu: 50 samples → Need 1,150 more (Bronze)

## References

- AI BRIDGE Framework: "Unified Data Collection, Rules & Annotation Guide"
- CSVW Standard: https://www.w3.org/TR/tabular-data-primer/
- Cohen's Kappa: https://en.wikipedia.org/wiki/Cohen%27s_kappa
- Krippendorff's Alpha: https://en.wikipedia.org/wiki/Krippendorff%27s_alpha
