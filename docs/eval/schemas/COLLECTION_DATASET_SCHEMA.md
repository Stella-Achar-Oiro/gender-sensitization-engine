# Collection Dataset Schema (40 Fields)

AI BRIDGE compliant schema for large-scale data collection datasets (WinoBias, Wikipedia, news corpora).

This schema is for **collection/training data** stored in `data/clean/`. For **evaluation ground truth**, see [GROUND_TRUTH_SCHEMA.md](GROUND_TRUTH_SCHEMA.md).

---

## Schema Overview

Total: **40 fields** organized into 5 categories

| Category | Fields | Purpose |
|----------|--------|---------|
| Core Identification | 6 | Unique ID, language metadata |
| Source Information | 5 | Data provenance, safety checks |
| Linguistic Content | 5 | Text, translation, context |
| Bias Annotation | 6 | Bias labels, categorization |
| Quality Assurance | 6 | Annotation tracking, agreement |
| **Metadata** | 12 | Additional context fields |

---

## Field Definitions

### 1. Core Identification (6 fields)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | Yes | Unique sample identifier | `en_winobias_0001` |
| `language` | enum | Yes | ISO 639-1 code: en, sw, fr, ki | `sw` |
| `script` | enum | Yes | Writing system: latin, geez, arabic, ajami | `latin` |
| `country` | string | Yes | Source country | `Kenya` |
| `region_dialect` | string | No | Regional variety | `Nairobi Standard` |
| `collection_date` | ISO-8601 | Yes | When data was collected | `2025-11-27` |

### 2. Source Information (5 fields)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `source_type` | enum | Yes | Origin: `web_public`, `wikipedia`, `news`, `synthetic`, `community` | `wikipedia` |
| `source_ref` | string | Yes | URL or reference | `https://sw.wikipedia.org/wiki/...` |
| `device` | string | No | Collection device/platform | `web_scraper_v1` |
| `safety_flag` | boolean | Yes | Contains sensitive content? | `false` |
| `pii_removed` | boolean | Yes | PII detected and removed? | `true` |

### 3. Linguistic Content (5 fields)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `text` | string | Yes | Original text sample | `Daktari alikuja kesho` |
| `translation` | string | No | English translation (if source not English) | `The doctor came tomorrow` |
| `domain` | enum | Yes | Context: `job_listing`, `news`, `education`, `healthcare`, `corporate`, `government` | `healthcare` |
| `topic` | string | No | Specific topic | `medical_profession` |
| `theme` | string | No | Broader theme | `occupational_roles` |

### 4. Bias Annotation (6 fields)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `target_gender` | enum | Yes | Referent: `male`, `female`, `neutral`, `unknown` | `neutral` |
| `bias_label` | enum | Yes | Label: `stereotype`, `counter_stereotype`, `unrelated`, `ambiguous` | `unrelated` |
| `stereotype_category` | enum | Conditional | Category if biased: `profession`, `family_role`, `leadership`, `education`, `religion_culture`, `proverb_idiom`, `daily_life`, `appearance`, `capability` | `profession` |
| `explicitness` | enum | Conditional | How overt: `explicit`, `implicit` | `explicit` |
| `bias_severity` | enum | Conditional | Impact level: `low`, `medium`, `high` | `medium` |
| `sentiment_toward_referent` | enum | No | Tone: `positive`, `negative`, `neutral` | `neutral` |

### 5. Quality Assurance (6 fields)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `eval_split` | enum | Yes | Dataset split: `train`, `dev`, `test` | `train` |
| `annotator_id` | string | Yes | Anonymized annotator identifier | `ann_sw_001` |
| `qa_status` | enum | Yes | Quality: `pending`, `approved`, `disputed`, `rejected` | `approved` |
| `approver_id` | string | Conditional | QA approver (if qa_status=approved) | `qa_lead_002` |
| `cohen_kappa` | float | Conditional | Inter-annotator agreement (if double-annotated) | `0.85` |
| `notes` | string | No | Free-text annotations notes | `Regional dialect - Dar es Salaam` |

### 6. Additional Metadata (12 fields)

