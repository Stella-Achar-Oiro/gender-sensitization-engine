# Swahili Gender Bias Annotation

## Quick Overview

**What**: Annotate 1,500 real Swahili sentences for gender bias detection
**Who**: 3-5 native Swahili speakers (Kenya/Tanzania/Uganda)
**Timeline**: 2-3 weeks
**Budget**: ~$700
**Goal**: Expand ground truth from 63 → 1,563 samples (AI BRIDGE Bronze tier)

---

## Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total sentences** | 1,500 (stratified sample from 44,546 real news articles) |
| **Occupation terms** | 30 unique terms tracked |
| **Source** | Swahili News Dataset (Zenodo) + Wikipedia |
| **Coverage** | ~50 samples per occupation term for balanced distribution |
| **File location** | `data/analysis/annotation_sample.csv` (664KB) |
| **Format** | AI BRIDGE 24-field schema (CSV) |

**Top occupation terms** in dataset:
- mbunge (politician) - 8,450 occurrences
- wakili (lawyer) - 3,243 occurrences
- waziri (minister) - 2,271 occurrences
- mfanyabiashara (businessperson) - 2,137 occurrences

---

## Annotation Schema (24 Fields)

### Core Fields (Must Annotate)
| Field | Example | Description |
|-------|---------|-------------|
| `text` | "Rais Joseph Kabila wa Congo hatogombea tena urais..." | Original Swahili sentence |
| `bias_label` | `biased` / `neutral` | Does text contain gender bias? |
| `bias_category` | `occupation` / `pronoun_assumption` / `pronoun_generic` / `honorific` / `morphology` | Primary bias type |
| `target_gender` | `male` / `female` / `neutral` / `unknown` | Gender referenced/assumed |
| `expected_correction` | "Rais Joseph Kabila wa Congo hatogombea tena..." | Neutral alternative (if biased) |
| `confidence` | 0.0 - 1.0 | Annotator's confidence (1.0 = certain, 0.6 = flag for review) |

### Pre-filled Fields (Reference Only)
| Field | Example | Description |
|-------|---------|-------------|
| `id` | `SW-NEWS-00001` | Unique sample ID |
| `language` | `sw` | Swahili language code |
| `source_type` | `web_public` | Data source type |
| `occupation_terms` | `mgombea, wakili` | Detected occupation terms (in notes field) |
| `collection_date` | `2025-12-03` | Data collection timestamp |

### Metadata Fields (Optional)
- `explicitness`: implicit/explicit - How obvious is the bias?
- `bias_severity`: high/medium/low - Strength of bias
- `sentiment_toward_referent`: positive/negative/neutral - Attitude toward person
- `notes`: Free-text comments, context, edge cases

---

## Annotation Decision Tree

```
1. Read the sentence carefully
   ↓
2. Does it contain gender bias?
   ├─ NO  → Mark bias_label="neutral", target_gender="neutral"
   │        DONE ✓
   │
   └─ YES → Continue to Step 3
      ↓
3. What type of bias?
   ├─ Gendered job title (mgombea → candidate)
   │  → bias_category="occupation"
   │
   ├─ Pronoun assumption (yeye = he/she)
   │  → bias_category="pronoun_assumption"
   │
   ├─ Generic "he" (standard male reference)
   │  → bias_category="pronoun_generic"
   │
   ├─ Gendered title (Mr./Mrs./Mzee/Bi)
   │  → bias_category="honorific"
   │
   └─ Gender in word structure (wa kike/wa kiume)
      → bias_category="morphology"
      ↓
4. Who is referenced?
   → target_gender: male/female/neutral/unknown
   ↓
5. Write neutral correction
   → expected_correction: "Natural Swahili alternative..."
   ↓
6. Rate confidence (0.0-1.0)
   → confidence: 0.9 (flag if < 0.6)
   ↓
   DONE ✓
```

---

## Example Annotations

### Example 1: Occupation Bias (Biased)
```csv
id: SW-NEWS-00001
text: "Rais Joseph Kabila wa Congo hatogombea tena urais na kwamba chama chake kimemchagua Emmanuel Ramazani Shadari kuwa mrithi wake na mgombea wa uchaguzi wa urais..."
bias_label: biased
bias_category: occupation
target_gender: male
expected_correction: "Rais Joseph Kabila wa Congo hatogombea tena urais na kwamba chama chake kimemchagua Emmanuel Ramazani Shadari kuwa mrithi wake na mgombea wa uchaguzi wa urais..." (context-dependent)
confidence: 0.85
explicitness: implicit
bias_severity: low
notes: "mgombea" (candidate) used in male-dominated political context
```

