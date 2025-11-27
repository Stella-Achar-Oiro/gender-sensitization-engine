# Swahili Gender Bias Detection: Deep Research & Improvement Strategy

**Date**: November 27, 2025
**Goal**: Improve Swahili bias detection from 12.5% to >70% bias removal rate, matching English performance

---

## Executive Summary

Current Swahili system performance:
- **F1 Score**: 0.681 (Precision: 1.000, Recall: 0.516)
- **Bias Removal Rate**: 12.5% (vs English: 100%)
- **Lexicon Size**: 15 terms (vs English: 514 entries)

**Key Finding**: Swahili is naturally gender-neutral in grammar but still exhibits occupational bias. The 12.5% removal rate indicates severe lexicon gaps, not detection accuracy issues.

---

## 1. Swahili Language Characteristics

### Natural Gender Neutrality

Swahili has significant advantages for inclusive language:

1. **Gender-neutral pronouns**: "yeye" means both "he" and "she"
2. **Gender-neutral occupations**: Most professional terms don't distinguish gender
   - "mwigizaji" (actor/actress - no distinction)
   - "mtumishi mezani" (waiter/waitress - no distinction)
   - "fundi" terms (skilled workers) are all gender-neutral
3. **No grammatical gender**: Unlike French/Spanish, Swahili doesn't assign gender to nouns