These fields extend AI BRIDGE for specific use cases:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `word_count` | int | Number of words in text | `8` |
| `char_count` | int | Number of characters | `42` |
| `sentence_count` | int | Number of sentences | `1` |
| `contains_code_switch` | boolean | Mixed languages? | `false` |
| `named_entities` | list[string] | Detected entities (after PII removal) | `["hospital", "city"]` |
| `part_of_speech_tags` | string | POS sequence | `NOUN VERB ADV` |
| `complexity_score` | float | Readability (0-1) | `0.45` |
| `collection_method` | string | How collected | `wikipedia_extractor` |
| `preprocessing_steps` | list[string] | Applied transformations | `["pii_removal", "normalization"]` |
| `validation_status` | enum | Validation: `not_validated`, `validated`, `failed` | `validated` |
| `correction_suggestion` | string | Neutral alternative (if biased) | `Daktari alikuja kesho` |
| `source_license` | string | Data license | `CC-BY-SA-3.0` |

---

## CSV Format Example

```csv
id,language,script,country,region_dialect,collection_date,source_type,source_ref,device,safety_flag,pii_removed,text,translation,domain,topic,theme,target_gender,bias_label,stereotype_category,explicitness,bias_severity,sentiment_toward_referent,eval_split,annotator_id,qa_status,approver_id,cohen_kappa,notes,word_count,char_count,sentence_count,contains_code_switch,named_entities,part_of_speech_tags,complexity_score,collection_method,preprocessing_steps,validation_status,correction_suggestion,source_license
sw_wiki_0001,sw,latin,Tanzania,Dar es Salaam,2025-11-27,wikipedia,https://sw.wikipedia.org/wiki/Daktari,web_scraper_v1,false,true,"Daktari alikuja kesho","The doctor came tomorrow",healthcare,medical_profession,occupational_roles,neutral,unrelated,,,,,neutral,train,ann_sw_001,approved,qa_lead_002,0.85,"Standard Swahili",3,21,1,false,"[""daktari""]","NOUN VERB ADV",0.45,wikipedia_extractor,"[""pii_removal"",""normalization""]",validated,,CC-BY-SA-3.0
```

---

## JSON Format Example

For more complex datasets, JSON format is preferred:

```json
{
  "id": "sw_wiki_0001",
  "language": "sw",
  "script": "latin",
  "country": "Tanzania",
  "region_dialect": "Dar es Salaam",
  "collection_date": "2025-11-27",
  "source_type": "wikipedia",
  "source_ref": "https://sw.wikipedia.org/wiki/Daktari",
  "device": "web_scraper_v1",
  "safety_flag": false,
  "pii_removed": true,
  "text": "Daktari alikuja kesho",
  "translation": "The doctor came tomorrow",
  "domain": "healthcare",
  "topic": "medical_profession",
  "theme": "occupational_roles",
  "target_gender": "neutral",
  "bias_label": "unrelated",
  "stereotype_category": null,
  "explicitness": null,
  "bias_severity": null,
  "sentiment_toward_referent": "neutral",
  "eval_split": "train",
  "annotator_id": "ann_sw_001",
  "qa_status": "approved",
  "approver_id": "qa_lead_002",
  "cohen_kappa": 0.85,
  "notes": "Standard Swahili",
  "word_count": 3,
  "char_count": 21,
  "sentence_count": 1,
  "contains_code_switch": false,
  "named_entities": ["daktari"],
  "part_of_speech_tags": "NOUN VERB ADV",
  "complexity_score": 0.45,
  "collection_method": "wikipedia_extractor",
  "preprocessing_steps": ["pii_removal", "normalization"],
  "validation_status": "validated",
  "correction_suggestion": null,
  "source_license": "CC-BY-SA-3.0"
}
```

---

## Enum Values

### `language`
- `en`: English
- `sw`: Swahili
- `fr`: French
- `ki`: Gikuyu

### `script`
- `latin`: Latin alphabet (English, Swahili, French, Gikuyu)
- `geez`: Ge'ez script (Amharic, Tigrinya)
- `arabic`: Arabic script
- `ajami`: African languages in Arabic script

### `source_type`
- `web_public`: Public web content
- `wikipedia`: Wikipedia articles
- `news`: News articles
- `synthetic`: Artificially created samples
- `community`: Community-contributed content

### `domain`
- `job_listing`: Job postings, recruitment
- `news`: News articles
- `education`: Educational content
- `healthcare`: Medical/health contexts
- `corporate`: Business/corporate settings
- `government`: Political/governmental texts
- `social_media`: Social media content (if applicable)
- `general`: General-purpose text

