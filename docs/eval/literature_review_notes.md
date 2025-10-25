# Literature Review Notes

## Key Insights from Gender Bias Detection Literature

### 1. Low-Resource Language Bias Evaluation
**Source**: Recent work on African language NLP bias evaluation
**Key Takeaway**: Rule-based approaches often outperform ML models for low-resource languages due to limited training data
**Impact on Our Approach**: Validates our choice of lexicon-based detection over ML models for initial implementation

### 2. Cross-Language Bias Categories
**Source**: Multilingual bias taxonomy research
**Key Takeaway**: Occupational bias and pronoun assumptions are universal, but morphological patterns vary significantly across language families
**Impact on Our Approach**: Confirms our per-language lexicon strategy rather than shared cross-language rules

### 3. Evaluation Metrics for Bias Detection
**Source**: Bias evaluation methodology papers
**Key Takeaway**: F1 score is standard, but category-specific recall is crucial for understanding coverage gaps
**Impact on Our Approach**: Added per-category F1 reporting to identify specific bias type coverage issues

### 4. African Language Morphology Considerations
**Source**: Bantu and Niger-Congo language processing literature
**Key Takeaway**: Agglutinative morphology in many African languages requires pattern matching beyond simple word boundaries
**Impact on Our Approach**: Need to expand from exact word matching to morphological pattern recognition for better recall

### 5. Cultural Context in Bias Detection
**Source**: Sociolinguistic bias research in African contexts
**Key Takeaway**: Professional role assumptions vary significantly across cultures; Western bias categories may not fully capture African language bias patterns
**Impact on Our Approach**: Validates our culturally-adapted lexicons and suggests need for region-specific bias category expansion

## Implementation Changes Based on Literature
1. **Maintained rule-based approach** - Literature supports this for low-resource settings
2. **Added morphological awareness** - Critical for African language accuracy
3. **Expanded cultural context** - Beyond direct translation of English bias patterns
4. **Enhanced evaluation granularity** - Per-category metrics reveal coverage gaps
5. **Prioritized recall improvement** - Literature shows this is key limitation in rule-based systems