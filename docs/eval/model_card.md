# JuaKazi Gender Sensitization Engine — Model Card
**Version**: 2.0 | **Last updated**: February 2026
**Update this card every time the model is retrained or lexicons are updated. Per AI BRIDGE protocol.**

---

## 1. Model Identity

| Field | Value |
|---|---|
| Model name | JuaKazi Gender Sensitization Engine |
| Version | 2.0 (Feb 2026) |
| Languages | English (en), Swahili (sw), French (fr), Gikuyu/Kikuyu (ki) |
| Task | Gender bias detection + neutral rewriting |
| Architecture | Rules engine (primary) + afro-xlmr-base fine-tuned (ML fallback, Stage 2) |
| License | MIT |
| Contact | JuaKazi team / AI BRIDGE submission |

---

## 2. Intended Use

**Primary use**: Flag and correct gender-biased language in written African-language text for content moderation, inclusive writing assistance, and editorial review.

**Primary users**: Journalists, content platforms, NGOs, educational publishers operating in East/West Africa.

**Out-of-scope**: Real-time speech transcription, personal messaging surveillance, automated mass-moderation without human review in the loop.

---

## 3. Detection Layer

### 3.1 Architecture

```
Input text
  → BiasDetector.detect_bias()
      ├── DEROGATION_PATTERNS      (hardcoded, highest priority)
      ├── COUNTER_STEREOTYPE_PATTERNS  (preserve — no correction)
      └── Lexicon rules (lexicon_{lang}_v3.csv)
            ├── ContextChecker (10 condition gates)
            │     quote | historical | proper_noun | biographical |
            │     statistical | medical | counter_stereotype |
            │     legal | artistic | organization
            ├── severity=replace → has_bias_detected=True
            └── severity=warn   → informational only
  → BiasDetectionResult { has_bias_detected, detected_edits, warn_edits }
```

**Key design choices**:
- Severity routing: `replace` triggers correction; `warn` is advisory only — never flips `has_bias_detected`.
- Context gating: `avoid_when` suppresses rules in biographical, statistical, and counter-stereotype contexts to reduce false positives.
- Case preservation: all replacements restore original casing (`Chairman` → `Chairperson`).
- Language independence: separate lexicons per language — no cross-lingual transfer that could violate cultural specificity.

### 3.2 Lexicons (Feb 2026)

| Language | File | Entries | Bias types covered |
|---|---|---|---|
| English | `rules/lexicon_en_v3.csv` | 538 | Occupation, pronoun, role, morphological |
| Swahili | `rules/lexicon_sw_v3.csv` | ~211 | Occupation, pronoun, role |
| French | `rules/lexicon_fr_v3.csv` | 78 | Occupation, morphological |
| Gikuyu | `rules/lexicon_ki_v3.csv` | ~1,232 | Occupation, role |

**Coverage gaps (known)**:
- Swahili proverbs: `mwanamke ni nyumba`, `mke mzuri ni utii`, `mwanamke ni shamba la baba` — not yet in lexicon
- Swahili Sheng: `dame`, `msupa wa ofisi`, `mrembo job` — not yet in lexicon
- Swahili bride-price patterns: `mahari`, `kuolea` — not yet in lexicon
- Male stereotype terms: ~2 entries across all languages (severely underrepresented)
- Implicit/proverb rows in ground truth: 0.9% — AIBRIDGE requires ≥5%

### 3.3 Detection Performance (Feb 2026)

Run `python3 run_evaluation.py` to reproduce.

| Language | Samples | Precision | Recall | F1 | AI BRIDGE tier (metrics) |
|---|---|---|---|---|---|
| English | 66 | 1.000 | 0.647 | 0.786 | Pre-Bronze |
| Swahili | 51,419 | 0.896 | 0.463 | 0.611 | Pre-Bronze (sample count: Gold) |
| French | 50 | 1.000 | 0.371 | 0.542 | Pre-Bronze |
| Gikuyu | 11,848 | 0.926 | 0.217 | 0.352 | Pre-Bronze (sample count: Bronze) |