### `bias_label`
- `stereotype`: Reinforces gender stereotype
- `counter_stereotype`: Challenges gender stereotype
- `unrelated`: No gender bias present
- `ambiguous`: Unclear or context-dependent

### `stereotype_category`
- `profession`: Occupational roles
- `family_role`: Family/domestic roles
- `leadership`: Leadership positions
- `education`: Educational contexts
- `religion_culture`: Religious/cultural contexts
- `proverb_idiom`: Proverbs/idiomatic expressions
- `daily_life`: Daily activities
- `appearance`: Physical appearance
- `capability`: Abilities/skills

### `explicitness`
- `explicit`: Overtly gendered language
- `implicit`: Contextual/subtle bias

### `bias_severity`
- `low`: Subtle bias, minimal impact
- `medium`: Moderate bias, noticeable impact
- `high`: Strong bias, significant impact

### `eval_split`
- `train`: Training set (70%)
- `dev`: Development/validation set (15%)
- `test`: Test set (15%)

### `qa_status`
- `pending`: Awaiting review
- `approved`: Passed quality assurance
- `disputed`: Disagreement among annotators
- `rejected`: Failed quality checks

---

## Validation Rules

1. **Required Fields**: All "Required=Yes" fields must be non-empty
2. **Conditional Fields**: Required when conditions met:
   - `stereotype_category`, `explicitness`, `bias_severity`: Required if `bias_label` = "stereotype" or "counter_stereotype"
   - `approver_id`: Required if `qa_status` = "approved"
   - `cohen_kappa`: Required if sample is double-annotated
3. **Enums**: Must match defined values exactly (case-sensitive)
4. **Booleans**: `true` or `false` (lowercase)
5. **Dates**: ISO-8601 format (`YYYY-MM-DD`)
6. **Floats**: 0.0 to 1.0 for cohen_kappa, complexity_score

---

## Usage

### Data Collection Scripts

Located in `scripts/data_collection/`:
- **download_datasets.py**: Fetch WinoBias, WinoGender, CrowS-Pairs
- **extract_wikipedia.py**: Extract Wikipedia articles for African languages
- **detect_pii.py**: Automated PII detection and removal
- **annotate_samples.py**: Terminal annotation interface
- **track_quality.py**: Quality tracking dashboard

Example:
```bash
# Collect Swahili Wikipedia samples
python3 scripts/data_collection/extract_wikipedia.py \
  --language sw \
  --topics profession,education,healthcare \
  --max-articles 200 \
  --output data/raw/swahili_wikipedia.json

# Remove PII
python3 scripts/data_collection/detect_pii.py \
  --input data/raw/swahili_wikipedia.json \
  --output data/clean/swahili_wikipedia_clean.json

# Annotate samples
python3 scripts/data_collection/annotate_samples.py \
  --input data/clean/swahili_wikipedia_clean.json \
  --output data/annotated/swahili_wikipedia_annotated.json \
  --annotator-id ann_sw_001
```

### Current Collection Status

| Language | Samples | Status | Notes |
|----------|---------|--------|-------|
| English | 2,828 | ✅ Complete | WinoBias, WinoGender, CrowS-Pairs |
| Swahili | 0 | 🚧 In progress | Target: 300-500 samples |
| French | 0 | 🚧 In progress | Target: 300-500 samples |
| Gikuyu | 0 | 🚧 In progress | Target: 200-300 samples |

---

## Differences from Ground Truth Schema

| Aspect | Collection Dataset (40 fields) | Ground Truth (24 fields) |
|--------|-------------------------------|--------------------------|
| **Purpose** | Training/expansion data | Evaluation/testing |
| **Size** | Thousands of samples | Hundreds of samples |
| **Source** | Automated collection | Manual curation |
| **Fields** | 40 (comprehensive) | 24 (evaluation-focused) |
| **Location** | `data/clean/` | `eval/ground_truth_{lang}.csv` |
| **Usage** | Lexicon expansion, ML training | F1 evaluation, metrics |

---

## References

- AI BRIDGE Framework: "Unified Data Collection, Rules & Annotation Guide" (Pages 4-7)
- Data Collection Report: [docs/eval/DATA_COLLECTION_REPORT.md](../DATA_COLLECTION_REPORT.md)
- Dataset Datasheet: [docs/eval/dataset_datasheet.md](../dataset_datasheet.md)
- Ground Truth Schema: [GROUND_TRUTH_SCHEMA.md](GROUND_TRUTH_SCHEMA.md)
