# Data Schemas Reference

Quick reference guide to all data schemas used in the JuaKazi Gender Sensitization Engine.

---

## Schema Overview

| Schema | Purpose | Files Using It | Status |
|--------|---------|----------------|--------|
| [Ground Truth](#ground-truth-schema) | Evaluation test data (AI BRIDGE) | `eval/ground_truth_{lang}.csv` | Active |
| [Lexicon](#lexicon-schema) | Bias detection rules | `rules/lexicon_{lang}_v2.csv` | Active |
| [Annotation Guidelines](#annotation-guidelines) | Human annotation protocol | `data/analysis/annotation_sample.csv` | Active |
| [Collection Dataset](#collection-dataset-schema) | Data mining output | `data/analysis/*_occupations.csv` | Active |
| [Audit Log](#audit-log-schema) | API correction tracking | `audit_logs/rewrites.jsonl` | Active |

---

## Ground Truth Schema

**Purpose**: Evaluation test data for measuring bias detection performance (AI BRIDGE compliant)

**GitLab**:
- [Full Schema Documentation](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/GROUND_TRUTH_SCHEMA.md)
- [Ground Truth Files](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/eval)

**Used By**:
- `eval/ground_truth_en.csv` (50 samples)
- `eval/ground_truth_sw.csv` (63 samples)
- `eval/ground_truth_fr.csv` (50 samples)
- `eval/ground_truth_ki.csv` (50 samples)

### Current Format (4 Fields - Basic)
```csv
text,has_bias,bias_category,expected_correction
"The chairman will lead the meeting",true,occupation,"The chairperson will lead the meeting"
```

### AI BRIDGE Extended Format (24 Fields - Target)
```csv
id,language,script,country,region_dialect,source_type,source_ref,collection_date,
text,translation,domain,topic,theme,sensitive_characteristic,target_gender,
bias_label,stereotype_category,explicitness,bias_severity,sentiment_toward_referent,
device,safety_flag,pii_removed,annotator_id,qa_status,approver_id,cohen_kappa,
notes,eval_split
```

### Key Fields
| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `text` | string | "Daktari alipima mgonjwa" | Original text sample |
| `bias_label` | boolean/string | `true` or `"biased"` | Does text contain gender bias? |
| `bias_category` | enum | `occupation` | Type: occupation, pronoun_assumption, pronoun_generic, honorific, morphology |
| `target_gender` | enum | `male` | Gender referenced: male, female, neutral, unknown |
| `expected_correction` | string | "Daktari alipima mgonjwa" | Neutral alternative |
| `confidence` | float | 0.85 | Annotator confidence (0.0-1.0) |
| `annotator_id` | string | `ANN-001` | Unique annotator identifier |

### AI BRIDGE Requirements
- **Bronze Tier**: 1,200+ samples per language, 10% double-annotated (Cohen's Kappa ≥0.70)
- **Silver Tier**: 5,000+ samples per language, 20% double-annotated (Kappa ≥0.75)
- **Gold Tier**: 10,000+ samples per language, 30% double-annotated (Kappa ≥0.80)

**Current Status**:
- English: 50 samples (need 1,150 more for Bronze)
- Swahili: 63 samples + **1,500 ready for annotation** (Bronze ready!)
- French: 50 samples (need 1,150 more for Bronze)
- Gikuyu: 50 samples (need 1,150 more for Bronze)

---

## Lexicon Schema

**Purpose**: Bias detection rules defining biased terms and neutral alternatives

**GitLab**:
- [Full Schema Documentation](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/LEXICON_SCHEMA.md)
- [Lexicon Files](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/rules)

**Used By**:
- `rules/lexicon_en_v2.csv` (514 entries)
- `rules/lexicon_sw_v2.csv` (55 entries) ← **Recently expanded**
- `rules/lexicon_fr_v2.csv` (51 entries)
- `rules/lexicon_ki_v2.csv` (22 entries)

### Format
```csv
language,biased,neutral_primary,neutral_alternatives,tags,pos,domain,register,
severity,ngeli,number,gender_marked,plural_form,diminutive,augmentative,
example_biased,example_neutral
```

### Key Fields
| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `language` | enum | `sw` | Language code: en, sw, fr, ki |
| `biased` | string | `chairman` | Gender-biased term |
| `neutral_primary` | string | `chairperson` | Primary neutral replacement |
| `neutral_alternatives` | string | `chair` | Alternative replacements (pipe-separated) |
| `severity` | enum | `replace` | Action: replace, warn |
| `tags` | string | `gender\|occupation` | Metadata tags (pipe-separated) |
| `pos` | enum | `noun` | Part of speech: noun, pronoun, verb, adjective |
| `ngeli` | string | `1/2` | Swahili noun class (m-wa for people) |

### Example Entries

**English**:
```csv
en,chairman,chairperson,chair,gender|occupation,noun,business,formal,replace,,,false,,,,"The chairman called the meeting","The chairperson called the meeting"
```

**Swahili**:
```csv
sw,daktari,daktari,,gender|occupation,noun,healthcare,formal,replace,1/2,sg,false,,,,"Daktari alipima mgonjwa","Daktari alipima mgonjwa"
```

**Current Growth**:
- Swahili: 15 → 55 terms (+267% in Nov-Dec 2025)
- Added: daktari, muuguzi, mhandisi, mkulima, dereva, etc.

---

## Annotation Guidelines

**Purpose**: Human annotation protocol for creating ground truth data (AI BRIDGE HITL compliance)

**GitLab**:
- [Full Guidelines](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/ANNOTATION_GUIDELINES.md)
- [One-Page Summary](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/ANNOTATION_ONE_PAGER.md)

**Used By**:
- `data/analysis/annotation_sample.csv` (1,500 Swahili samples ready)

### Annotation Process
1. **Read** the text carefully
2. **Identify** if gender bias exists (yes/no)
3. **Categorize** bias type (occupation, pronoun_assumption, etc.)
4. **Determine** target gender (male, female, neutral, unknown)
5. **Write** neutral correction (if biased)
6. **Rate** confidence (0.0-1.0)
7. **Add** metadata (severity, explicitness, notes)

### Bias Categories
| Category | Definition | Example |
|----------|------------|---------|
| `occupation` | Gendered job title | chairman → chairperson |
| `pronoun_assumption` | Gendered pronoun where gender unknown | "The doctor... he" |
| `pronoun_generic` | Generic "he" as universal | "Each student should bring his book" |
| `honorific` | Gendered title | Mr./Mrs./Ms. |
| `morphology` | Gender in word structure | actor/actress |

### Quality Metrics (AI BRIDGE HITL)
- **Cohen's Kappa (κ)**: ≥0.70 (inter-annotator agreement, 2 annotators)
- **Krippendorff's Alpha (α)**: ≥0.80 (multi-annotator reliability, 3+ annotators)
- **HMAR**: ≥0.80 (Human-Model Agreement Rate)
- **Confidence threshold**: Flag any annotation < 0.6 for expert review

---

## Collection Dataset Schema

**Purpose**: Output format for data mining scripts (occupation sentence extraction)

**GitLab**:
- [Full Schema Documentation](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/COLLECTION_DATASET_SCHEMA.md)
- [Data Collection Scripts](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/scripts/data_collection)

**Used By**:
- `data/analysis/swahili_news_occupations.csv` (44,505 sentences, 7.5MB) ← **Not tracked in git**
- `data/analysis/wikipedia_sw_occupations.csv` (41 sentences)

### Format
```csv
sentence_id,source,url,title,date_published,sentence,occupation_terms,
sentence_length,has_url,has_hashtag,content_ratio
```

### Key Fields
| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `sentence_id` | string | `NEWS-00001` | Unique sentence identifier |
| `source` | string | `swahili_news` | Data source name |
| `sentence` | string | "Daktari alipima mgonjwa..." | Extracted sentence |
| `occupation_terms` | string | `daktari,muuguzi` | Detected occupation terms (comma-separated) |
| `sentence_length` | int | 85 | Character count |
| `content_ratio` | float | 0.92 | Letters/total characters (quality metric) |

### Quality Filters
- Minimum length: 20 characters
- Maximum length: 500 characters
- Content ratio: ≥0.70 (70% letters)
- No URLs or hashtags (web noise)
- At least one occupation term from lexicon

**Current Collection**:
- Swahili News: 44,505 sentences from 31,041 articles
- Wikipedia: 41 sentences
- **Total**: 44,546 real Swahili sentences (4.5× Gold tier requirement!)

---

## Audit Log Schema

**Purpose**: API correction tracking for transparency and analysis

**GitLab**:
- [Full Schema Documentation](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/AUDIT_LOG_SCHEMA.md)
- [API Source](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/api/main.py)

**Used By**:
- `audit_logs/rewrites.jsonl` (API correction logs)
- `audit_logs/reviews.jsonl` (Human review decisions)

### Format (JSONL - one JSON object per line)
```json
{
  "id": "req-1234567890",
  "timestamp": "2025-12-03T10:30:45Z",
  "language": "sw",
  "original_text": "Daktari yeye ni mzuri",
  "rewrite": "Daktari ni mzuri",
  "edits": [
    {
      "original": "yeye ni",
      "replacement": "ni",
      "category": "pronoun_assumption",
      "position": 8
    }
  ],
  "confidence": 0.95,
  "source": "rules",
  "model_version": "v2.0",
  "flags": {}
}
```

### Key Fields
| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `req-1234567890` | Unique request ID |
| `timestamp` | ISO8601 | `2025-12-03T10:30:45Z` | When correction was made |
| `language` | enum | `sw` | Language code |
| `original_text` | string | "Daktari yeye ni mzuri" | Input text |
| `rewrite` | string | "Daktari ni mzuri" | Corrected output |
| `edits` | array | `[{...}]` | List of changes made |
| `confidence` | float | 0.95 | System confidence (0.0-1.0) |
| `source` | enum | `rules` | Detection method: rules, ml, hybrid |

### Use Cases
- **Transparency**: Track all corrections made by API
- **Analysis**: Identify common bias patterns
- **Debugging**: Investigate incorrect corrections
- **Audit Trail**: Compliance and accountability

---

## Quick Links

### Documentation
- [CLAUDE.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/CLAUDE.md) - Project overview
- [DATA_COLLECTION_REPORT.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/DATA_COLLECTION_REPORT.md) - Phase 3-4 results
- [ANNOTATION_ONE_PAGER.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/ANNOTATION_ONE_PAGER.md) - Quick annotation guide

### Schema Files
- [GROUND_TRUTH_SCHEMA.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/GROUND_TRUTH_SCHEMA.md)
- [LEXICON_SCHEMA.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/LEXICON_SCHEMA.md)
- [ANNOTATION_GUIDELINES.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/ANNOTATION_GUIDELINES.md)
- [COLLECTION_DATASET_SCHEMA.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/COLLECTION_DATASET_SCHEMA.md)
- [AUDIT_LOG_SCHEMA.md](https://gitlab.com/juakazike/gender-sensitization-engine/-/blob/feature/swahili-lexicon-expansion/docs/eval/schemas/AUDIT_LOG_SCHEMA.md)

### Data Files
- [Ground Truth Files](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/eval)
- [Lexicon Files](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/rules)
- [Data Collection Scripts](https://gitlab.com/juakazike/gender-sensitization-engine/-/tree/feature/swahili-lexicon-expansion/scripts/data_collection)

---

## Current Status (Dec 3, 2025)

### Swahili Language (Priority)
- **Lexicon**: 55 terms (37% of Gold tier target of 150+)
- **Ground Truth**: 63 samples + **1,500 ready for annotation**
- **Data Collection**: 44,546 real sentences (4.5× Gold tier requirement!)
- **Next**: Human annotation (~$700, 2-3 weeks)

### Other Languages (Pending Expansion)
- **English**: 514 lexicon terms, 50 ground truth samples
- **French**: 51 lexicon terms, 50 ground truth samples
- **Gikuyu**: 22 lexicon terms, 50 ground truth samples

---

**Questions?** Refer to full schema documentation linked above or contact project lead.
