# Swahili F1: why 1.0 is hard and what helps

**Current (Mar 2026):** Swahili F1 ≈ 0.77, Precision ≈ 0.73, Recall ≈ 0.82 on ~64.7k ground-truth rows. Narrow advocacy context patterns in `core/context_checker.py` (haki za / elimu ya wasichana|watoto) skip correction only in clear rights/education phrasing, improving recall slightly without hurting precision. **English** F1 0.847 (slim lexicon, P=1.0).

**Why F1 = 1.0 is very hard with rules only**

- **Precision < 1:** Phrases like *Watoto wa Kike*, *mtoto wa kike*, *mtoto wa kiume* appear in both biased and non‑biased contexts (e.g. girls’ rights advocacy, medical “mtoto wa kiume”). The lexicon correctly flags them in many sentences, but in advocacy/medical contexts the same phrases are often not bias. Tightening with `avoid_when` (e.g. `counter_stereotype`) improves precision but has in the past reduced recall a lot (e.g. F1 down to ~0.50 when those terms were made warn‑only).
- **Recall < 1:** Some biased constructions are not yet in the lexicon or the “X wa kiume/kike” pattern (e.g. rarer occupations, implicit bias, proverbs). Closing the gap means adding more safe, high‑precision entries and/or better pattern coverage.

**What improves Swahili F1**

1. **Recall:** Add more lexicon entries and patterns (e.g. occupations, phrases) that match biased rows without increasing false positives. Use `/sw-lexicon` and validated occupation lists; run eval after each batch.
2. **Precision:** Refine context (e.g. `avoid_when`, or more targeted counter‑stereotype/advocacy detection) so we skip correction only in clear advocacy/medical contexts, not everywhere. This needs careful tuning so recall does not drop.
3. **Data:** Align ground truth with intended policy (e.g. mark clear advocacy uses as non‑bias so the evaluator does not count them as FPs).
4. **Model:** A classifier or hybrid (rules + model) can learn context better than rules alone; Stage 2 ML is already used for warn‑only suggestions.

**Rule:** Every lexicon change must be checked with `python3 run_evaluation.py`; avoid lowering precision on replace‑severity rules.

---

## Path to Swahili F1 = 1.0

F1 = 1.0 requires **both** Precision = 1.0 and Recall = 1.0. Right now P ≈ 0.73 and R ≈ 0.81, so both need to move.

| Goal | What to do | Risk |
|------|------------|------|
| **Precision → 1.0** | (1) **Ground truth:** Mark clear advocacy/medical uses of *Watoto wa Kike*, *mtoto wa kike/kiume* as neutral (so detector no longer “over-fires”). (2) **Context:** Add targeted `avoid_when` or context patterns so we skip only in those contexts; test each change with `run_evaluation.py` so recall does not drop. (3) **Audit FPs:** Run failure analysis, find top FP rules, downgrade to `warn` or add narrow `avoid_when` per row. | Broad avoid_when (e.g. medical on *mtoto wa kiume*) can skip real biases and lower recall. |
| **Recall → 1.0** | (1) **Lexicon:** Add missing occupations, proverbs (5), Sheng (10), bride-price/religious patterns via `/sw-lexicon`; run eval after each batch. (2) **Patterns:** Extend detector patterns for “X wa kiume/kike” and implicit bias. (3) **ML:** Use Stage 2 classifier (or hybrid) for warn path; retrain on current data. | New replace rules must not add FPs (precision ≥ 1.0). |
| **Both** | Combine: fix precision (GT + context + FP audit) and recall (lexicon + patterns + ML). Rules-only F1 = 1.0 is very hard; a **hybrid (rules + model)** that learns context is the most realistic route. |
