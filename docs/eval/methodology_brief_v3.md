# JuaKazi Gender Sensitization Engine
## Methodology Brief — Version 3
**March 2026 | AI BRIDGE Submission**

---

## 1. Overview

The JuaKazi Gender Sensitization Engine is a multilingual system for detecting and correcting gender-biased language in written text, with a focus on East African languages. The system targets four languages — Swahili, English, French, and Gikuyu/Kikuyu — and is designed for use by journalists, content platforms, NGOs, and educational publishers.

The system performs two functions:
1. **Detection** — identifies gender-biased expressions with a reason and severity level
2. **Correction** — proposes neutral rewrites while preserving the original meaning

---

## 2. Problem Statement

Gender bias in language is pervasive across African media, education, and public discourse. Common patterns include:

- Occupational terms that assume gender (e.g. *daktari wa kiume* — "male doctor", implying medicine is male by default)
- Proverbs that prescribe gender roles (e.g. *mwanamke ni chombo* — "a woman is a tool")
- Derogatory gendered terms in informal registers (Sheng)
- Morphological bias in French and English (e.g. *waitress*, *chairman*)

Existing tools address high-resource languages like English and do not cover Swahili, French in African contexts, or Gikuyu. JuaKazi addresses this gap directly.

---

## 3. Architecture

The system uses a three-stage pipeline:

```
Input text
    │
    ▼
Stage 1: Rules Engine
    ├── Hardcoded derogation patterns (highest priority)
    ├── Counter-stereotype patterns (preserve — no correction)
    └── Lexicon rules per language (lexicon_{lang}_v3.csv)
          ├── severity=replace → triggers correction
          └── severity=warn   → advisory flag only
    │
    ▼
Stage 2: Context Gating
    └── ContextChecker suppresses false positives in:
          quote | historical | proper_noun | biographical |
          statistical | medical | counter_stereotype |
          legal | artistic | organization
    │
    ▼
Stage 3: ML Fallback (Swahili only)
    └── afro-xlmr-base fine-tuned on 64,723 Swahili rows
        Activates only when Stage 1 finds zero matches
        Produces advisory flags — never auto-corrects
```

**Design principles:**
- Rules are the primary signal — interpretable, auditable, language-specific
- Context gating prevents suppression of legitimate cultural/historical references
- ML fallback extends coverage to implicit bias the rules cannot capture
- Every edit carries a human-readable reason field for transparency

---

## 4. Lexicons

Lexicons are the core knowledge base of the rules engine. Each language has an independent lexicon in CSV format with fields for the biased term, neutral replacement, bias type, severity, stereotype category, and context suppression conditions.

| Language | Entries | Bias types covered |
|---|---|---|
| Swahili | 267 | Occupation, pronoun, role, proverb/idiom, derogation, Sheng |
| English | 68 | Occupation, pronoun, role, morphological |
| French | 101 | Occupation, morphological |
| Gikuyu | ~1,240 | Occupation, role |

**Swahili lexicon expansions (March 2026):**
- 11 proverbs added: *mwanamke ni chombo*, *mke mzuri ni utii*, *mwanamke ni shamba la baba*, *mwanaume ni kichwa mwanamke ni shingo*, and 7 others
- 10 Sheng terms added: *dem*, *mresh*, *mami*, *manzi*, *msupa wa ofisi*, and 5 others — all advisory (`severity=warn`)

---

## 5. Ground Truth Dataset

The evaluation ground truth was built through a multi-stage annotation process:

| Language | Rows | Source |
|---|---|---|
| Swahili | 64,723 | Zenodo 4300294 (Helsinki Tanzanian corpus), BBC Swahili News, AfriSenti, MasakhaNER |
| Gikuyu | 11,848 | Internal collection |
| English | 66 | Hand-curated |
| French | 50 | Hand-curated |

**Swahili ground truth quality (March 2026):**
- `ann_sw_v3` AI annotation pass: 13,304 rows labelled
- Human review batch: 274 rows reviewed by native speaker annotator
- 26 `annotation_error` rows resolved: 2 confirmed bias, 19 neutral, 5 counter-stereotype
- Counter-stereotype rows: 15.63% (AIBRIDGE minimum ≥15% — met)
- Implicit/proverb rows: 5.01% (AIBRIDGE minimum ≥5% — met)
- PII scrubbed: 110 rows with emails/phone numbers replaced with `[EMAIL]`/`[PHONE]`
- Region dialect tagged: Kenya (18,008 rows), Tanzania (33,411 rows)
- Cohen's Kappa: **in progress** — 2nd annotator engaged, 250-row overlap set prepared

---

## 6. ML Classifier — Version History

The ML classifier (Swahili only) serves as a Stage 3 fallback. It has been trained three times:

### v1 (2024)
- Base model: afro-xlmr-base
- Training data: 51K rows
- Val F1: 0.854 | Precision: 0.938 | Recall: 0.784
- Status: superseded

### v2 (Early 2026)
- Training data: 51K rows, 4K neutral rows
- pos_weight: ~58x (n_neg/n_pos ratio)
- Val F1: 0.953 (on internal validation split)
- **External evaluation (9,709-sample independent test set):** Precision: 0.330, Recall: 0.976, F1: 0.493 — 333 false positives
- Root cause: extreme pos_weight caused the model to flag any gendered surface term as bias regardless of context; counter-stereotype rows were incorrectly labelled as BIAS in training
- Status: being replaced

