# Baseline Comparison Analysis

## Methodology
Comparison between our rule-based lexicon approach and a simple keyword baseline detector.

**Baseline Detector**: Simple keyword matching using basic gendered terms per language
**Our Approach**: Comprehensive lexicon-based rules with morphological awareness

## Performance Comparison

| Language | Baseline F1 | Our F1 | Improvement | Analysis |
|----------|-------------|--------|-------------|----------|
| English  | 0.684       | 0.810  | +0.126      | Lexicon provides better coverage |
| Swahili  | 0.438       | 0.750  | +0.312      | Significant improvement from cultural adaptation |
| Hausa    | 0.889       | 0.780  | -0.109      | Baseline performs surprisingly well |
| Igbo     | 0.936       | 0.684  | -0.252      | Baseline keywords well-matched to test set |
| Yoruba   | 1.000       | 0.936  | -0.064      | Baseline achieves perfect score |

## Key Insights

### Where Our Approach Excels
1. **English & Swahili**: Significant improvements due to comprehensive occupational term coverage
2. **Cultural Adaptation**: Swahili shows largest gain (+0.312) from culturally-adapted lexicon
3. **Precision Maintenance**: Both approaches maintain perfect precision (1.000)

### Unexpected Baseline Performance
1. **Hausa, Igbo, Yoruba**: Simple baseline performs exceptionally well
2. **Possible Causes**: 
   - Test set may be biased toward simple gendered keywords
   - Our lexicon may be over-engineered for current test cases
   - African language test sets contain more obvious bias patterns

### Implications for Approach
1. **Validation of Method**: English/Swahili results confirm lexicon approach value
2. **Test Set Review**: African language results suggest need for more complex test cases
3. **Lexicon Optimization**: May need to balance comprehensive coverage with core term focus

## Recommendations
1. **Expand Test Complexity**: Add more subtle bias cases to African language test sets
2. **Hybrid Approach**: Consider combining baseline keywords with advanced lexicon rules
3. **Performance Monitoring**: Track both approaches as test sets evolve
4. **Cost-Benefit Analysis**: Simple baseline may be sufficient for some languages initially

## Ablation Study Preview
Results suggest that for some languages, core keyword detection captures most bias patterns in current test sets. Full ablation study will quantify contribution of:
- Core gendered keywords (baseline level)
- Occupational term expansion  
- Morphological pattern matching
- Cultural context adaptation