# How to improve F1

Current metrics (Mar 2026, `python3 run_evaluation.py`):

| Language | F1   | Precision | Recall | Main limiter        |
|----------|------|-----------|--------|---------------------|
| Swahili  | 0.771| 0.734     | 0.811  | Precision (false positives) |
| English  | 0.786| 1.000     | 0.647  | Recall              |
| French  | 0.542| 1.000     | 0.371  | Recall              |
| Kikuyu   | 0.352| 0.926     | 0.217  | Recall              |

F1 = 2 × (Precision × Recall) / (Precision + Recall). So you improve F1 by raising the metric that is currently lower (or both).

---

## 1. Swahili (F1 0.771) — raise **precision** (0.734)

**Cause:** Lexicon over-fires on **advocacy / girls’-rights** contexts. Phrases like *Watoto wa Kike*, *mtoto wa kike*, *mtoto wa kiume* are often used in neutral or positive “rights/education” sentences; labelling them as bias lowers precision.

**What to do:**

1. **Tighten `avoid_when` for ambiguous phrases**  
   In `rules/lexicon_sw_v3.csv`, ensure any row that can appear in advocacy/rights contexts has:
   - `avoid_when` including `counter_stereotype` (and other conditions that match those contexts).
   - Optionally **downgrade to `severity=warn`** for phrases that are ambiguous (e.g. “Watoto wa Kike” in titles/rights) so they never set `has_bias_detected=True`.

2. **Improve context detection for advocacy**  
   In `core/context_checker.py`, extend `ContextCondition.COUNTER_STEREOTYPE` (or add a dedicated condition) so that **rights/advocacy** wording (e.g. *haki za*, *elimu*, *watoto wa kike* in “rights/education” sentences) is detected and correction is skipped. That reduces false positives without removing useful rules.

3. **Audit high-FP rules**  
   Run eval, collect sentences where the detector fires but ground truth is neutral; find which lexicon rows and which contexts cause it; then add `avoid_when` or downgrade to `warn` for those rows.  
   (You can use `eval/failure_analyzer.py` or a one-off script over `eval/ground_truth_sw_v5.csv`.)

4. **Rule: no new replace without checking precision**  
   Per CLAUDE.md: *Precision ≥ 1.000 on replace-severity rules.* Before adding or promoting any rule to `severity=replace`, check that it doesn’t create false positives on current (and ideally new) eval data.

**After changes:** Run `python3 run_evaluation.py` and confirm SW precision and F1 improve without tanking recall.

---

## 2. Swahili — raise **recall** (0.811)

**Cause:** Lexicon **coverage gaps** — some biased constructions never match.

**What to do:**

1. **Expand lexicon** with `/sw-lexicon` (and manual review):
   - More occupation/role terms and phrases.
   - **5 proverbs** and **10 Sheng terms** (Sprint 2; see CLAUDE.md).
   - Bride-price / religious framing / male-stereotype entries if needed.

2. **Keep ML classifier (Stage 2)**  
   It’s warn-only but improves effective recall (more cases flagged for review). Retrain with current data (see `docs/TRAINING.md`) and set `JUAKAZI_ML_MODEL`; target val F1 ~0.82–0.88.

3. **Review missed positives**  
   From eval or failure analysis, list rows where ground truth is bias but the detector says no; add or adjust lexicon/patterns (and context) so those are caught without hurting precision.

---

## 3. English / French / Kikuyu — raise **recall**

For these, **precision is already high (0.93–1.0)**; the main limiter is **recall** (many biased cases not detected).

**What to do:**

1. **Expand lexicons** (`rules/lexicon_en_v3.csv`, `lexicon_fr_v3.csv`, `lexicon_ki_v3.csv`):
   - Add missing gendered terms, phrases, and stereotypes.
   - Use the same discipline: prefer `warn` or strong `avoid_when` so precision stays ≥ 1.0 for replace rules.

2. **More ground truth**  
   EN/FR/KI have small eval sets (66 / 50 / 11,848). Adding more labelled data (and re-running stratified split + eval) gives a more reliable F1 and highlights remaining gaps.

3. **Language-specific patterns**  
   For KI/FR, add any detector patterns (e.g. in `eval/detector_patterns.py` or equivalent) for constructions that are common in the data but not yet covered by the lexicon.

---

## 4. Cross-cutting

- **Every lexicon change:** run `python3 run_evaluation.py` and compare before/after F1, P, R per language.
- **Replace rules:** add only when precision on that rule (or on the language) stays at 1.000 (or acceptable); use `warn` when in doubt.
- **Context:** use `avoid_when` (pipe-separated `ContextCondition` values) so rules don’t fire in quote, historical, biographical, counter_stereotype, etc.
- **ML (Swahili):** retrain periodically; update Model Card and `JUAKAZI_ML_MODEL` when you deploy a new model.

---

## 5. Quick checklist (Swahili focus)

| Action | Effect | Owner |
|--------|--------|--------|
| Add `counter_stereotype` (or advocacy) patterns in context_checker | ↑ Precision | Engineer |
| Set `avoid_when` / downgrade to warn for “Watoto wa Kike”–type phrases | ↑ Precision | Data/Engineer |
| Run failure analysis → fix top FP lexicon rows | ↑ Precision | Engineer |
| Add 5 proverbs + 10 Sheng to lexicon_sw_v3 | ↑ Recall | Data / `/sw-lexicon` |
| Expand occupation/role lexicon from corpus | ↑ Recall | Data / `/sw-lexicon` |
| Retrain ML classifier (Kaggle/local GPU) | ↑ Recall (warn path) | Engineer |
| Add more EN/FR/KI ground truth + lexicon | ↑ Recall (and stable F1) | Data |

Using this, you can target either precision (Swahili) or recall (all languages) depending on which metric is limiting F1.