**Qualifications**:
- Swahili Precision=0.896 (not 1.000): ~100 false positives from verbatim-article lexicon entries — Sprint 0 fix pending.
- Swahili/Gikuyu sample counts qualify for Gold/Bronze tier on volume; F1 and Cohen's Kappa do not yet meet tier thresholds.
- 0% human annotation on Swahili ground truth — all rows annotated by `ann_sw_auto_v1`. Cohen's Kappa is unmeasurable.
- English/French ground truth: hand-curated; no κ computed (single annotator).

### 3.4 Bias Type Coverage

| Bias type | Detected | Corrected | Notes |
|---|---|---|---|
| Occupational (explicit) | Yes | Yes | Core coverage — 92.7% of Swahili biased rows |
| Capability stereotype | Yes | Yes | 5.5% of Swahili biased rows |
| Pronoun (generic he/she) | Partial | Partial | 3% of Swahili biased rows; English coverage stronger |
| Family role | Yes | Yes | 0.8% of Swahili biased rows |
| Proverb / implicit | Minimal | No | 0.9% of Swahili biased rows; proverbs preserved, not corrected |
| Counter-stereotype | Detected (preserved) | No correction | Subverts bias — no neutralization applied |
| Derogation | Yes | Yes | Detected via DEROGATION_PATTERNS (high priority) |
| Morphological (gendered suffix) | Yes (EN/FR) | Yes (EN/FR) | e.g., waitress→server, actrice→acteur·rice |

### 3.5 Bias Severity Classification

| Level | Value | Meaning |
|---|---|---|
| 0 | No bias | Neutral text, no flags |
| 1 | Mild | Implicit assumption; warn only |
| 2 | Moderate | Clear lexical bias; replace recommended |
| 3 | Significant | Derogatory or strong stereotype; replace required |
| 4 | Severe | Hate speech-adjacent; flag for human review |
| 5 | Critical | Direct derogation targeting a gender group |

---

## 4. Correction Layer

### 4.1 Architecture

```
POST /rewrite { id, lang, text, region_dialect?, flags? }
  → apply_rules_on_spans()   — lexicon replacements with context gating
  → semantic preservation check (threshold 0.70, BLEU+ROUGE-L composite)
  → ml_rewrite() fallback   — only when zero rule matches
  → audit log → audit_logs/rewrites.jsonl
  ← { original_text, rewrite, edits, confidence, source, semantic_score, reason }
```

Each edit in the response includes a human-readable `reason` field: e.g., `"flagged because it assigns a fixed gender to an occupational role"`.

### 4.2 Correction Quality Metrics

| Metric | Description | Current value |
|---|---|---|
| Bias removal accuracy | % of detected biases successfully neutralized | English: 100% · Swahili: unmeasured (0 human reviews) |
| Meaning preservation score | BLEU + ROUGE-L composite (threshold 0.70) | Implemented in `eval/semantic_preservation.py` · Not yet run at scale |
| Human validation index | % of corrections approved by human reviewers | 0% — no human reviews recorded yet (`audit_logs/reviews.jsonl` empty) |
| Correction source breakdown | Rules vs ML fallback | Tracked per entry in `audit_logs/rewrites.jsonl` |
| Fairness index | Detection rate parity across gender groups | Computed by `eval/fairness_calculator.py` |

**Status**: Correction quality metrics cannot be reported until human review sessions produce at least 50 validated rewrites.

### 4.3 Correction Bias Type Breakdown

| Bias type | Correction strategy | Ngeli-safe? |
|---|---|---|
| Proverbial | Preserve + flag (no rewrite) | N/A |
| Morphological (EN/FR) | Suffix replacement (actor·rice) | N/A |
| Contextual (pronoun) | Pronoun neutralisation (their/them) | Partial |
| Cultural (occupational) | Lexicon replacement | Yes (Swahili ngeli tracked) |

**Ngeli**: Swahili noun class agreement markers are tracked by `eval/ngeli_tracker.py`. Replacement rules must preserve agreement across the sentence. Gate not yet wired for possessives — Sprint 2 item.

---

## 5. Human-in-the-Loop (HITL)

| Component | Location | Status |
|---|---|---|
| Review UI | `ui/` (Streamlit) | Live — loads rewrites.jsonl, records decisions |
| Review actions | approve / approve_with_edit / reject / flag_as_incorrect | Implemented |
| Feedback log | `audit_logs/reviews.jsonl` | Empty — no sessions run yet |
| Feedback → annotation pipeline | scripts/export_for_annotation.py | Implemented |
| Annotator annotation queue | Via sw-annotate skill | Active (batch 001 complete, 50 rows) |

