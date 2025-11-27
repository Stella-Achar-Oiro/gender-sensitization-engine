# Lexicon Validation Guide - French & Gikuyu

## Current Status (Nov 20, 2025)

### French Lexicon
- **File**: `rules/lexicon_fr_v2.csv`
- **Size**: 51 terms
- **Status**: Created but pending validation
- **Issue**: Terms may not reflect African French dialects and usage

### Gikuyu Lexicon
- **File**: `rules/lexicon_ki_v2.csv`
- **Size**: 22 terms
- **Status**: Created but pending validation
- **Issue**: Very limited test data (1 Wikipedia sample)

---

## Validation Approach

### Phase 1: Native Speaker Review (Critical)

#### French Validation

**Who to recruit:**
1. **African French speakers** (not European French)
   - Ideal: Linguistics students or researchers from:
     - University of Yaoundé (Cameroon)
     - Université Cheikh Anta Diop (Senegal)
     - Université d'Abomey-Calavi (Benin)
     - Université Félix Houphouët-Boigny (Côte d'Ivoire)

2. **What they review:**
   - Each term in `lexicon_fr_v2.csv`
   - Check if neutral alternatives are culturally appropriate
   - Identify missing gendered terms common in African French
   - Verify that corrections maintain natural language flow

**Validation questions for each term:**
```
Term: président
Current neutral: président·e
Questions:
1. Is "président" considered gendered in African French contexts?
2. Is "président·e" the most natural gender-neutral alternative?
3. Are there other common alternatives? (e.g., "présidence", "personne dirigeante")
4. Does this term appear frequently in African French text?
5. Cultural appropriateness rating: 1-5
```

**Deliverable**: Validation report with:
- Approved terms (keep as-is)
- Modified terms (with corrections)
- Rejected terms (remove from lexicon)
- Missing terms (add to lexicon)

#### Gikuyu Validation

**Who to recruit:**
1. **Gikuyu native speakers** from:
   - University of Nairobi (Kenya)
   - Kenyatta University (Kenya)
   - Local community organizations in Central Kenya

2. **What they review:**
   - All 22 terms in `lexicon_ki_v2.csv`
   - Grammatical correctness (Gikuyu has noun classes)
   - Cultural context (gender roles in Gikuyu culture)
   - Modern vs. traditional usage

**Validation questions for each term:**
```
Term: mũndũ mũrũme (man/male person)
Current neutral: mũndũ (person)
Questions:
1. Is this the correct gender-neutral form?
2. Does "mũndũ" truly remove gender assumption?
3. Are there contexts where this feels unnatural?
4. What terms are we missing for occupations/roles?
5. Does this respect Gikuyu cultural context?
```

**Critical challenge**: Gikuyu has only ~1,000 Wikipedia articles
- May need to collect data from other sources (radio, newspapers, community texts)
- Need community partnership for data access

---

### Phase 2: Technical Validation

Once native speakers approve terms, validate technically:

#### 1. Create Ground Truth Test Sets

**French**: Create `eval/ground_truth_fr.csv` with 50+ samples
```bash
# Example process:
# 1. Collect French bias samples from validated sources
# 2. Have native speaker annotate with:
#    - is_biased: true/false
#    - expected_correction: what it should be corrected to
#    - category: occupation, pronoun, etc.
# 3. Format as CSV matching existing ground truth structure
```

**Gikuyu**: Create `eval/ground_truth_ki.csv` with 50+ samples
```bash
# This is harder due to limited data
# Options:
# 1. Translate validated English samples (with native speaker review)
# 2. Collect from Gikuyu community media
# 3. Create synthetic examples (reviewed by native speakers)
```

#### 2. Update Language Enum

```python
# In eval/models.py, add:
class Language(Enum):
    ENGLISH = "en"
    SWAHILI = "sw"
    FRENCH = "fr"    # Add this
    GIKUYU = "ki"    # Add this
    # ... existing ones
```

#### 3. Run Initial Evaluation

```bash
# After ground truth created and Language enum updated:
python3 run_evaluation.py

# Expected output:
# - F1 scores for French
# - F1 scores for Gikuyu
# - Precision (should be 1.000 if lexicon is accurate)
# - Recall (will depend on lexicon coverage)
```

#### 4. Correction Effectiveness Test

```bash
python3 eval/correction_evaluator.py

# Check:
# - Bias removal rate (target: >70%)
# - Meaning preservation
# - Over-corrections (should be 0)
```

---

### Phase 3: Iterative Improvement

Based on evaluation results:

1. **Low Recall** (<0.50)?
   - Lexicon is too small
   - Work with native speakers to add more terms
   - Focus on most frequent bias patterns first

2. **Precision < 1.000**?
   - False positives detected
   - Review flagged terms with native speakers
   - Remove or refine problematic patterns

3. **Low Bias Removal Rate** (<70%)?
   - Detection works but correction fails
   - Check neutral alternatives are correct
   - May need multiple alternatives per term

---

## Validation Timeline (Recommended)

### Week 1-2: Recruit Validators
- Contact university linguistics departments
- Reach out to African language NLP communities
- Post on relevant forums/groups
- Offer acknowledgment in paper/dataset

### Week 3-4: Native Speaker Review
- Send lexicon files to validators
- Provide validation questionnaire
- Hold video calls for discussion
- Collect feedback and corrections

### Week 5: Apply Corrections
- Update lexicon files based on feedback
- Create ground truth test sets
- Update Language enum and evaluator

### Week 6: Technical Validation
- Run evaluations
- Measure F1 scores
- Test bias removal effectiveness
- Document results

### Week 7-8: Iteration
- Address gaps found in evaluation
- Expand lexicons if needed
- Re-validate with native speakers
- Final evaluation run

**Total: ~8 weeks to production-ready**

---

## Quick Start: Minimal Validation (1-2 weeks)

If timeline is tight, do minimal validation:

1. **Find ONE native speaker per language** (via university contacts)
2. **Video call review** (2 hours per language)
   - Go through all terms together
   - Mark approve/reject/modify
   - Identify top 10 missing terms
3. **Apply immediate fixes**
4. **Create 20-30 test samples** (with their help)
5. **Run basic evaluation**
6. **Mark as "Beta - partial validation"**

This gives you:
- ✅ At least one expert review
- ✅ Some test data
- ✅ Basic F1 score
- ✅ Honest "beta" status

Then plan full validation for later.

---

## Validation Checklist

### Before Validation
- [ ] French lexicon reviewed by team (remove obvious errors)
- [ ] Gikuyu lexicon reviewed by team (remove obvious errors)
- [ ] Validation questionnaire prepared
- [ ] Native speaker recruitment started
- [ ] Budget/compensation plan (if applicable)

### During Validation
- [ ] At least 2 native speakers per language recruited
- [ ] All terms reviewed and rated
- [ ] Missing terms identified
- [ ] Cultural appropriateness confirmed
- [ ] Feedback documented

### After Validation
- [ ] Lexicons updated with corrections
- [ ] Ground truth test sets created (50+ samples each)
- [ ] Language enum updated
- [ ] Evaluation runs successfully
- [ ] F1 scores documented
- [ ] Validators acknowledged

### Production Ready Criteria
- [ ] F1 score ≥ 0.75
- [ ] Precision = 1.000 (zero false positives)
- [ ] Bias removal rate ≥ 70%
- [ ] At least 2 native speakers validated
- [ ] Ground truth has 50+ diverse samples
- [ ] Documentation updated

---

## Recruitment Resources

### French (African)
- **Organizations**:
  - AfriNLP (African NLP community)
  - Masakhane (African language NLP initiative)
  - Organisation internationale de la Francophonie

- **Universities**:
  - List of African French-speaking universities
  - Linguistics and NLP departments

- **Online**:
  - r/french (Reddit) - mention African French need
  - African linguistics mailing lists
  - Twitter: #AfricanNLP, #AfricanLanguages

### Gikuyu
- **Organizations**:
  - Gikuyu Cultural Centre (Kenya)
  - Kenya National Commission on UNESCO
  - Institute of African Studies (University of Nairobi)

- **Universities**:
  - University of Nairobi - African Studies
  - Kenyatta University - Linguistics Dept

- **Online**:
  - Kenya linguistics forums
  - Gikuyu language preservation groups
  - Twitter: #Gikuyu, #KenyanLanguages

---

## Tools to Support Validation

### 1. Web-Based Review Interface (Optional)

Create a simple Streamlit app for validators:

```python
# validation_app.py
import streamlit as st
import pandas as pd

# Load lexicon
df = pd.read_csv('rules/lexicon_fr_v2.csv')

st.title("French Lexicon Validation")

for idx, row in df.iterrows():
    st.subheader(f"Term {idx+1}: {row['biased']}")
    st.write(f"Current neutral: {row['neutral_primary']}")

    rating = st.select_slider(
        "Cultural appropriateness:",
        options=[1, 2, 3, 4, 5],
        key=f"rating_{idx}"
    )

    corrections = st.text_area(
        "Suggested corrections:",
        key=f"corrections_{idx}"
    )

    st.divider()
```

Run: `streamlit run validation_app.py`

### 2. Validation Spreadsheet (Simpler)

Export lexicon to Google Sheets:
- Share with validators
- Add columns: "Approved (Y/N)", "Corrections", "Comments", "Rating (1-5)"
- Validators review online
- Import back to CSV

### 3. Inter-Annotator Agreement

If you have 2+ validators:

```python
# Calculate Cohen's Kappa for agreement
from sklearn.metrics import cohen_kappa_score

validator1_ratings = [4, 5, 3, 5, 4, ...]
validator2_ratings = [4, 4, 3, 5, 5, ...]

kappa = cohen_kappa_score(validator1_ratings, validator2_ratings)
print(f"Agreement: {kappa:.3f}")  # Target: ≥ 0.75
```

---

## Expected Outcomes

### French (Optimistic)
- **Timeline**: 4-6 weeks
- **Expected F1**: 0.70-0.80 (if well-validated)
- **Removal Rate**: 60-80%
- **Status**: Beta (6 weeks) → Production (8 weeks)

### Gikuyu (Challenging)
- **Timeline**: 6-10 weeks (data collection harder)
- **Expected F1**: 0.60-0.70 (limited test data)
- **Removal Rate**: 40-60%
- **Status**: Prototype (8 weeks) → Beta (12 weeks)

---

## What NOT to Do

❌ **Don't validate yourself** - You're not a native speaker
❌ **Don't use Google Translate** - Cultural context is critical
❌ **Don't skip native speaker review** - This is the most important step
❌ **Don't use European French speakers for African French** - Dialects differ significantly
❌ **Don't assume translation works** - Direct translation misses cultural nuance
❌ **Don't launch without ground truth** - Can't measure performance without test data

---

## Next Steps

**Immediate (This Week)**:
1. Draft recruitment email for validators
2. Identify 3-5 target universities per language
3. Prepare validation questionnaire
4. Budget approval (if offering compensation)

**Short-term (Weeks 1-2)**:
1. Send recruitment emails
2. Post on NLP communities
3. Set up validation tools (spreadsheet or app)
4. Prepare example validation session

**Medium-term (Weeks 3-6)**:
1. Conduct validation sessions
2. Apply corrections
3. Create ground truth
4. Run evaluations

**Long-term (Weeks 7-8)**:
1. Iterate based on F1 scores
2. Expand lexicons
3. Final validation
4. Mark as production-ready

---

**Last Updated**: November 20, 2025
**Status**: Guidance document for French and Gikuyu lexicon validation
**Owner**: JuaKazi Team
