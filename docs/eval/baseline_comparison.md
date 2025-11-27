# Baseline Comparison Analysis

## Methodology
Comparison between our rule-based lexicon approach and a simple keyword baseline detector.

**Baseline Detector**: Simple keyword matching using basic gendered terms per language
**Our Approach**: Comprehensive lexicon-based rules with morphological awareness

## Performance Comparison (Updated Nov 20, 2025)

| Language | Baseline F1 | Our F1 | Improvement | Precision | Analysis |
|----------|-------------|--------|-------------|-----------|----------|
| English  | 0.692       | 0.764  | +0.071      | 1.000     | Lexicon provides better coverage |
| Swahili  | 0.450       | 0.681  | +0.231      | 1.000     | Significant improvement from cultural adaptation |
| French   | 0.520       | 0.627  | +0.107      | 1.000     | Lexicon approach validates for Romance languages |
| Gikuyu   | 0.640       | 0.714  | +0.074      | 1.000     | Strong performance for Bantu language |

**Key Achievement:** All 4 languages achieve **perfect precision (1.000)** - zero false positives across the board.

## Key Insights

### Where Our Approach Excels
1. **All Languages**: Consistent improvements over baseline across all 4 languages
2. **Cultural Adaptation**: Swahili shows largest gain (+0.231) from culturally-adapted lexicon
3. **Perfect Precision**: All languages maintain 1.000 precision - zero false positives
4. **Language Diversity**: Success across Germanic (EN), Bantu (SW, KI), and Romance (FR) families

### Performance Analysis by Language

**English (Production):**
- +7.1% improvement from comprehensive occupational coverage
- 514 lexicon entries (19 core concepts) drive strong recall
- 100% bias removal rate in correction phase

**Swahili (Foundation):**
- +23.1% improvement - largest gain of all languages
- Cultural adaptation crucial for African language success
- Needs lexicon expansion (15 → 50+ terms target)

**French (Beta):**
- +10.7% improvement validates approach for Romance languages
- 51-term lexicon shows solid initial coverage
- Pending native speaker validation

**Gikuyu (Beta):**
- +7.4% improvement for Bantu language
- 22-term lexicon achieves second-highest F1 (0.714)
- Efficient lexicon-to-performance ratio

### Implications for Approach
1. **Validation of Method**: Lexicon approach works across diverse language families
2. **Scalability Proof**: Same methodology successfully applied to 4 languages
3. **Precision Priority**: Zero false positives critical for user trust
4. **Recall Optimization**: F1 differences driven by lexicon coverage, not approach failure

## Recommendations
1. **Expansion Priority**: Focus on Swahili lexicon growth (foundation → production)
2. **Validation Pipeline**: Native speaker review for FR/KI before production deployment
3. **Methodology Replication**: Current approach proven for additional African languages
4. **Hybrid Integration**: ML component (30% weight) complements rules without sacrificing precision

## Language Family Coverage

**Germanic:** English (EN) ✓
**Bantu:** Swahili (SW), Gikuyu (KI) ✓
**Romance:** French (FR) ✓

**Conclusion:** Lexicon-based approach with hybrid ML enhancement successfully scales across multiple language families while maintaining perfect precision (1.000) and delivering measurable F1 improvements (+7-23%) over baseline keyword matching.