**Target**: ≥200 human-reviewed corrections before reporting correction quality metrics externally.

---

## 6. Fairness Considerations

- **Gender balance in detection**: Rules cover male and female stereotype terms. Male stereotypes are underrepresented (~2 entries across all languages). Sprint 3 target: ≥13 male stereotype entries.
- **Dialect coverage**: Swahili ground truth — 65% Tanzania (Helsinki corpus), 35% Kenya. Sheng and Uganda Swahili: 0 rows. Coastal Swahili: 0 rows.
- **Annotator gender breakdown**: 0 human annotators to date. All labels from `ann_sw_auto_v1`. Target: ≥2 native-speaker annotators with documented gender breakdown.
- **Counter-stereotype handling**: Counter-stereotype sentences are detected and preserved, not corrected. Current counter-stereotype rate: 0% of biased rows (AIBRIDGE requires ≥15%).
- **Bias in corrections**: Corrections are word-level substitutions from a curated lexicon. They do not introduce new stereotypes. Semantic preservation threshold (0.70) guards against meaning distortion.

---

## 7. Known Limitations

1. **Low recall** — Swahili F1=0.611, Recall=0.463. ~537 biased rows not detected. Primary cause: lexicon coverage gaps, not model errors.
2. **Zero implicit bias detection** — Proverbs and indirect bias not captured by word-level rules. 0.9% of biased rows are implicit; AIBRIDGE requires ≥5%.
3. **No κ measurement** — All Swahili labels are auto-generated. Cohen's Kappa cannot be reported. Required for AI BRIDGE tier certification.
4. **Correction quality unvalidated** — No human review sessions completed. Bias removal accuracy for Swahili is unknown.
5. **Sheng/dialect gap** — System has no training signal from Sheng or Tanzanian coastal Swahili.
6. **ML Stage 2 fallback** — `juakazike/sw-bias-classifier-v1` (afro-xlmr-base fine-tuned on 51K SW rows). Val metrics: P=0.938, R=0.784, F1=0.854. Produces warn-only edits — never modifies text directly.

---

## 8. Evaluation Reproducibility

```bash
# Full detection eval across all languages
python3 run_evaluation.py

# Correction quality (requires filled expected_correction)
python3 eval/correction_evaluator.py

# Semantic preservation
python3 eval/semantic_preservation.py

# Fairness metrics
python3 tests/test_fairness_metrics.py

# System tests (5/5 must pass before any merge)
python3 tests/test_system.py
```

Results written to `eval/results/f1_report_YYYYMMDD_HHMMSS.csv`.

---

## 9. Update Protocol

**This card must be updated every time**:
- A lexicon version is incremented (e.g., v3 → v4)
- `run_evaluation.py` produces new metrics
- A human annotation batch is completed (update Human Validation Index)
- A new language is added
- The ML fallback model is retrained or swapped

**Update checklist**:
- [ ] Run `python3 run_evaluation.py` and paste new metrics into §3.3
- [ ] Record what changed and why (sprint, commit hash, data source)
- [ ] Update lexicon entry counts in §3.2
- [ ] Update correction quality metrics in §4.2 if human reviews were added
- [ ] Note any new limitations discovered
- [ ] Increment Model Card version number and date

**Reporting practice** (per Rebecca / AI BRIDGE): For each version update, record:
1. What bias patterns were added to the lexicon
2. What changed in the ground truth
3. Before/after F1, Precision, Recall per language
4. Any fairness metric changes

---

## 10. Version History

| Model Card version | Date | Key changes | F1 (SW) | Commit |
|---|---|---|---|---|
| 1.0 | Oct 2024 | Initial (approach_card.md) | 0.681 | — |
| 2.0 | Feb 2026 | Full rewrite: modular API, reason field, region_dialect, annotation pipeline, HITL UI, correct metrics | 0.611 | See feat/annotation-export |

---

*Per AI BRIDGE protocol, this card is the authoritative source of truth for model behaviour, limitations, and update history. Do not use `docs/eval/approach_card.md` — that file is outdated and will be archived.*