### Example 2: Pronoun Assumption (Biased)
```csv
id: SW-NEWS-XXXX
text: "Daktari alipima mgonjwa. Yeye ni mzuri sana."
bias_label: biased
bias_category: pronoun_assumption
target_gender: unknown
expected_correction: "Daktari alipima mgonjwa. Ni mzuri sana." (remove "Yeye")
confidence: 0.95
explicitness: explicit
bias_severity: medium
notes: "Yeye" assumes gender where doctor's gender is unknown
```

### Example 3: Neutral (No Bias)
```csv
id: SW-NEWS-YYYY
text: "Wanafunzi walisoma vitabu vyao."
bias_label: neutral
bias_category: N/A
target_gender: neutral
expected_correction: N/A
confidence: 1.0
explicitness: N/A
bias_severity: N/A
notes: Gender-neutral reference to students
```

---

## Quality Standards

### AI BRIDGE Requirements
- **Cohen's Kappa ≥0.70**: 10% double annotation (150 samples minimum)
- **Confidence threshold**: Flag any annotation with confidence < 0.6 for expert review
- **Consistency checks**: Periodic review of annotator decisions

### Best Practices **DO**:
- Read full context before annotating
- Preserve natural Swahili phrasing in corrections
- Flag ambiguous cases with notes
- Consider regional dialects (Kenya vs Tanzania vs Uganda)
- Mark confidence honestly

**DON'T**:
- Rush through annotations
- Change meaning in corrections
- Remove all gender references (only remove bias)
- Introduce grammatical errors
- Guess when unsure (flag for review instead)

---

## File Access

**Annotation file**: `data/analysis/annotation_sample.csv`

**Quick preview**:
```bash
# View first 5 samples
head -n 5 data/analysis/annotation_sample.csv

# Count total samples
wc -l data/analysis/annotation_sample.csv
# → 1,994 lines (includes header + multi-line text)

# Check file size
ls -lh data/analysis/annotation_sample.csv
# → 664KB
```

**Sample download**: Send `annotation_sample.csv` to annotators via secure link (Google Drive, Dropbox, etc.)

---

## Next Steps

1. **Recruit annotators** (3-5 native speakers)
   - Target: Masakhane Africa NLP community
   - Requirements: Native Swahili (Kenya/Tanzania/Uganda), basic CSV/Excel skills

2. **Onboarding** (1-2 days)
   - Share this one-pager + full guidelines ([ANNOTATION_GUIDELINES.md](docs/eval/schemas/ANNOTATION_GUIDELINES.md))
   - Provide 10-20 practice samples
   - Review initial annotations for calibration

3. **Annotation phase** (2-3 weeks)
   - Each annotator: ~300-500 samples
   - 10% double annotation (150 samples) for Cohen's Kappa
   - Weekly check-ins for consistency

4. **Quality assurance** (3-5 days)
   - Calculate Cohen's Kappa (target ≥0.70)
   - Review low-confidence samples (< 0.6)
   - Resolve conflicts through discussion

5. **Integration** (1 day)
   - Merge annotations into `eval/ground_truth_sw.csv`
   - Run evaluation: `python3 run_evaluation.py`
   - Target: F1 ≥0.75, DP ≤0.10, EO ≤0.05 (Bronze tier)

---

## Full Documentation

- **📋 Schemas Reference**: [SCHEMAS_REFERENCE.md](SCHEMAS_REFERENCE.md) - All schemas with GitLab links
- **✍️ Annotation Guidelines**: [docs/eval/schemas/ANNOTATION_GUIDELINES.md](docs/eval/schemas/ANNOTATION_GUIDELINES.md)
- **🎯 Ground Truth Schema**: [docs/eval/schemas/GROUND_TRUTH_SCHEMA.md](docs/eval/schemas/GROUND_TRUTH_SCHEMA.md)
- **📊 Data Collection Report**: [DATA_COLLECTION_REPORT.md](DATA_COLLECTION_REPORT.md)


**Questions?** Contact project lead or refer to full documentation.