### v3 (March 2026) — Current
- Training data: 64,723 rows (full ground truth), 40,000 neutral rows
- pos_weight: 10.0 (hard cap)
- Counter-stereotype rows correctly labelled NEUTRAL in training
- `annotation_error` rows excluded from training
- Stratified 80/20 train/val split
- Base model: Davlan/afro-xlmr-base | Epochs: 10 (early stopping, patience=3) | LR: 2e-5

**v3 validation metrics (internal split, 8,052 rows):**

| Metric | Value |
|---|---|
| BIAS Precision | 0.898 |
| BIAS Recall | 0.910 |
| BIAS F1 | 0.904 |
| Decision threshold | 0.50 |

**v3 external evaluation (9,709-sample independent test set):**

| Metric | v2 | v3 |
|---|---|---|
| BIAS Precision | 0.330 | **0.810** |
| BIAS Recall | 0.976 | **0.942** |
| BIAS F1 | 0.493 | **0.871** |
| False Positives | 333 | **39** |

All targets set by the independent evaluator were exceeded: BIAS F1 ≥ 0.70 ✓, Precision ≥ 0.60 ✓, Recall ≥ 0.85 ✓.

---

## 7. Detection Performance (March 2026)

| Language | Samples | Precision | Recall | F1 |
|---|---|---|---|---|
| English | 66 | 1.000 | 0.794 | 0.885 |
| Swahili | 64,723 | 0.741 | 0.919 | 0.821 |
| French | 50 | 1.000 | 0.657 | 0.793 |
| Gikuyu | 11,848 | 0.916 | 0.231 | 0.368 |

**Notes:**
- English and French achieve perfect precision (1.000) — no false positives
- Swahili precision is 0.741 — a known, accepted precision hit driven by genuinely ambiguous phrases (*watoto wa kike*, *mtoto wa kiume*) that appear in both advocacy and prescriptive contexts; context gating cannot reliably distinguish these
- Gikuyu recall (0.231) reflects a lexicon coverage gap, not model failure; the lexicon was built from limited Gikuyu digital resources

---

## 8. Correction Quality

An independent external evaluation of the correction layer assessed five dimensions:

| Dimension | Finding |
|---|---|
| Bias neutralization | Strong — gendered terms successfully replaced with neutral alternatives |
| Semantic preservation | Core meaning retained in corrected output |
| Grammar and fluency | Corrections grammatically valid; inline advisory suggestions reduce fluency |
| Bias reduction (ΔBias) | Measurable reduction in bias markers between original and corrected text |
| New bias introduced | None — neutral replacements do not shift discrimination toward other groups |

**Correction metrics (external evaluation):**

| Metric | Value |
|---|---|
| F1 | 0.953 |
| Recall | 0.960 |
| Precision | 0.940 |

**Known limitation:** Advisory (`warn`) edits are displayed as inline suggestions (e.g. *[consider mtu]*) rather than applied automatically. This is intentional — warn-severity edits require human review. Improving the display format of these suggestions is a planned improvement.

---

## 9. Rewrite API

The system exposes a REST API for integration:

```
POST /rewrite
{
  "text": "Daktari wa kiume alifika asubuhi",
  "language": "sw",
  "region_dialect": "kenya"
}
```

Response includes:
- `rewritten_text` — corrected version
- `edits` — list of changes with `original`, `replacement`, `reason`, `severity`, `confidence`
- `source` — `rules`, `ml_fallback`, or `preserved` (if semantic gate blocked the rewrite)
- `has_bias_detected` — boolean

A semantic preservation gate (cosine similarity threshold 0.70) prevents rewrites that distort meaning. If the rewrite diverges semantically, the original is returned with `source=preserved`.

---

## 10. Ethical Considerations

- **Human review in the loop:** The system flags and suggests — it does not auto-block or auto-publish. All corrections are advisory.
- **Cultural specificity:** Each language has its own lexicon. No cross-lingual transfer that could impose one language's gender norms onto another.
- **Counter-stereotype preservation:** Sentences that challenge stereotypes (e.g. *Mama huyu ni daktari bora*) are detected but explicitly not corrected.
- **Annotation bias:** Current ground truth has a single annotator for most rows. Cohen's Kappa measurement is in progress to quantify inter-annotator agreement.
- **Gender framing:** The system uses a binary gender framework in its lexicon. Non-binary and intersectional gender expressions are not yet covered — a known gap for future work.

---

## 11. Reproducibility

```bash
# Detection evaluation — all 4 languages
python3 run_evaluation.py

# System tests (5/5 must pass)
python3 tests/test_system.py

# Correction quality
python3 eval/correction_evaluator.py

# API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

All evaluation results are written to `eval/results/` and `eval/metrics.json`.

---

## 12. Version Summary

| Version | Date | SW F1 | Key milestone |
|---|---|---|---|
| 1.0 | Oct 2024 | 0.681 | Initial rules-based system |
| 2.0 | Feb 2026 | 0.611 | Full architecture rewrite — modular API, 4 languages, annotation pipeline |
| 2.1 | Mar 2026 | 0.816 | Ground truth expanded to 64K, tester feedback fixes, proverb + Sheng lexicon |
| 2.2 | Mar 2026 | 0.819 | AIBRIDGE submission prep, lexicons restored, schema compliance verified |
| 2.3 | Mar 2026 | 0.819 | ML classifier upgraded v1→v3: precision fixed (FPs 333→39), val F1 0.904 |

---

*JuaKazi Gender Sensitization Engine · March 2026 · AI BRIDGE Submission*
