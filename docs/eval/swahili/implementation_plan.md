# Swahili Lexicon Expansion: Implementation Plan

**Branch**: `feature/swahili-lexicon-expansion`
**Goal**: Improve Swahili bias removal from 12.5% to 75%+
**Timeline**: 12 weeks
**Status**: In Progress

---

## Current State (Baseline)

### Metrics
- **F1 Score**: 0.681 (Precision: 1.000, Recall: 0.516)
- **Bias Removal Rate**: 12.5%
- **Lexicon Size**: 15 terms
- **Ground Truth**: 63 samples

### Files to Modify
```
rules/lexicon_sw_v2.csv                    # 15 → 150+ terms
eval/ground_truth_sw.csv                   # 63 → 200+ samples
eval/bias_detector.py                      # Add Swahili-specific detection
eval/correction_evaluator.py               # Already updated ✓
scripts/data_collection/extract_wikipedia.py  # Use for mining
```

---

## Target State (Week 12)

### Metrics
- **F1 Score**: 0.800+ (maintain Precision: 1.000, Recall: 0.750+)
- **Bias Removal Rate**: 75%+
- **Lexicon Size**: 150+ terms (10x increase)
- **Ground Truth**: 200+ samples (3x increase)

---

## Phase 1: Data Collection (Weeks 1-2)

### Task 1.1: Extract Swahili Wikipedia Corpus
**File**: `scripts/data_collection/extract_wikipedia.py`

