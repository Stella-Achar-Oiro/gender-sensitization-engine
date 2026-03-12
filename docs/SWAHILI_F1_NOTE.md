# Swahili F1: why 1.0 is hard and what helps

**Current (Mar 2026):** Swahili F1 ≈ 0.77, Precision ≈ 0.74, Recall ≈ 0.81 on ~64.7k ground-truth rows.

**Why F1 = 1.0 is very hard with rules only**

- **Precision < 1:** Phrases like *Watoto wa Kike*, *mtoto wa kike*, *mtoto wa kiume* appear in both biased and non‑biased contexts (e.g. girls’ rights advocacy, medical “mtoto wa kiume”). The lexicon correctly flags them in many sentences, but in advocacy/medical contexts the same phrases are often not bias. Tightening with `avoid_when` (e.g. `counter_stereotype`) improves precision but has in the past reduced recall a lot (e.g. F1 down to ~0.50 when those terms were made warn‑only).
- **Recall < 1:** Some biased constructions are not yet in the lexicon or the “X wa kiume/kike” pattern (e.g. rarer occupations, implicit bias, proverbs). Closing the gap means adding more safe, high‑precision entries and/or better pattern coverage.

**What improves Swahili F1**

1. **Recall:** Add more lexicon entries and patterns (e.g. occupations, phrases) that match biased rows without increasing false positives. Use `/sw-lexicon` and validated occupation lists; run eval after each batch.
2. **Precision:** Refine context (e.g. `avoid_when`, or more targeted counter‑stereotype/advocacy detection) so we skip correction only in clear advocacy/medical contexts, not everywhere. This needs careful tuning so recall does not drop.
3. **Data:** Align ground truth with intended policy (e.g. mark clear advocacy uses as non‑bias so the evaluator does not count them as FPs).
4. **Model:** A classifier or hybrid (rules + model) can learn context better than rules alone; Stage 2 ML is already used for warn‑only suggestions.

**Rule:** Every lexicon change must be checked with `python3 run_evaluation.py`; avoid lowering precision on replace‑severity rules.
