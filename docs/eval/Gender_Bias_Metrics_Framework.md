
# Gender Bias Correction Evaluation Metrics Framework

**Project:** JuaKazi Gender Sensitization Engine
**Languages:** English, Swahili, French, Gikuyu
**Updated:** November 20, 2025

## Bias Mitigation

| Metric Name | Definition / Formula | Purpose / Interpretation | Target |
|------------|--------------------|-------------------------|--------|
| **Bias Removal Rate (BRR)** | % of originally biased sentences that become non-biased after correction. **BRR = (# corrected non-biased) / (# biased inputs)** | Measures effectiveness of debiasing | ≥ 85% |
| **Residual Bias Score (RBS)** | Avg. probability of bias from independent classifier after correction (Lower is better) | Detects remaining bias in corrected text | ≤ 0.15 |
| **Verifier Agreement Rate** | % of corrections that pass verifier’s bias-free check | Sanity check for verifier | ≥ 90% |

---

## Semantic Integrity

| Metric Name | Definition / Formula | Purpose / Interpretation | Target |
|------------|--------------------|-------------------------|--------|
| **Semantic Similarity (SBERT / LaBSE)** | Cosine similarity between original + corrected embeddings | Ensure meaning preservation | ≥ 0.80 |
| **BERTScore / BLEURT** | Token-level semantic similarity score | Richer semantic match | ≥ 0.75 |
| **Entity & Slot Preservation** | % of named entities, numbers, dates preserved | Checks factual consistency | ≥ 95% |
| **Coreference Consistency** | % coreference chains maintained | Ensures correct pronoun replacement | ≥ 90% |

---


## Fluency & Naturalness

| Metric Name | Definition / Formula | Purpose / Interpretation | Target |
|------------|--------------------|-------------------------|--------|
| **Perplexity (LM-based)** | Avg perplexity of corrected outputs (Lower is better) | Measures fluency | ≤ baseline +10% |
| **Grammar Error Rate** | # grammar errors / 100 words | Detects grammatical degradation | ≤ 5 |
| **Fluency Rating (Human)** | Likert score 1–5 | Human judgment of naturalness | ≥ 4.0 |

---

## Structural Consistency

| Metric Name | Definition / Formula | Purpose / Interpretation | Target |
|------------|--------------------|-------------------------|--------|
| **Token Edit Ratio** | edit_distance / len(original_tokens) | Minimal edits desired | ≤ 0.30 |
| **Normalized Levenshtein Distance** | Edit distance normalized | Measures extent of change | ≤ 0.25 |
| **NER Match Rate** | Named entities preserved | Avoid structural distortion | ≥ 0.95 |
| **Length Ratio** | len(corrected)/len(original) | Prevents shortening/elongation | 0.8 ≤ ratio ≤ 1.2 |

---

## Human Evaluation & System-Level Metrics

| Metric Name | Definition / Formula | Purpose / Interpretation | Target |
|------------|--------------------|-------------------------|--------|
| **Human Bias Removal Score** | Annotator Yes/No (or 1–5 scale) | Ground-truth validation | ≥ 90% “Yes” |
| **Meaning Preservation (Human)** | Annotator 1–5 rating | Validates semantic fidelity | ≥ 4.0 |
| **Overall Acceptability** | Accept or Reject | Final human decision | ≥ 85% |
| **Inter-Annotator Agreement** | Cohen’s κ or Krippendorff’s α | Reliability of human eval | κ ≥ 0.75 |
| **Latency (sec/sentence)** | Inference speed | Efficiency measure | ≤ 1.5 sec |
| **Composite Quality Score (S_final)** | Weighted sum of core metric categories | Unified performance score | ≥ 0.75 |
| **95% Confidence Interval** | Bootstrapped CI | Statistical reliability | Narrow (< ±0.03) |

---

## Hybrid Debiasing Approach Summary

| Component | Strength | Weakness | Implementation Status |
|----------|----------|----------|----------------------|
| **Rules-Based Lexicon** | Fast, precise, zero false positives | Recall limited by lexicon coverage | Production (70% weight) |
| **ML Detector (XLM-R)** | Context-aware, multilingual | Requires training data | Demo mode (30% weight) |
| **MT5 Corrector** | Deep context-aware rewriting | Slower, may hallucinate | Optional (requires requirements_ml.txt) |
| **Hybrid Routing** | Balanced performance | Threshold tuning needed | Implemented |

---

## Current Performance (Nov 20, 2025)

| Language | F1 Score | Precision | Recall | Bias Removal | Status |
|----------|----------|-----------|--------|--------------|--------|
| English  | 0.764    | 1.000     | 0.618  | 100.0%       | Production |
| Gikuyu   | 0.714    | 1.000     | 0.556  | Pending      | Beta |
| Swahili  | 0.681    | 1.000     | 0.516  | 12.5%        | Foundation |
| French   | 0.627    | 1.000     | 0.457  | Pending      | Beta |

**Key Achievement:** Perfect precision (1.000) across all 4 languages - zero false positives.

---

### Language Models & Embeddings
- XLM-RoBERTa (multilingual detection)
- DistilBERT (English detection)
- MT5 (optional correction, requires ML deps)
- LaBSE (semantic similarity)

---

© JuaKazi — Gender Bias Detection & Correction Initiative
