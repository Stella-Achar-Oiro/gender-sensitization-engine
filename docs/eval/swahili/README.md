# Swahili Lexicon Expansion Documentation

This folder contains all documentation related to improving Swahili gender bias detection from 12.5% to 75%+ bias removal rate.

## Contents

### [improvement_research.md](improvement_research.md)
**600+ lines** of comprehensive research including:
- Available Swahili NLP datasets (KenCorpus, Wikipedia, news corpora)
- Recent research papers (2024-2025) on African language bias
- Lexicon creation methodologies
- Crowdsourcing strategies via Masakhane
- Native speaker annotation best practices
- Swahili language characteristics (gender neutrality, bias sources)

**Key Finding**: Swahili is naturally gender-neutral, making bias correction easier than gendered languages.

### [implementation_plan.md](implementation_plan.md)
**Detailed 12-week plan** with:
- Phase-by-phase breakdown (5 phases)
- File-by-file modification checklist
- Specific code changes needed
- Success metrics and checkpoints
- Budget: ~$2,250
- Timeline: 12 weeks

## Project Goals

### Current State
- **F1 Score**: 0.681 (Precision: 1.000, Recall: 0.516)
- **Bias Removal**: 12.5%
- **Lexicon**: 15 terms
- **Dataset**: 63 samples

### Target State (Week 12)
- **F1 Score**: 0.800+ (Precision: 1.000, Recall: 0.750+)
- **Bias Removal**: 75%+
- **Lexicon**: 150+ terms (10x)
- **Dataset**: 200+ samples (3x)

## Implementation Phases

1. **Phase 1 (Weeks 1-2)**: Data Collection
   - Extract Swahili Wikipedia corpus
   - Mine news articles for bias terms
   - Scrape job listings
   - Compile 500+ candidate terms

2. **Phase 2 (Weeks 3-4)**: Native Speaker Validation
   - Recruit 5-10 annotators via Masakhane
   - Create annotation guidelines
   - Validate 200+ terms
   - Document regional variations (Kenya/Tanzania/Uganda)

3. **Phase 3 (Weeks 5-6)**: Lexicon & Dataset Expansion
   - Expand lexicon to 150+ terms
   - Add enhanced fields (alternatives, examples, regional notes)
   - Expand ground truth to 200+ samples
   - Create WinoBias-style Swahili templates

4. **Phase 4 (Weeks 7-10)**: Technical Implementation
   - Add context-aware Swahili detection
   - Implement pronoun assumption detection
   - Track Swahili noun classes (ngeli)
   - Fine-tune mT5 model

5. **Phase 5 (Weeks 11-12)**: Evaluation & Iteration
   - Run full evaluation
   - Verify targets met (Recall >0.75, Removal >75%)
   - Document lessons learned

## Files to Modify

### Core Files
```
✓ rules/lexicon_sw_v2.csv                     [15 → 150+ terms]
✓ eval/ground_truth_sw.csv                    [63 → 200+ samples]
✓ eval/bias_detector.py                       [Add Swahili detection]
✓ README.md                                   [Update metrics]
✓ CLAUDE.md                                   [Add Swahili docs]
```

### New Files to Create
```
✓ scripts/data_collection/mine_swahili_news.py
✓ scripts/data_collection/scrape_job_listings.py
✓ eval/swahili_ml_detector.py
✓ eval/winobias_swahili_templates.txt
✓ docs/eval/swahili/annotation_guidelines.md
✓ docs/eval/swahili/annotator_recruitment.md
✓ docs/eval/swahili/failure_analysis.md
✓ docs/eval/swahili/expansion_summary.md
```

## Community Resources

### Partners
- [Masakhane NLP](https://www.masakhane.io/) - African NLP community
- University of Nairobi - Linguistics Department
- University of Dar es Salaam - Kiswahili Studies
- [Knowledge 4 All Foundation](https://k4all.org/) - Kiswahili database project

### Datasets Used
- [KenCorpus](https://arxiv.org/pdf/2208.12081) - 1.8M words
- [Swahili Wikipedia Corpus](https://kevindonnelly.org.uk/swahili/swwiki/) - 2.8M words
- [Swahili News Dataset](https://lacunafund.org/datasets/language/) - 31K articles
- [KenSwQuAD](https://lacunafund.org/datasets/language/) - 7,526 QA pairs

## Budget Breakdown

- **Native Speaker Annotators**: $1,200 (5-10 people × 40 hours × $15-20/hr)
- **Linguistic Consultant**: $1,000 (1 person × 20 hours × $50/hr)
- **ML Training**: $50 (Google Colab GPU credits)
- **Total**: ~$2,250

## Success Metrics

### Technical Metrics
-  Precision: 1.000 (maintain zero false positives)
-  Recall: 0.516 → 0.750+ (+45%)
-  F1 Score: 0.681 → 0.800+ (+17%)
-  Bias Removal: 12.5% → 75%+ (6x improvement)

### Checkpoints
- **Week 2**: 500+ candidate terms identified
- **Week 4**: 200+ terms validated
- **Week 6**: 100+ terms in lexicon, 150+ samples
- **Week 8** (MVP): Recall 0.650+, Removal 60%+
- **Week 10**: Recall 0.750+, Removal 75%+
- **Week 12**: All targets met, docs complete

##  Getting Started

1. **Read the Research**: Start with [improvement_research.md](improvement_research.md)
2. **Review the Plan**: Check [implementation_plan.md](implementation_plan.md)
3. **Track Progress**: Use the todo list in the repository
4. **Join Community**: Connect with Masakhane NLP

##  Additional Documentation

As the project progresses, additional documents will be added:
- `annotation_guidelines.md` - For native speaker annotators
- `annotator_recruitment.md` - Recruitment strategy and criteria
- `failure_analysis.md` - Analysis of missed bias cases
- `expansion_summary.md` - Final results and lessons learned

##  Important Notes

1. **Maintain Perfect Precision**: Zero false positives is non-negotiable
2. **Regional Variations**: Document differences between Kenya, Tanzania, Uganda
3. **Cultural Sensitivity**: Engage native speakers for validation
4. **Phased Approach**: Can achieve 60% removal at Week 8 if budget/time constrained

---

**Status**: Planning Complete  | **Next**: Begin Data Collection (Phase 1)
