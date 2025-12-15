# Annotation Guidelines - AI BRIDGE Compliant

Comprehensive guidelines for annotating gender bias in text across JuaKazi languages (English, Swahili, French, Gikuyu) with Human-in-the-Loop (HITL) protocols.

## Table of Contents

1. [Overview](#overview)
2. [Annotation Task](#annotation-task)
3. [HITL Protocol](#hitl-protocol)
4. [Bias Categories](#bias-categories)
5. [Language-Specific Guidelines](#language-specific-guidelines)
6. [Quality Standards](#quality-standards)
7. [Examples](#examples)

---

## Overview

### Purpose

Create high-quality ground truth data for evaluating bias detection systems, ensuring:
- **Reliability**: Cohen's Kappa ≥0.70 between annotators
- **Validity**: Human-Model Agreement Rate ≥0.80
- **Fairness**: Balanced demographic representation
- **Consistency**: Clear, reproducible decisions

### AI BRIDGE Requirements

| Metric | Target | Purpose |
|--------|--------|---------|
| Cohen's Kappa (κ) | ≥0.70 | Inter-annotator agreement |
| Krippendorff's Alpha (α) | ≥0.80 | Multi-annotator reliability |
| HMAR | ≥0.80 | Human-model alignment |
| Sample Size (Bronze) | 1,200+ per language | Statistical power |
| Multi-Annotator Coverage | 10% minimum | Quality validation |

---

## Annotation Task

### Step 1: Read the Text

Carefully read the text sample in its entirety. Consider:
- Context and intended meaning
- Cultural and linguistic nuances
- Domain (job listing, news, education, etc.)

### Step 2: Identify Bias

Ask yourself:
1. **Does this text contain gender bias?**
   - Yes: Proceed to Step 3
   - No: Mark `has_bias=false` and submit

2. **What makes it biased?**
   - Gendered occupational term (chairman, mwalimu)
   - Pronoun assumption (he/she where gender unknown)
   - Stereotypical association (nurses are women)

### Step 3: Categorize Bias

Select the **primary** bias category:

| Category | Definition | Example |
|----------|------------|---------|
| `occupation` | Gendered job title or role | chairman → chairperson |
| `pronoun_assumption` | Gendered pronoun where gender unknown | "The doctor... he" |
| `pronoun_generic` | Generic "he" as universal | "Each student should bring his book" |
| `honorific` | Gendered title | Mr./Mrs./Ms. |
| `morphology` | Gender in word structure | actor/actress |

### Step 4: Provide Correction

Write a **neutral, natural-sounding** alternative:

**Good corrections**:
- Preserve meaning and context
- Sound natural in the language
- Remove only the bias, not stylistic elements
- Maintain grammatical correctness

**Bad corrections**:
- ❌ Change meaning or context
- ❌ Sound awkward or robotic
- ❌ Remove non-biased gender references
- ❌ Introduce new errors

### Step 5: Rate Confidence

Rate your confidence in this annotation (0.0 to 1.0):
- **1.0**: Completely certain, clear-cut case
- **0.9**: Very confident, minimal ambiguity
- **0.8**: Confident, some minor uncertainty
- **0.7**: Somewhat confident, moderate ambiguity
- **0.6 or below**: Unsure, flag for expert review

### Step 6: Add Metadata

Complete additional fields:
- `severity`: high/medium/low (how strongly gendered?)
- `explicitness`: explicit/implicit (overt or subtle?)
- `demographic_group`: male/female/neutral/unknown
- `domain`: job_listing/news/education/etc.
- `notes`: Any observations or context

---

## HITL Protocol

### Double Annotation Process

**AI BRIDGE Bronze Tier Requirement**: 10% of samples must be double-annotated.

1. **Primary Annotation**:
   - Annotator A reviews sample independently
   - Completes all fields without seeing others' work

2. **Secondary Annotation**:
   - Annotator B reviews **same** sample independently
   - Also completes all fields without seeing A's work

3. **Agreement Check**:
   - System calculates Cohen's Kappa for A vs B
   - If κ < 0.70, proceed to consensus resolution

4. **Consensus Resolution** (if needed):
   - Annotators A and B discuss disagreement
   - Expert annotator C adjudicates if no agreement
   - Final consensus recorded with `consensus_method`

### Krippendorff's Alpha (Triple Annotation)

For **critical** or **disputed** samples:
- 3+ annotators review independently
- Krippendorff's Alpha calculated
- Target: α ≥0.80 for high-quality data

### When to Flag for Expert Review

Flag samples if:
- Your confidence < 0.70
- Cultural context unclear
- Ambiguous gender reference
- Regional dialect unfamiliar
- Novel bias pattern not in guidelines

---

## Bias Categories

### 1. Occupation Bias

**Definition**: Job titles, roles, or professions with gendered assumptions.

**English Examples**:
- ✅ `chairman` → `chairperson` or `chair`
- ✅ `policeman` → `police officer`
- ✅ `fireman` → `firefighter`
- ❌ `doctor` (gender-neutral, no bias)

**Swahili Examples**:
- ⚠️ `mwalimu` (teacher): Contextual bias if assumed male
- ⚠️ `daktari` (doctor): Gender-neutral, no inherent bias
- ✅ `askari` (policeman) → `afisa wa usalama` (security officer)

**Key Consideration**: In Swahili, many occupations are grammatically gender-neutral but carry **contextual** bias through stereotypes.

### 2. Pronoun Assumption

**Definition**: Using gendered pronouns (he/she) when gender is unknown or irrelevant.

**English Examples**:
- ✅ "A doctor should wash his hands" → "their hands"
- ✅ "The nurse said she would..." → "they would"

**Swahili Examples**:
- ⚠️ Swahili has gender-neutral `yeye` (he/she)
- ✅ Bias appears via context: "Yeye ni daktari mzuri, mwanamume" (He is a good doctor, a man) - assumption that doctors are male

### 3. Pronoun Generic

**Definition**: Using "he" as a universal pronoun to represent all genders.

**English Examples**:
- ✅ "Each employee must submit his report" → "their report"
- ✅ "A student should do his best" → "their best"

**Swahili**: Less common due to gender-neutral `yeye`.

### 4. Honorific Bias

**Definition**: Gendered titles that assume marital status or gender.

**English Examples**:
- ✅ `Mr./Mrs./Ms.` → Use name directly or `Mx.`
- ❌ `Dr.` (gender-neutral title, no bias)

**Swahili Examples**:
- ⚠️ `Bwana/Bibi` (Mr./Mrs.) → `Mheshimiwa` (Honorable)

### 5. Morphology Bias

**Definition**: Gender encoded in word structure (less common in English, rare in Swahili).

**English Examples**:
- ✅ `actor/actress` → `actor` (neutral)
- ✅ `waiter/waitress` → `server`

**Swahili**: Not applicable (Swahili lacks gendered morphology).

---

## Language-Specific Guidelines

### Swahili (sw)

#### Unique Characteristics

1. **Gender-Neutral Grammar**:
   - Pronouns: `yeye` (he/she), `wao` (they)
   - No grammatical gender in nouns
   - Noun classes (ngeli) based on semantics, not gender

2. **Contextual Bias**:
   - Bias appears through **assumptions**, not grammar
   - Example: Associating `mwalimu` (teacher) with males
   - Watch for context clues: `mwanamume` (man), `mwanamke` (woman)

3. **Regional Variations**:
   - **Kenya**: More English loanwords, urban slang
   - **Tanzania**: Standard Swahili, more formal
   - **Uganda**: Mixed with Luganda influences
   - **Note**: Document regional variant in `regional_variant` field

#### Annotation Tips for Swahili

- **Focus on context**, not just words
- **Occupational stereotypes** are primary bias source
- **Cultural norms** vary by region (consult native speakers)
- **Neutral alternatives**: Preserve Swahili structure (avoid direct English translations)

#### Common Swahili Bias Patterns

| Biased Pattern | Neutral Alternative | Category |
|----------------|---------------------|----------|
| Mwalimu (teacher, assumed male) | Mwalimu (with neutral context) | occupation |
| Askari (policeman) | Afisa wa usalama | occupation |
| Mama msafishaji (cleaning lady) | Mfanyakazi wa usafi | occupation |
| Yeye ni daktari mzuri, mwanamume | Yeye ni daktari mzuri | pronoun_assumption |

### English (en)

Standard English bias detection guidelines apply. See examples in [Bias Categories](#bias-categories).

### French (fr)

**Note**: French has grammatical gender (le/la), which complicates bias detection.

#### Key Considerations

1. **Grammatical Gender ≠ Bias**:
   - `le médecin` (the doctor, masculine grammar) - NOT bias
   - `le médecin... il` (the doctor... he) - IS bias (assumption)

2. **Gendered Occupations**:
   - ✅ `acteur/actrice` → `artiste` (artist, neutral)
   - ✅ `auteur/auteure` → `auteur` (author, neutral becoming standard)

3. **Inclusive Writing**:
   - Emerging: `étudiant·e·s` (students, inclusive)
   - Traditional neutral: `les étudiants` (students, masculine plural)

### Gikuyu (ki)

**Note**: Limited Gikuyu NLP resources. Consult native speakers.

#### Key Characteristics

1. **Noun Classes**: Similar to Swahili, semantic-based (not gender)
2. **Bias Sources**: Occupational stereotypes, cultural associations
3. **Emerging Lexicon**: Limited digital corpus, ongoing research

---

## Quality Standards

### Annotation Quality Checklist

Before submitting, verify:

- [ ] **Completeness**: All required fields filled
- [ ] **Correctness**: Bias categorized accurately
- [ ] **Naturalness**: Correction sounds natural in the language
- [ ] **Consistency**: Similar to previous annotations
- [ ] **Confidence**: Rated honestly (≥0.80 preferred)
- [ ] **Context**: Domain and demographic group identified

### Common Mistakes to Avoid

1. **Over-correction**:
   - ❌ Changing `mother` to `parent` when context is biological
   - ✅ Only remove bias, not legitimate gender references

2. **Under-correction**:
   - ❌ Marking `chairman` as "no bias" because it's common
   - ✅ Mark bias even if term is widely used

3. **Translation Errors** (Swahili):
   - ❌ Using direct English translations (`police officer` → `afisa wa polisi`)
   - ✅ Use natural Swahili (`afisa wa usalama`)

4. **Ignoring Context**:
   - ❌ Assuming `mwalimu` is always biased
   - ✅ Check if context implies gender (e.g., `mwalimu... yeye ni mwanamume`)

5. **Inconsistent Severity**:
   - `chairman` should always be `high` severity (explicit)
   - `teacher` assumption should be `medium` severity (implicit)

---

## Examples

### Example 1: English - Occupation Bias (High Severity)

**Text**: `The chairman will lead the meeting and his assistant will take notes.`

**Annotation**:
```csv
has_bias: true
bias_category: occupation
expected_correction: "The chairperson will lead the meeting and their assistant will take notes."
severity: high
explicitness: explicit
bias_source: "chairman, his"
demographic_group: male
domain: corporate
annotation_confidence: 1.0
notes: "Classic gendered title with pronoun assumption"
```

**Rationale**: "Chairman" is explicitly gendered, and "his" assumes male assistant.

---

### Example 2: Swahili - Contextual Occupation Bias (Medium Severity)

**Text**: `Mwalimu alipika chakula kwa familia yake.` (The teacher cooked food for his family.)

**Annotation**:
```csv
has_bias: true
bias_category: occupation
expected_correction: "Mwalimu alipika chakula kwa familia yake."
severity: medium
explicitness: implicit
bias_source: "mwalimu (contextual male assumption)"
demographic_group: male
domain: education
regional_variant: kenya
annotation_confidence: 0.85
notes: "Swahili 'mwalimu' is gender-neutral grammatically, but cultural context often assumes male teacher, especially in household/cooking context which stereotypically female activity assigned to male subject creates implicit bias"
```

**Rationale**: The sentence structure implies a male teacher, as cooking (stereotypically female) is presented as noteworthy for a (assumed male) teacher.

**CAUTION**: This is a **subtle** case. If uncertain, consult native speaker.

---

### Example 3: English - No Bias (Legitimate Gender Reference)

**Text**: `She is pregnant and will take maternity leave.`

**Annotation**:
```csv
has_bias: false
bias_category:
expected_correction:
demographic_group: female
domain: healthcare
annotation_confidence: 1.0
notes: "Legitimate biological gender reference, not bias"
```

**Rationale**: "She" is appropriate because pregnancy is biological female context.

---

### Example 4: Swahili - No Bias (Gender-Neutral)

**Text**: `Daktari alisema yeye atakuja kesho.` (The doctor said they will come tomorrow.)

**Annotation**:
```csv
has_bias: false
bias_category:
expected_correction:
demographic_group: neutral
domain: healthcare
regional_variant: tanzania
annotation_confidence: 0.95
notes: "Gender-neutral pronoun 'yeye' with no contextual bias indicators"
```

**Rationale**: `Yeye` is gender-neutral, and no context implies gender assumption.

---

### Example 5: Disagreement → Consensus (HITL Protocol)

**Text**: `The nurse prepared the patient for surgery.`

**Annotator A**:
```csv
has_bias: false
notes: "'Nurse' is gender-neutral term"
annotation_confidence: 0.90
```

**Annotator B**:
```csv
has_bias: true
bias_category: occupation
expected_correction: "The nurse prepared the patient for surgery." (no change)
severity: low
explicitness: implicit
notes: "Cultural stereotype: nursing assumed female profession, though term itself neutral"
annotation_confidence: 0.70
```

**Cohen's Kappa**: Disagreement (A=false, B=true)

**Consensus Resolution**:
- **Discussion**: Annotators agree that:
  - "Nurse" itself is gender-neutral (no morphological bias)
  - Cultural stereotype exists (implicit bias) but not in text
  - Text does not explicitly or implicitly gender the nurse
- **Final Label**: `has_bias=false`
- **Consensus Method**: `discussion`
- **Expert Note**: "Cultural stereotypes do not constitute text-level bias unless manifested in language"

**Lesson**: Distinguish between:
- **Cultural stereotypes** (external to text)
- **Textual bias** (present in language itself)

Only annotate textual bias.

---

## Annotator Training

### Phase 1: Onboarding (2 hours)

1. **Read Guidelines**: This entire document
2. **Watch Tutorial**: Video walkthrough (if available)
3. **Quiz**: 10-question comprehension check (≥80% to pass)

### Phase 2: Practice Annotation (4 hours)

1. **Annotate 50 practice samples**:
   - 25 with known labels (immediate feedback)
   - 25 blind (reviewed by expert)
2. **Target**: ≥85% agreement with expert labels

### Phase 3: Calibration (1 hour)

1. **Group discussion**: Review 10 challenging cases
2. **Align understanding**: Ensure consistent interpretation
3. **Clarify edge cases**: Document novel patterns

### Phase 4: Production Annotation

1. **Start with easy samples**: Build confidence
2. **Random quality checks**: 5% of annotations reviewed
3. **Weekly calibration**: Group review of disagreements

---

## Support and Resources

### Questions or Unclear Cases

Contact:
- **Email**: annotations@juakazi.org (placeholder)
- **Slack**: #annotation-team channel
- **Expert Annotator**: Available for escalations

### Swahili Language Resources

- **Masakhane NLP**: African language NLP community
- **SAWA Corpus**: Swahili language resources
- **Native Speaker Network**: Regional consultants (Kenya/Tanzania/Uganda)

### Tools and Interfaces

- **Annotation Platform**: [TBD - Prodigy, Label Studio, or custom]
- **Data Format**: CSV (see [GROUND_TRUTH_SCHEMA_AIBRIDGE.md](GROUND_TRUTH_SCHEMA_AIBRIDGE.md))
- **Version Control**: Git-based review system

---

## Appendix: Quick Reference

### Decision Tree

```
1. Does text contain gendered language?
   ├─ No → has_bias=false (DONE)
   └─ Yes ↓

2. Is the gendered language necessary/appropriate?
   ├─ Yes (biological, legitimate) → has_bias=false (DONE)
   └─ No (assumption, stereotype) ↓

3. Categorize bias:
   ├─ Gendered job title → occupation
   ├─ Pronoun assumption → pronoun_assumption
   ├─ Generic "he" → pronoun_generic
   ├─ Mr./Mrs./Ms. → honorific
   └─ Actor/actress → morphology

4. Write neutral correction (preserve context)

5. Rate confidence (1.0 = certain, 0.6 = unsure)

6. Add metadata (severity, demographic, domain)
```

### Confidence Rating Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 1.0 | Completely certain | Submit |
| 0.9 | Very confident | Submit |
| 0.8 | Confident | Submit |
| 0.7 | Some uncertainty | Submit, add notes |
| 0.6 | Unsure | Flag for review |
| <0.6 | Very unsure | Flag for expert |

### Severity Guide

| Level | Definition | Example |
|-------|------------|---------|
| **High** | Strongly gendered, unambiguous | chairman, he (generic) |
| **Medium** | Moderate bias, some context needed | Contextual assumptions |
| **Low** | Subtle, borderline cases | Cultural implications |

---

**Document Version**: 1.0
**Last Updated**: 2025-11-27
**Next Review**: Before Phase 2 annotation begins
**Contact**: JuaKazi AI BRIDGE Team
