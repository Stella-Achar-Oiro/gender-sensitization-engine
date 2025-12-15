# Schema Documentation

This folder contains all data schema definitions for the JuaKazi Gender Sensitization Engine.

## Schema Files

### [LEXICON_SCHEMA.md](LEXICON_SCHEMA.md)
**Purpose**: Defines the structure for bias detection lexicon files (rules)

**Used by**:
- [rules/lexicon_en_v2.csv](../../rules/lexicon_en_v2.csv) (514 entries)
- [rules/lexicon_sw_v2.csv](../../rules/lexicon_sw_v2.csv) (15 entries)
- [rules/lexicon_fr_v2.csv](../../rules/lexicon_fr_v2.csv) (51 entries)
- [rules/lexicon_ki_v2.csv](../../rules/lexicon_ki_v2.csv) (22 entries)

**Key fields**: `language`, `biased`, `neutral_primary`, `neutral_alternatives`, `severity`, `tags`, `pos`, `ngeli` (Swahili)

**Example**:
```csv
language,biased,neutral_primary,neutral_alternatives,tags,pos,severity
en,chairman,chairperson,chair,gender|occupation,noun,replace
```

---

### [GROUND_TRUTH_SCHEMA.md](GROUND_TRUTH_SCHEMA.md)
**Purpose**: Defines the structure for evaluation ground truth data (AI BRIDGE compliant)

**Used by**:
- [eval/ground_truth_en.csv](../ground_truth_en.csv) (50 samples)
- [eval/ground_truth_sw.csv](../ground_truth_sw.csv) (63 samples)
- [eval/ground_truth_fr.csv](../ground_truth_fr.csv) (50 samples)
- [eval/ground_truth_ki.csv](../ground_truth_ki.csv) (50 samples)

**Current format**: 4 fields (basic)
```csv
text,has_bias,bias_category,expected_correction
```

**AI BRIDGE extended format**: 24 fields (target)
```csv
sample_id,text,language,has_bias,bias_category,expected_correction,
annotator_id,annotation_date,annotation_confidence,annotator_2_label,
demographic_group,domain,regional_variant,severity,explicitness,
validation_status,notes,...
```

**Migration status**: In progress (see [GROUND_TRUTH_SCHEMA.md](GROUND_TRUTH_SCHEMA.md) for full specification)

---

### [COLLECTION_DATASET_SCHEMA.md](COLLECTION_DATASET_SCHEMA.md)
**Purpose**: Defines the structure for large-scale training/collection data (40 fields, AI BRIDGE compliant)

**Used by**:
- [data/clean/english_collection.json](../../../data/clean/) (2,828 samples)
- [data/clean/swahili_collection.json](../../../data/clean/) (target: 300-500)
- [data/clean/french_collection.json](../../../data/clean/) (target: 300-500)
- [data/clean/gikuyu_collection.json](../../../data/clean/) (target: 200-300)

**Key fields**:
```csv
id,language,script,country,source_type,source_ref,text,translation,domain,
target_gender,bias_label,stereotype_category,explicitness,annotator_id,
qa_status,cohen_kappa,pii_removed,...
```

**Sources**: WinoBias, WinoGender, CrowS-Pairs, Wikipedia, news corpora

**Purpose**: Lexicon expansion, ML training, data augmentation (NOT evaluation)

---

### [AUDIT_LOG_SCHEMA.md](AUDIT_LOG_SCHEMA.md)
**Purpose**: Defines the structure for API correction audit logs

**Used by**:
- [audit_logs/rewrites.jsonl](../../audit_logs/rewrites.jsonl)
- [audit_logs/reviews.jsonl](../../audit_logs/reviews.jsonl)

**Format**: JSONL (newline-delimited JSON)

**Key fields**: `id`, `timestamp`, `original_text`, `rewrite`, `edits`, `confidence`, `source` (rules/ml)

**Example**:
```json
{"id":"abc123","timestamp":"2025-11-27T10:30:00Z","original_text":"The chairman will lead","rewrite":"The chairperson will lead","edits":[{"from":"chairman","to":"chairperson"}],"confidence":1.0,"source":"rules"}
```

---

### [ANNOTATION_GUIDELINES.md](ANNOTATION_GUIDELINES.md)
**Purpose**: Human annotation guidelines for creating ground truth data (AI BRIDGE compliant)

**Audience**: Native speaker annotators, linguistic consultants, data quality reviewers