**Source**: [Swahili Pronouns--and Some Titles--Are Gender Neutral](https://www.linkedin.com/pulse/swahili-pronouns-and-some-titles-are-gender-neutral-tom-midigo)

### Where Bias Still Exists

Despite natural neutrality, bias manifests in:
1. **Colonial occupation terms**: Borrowed from English/Arabic with gendered implications
2. **Cultural assumptions**: Role-based expectations (e.g., "mwuguzi" = nurse, often assumed female)
3. **Media representation**: East African media reinforces gender stereotypes in reporting
4. **Implicit associations**: "askari" (soldier/guard) carries masculine connotations

**Source**: [Coverage and Framing of Women in East African Media](https://aku.edu/gsmc/Documents/The%20State%20Of%20Women%20in%20Media%20Book.pdf)

---

## 2. Available Swahili NLP Datasets

### Large-Scale Text Corpora

#### **KenCorpus (2022)**
- **Size**: 2,585 texts (~1.8M words) + 27 hours transcribed speech
- **Content**: Mix of written and spoken Swahili from Kenya
- **Use Case**: Can mine for occupational terms and bias patterns
- **Source**: [KenCorpus: A Kenyan Language Corpus](https://arxiv.org/pdf/2208.12081)

#### **Helsinki Corpus of Swahili 2.0 (HCS 2.0)**
- Comprehensive annotated corpus for linguistic analysis
- **Source**: [Helsinki Corpus of Swahili 2.0](https://www.kielipankki.fi/corpora/hcs2/)

#### **Kwici: Swahili Wikipedia Corpus**
- **Size**: 151,753 sentences, 2.8M words (as of Dec 2015)
- **Use Case**: Mine for professional/occupational contexts
- **Source**: [Kwici: Swahili Wikipedia corpus](https://kevindonnelly.org.uk/swahili/swwiki/)

#### **Swahili News Dataset**
- **Size**: 31,000+ news articles across categories (local, business, health, sports)
- **Use Case**: Analyze gender representation in media contexts
- **Bias**: East Africa media study found only 3% of GBV stories focused on perpetrators
- **Source**: [Language Datasets - Lacuna Fund](https://lacunafund.org/datasets/language/)

### Question-Answering & Sentiment Datasets

#### **KenSwQuAD (Swahili QA Dataset)**
- **Size**: 7,526 QA pairs from 1,445 Swahili texts
- **Annotators**: Native speakers
- **Use Case**: Context-aware bias detection training
- **Source**: [Language Datasets - Lacuna Fund](https://lacunafund.org/datasets/language/)

#### **AfriSenti Corpus (includes Swahili)**
- **Size**: 110,000+ tweets across 14 African languages
- **Annotators**: 3 native speakers per tweet
- **Use Case**: Social media bias patterns
- **Source**: [State of NLP in Kenya: A Survey](https://arxiv.org/html/2410.09948v1)

---

## 3. Recent Research on African Language Bias

### Major Survey Findings (2024-2025)

#### **"Charting the Landscape of African NLP" (2025)**
- Analyzed **734 research papers** on African NLP (5-year span)
- **29 papers** addressed ethics, bias, and fairness
- **Most addressed**: Gender bias and cultural bias
- **Gap**: "Much remains to be done to address bias and ensure equity"
- **Source**: [Charting the Landscape of African NLP](https://arxiv.org/html/2505.21315v3)

#### **"Benchmarking Sociolinguistic Diversity in Swahili" (2025)**
- **Dataset**: 2,170 free-text responses from Kenyan Swahili speakers
- **Metadata**: Gender, tribe, income, education
- Enables **intersectional bias analysis** (gender × tribe, gender × income)
- **Key Finding**: Biases at confluence of tribal affiliations and gender
- **Source**: [Benchmarking Sociolinguistic Diversity in Swahili NLP](https://arxiv.org/html/2508.14051)

#### **Bias in Machine Translation for African Languages (2024)**
- **Finding**: 93% of Afan Oromo, 80% of Tigrinya, 72% of Amharic sentences showed gender bias
- **Gap**: "Limited research exploring gender bias in low-resource languages"
- **Swahili Status**: Underrepresented despite 100-150M speakers
- **Source**: [Current State-of-the-Art of Bias Detection in MT](https://arxiv.org/html/2410.21126v1)

### ASR Bias in African Languages

- **Finding**: African named entities cause significant ASR performance degradation
- **Mitigation**: Multilingual pre-training, intelligent data augmentation, fine-tuning on multiple African accents
- **Source**: [Systematic Review on Bias in ASR for African Languages](https://dl.acm.org/doi/10.1145/3769089)

---

## 4. Lexicon Creation Methodologies

### State-of-the-Art Approaches

#### **1. Supervised Learning Method (Chinese Gender Lexicon, 2023)**
- **Process**:
  1. Collect job advertisements corpus
  2. Use Word2Vec to identify candidate gender words
  3. Train SVR model to determine gender scores
  4. Validate with human annotators
- **Result**: Scalable, data-driven lexicon
- **Source**: [Creating a Chinese gender lexicon](https://www.sciencedirect.com/science/article/abs/pii/S0306457323001619)

#### **2. Taxonomy-Based Approach (2022)**
- **Categories**:
  - Generic He/She
  - Explicit Marking of Sex
  - Gendered Neologisms
  - Occupational Stereotypes
- **Output**: Labeled datasets + exhaustive lexicons
- **Source**: [Gender Bias in Text: Labeled Datasets and Lexicons](https://arxiv.org/abs/2201.08675)

#### **3. WinoBias Methodology**
- **Format**: Winograd Schema for coreference resolution
- **Source**: US Department of Labor occupational statistics
- **Categories**: Stereotypical vs. non-stereotypical scenarios
- **Limitation**: No African language adaptations found
- **Source**: [Mitigating Gender-Occupational Stereotypes](https://www.johnsnowlabs.com/mitigating-gender-occupational-stereotypes-in-ai-evaluating-language-models-with-the-wino-bias-test-through-the-langtest-library/)

### Annotation Best Practices

#### **Phase 1: Training & Guidelines**
- Overall training on annotation process
- Develop annotation schema
- Refine definitions with iterative review
- Create harm-awareness protocols (bias content can be triggering)

#### **Phase 2: Gold Standard Creation**
- Multiple annotators per sample (AfriSenti used 3)
- Inter-annotator agreement checks
- Native speaker requirement
- Diverse annotator backgrounds (gender, status, education)

**Source**: [Gender Bias in Text: Labeled Datasets and Lexicons](https://arxiv.org/abs/2201.08675)

---

## 5. Crowdsourcing & Native Speaker Engagement

### Masakhane NLP Initiative

- **Approach**: Build NLP clubs around partner universities
- **Languages**: Includes Swahili
- **Activities**:
  - Mozilla Common Voice platform contributions
  - Community-driven data collection
  - Collaborative transcription
- **Source**: [Masakhane - MakerereNLP](https://www.masakhane.io/ongoing-projects/makererenlp-text-speech-for-east-africa)

### Successful Crowdsourcing Examples

#### **KenSwQuAD Creation**
- **Method**: Crowdsource QA pairs from Swahili texts
- **Annotators**: Native speakers
- **Output**: 7,526 QA pairs from 1,445 texts
- Each text: minimum 5 QA pairs

#### **AfriSenti Annotation**
- **Method**: 3 native speakers per tweet
- **Scale**: 110,000+ tweets
- **Languages**: 14 African languages including Swahili

#### **Lacuna Fund Parallel Corpora**
- **Goal**: 900,000 sentence pairs via crowdsourcing
- **Method**: Leverage online communities and social media
- **Benefit**: Culturally sensitive, native knowledge pooling

**Source**: [Low-Resource Languages: Building NLP Datasets](https://keylabs.ai/blog/annotating-low-resource-languages-building-nlp-datasets-from-scratch/)

---

## 6. Data Collection Strategy for Swahili

### Phase 1: Corpus Mining (Weeks 1-2)

#### **A. Wikipedia Mining**
```python
# Target: Kwici corpus (2.8M words)
# Focus areas:
- Professional biographies (occupations)
- Educational articles (roles, titles)
- Historical figures (gendered descriptions)
```

**Action**: Use `scripts/data_collection/extract_wikipedia.py` to extract Swahili Wikipedia

#### **B. News Corpus Analysis**
```python
# Target: 31,000+ Swahili news articles
# Categories to mine:
- Business (CEO, entrepreneur, manager)
- Health (doctor, nurse, therapist)
- Sports (coach, athlete, referee)
- Politics (leader, minister, spokesperson)
```

**Expected Output**: 500+ candidate bias terms

#### **C. Job Listing Scraping**
- **Sources**: BrighterMonday Kenya, Fuzu, Brighter Monday Tanzania
- **Method**: Scrape job titles and descriptions in Swahili
- **Expected**: 200+ occupational terms

### Phase 2: Term Validation (Weeks 3-4)

#### **A. Native Speaker Annotation**
**Method**: Recruit 5-10 Swahili native speakers via:
- Masakhane NLP community
- University partnerships (Kenya, Tanzania)
- Upwork/Fiverr with strict vetting

**Task**: Annotate terms for:
1. Is this term gendered? (Yes/No)
2. Severity (Replace / Warn)
3. Neutral alternative(s)
4. Context examples

**Compensation**: $15-20/hour (fair rate for East Africa)

#### **B. Cultural Context Validation**
**Questions for each term**:
- Does this term carry gender assumptions in Kenya? Tanzania? Uganda?
- Are there regional variations?
- What is the culturally appropriate neutral term?

### Phase 3: Dataset Creation (Weeks 5-6)

#### **A. Ground Truth Expansion**
**Current**: 63 samples
**Target**: 200+ samples

**Sources**:
1. Adapt WinoBias templates to Swahili
2. Mine real examples from news corpus
3. Create coreference resolution scenarios
4. Add pronoun assumption cases

**Distribution**:
- Occupation: 100 samples
- Pronoun assumption: 50 samples
- Pronoun generic: 30 samples
- Honorifics: 20 samples

#### **B. Lexicon Expansion**
**Current**: 15 terms
**Target**: 150+ terms (10x increase)

**Structure**:
```csv
biased,neutral_primary,neutral_alternatives,severity,tags,examples,regional_notes
askari,afisa wa usalama,mlinzi,replace,occupation,"askari alimkamata","More neutral in Tanzania"
```

---

## 7. Specific Swahili Bias Categories to Target

### Category 1: Occupational Terms (Priority: HIGH)

**Colonial/Arabic Borrowed Terms** (often carry gender bias):
```
Current lexicon (15 terms):
- askari → afisa wa usalama (security officer)
- waiter/waitress → mtumishi mezani
- [13 more needed]

To add (estimated 80+ terms):
- polisi/askari polisi → afisa wa polisi
- daktari → mtaalamu wa afya (when gendered)
- mwalimu mkuu → kiongozi wa shule (headmaster → head teacher)
- katibu → katibu mkuu (secretary, when implying gender)
- karani → mfanyakazi wa ofisi
- msichana wa nyumbani → mfanyakazi wa nyumbani (house girl)
- mpishi → mtayarishaji chakula (cook, when gendered)
- dereva → mwendeshaji gari (driver, when gendered)
```

### Category 2: Pronoun Assumptions (Priority: HIGH)

**Examples to add**:
```
Biased: "Mwuguzi alimhudumia mgonjwa wake, yeye ni mwanamke mzuri"
(The nurse served their patient, she is a good woman)

Neutral: "Mwuguzi alimhudumia mgonjwa wake, yeye ni mfanyakazi mzuri"
(The nurse served their patient, they are a good worker)

Biased: "Injinia alisema kwamba anajenga daraja, huyu mwanamume ni hodari"
(The engineer said they are building a bridge, this man is skilled)

Neutral: "Injinia alisema kwamba anajenga daraja, huyu ni hodari"
(The engineer said they are building a bridge, this person is skilled)
```

### Category 3: Familial Role Assumptions

**Current gap**: Not in lexicon
**Examples**:
```
- mama wa nyumbani → mzazi wa nyumbani (housewife → homemaker/parent)
- baba wa familia → kiongozi wa familia (family patriarch → family leader)
- binti → mtoto (girl, when assuming gender)
- mvulana → mtoto (boy, when assuming gender)
```

### Category 4: Courtesy Titles

**Current gap**: Not in lexicon
**Examples**:
```
- Bwana/Bibi → Mheshimiwa (Mr./Mrs. → Respected One)
- Shangazi/Mjomba → ndugu (gendered aunt/uncle → relative)
```

---

## 8. Technical Implementation Strategy

### A. Expand Lexicon Structure

**Current structure**:
```csv
biased,neutral_primary,severity
```

**Proposed enhanced structure**:
```csv
biased,neutral_primary,neutral_alternatives,severity,tags,context_required,examples_biased,examples_neutral,regional_variations,ngeli_class
```

**New fields**:
- `neutral_alternatives`: Comma-separated list of alternatives
- `context_required`: Boolean - does correction need context analysis?
- `examples_biased`: Real-world biased usage
- `examples_neutral`: Corrected version
- `regional_variations`: "KE:X,TZ:Y,UG:Z" format
- `ngeli_class`: Swahili noun class (for agreement rules)

### B. Add Context-Aware Correction

**Current limitation**: Simple word replacement
**Problem**: "Yeye ni daktari mzuri" could mean "He/She is a good doctor"

**Solution**: Implement context window analysis
```python
def detect_pronoun_assumption(text: str, language: Language) -> bool:
    """Detect when 'yeye' is incorrectly assumed gendered via context."""
    # Pattern: yeye + occupation + gendered descriptor
    patterns = [
        r'yeye\s+\w+\s+(mwanamume|mwanamke)',  # yeye ... man/woman
        r'(mwanamume|mwanamke)\s+\w+\s+yeye',  # man/woman ... yeye
    ]
    return any(re.search(p, text) for p in patterns)
```

### C. Improve Category Detection

**Add morphology analysis**:
- Swahili uses noun classes (ngeli) for agreement
- Track m-wa class (people): mtu/watu, mfanyakazi/wafanyakazi
- Use class information to detect occupational contexts

### D. Implement ML Fallback (30% weight)

**Training data sources**:
1. Expanded ground truth (200+ samples)
2. KenSwQuAD (7,526 QA pairs) - mine for bias patterns
3. AfriSenti (Swahili subset) - social context

**Model**: Fine-tune mT5 on Swahili bias correction
```python
from transformers import MT5ForConditionalGeneration

# Input: "Yeye ni daktari mzuri, mwanamume huyu"
# Output: "Yeye ni daktari mzuri"  # Remove gender marker
```

---

## 9. Evaluation Metrics & Targets

### Current Performance
```
Precision: 1.000 ✓ (maintain)
Recall: 0.516 → Target: 0.750
F1 Score: 0.681 → Target: 0.800
Bias Removal: 12.5% → Target: 75%+
```

### Improvement Milestones

**Week 4** (Quick wins - Lexicon expansion):
- Lexicon: 15 → 50 terms
- Expected Recall: 0.516 → 0.600
- Expected Bias Removal: 12.5% → 40%

**Week 8** (Full lexicon + validation):
- Lexicon: 50 → 150 terms
- Ground truth: 63 → 200 samples
- Expected Recall: 0.600 → 0.750
- Expected Bias Removal: 40% → 75%

**Week 12** (ML integration):
- Add mT5 fine-tuned model
- Context-aware corrections
- Expected Recall: 0.750 → 0.800+
- Expected Bias Removal: 75% → 85%+

---

## 10. Resource Requirements

### Human Resources

#### **Native Speakers** (5-10 annotators)
- **Task**: Term validation, example creation
- **Time**: 40-60 hours total
- **Rate**: $15-20/hour
- **Total cost**: $600-1,200

#### **Linguistic Expert** (1 consultant)
- **Task**: Review lexicon, validate cultural appropriateness
- **Time**: 20 hours
- **Rate**: $50-75/hour
- **Total cost**: $1,000-1,500

### Computational Resources

- **Wikipedia extraction**: Existing scripts
- **ML training**: Google Colab free tier or $50 GPU credits
- **Storage**: <5GB (free tier sufficient)

### Total Estimated Budget: $1,650-2,750

---

## 11. Key Papers to Reference

### Must-Read Research

1. **[Benchmarking Sociolinguistic Diversity in Swahili NLP (2025)](https://arxiv.org/html/2508.14051)** - Latest Swahili bias research with intersectional analysis

2. **[Building Text and Speech Benchmark Datasets for East African Languages (2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/ail2.92)** - Best practices for dataset creation

3. **[Gender Bias in Text: Labeled Datasets and Lexicons (2022)](https://arxiv.org/abs/2201.08675)** - Taxonomy and methodology for lexicon creation

4. **[Charting the Landscape of African NLP (2025)](https://arxiv.org/html/2505.21315v3)** - Comprehensive survey of African NLP including bias research

5. **[Creating a Chinese Gender Lexicon (2023)](https://www.sciencedirect.com/science/article/abs/pii/S0306457323001619)** - Supervised learning methodology for lexicon expansion

6. **[Current State-of-the-Art: Bias Detection in MT for African Languages (2024)](https://arxiv.org/html/2410.21126v1)** - Bias in African language machine translation

---

## 12. Action Plan (12-Week Timeline)

### Weeks 1-2: Data Collection
- [ ] Extract Swahili Wikipedia using existing scripts
- [ ] Access Swahili news corpus (31,000 articles)
- [ ] Scrape East African job listings
- [ ] Mine 500+ candidate bias terms

### Weeks 3-4: Native Speaker Validation
- [ ] Recruit 5-10 Swahili native speakers via Masakhane/universities
- [ ] Create annotation guidelines (adapt from [Gender Bias in Text paper](https://arxiv.org/abs/2201.08675))
- [ ] Validate 200+ terms with native speakers
- [ ] Document regional variations (KE/TZ/UG)

### Weeks 5-6: Dataset Expansion
- [ ] Expand ground truth: 63 → 200+ samples
- [ ] Create WinoBias-style Swahili templates
- [ ] Mine real examples from news corpus
- [ ] Add pronoun assumption & generic cases

### Weeks 7-8: Lexicon Development
- [ ] Expand lexicon: 15 → 150 terms (10x)
- [ ] Add enhanced fields (alternatives, examples, regional notes)
- [ ] Implement noun class (ngeli) tracking
- [ ] Document cultural context for each term

### Weeks 9-10: Technical Implementation
- [ ] Implement context-aware pronoun detection
- [ ] Add morphology analysis for noun classes
- [ ] Fine-tune mT5 on expanded dataset
- [ ] Integrate ML fallback (30% weight)

### Weeks 11-12: Evaluation & Iteration
- [ ] Run full evaluation on 200+ samples
- [ ] Target: Recall >0.75, Bias Removal >75%
- [ ] Failure analysis & lexicon refinement
- [ ] Document lessons learned

---

## 13. Community Partnerships

### Organizations to Contact

1. **[Masakhane NLP](https://www.masakhane.io/)** - African NLP community
2. **[Knowledge 4 All Foundation](https://k4all.org/)** - Kiswahili language database project
3. **University of Nairobi** - Linguistics Department
4. **University of Dar es Salaam** - Kiswahili Studies
5. **Aga Khan University** - Media research on gender in East Africa

### Crowdsourcing Platforms

1. **Mozilla Common Voice** - Voice data collection
2. **Appen** - Professional annotation services
3. **Upwork/Fiverr** - Vetted native speaker annotators
4. **AfricaNLP Workshop** - Academic collaboration

---

## 14. Success Metrics

### Technical Metrics
- ✓ **Precision maintained**: 1.000 (zero false positives)
- 📈 **Recall improvement**: 0.516 → 0.750+ (+45%)
- 📈 **F1 Score improvement**: 0.681 → 0.800+ (+17%)
- 🎯 **Bias Removal Rate**: 12.5% → 75%+ (6x improvement)
- 📚 **Lexicon expansion**: 15 → 150+ terms (10x)
- 📊 **Dataset expansion**: 63 → 200+ samples (3x)

### Impact Metrics
- Number of native speakers engaged
- Regional coverage (Kenya, Tanzania, Uganda)
- Cultural appropriateness validation score
- Community acceptance rate

---

## 15. Risk Mitigation

### Risk 1: Native Speaker Recruitment
**Mitigation**: Partner with Masakhane, university communities, offer fair compensation

### Risk 2: Regional Variations
**Mitigation**: Recruit annotators from Kenya, Tanzania, Uganda; document variations

### Risk 3: Cultural Sensitivity
**Mitigation**: Engage linguistic expert consultant, community review

### Risk 4: Budget Constraints
**Mitigation**: Prioritize high-impact terms, phased approach, leverage free corpora

---

## Conclusion

The 12.5% bias removal rate is solvable through systematic lexicon expansion. Swahili's natural gender-neutrality is an advantage - we're not fighting the language, we're filling gaps.

**Key Insight**: Unlike English where bias is deeply embedded, Swahili bias comes from:
1. Colonial/borrowed terms
2. Cultural assumptions in media
3. Occupational stereotypes

With 150+ validated terms and 200+ test samples, we can achieve 75%+ bias removal while maintaining perfect precision.

**Next Step**: Begin Wikipedia extraction this week.

---

## References

All sources are hyperlinked throughout the document. Key resource repositories:

- [Lacuna Fund Language Datasets](https://lacunafund.org/datasets/language/)
- [African NLP Public Datasets (GitHub)](https://github.com/Andrews2017/africanlp-public-datasets)
- [Masakhane NLP](https://www.masakhane.io/)
- [AfricaNLP Workshop](https://sites.google.com/view/africanlp2024/home)
