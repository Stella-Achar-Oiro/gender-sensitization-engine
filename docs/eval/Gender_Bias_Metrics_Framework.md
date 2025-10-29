
# Gender Bias Correction Evaluation Metrics Framework

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

| Component | Strength | Weakness | Why It Fits |
|----------|----------|----------|-------------|
| **LaserTagger** | Fast, precise | Limited with complex syntax | Good for lexical bias |
| **mT5 / mBART / AfriT5** | Deep context-aware rewriting | Slower, may hallucinate | Handles structural stereotypes |
| **Verifier** | Ensures quality & trust | Adds latency | Quality safeguard |
| **Hybrid Routing** | Balanced performance | Threshold tuning needed | Best tradeoff accuracy vs speed |

---

### Language Models & Embeddings
- LaBSE
- AfriSimCSE

---

© JuaKazi — Gender Bias Correction Initiative