**Covers**:
- Bias identification criteria
- Categorization decision tree
- Language-specific guidelines (Swahili, English, French, Gikuyu)
- HITL (Human-in-the-Loop) protocols
- Quality standards (Cohen's Kappa ≥0.70, HMAR ≥0.80)
- Annotation examples and edge cases

**AI BRIDGE requirements**:
- Double annotation (10% minimum for Bronze tier)
- Inter-annotator agreement tracking
- Confidence rating (0.0 to 1.0)
- Consensus resolution protocols

---

## Schema Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    JuaKazi Data Flow                        │
└─────────────────────────────────────────────────────────────┘

[LEXICON_SCHEMA.md] ──> rules/lexicon_{lang}_v2.csv
                              │
                              ↓
                     [BiasDetector]
                              │
                              ↓
[GROUND_TRUTH_SCHEMA.md] ──> eval/ground_truth_{lang}.csv
                              │
                              ↓
                      [Evaluator] ─────> Results
                              │
                              ↓
[AUDIT_LOG_SCHEMA.md] ──> audit_logs/rewrites.jsonl


[ANNOTATION_GUIDELINES.md] ──> Used by annotators to create:
                                 - Ground truth data
                                 - Lexicon validation
                                 - HITL quality checks
```

## AI BRIDGE Compliance

All schemas are designed to meet AI BRIDGE framework requirements:

| Requirement | Schema | Compliance |
|-------------|--------|------------|
| F1 ≥ 0.75 | GROUND_TRUTH_SCHEMA.md | ✅ Supports evaluation |
| Precision ≥ 0.90 | LEXICON_SCHEMA.md | ✅ Zero false positives |
| Cohen's Kappa ≥ 0.70 | ANNOTATION_GUIDELINES.md | ✅ HITL protocols |
| Demographic Parity ≤ 0.10 | GROUND_TRUTH_SCHEMA.md | ✅ `demographic_group` field |
| Equal Opportunity ≤ 0.05 | GROUND_TRUTH_SCHEMA.md | ✅ Fairness tracking |
| Sample size (Bronze) | GROUND_TRUTH_SCHEMA.md | 🚧 1,200+ per language (target) |

**Legend**: ✅ Compliant | 🚧 In progress | ❌ Not compliant

## Version History

| Schema | Version | Last Updated | Changes |
|--------|---------|--------------|---------|
| LEXICON_SCHEMA.md | 2.0 | 2024-11-27 | Added `ngeli`, `agreement_notes` for Swahili |
| GROUND_TRUTH_SCHEMA.md | 1.0 | 2025-11-27 | Created AI BRIDGE 24-field format |
| AUDIT_LOG_SCHEMA.md | 1.0 | 2024-11-27 | Initial version |
| ANNOTATION_GUIDELINES.md | 1.0 | 2025-11-27 | AI BRIDGE HITL protocols |

## Usage Examples

### Creating New Lexicon Entry

See [LEXICON_SCHEMA.md](LEXICON_SCHEMA.md) for full specification.

```python
# Add to rules/lexicon_sw_v2.csv
new_entry = {
    'language': 'sw',
    'biased': 'mwalimu',
    'neutral_primary': 'mwalimu',
    'neutral_alternatives': 'mwalimu wa shule',
    'tags': 'gender|occupation',
    'pos': 'noun',
    'scope': 'education',
    'register': 'formal',
    'severity': 'replace',
    'ngeli': '1/2',
    'example_biased': 'Mwalimu alipika chakula',
    'example_neutral': 'Mwalimu alipika chakula'
}
```

### Creating Ground Truth Sample

See [GROUND_TRUTH_SCHEMA.md](GROUND_TRUTH_SCHEMA.md) for full specification.

```python
# Add to eval/ground_truth_sw.csv (current 4-field format)
basic_sample = {
    'text': 'Daktari alikuja kesho',
    'has_bias': 'false',
    'bias_category': '',
    'expected_correction': ''
}

# Future 24-field AI BRIDGE format
extended_sample = {
    'sample_id': 'sw_064',
    'text': 'Daktari alikuja kesho',
    'language': 'sw',
    'has_bias': 'false',
    'bias_category': '',
    'expected_correction': '',
    'annotator_id': 'ann_001',
    'annotation_date': '2025-11-27T10:30:00Z',
    'annotation_confidence': '0.95',
    'demographic_group': 'neutral',
    'domain': 'healthcare',
    'regional_variant': 'kenya',
    'validation_status': 'validated',
    # ... (12 more fields)
}
```

### Using Annotation Guidelines

See [ANNOTATION_GUIDELINES.md](ANNOTATION_GUIDELINES.md) for complete instructions.

**Annotator workflow**:
1. Read text sample
2. Identify bias (yes/no)
3. Categorize bias (occupation, pronoun_assumption, etc.)
4. Provide neutral correction
5. Rate confidence (0.0 to 1.0)
6. Add metadata (severity, demographic_group, domain)
7. For 10% of samples: Double annotation for Cohen's Kappa

## References

- **AI BRIDGE Framework**: Official project requirements
- **CSVW Standard**: https://www.w3.org/TR/tabular-data-primer/
- **Cohen's Kappa**: Inter-annotator agreement metric
- **Krippendorff's Alpha**: Multi-annotator reliability metric

## Questions?

For schema questions or proposals:
- Create an issue on GitLab
- Consult [docs/eval/](../eval/) for detailed evaluation documentation
- Review [CLAUDE.md](../../CLAUDE.md) for project overview