**Action Items**:
- [ ] Configure script for Swahili Wikipedia (sw.wikipedia.org)
- [ ] Target: Extract 2.8M words from [Kwici corpus](https://kevindonnelly.org.uk/swahili/swwiki/)
- [ ] Focus on: Professional biographies, education, occupations
- [ ] Output: `data/raw/swahili_wikipedia_corpus.txt`

**Command**:
```bash
python3 scripts/data_collection/extract_wikipedia.py --language sw --output data/raw/swahili_wikipedia_corpus.txt
```

**Expected Output**: 500+ occupational term candidates

---

### Task 1.2: Mine Swahili News Corpus
**New File**: `scripts/data_collection/mine_swahili_news.py`

**Action Items**:
- [ ] Access 31,000+ Swahili news articles dataset
- [ ] Categories: Business, Health, Sports, Politics, Local
- [ ] Extract sentences containing occupational keywords
- [ ] Output: `data/raw/swahili_news_bias_candidates.csv`

**Pseudo-code**:
```python
# Target occupations to find in context
target_occupations = [
    'daktari', 'mwalimu', 'polisi', 'askari', 'karani',
    'mwuguzi', 'dereva', 'mpishi', 'injinia', 'waziri'
]

# Extract sentences containing these terms
# Analyze if gender assumptions are present
# Flag: pronoun following occupation, gendered descriptors
```

**Expected Output**: 200+ contextual examples

---

### Task 1.3: Scrape East African Job Listings
**New File**: `scripts/data_collection/scrape_job_listings.py`

**Action Items**:
- [ ] Target sites: BrighterMonday Kenya, Fuzu, JobWebTanzania
- [ ] Extract Swahili job titles and descriptions
- [ ] Filter for unique occupational terms
- [ ] Output: `data/raw/swahili_job_terms.csv`

**Fields to Extract**:
```csv
job_title,company,location,language_detected,has_gendered_terms
```

**Expected Output**: 100+ unique occupational terms

---

### Task 1.4: Compile Master Candidate List
**New File**: `data/clean/swahili_bias_candidates_master.csv`

**Structure**:
```csv
candidate_term,source,frequency,contexts,priority_score
askari,wikipedia+news+jobs,1250,"askari alimkamata...",HIGH
daktari,wikipedia+news,890,"daktari alisema...",HIGH
mwuguzi,news+jobs,450,"mwuguzi alihudumia...",MEDIUM
```

**Action Items**:
- [ ] Merge all sources (Wikipedia, news, jobs)
- [ ] Remove duplicates
- [ ] Calculate frequency scores
- [ ] Prioritize by frequency + existing bias evidence
- [ ] Target: 500+ candidate terms

---

## Phase 2: Native Speaker Validation (Weeks 3-4)

### Task 2.1: Recruit Annotators
**Document**: `docs/eval/SWAHILI_ANNOTATOR_RECRUITMENT.md`

**Action Items**:
- [ ] Post on [Masakhane NLP community](https://www.masakhane.io/)
- [ ] Contact University of Nairobi Linguistics Dept
- [ ] Contact University of Dar es Salaam Kiswahili Studies
- [ ] Post on Upwork/Fiverr with vetting criteria
- [ ] Target: 5-10 annotators (Kenya: 3, Tanzania: 3, Uganda: 2)

**Requirements**:
- Native Swahili speaker
- University education (linguistics/social sciences preferred)
- Familiar with gender bias concepts
- Diverse gender representation
- Rate: $15-20/hour

---

### Task 2.2: Create Annotation Guidelines
**New File**: `docs/eval/SWAHILI_ANNOTATION_GUIDELINES.md`

**Content**:
```markdown
# Swahili Gender Bias Annotation Guidelines

## Objective
Identify terms that carry gender assumptions in Swahili text.

## Task Overview
For each term, annotate:
1. Is this term gendered? (Yes/No/Context-dependent)
2. Severity (Replace/Warn/Monitor)
3. Neutral alternative(s)
4. Regional variations (Kenya/Tanzania/Uganda)
5. Example sentences (biased and neutral)

## Categories
- Occupation (askari, daktari, mwalimu)
- Pronoun assumption (yeye + occupation + mwanamume/mwanamke)
- Familial roles (mama wa nyumbani, baba wa familia)
- Courtesy titles (Bwana, Bibi)

## Examples
[Include 10+ annotated examples]

## Regional Considerations
- Kenya vs Tanzania vocabulary differences
- Urban vs rural usage
- Formal vs informal contexts
```

**Action Items**:
- [ ] Create comprehensive guidelines with 20+ examples
- [ ] Include harm-awareness protocol (content may be triggering)
- [ ] Provide opt-out/skip options
- [ ] Add inter-annotator agreement checks

---

### Task 2.3: Annotation Platform Setup
**Tool**: Google Sheets or Label Studio

**Structure**:
```
Sheet 1: Terms to Annotate (500+ rows)
- candidate_term
- source_context
- annotator_1_decision
- annotator_2_decision
- annotator_3_decision
- consensus_decision

Sheet 2: Regional Variations
- term
- kenya_usage
- tanzania_usage
- uganda_usage
- notes
```

**Action Items**:
- [ ] Set up annotation platform
- [ ] Load 500+ candidate terms
- [ ] Assign terms to annotators (overlap for agreement checks)
- [ ] Track progress weekly

---

### Task 2.4: Run Annotation Sessions
**Duration**: 2 weeks

**Process**:
1. Week 3: Train annotators (5 hours)
   - Review guidelines
   - Practice on 50 sample terms
   - Calculate inter-annotator agreement
   - Refine guidelines based on disagreements

2. Week 4: Full annotation (35-40 hours total)
   - Annotate 500+ candidate terms
   - 3 annotators per term (for quality)
   - Weekly check-ins for questions
   - Document edge cases

**Expected Output**:
- 200+ validated bias terms
- Regional variation notes
- 100+ neutral alternatives documented

---

## Phase 3: Lexicon & Dataset Expansion (Weeks 5-6)

### Task 3.1: Update Lexicon Structure
**File**: `rules/lexicon_sw_v2.csv`

**Current Structure** (15 terms):
```csv
biased,neutral_primary,severity
askari,afisa wa usalama,replace
```

**New Enhanced Structure** (150+ terms):
```csv
biased,neutral_primary,neutral_alternatives,severity,tags,context_required,examples_biased,examples_neutral,regional_variations,ngeli_class,source,validation_date
askari,afisa wa usalama,"mlinzi;mtu wa usalama",replace,occupation,false,"askari alimkamata","afisa wa usalama alimkamata","KE:askari;TZ:askari;UG:mlinzi",m-wa,wikipedia+news+annotators,2025-11-27
```

**New Fields Explained**:
- `neutral_alternatives`: Semicolon-separated list of alternatives
- `context_required`: Boolean - needs context analysis for correction?
- `examples_biased`: Real-world biased usage
- `examples_neutral`: Corrected version
- `regional_variations`: Format "KE:term;TZ:term;UG:term"
- `ngeli_class`: Swahili noun class (m-wa for people, m-mi for things)
- `source`: Where term was discovered
- `validation_date`: When native speakers validated

**Action Items**:
- [ ] Backup current `lexicon_sw_v2.csv`
- [ ] Add header row with all new fields
- [ ] Migrate existing 15 terms to new structure
- [ ] Add 135+ new validated terms
- [ ] Sort by priority/frequency

---

### Task 3.2: Expand with Specific Categories

#### **Occupational Terms** (Target: 80 terms)
```csv
# Colonial/borrowed terms
askari,afisa wa usalama,replace,occupation
polisi,afisa wa polisi,replace,occupation
karani,mfanyakazi wa ofisi,replace,occupation
dereva,mwendeshaji gari,warn,occupation

# Professional roles
daktari,mtaalamu wa afya,warn,occupation
mwuguzi,mtunza afya,warn,occupation
mwalimu,mhadhiri;mkufunzi,warn,occupation
injinia,mtaalamu wa uhandisi,warn,occupation

# Service workers
mpishi,mtayarishaji chakula,warn,occupation
mtumishi mezani,mhudumu,replace,occupation
msichana wa nyumbani,mfanyakazi wa nyumbani,replace,occupation

# Leadership roles
mwenyekiti,kiongozi wa mkutano,replace,occupation
mkurugenzi,kiongozi mkuu,warn,occupation
waziri,kiongozi wa wizara,warn,occupation
```

#### **Pronoun Assumptions** (Target: 30 terms)
```csv
# Pattern: yeye + occupation + gendered descriptor
yeye ni mwanamume,yeye,replace,pronoun_assumption
yeye ni mwanamke,yeye,replace,pronoun_assumption
huyu mwanamume ni daktari,huyu ni daktari,replace,pronoun_assumption
mwanamke huyu ni mwalimu,huyu ni mwalimu,replace,pronoun_assumption
```

#### **Familial Roles** (Target: 20 terms)
```csv
mama wa nyumbani,mzazi wa nyumbani,replace,familial
baba wa familia,kiongozi wa familia,replace,familial
binti,mtoto,warn,familial
mvulana,mtoto,warn,familial
dada,ndugu,warn,familial
kaka,ndugu,warn,familial
```

#### **Courtesy Titles** (Target: 10 terms)
```csv
Bwana,Mheshimiwa,replace,honorific
Bibi,Mheshimiwa,replace,honorific
Shangazi,ndugu,warn,honorific
Mjomba,ndugu,warn,honorific
```

#### **Generic Pronouns** (Target: 10 terms)
```csv
kila mtu anapaswa kufanya kazi yake,kila mtu anapaswa kufanya kazi yao,replace,pronoun_generic
```

**Total Target**: 150 terms

---

### Task 3.3: Expand Ground Truth Dataset
**File**: `eval/ground_truth_sw.csv`

**Current**: 63 samples
**Target**: 200+ samples

**Distribution by Category**:
```
Occupation:           100 samples (50%)
Pronoun Assumption:    50 samples (25%)
Pronoun Generic:       30 samples (15%)
Familial:              15 samples (7.5%)
Honorifics:             5 samples (2.5%)
```

**Action Items**:
- [ ] Create WinoBias-style templates for Swahili
- [ ] Mine real examples from news corpus
- [ ] Add coreference resolution scenarios
- [ ] Balance positive/negative cases (prevent data bias)
- [ ] Have native speakers validate naturalness

**Template Example**:
```csv
text,has_bias,bias_category,expected_correction
"Daktari alisema kwamba yeye ni mwanamume hodari",true,occupation,"Daktari alisema kwamba yeye ni hodari"
"Mwalimu alifundisha wanafunzi wake vizuri",false,none,""
"Askari alimkamata mshtakiwa, mwanamume huyu ni shujaa",true,pronoun_assumption,"Askari alimkamata mshtakiwa, huyu ni shujaa"
```

---

### Task 3.4: Create WinoBias Templates
**New File**: `eval/winobias_swahili_templates.txt`

**Structure**:
```
Template: [OCCUPATION] [VERB] [OBJECT], yeye ni [GENDERED_DESCRIPTOR]
Example: Daktari alisaidia mgonjwa, yeye ni mwanamke hodari
Neutral: Daktari alisaidia mgonjwa, yeye ni hodari

Template: [OCCUPATION] alisema kwamba [PRONOUN] [VERB]
Example: Injinia alisema kwamba yeye anaj enga daraja
Neutral: Injinia alisema kwamba wao wanajenga daraja
```

**Action Items**:
- [ ] Create 20+ Swahili-specific templates
- [ ] Generate 100+ samples from templates
- [ ] Validate with native speakers for naturalness

---

## Phase 4: Technical Implementation (Weeks 7-10)

### Task 4.1: Enhance Bias Detector for Swahili
**File**: `eval/bias_detector.py`

**Current Limitation**: Simple word-boundary regex
**Problem**: Doesn't catch pronoun assumptions like "yeye... mwanamume"

**New Feature**: Context-aware Swahili detection

**Code Changes**:
```python
# Add to BiasDetector class

def detect_swahili_pronoun_assumption(self, text: str) -> list[dict[str, str]]:
    """
    Detect when 'yeye' (he/she) is incorrectly gendered via context.

    Pattern examples:
    - "yeye ni mwanamume" (he is a man)
    - "yeye ni mwanamke" (she is a woman)
    - "mwanamume huyu" (this man)
    - "mwanamke huyu" (this woman)
    """
    edits = []

    # Pattern 1: yeye + occupation + gendered descriptor
    pattern1 = r'yeye\s+(\w+)\s+(mwanamume|mwanamke)'
    matches = re.finditer(pattern1, text, re.IGNORECASE)
    for match in matches:
        edits.append({
            'from': match.group(0),
            'to': f"yeye {match.group(1)}",  # Remove gender marker
            'severity': 'replace',
            'category': 'pronoun_assumption'
        })

    # Pattern 2: gendered descriptor before yeye
    pattern2 = r'(mwanamume|mwanamke)\s+\w+\s+yeye'
    matches = re.finditer(pattern2, text, re.IGNORECASE)
    for match in matches:
        edits.append({
            'from': match.group(0),
            'to': match.group(0).replace(match.group(1), '').strip(),
            'severity': 'replace',
            'category': 'pronoun_assumption'
        })

    return edits

def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
    """Enhanced detection with Swahili-specific logic."""
    # Existing lexicon-based detection
    detected_edits = self._lexicon_based_detection(text, language)

    # Add Swahili-specific pronoun detection
    if language == Language.SWAHILI:
        pronoun_edits = self.detect_swahili_pronoun_assumption(text)
        detected_edits.extend(pronoun_edits)

    return BiasDetectionResult(
        text=text,
        has_bias_detected=len(detected_edits) > 0,
        detected_edits=detected_edits
    )
```

**Action Items**:
- [ ] Add `detect_swahili_pronoun_assumption()` method
- [ ] Integrate with main `detect_bias()` flow
- [ ] Add unit tests for Swahili patterns
- [ ] Test on ground truth samples

---

### Task 4.2: Add Swahili Noun Class Tracking
**File**: `eval/bias_detector.py`

**Background**: Swahili uses noun classes (ngeli) for grammatical agreement:
- **m-wa class**: People (mtu/watu, mfanyakazi/wafanyakazi)
- **m-mi class**: Trees/plants
- **ki-vi class**: Things, languages

**Why Important**: Helps identify occupational contexts

**Code Changes**:
```python
# Add to models.py
@dataclass
class SwahiliNounClass:
    """Swahili noun class information."""
    singular_prefix: str  # "m" for m-wa class
    plural_prefix: str    # "wa" for m-wa class
    class_name: str       # "m-wa"
    semantic_category: str  # "people", "things", etc.

# Common noun classes for occupations (m-wa class)
SWAHILI_OCCUPATION_MARKERS = {
    'm': 'singular',  # mfanyakazi (worker)
    'wa': 'plural',   # wafanyakazi (workers)
    'mw': 'singular'  # mwalimu (teacher)
}

def detect_occupation_context(text: str) -> bool:
    """Check if text contains occupational noun class markers."""
    for marker in SWAHILI_OCCUPATION_MARKERS:
        if re.search(rf'\b{marker}\w+', text):
            return True
    return False
```

**Action Items**:
- [ ] Add noun class tracking to lexicon
- [ ] Implement `detect_occupation_context()` helper
- [ ] Use for improving recall (catch occupation variants)

---

### Task 4.3: Implement ML Fallback for Swahili
**New File**: `eval/swahili_ml_detector.py`

**Approach**: Fine-tune mT5-small on expanded Swahili dataset

**Training Data**:
- 200+ ground truth samples (biased → neutral pairs)
- 7,526 KenSwQuAD QA pairs (context examples)
- AfriSenti Swahili subset (social context)

**Model**: `google/mt5-small` (300M parameters, multilingual)

**Code Structure**:
```python
from transformers import MT5ForConditionalGeneration, MT5Tokenizer

class SwahiliMLDetector:
    """ML-based Swahili bias detector using fine-tuned mT5."""

    def __init__(self, model_path: str = "models/mt5-swahili-bias"):
        self.model = MT5ForConditionalGeneration.from_pretrained(model_path)
        self.tokenizer = MT5Tokenizer.from_pretrained(model_path)

    def detect_bias(self, text: str) -> dict:
        """
        Detect bias using ML model.
        Returns: {'has_bias': bool, 'confidence': float, 'corrected': str}
        """
        # Input format: "detect bias: {text}"
        input_text = f"detect bias: {text}"
        inputs = self.tokenizer(input_text, return_tensors="pt")

        # Generate correction
        outputs = self.model.generate(**inputs, max_length=128)
        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # If corrected differs from original, bias detected
        has_bias = corrected != text

        return {
            'has_bias': has_bias,
            'confidence': 0.8,  # Can calculate from model logits
            'corrected': corrected if has_bias else text
        }
```

**Action Items**:
- [ ] Prepare training dataset (biased → neutral pairs)
- [ ] Fine-tune mT5-small on Swahili bias correction
- [ ] Integrate with hybrid detector (30% weight)
- [ ] Evaluate on held-out test set

---

### Task 4.4: Update Correction Evaluator
**File**: `eval/correction_evaluator.py`

**Status**: ✅ Already updated with detailed metrics

**Verification**:
- [ ] Test on new 200-sample dataset
- [ ] Verify category breakdown works with new categories
- [ ] Check regional variation tracking

---

## Phase 5: Evaluation & Iteration (Weeks 11-12)

### Task 5.1: Run Full Evaluation
**Command**:
```bash
python3 eval/correction_evaluator.py
```

**Expected Output**:
```
SUMMARY TABLE - Correction Effectiveness
================================================================================
Language     Pre-F1     Post-F1    Removal%     Status
--------------------------------------------------------------------------------
SW           0.800      0.200      75.0%        Effective
================================================================================
```

**Success Criteria**:
- ✓ Precision: 1.000 (maintain zero false positives)
- ✓ Recall: 0.750+ (improve from 0.516)
- ✓ F1 Score: 0.800+ (improve from 0.681)
- ✓ Bias Removal: 75%+ (improve from 12.5%)

---

### Task 5.2: Failure Analysis
**New File**: `docs/eval/swahili_failure_analysis.md`

**Process**:
1. Identify False Negatives (bias missed)
   - What patterns are we missing?
   - Are they in new lexicon?
   - Are they regional variations?

2. Identify Incomplete Corrections
   - Which terms corrected but bias remains?
   - Are neutral alternatives appropriate?
   - Do we need better context detection?

3. Document Edge Cases
   - Regional variation conflicts
   - Context-dependent terms
   - Ambiguous cases

**Action Items**:
- [ ] Analyze all FN cases
- [ ] Categorize failure types
- [ ] Prioritize lexicon additions
- [ ] Iterate on detection logic

---

### Task 5.3: Community Validation
**Process**:
1. Share results with annotators
2. Review corrections for cultural appropriateness
3. Collect feedback on neutral alternatives
4. Validate regional variation accuracy

**Action Items**:
- [ ] Prepare validation survey for annotators
- [ ] Share 50 example corrections
- [ ] Incorporate feedback into lexicon
- [ ] Document acceptance rate

---

### Task 5.4: Documentation Updates

#### **Update README.md**
**File**: `README.md`

**Changes**:
```markdown
### Detection Performance (Updated Dec 2025)
| Language | F1 Score | Precision | Recall | Lexicon Size | Status |
|----------|----------|-----------|--------|--------------|---------|
| English  | 0.764    | 1.000     | 0.618  | 514 entries  | Production |
| Swahili  | 0.800    | 1.000     | 0.750  | 150 terms    | Production ← UPDATED |
| French   | 0.627    | 1.000     | 0.457  | 51 terms     | Beta |
| Gikuyu   | 0.714    | 1.000     | 0.556  | 22 terms     | Beta |

### Correction Effectiveness (Updated Dec 2025)
| Language | Detection Rate | Bias Removal Rate | Status |
|----------|---------------|-------------------|---------|
| English  | 61.8%         | **100.0%**        | Production |
| Swahili  | 75.0%         | **75.0%**         | Production ← UPDATED |
| French   | 45.7%         | 56.2%             | Beta |
| Gikuyu   | 55.6%         | 70.0%             | Beta |
```

#### **Update CLAUDE.md**
**File**: `CLAUDE.md`

**Add Swahili Section**:
```markdown
## Swahili-Specific Implementation

### Natural Gender Neutrality
Swahili is grammatically gender-neutral:
- Single pronoun "yeye" = he/she
- No gendered nouns (unlike French/Spanish)
- Occupational terms generally neutral

### Bias Sources
1. Colonial/borrowed terms (askari, polisi)
2. Cultural assumptions in media
3. Pronoun assumptions (yeye + gendered descriptors)

### Detection Approach
1. **Lexicon-based** (150+ terms)
2. **Context-aware pronoun detection**
3. **Noun class (ngeli) tracking for occupations**
4. **ML fallback** (mT5-small, 30% weight)

### Regional Variations
- Kenya: askari (guard/soldier)
- Tanzania: askari (soldier/police)
- Uganda: mlinzi (guard)

Lexicon includes regional variation notes for accurate correction.
```

#### **Create Implementation Summary**
**New File**: `docs/eval/SWAHILI_EXPANSION_SUMMARY.md`

**Content**:
```markdown
# Swahili Lexicon Expansion Summary

## Outcome
- **Lexicon**: 15 → 150 terms (10x increase)
- **Ground Truth**: 63 → 200 samples (3x increase)
- **F1 Score**: 0.681 → 0.800 (+17%)
- **Recall**: 0.516 → 0.750 (+45%)
- **Bias Removal**: 12.5% → 75% (6x improvement)

## Key Learnings
[Document what worked, what didn't, lessons for French/Gikuyu]

## Contributors
[List native speaker annotators with permission]

## Resources Used
[Link to datasets, tools, community support]
```

---

## Files Modified Summary

### Core Files
```
✓ rules/lexicon_sw_v2.csv                     [15 → 150+ terms]
✓ eval/ground_truth_sw.csv                    [63 → 200+ samples]
✓ eval/bias_detector.py                       [Add Swahili detection]
✓ eval/correction_evaluator.py                [Already updated]
✓ README.md                                   [Update metrics]
✓ CLAUDE.md                                   [Add Swahili docs]
```

### New Files Created
```
✓ scripts/data_collection/mine_swahili_news.py
✓ scripts/data_collection/scrape_job_listings.py
✓ data/clean/swahili_bias_candidates_master.csv
✓ eval/swahili_ml_detector.py
✓ eval/winobias_swahili_templates.txt
✓ docs/eval/SWAHILI_ANNOTATOR_RECRUITMENT.md
✓ docs/eval/SWAHILI_ANNOTATION_GUIDELINES.md
✓ docs/eval/swahili_failure_analysis.md
✓ docs/eval/SWAHILI_EXPANSION_SUMMARY.md
✓ docs/eval/SWAHILI_IMPROVEMENT_RESEARCH.md    [Already created]
✓ docs/eval/SWAHILI_IMPLEMENTATION_PLAN.md     [This file]
```

### Data Files
```
✓ data/raw/swahili_wikipedia_corpus.txt
✓ data/raw/swahili_news_bias_candidates.csv
✓ data/raw/swahili_job_terms.csv
✓ data/clean/swahili_bias_candidates_master.csv
```

---

## Resource Requirements

### Budget
- **Annotators**: $1,200 (5-10 people × 40 hours × $15-20/hr)
- **Linguistic Consultant**: $1,000 (1 person × 20 hours × $50/hr)
- **ML Training**: $50 (Google Colab GPU credits)
- **Total**: ~$2,250

### Time
- **Data Collection**: 2 weeks
- **Native Speaker Validation**: 2 weeks
- **Dataset Expansion**: 2 weeks
- **Technical Implementation**: 4 weeks
- **Evaluation & Iteration**: 2 weeks
- **Total**: 12 weeks

### Tools
- Google Sheets or Label Studio (annotation)
- Python 3.12+ (existing)
- Transformers library (mT5 fine-tuning)
- Google Colab (free GPU tier or $10/month)

---

## Risk Mitigation

### Risk 1: Annotator Recruitment Delays
**Impact**: High
**Probability**: Medium
**Mitigation**:
- Start recruitment immediately (Week 1)
- Have backup platforms (Upwork, Fiverr)
- Partner with universities early
- Offer competitive rates

### Risk 2: Low Inter-Annotator Agreement
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Comprehensive training (5 hours)
- Clear annotation guidelines with examples
- Weekly check-ins to resolve confusion
- 3 annotators per term for quality control

### Risk 3: Regional Variation Conflicts
**Impact**: Medium
**Probability**: High
**Mitigation**:
- Document all variations in lexicon
- Recruit from Kenya, Tanzania, Uganda
- Prioritize majority consensus
- Mark context-dependent terms

### Risk 4: Budget Overrun
**Impact**: Low
**Probability**: Low
**Mitigation**:
- Fixed annotator rates ($15-20/hr)
- Use free corpora (Wikipedia, news)
- Use Google Colab free tier
- Phased approach (can stop at 100 terms if needed)

### Risk 5: Timeline Slip
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Weekly progress tracking
- Parallel workstreams where possible
- MVP at Week 8 (100 terms, 150 samples)
- Full target by Week 12

---

## Success Metrics Dashboard

### Week 2 Checkpoint
- [ ] Wikipedia corpus extracted
- [ ] 500+ candidate terms identified
- [ ] Annotators recruited

### Week 4 Checkpoint
- [ ] 200+ terms validated
- [ ] Regional variations documented
- [ ] Annotation complete

### Week 6 Checkpoint
- [ ] Lexicon: 100+ terms added
- [ ] Ground truth: 150+ samples
- [ ] WinoBias templates created

### Week 8 Checkpoint (MVP)
- [ ] Lexicon: 100 terms total
- [ ] Ground truth: 150 samples
- [ ] Context detection implemented
- [ ] **Expected Recall**: 0.650+
- [ ] **Expected Removal**: 60%+

### Week 10 Checkpoint
- [ ] Lexicon: 150+ terms
- [ ] Ground truth: 200+ samples
- [ ] ML fallback integrated
- [ ] **Expected Recall**: 0.750+
- [ ] **Expected Removal**: 75%+

### Week 12 Final
- [  ] All targets met
- [ ] Documentation complete
- [ ] Community validation done
- [ ] PR ready for main branch

---

## Next Actions (This Week)

### Immediate (Day 1-2)
1. ✅ Create feature branch: `feature/swahili-lexicon-expansion`
2. ✅ Set up todo list tracking
3. ✅ Create implementation plan (this document)
4. [ ] Start Wikipedia extraction
5. [ ] Post annotator recruitment on Masakhane

### Week 1 (Days 3-7)
1. [ ] Extract full Swahili Wikipedia corpus
2. [ ] Access Swahili news dataset
3. [ ] Create job listing scraper
4. [ ] Compile master candidate list (500+ terms)
5. [ ] Finalize annotator recruitment

---

## Sign-Off

**Branch**: `feature/swahili-lexicon-expansion`
**Owner**: Development Team
**Reviewers**: Native Speaker Consultants + Linguistic Expert
**Target Completion**: Week 12
**Success Criteria**: Recall >0.75, Removal >75%, Precision maintained at 1.000

---

**Let's improve Swahili! 🇰🇪 🇹🇿 🇺🇬**
