# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JuaKazi Gender Sensitization Engine: Gender bias detection and correction system for African languages (English, Swahili, French, Gikuyu). Rules-based engine with context-aware correction, ML fallback (mT5-small), FastAPI backend, Streamlit review UI, and AIBRIDGE-compliant evaluation framework.

## Active Branch

`main` (annotation work happens in short-lived `feat/annotation-batch-NNN` branches, squash-merged to main)

---

## Actual Performance Metrics (Feb 2026)

Run `python3 run_evaluation.py` to verify. These are the real numbers — do not use the older claimed figures.

| Language | F1 | Precision | Recall | Samples | Tier |
|---|---|---|---|---|---|
| English | 0.786 | 1.000 | 0.647 | 66 | Pre-Bronze |
| **Swahili** | **0.802** | **0.970** | **0.684** | **51,419** | Gold (sample count) |
| French | 0.542 | 1.000 | 0.371 | 50 | Pre-Bronze |
| Kikuyu | 0.352 | 0.926 | 0.217 | 11,848 | Bronze (sample count) |

**Important qualifications:**
- Swahili/Kikuyu Gold/Bronze = sample count achieved only. IAA (Cohen's Kappa) is unmeasurable — human annotation in progress (Phase 2).
- Swahili F1 improved from 0.611 → 0.802 after Bug 2 fix (removed verbatim article FPs from lexicon). Verified Feb 26 2026.
- Swahili Recall=0.684 (up from 0.463) — real improvement. Residual gap = real detector coverage misses.
- Low recall across all langs = primary driver of low F1. Root cause: lexicon coverage gaps, not false positives.
- SW human annotation in progress: batches 001–017 reviewed (850 rows, ann_sw_v2). 269 candidates remaining.

---

## Bugs — Status

### Bug 1: Correction not applying in demo ✅ FIXED (Phase 0)
`demo_live.py` now uses `apply_rules_on_spans()` from `api/rules_engine.py`. Case-safe, span-aware.

### Bug 2: Verbatim article paragraphs in Swahili lexicon ✅ FIXED (Phase 0)
Removed all `biased` entries >80 chars that were full article paragraphs. SW Precision should improve on next eval run.

### Bug 3: `avoid_when` field has prose not enum values ✅ FIXED (Phase 0)
All 7 rows in `rules/lexicon_sw_v3.csv` updated to pipe-separated ContextCondition enum values.
Valid values: `quote|historical|proper_noun|biographical|statistical|medical|counter_stereotype|legal|artistic|organization`

---

## Production Plan

### What to keep — the architecture is correct
- `BiasDetector` (rules engine with severity routing, context gating) — solid
- `ContextChecker` (10 condition types) — fully built, just needs lexicon wired
- `api/main.py` (FastAPI + audit logging) — production-ready structure
- `review_ui/app.py` (Streamlit human review) — HITL infrastructure exists
- 51K+ real Swahili sentences, 11K+ Kikuyu — real data is the hardest thing to get

### What is done — product layer ✅
1. **Explainability**: Plain-language `reason` field on every edit (api/rules_engine.py `build_reason`); shown in demo and UI.
2. **Feedback button**: Full review form in ui/ — approve/approve_with_edit/reject/flag → `audit_logs/reviews.jsonl`.
3. **Dialect tagging**: `region_dialect` tagged on all 51,419 SW rows (kenya=18,008, tanzania=33,411).
4. **Human annotation**: In progress — 850 rows reviewed by ann_sw_v2 across batches 001–017; 269 candidates remaining.

### What is still missing
1. **Cohen's Kappa**: Requires 2nd annotator on overlapping 500-row sample. No second annotator recruited yet.
2. **Sheng/Uganda coverage**: region_dialect has 0 Sheng/Uganda rows.
3. **expected_correction gaps**: ~950 bias=true rows still missing expected_correction (down from 1,071).

### Sprint 0 — Stabilise ✅ COMPLETE (Phase 0, merged to main)
All 3 bugs fixed. 4/4 tests passing. Demo works end-to-end.

### Sprint 1 — Explainability + Feedback ✅ COMPLETE (Phase 1, merged to main)
`reason` field on all edits. Full review UI. region_dialect tagged on all SW rows. Dataset Card v3. Model Card v2.

### Sprint 2 — Human Annotation + Real Metrics (Phase 2 — IN PROGRESS)
| Task | Owner | Effort |
|---|---|---|
| Recruit 2 Swahili native speakers (Masakhane community) | Shaka | 1 week |
| Annotate 500-row overlapping sample, compute Cohen's Kappa | Data + annotators | 1 week |
| Fill `expected_correction` on bias=true rows missing it (ann_sw_v2 batches 001–017 in progress: ~950 remaining) | ann_sw_v2 | ongoing |
| Run correction evaluator on filled rows | Eng | 2h |
| Add 5 Swahili proverbs to lexicon (`mwanamke ni nyumba` etc) | Data | 3h |
| Add 10 Sheng terms (`dame`, `msupa wa ofisi` etc) | Data | 3h |

After Sprint 2: real F1, real κ, real correction quality score → Model Card numbers.

### Sprint 3 — Dataset Balance + AIBRIDGE Submission (4 weeks)
| Task | Owner | Effort |
|---|---|---|
| Generate 100 minimal pairs (gender-swap variants) | Data | 1 week |
| Add counter-stereotype rows → reach ≥15% of dataset | Data | 2 weeks |
| Add implicit/proverb rows → reach ≥5% of dataset | Data | 2 weeks |
| Add health, education, household domains | Data | 2 weeks |
| Write Dataset Card (AI BRIDGE template) | Shaka | 3h |
| Write Model Card (AI BRIDGE template, update each retraining) | Eng + Shaka | 3h |
| Tag all rows with `region_dialect` | Data | 1 week |
| Document annotator gender breakdown | Shaka | 30m |
| CSVW JSON-LD metadata + PROV lineage | Eng | 4h |

After Sprint 3: AIBRIDGE submission-ready. Dataset Card + Model Card complete.

---

## Architecture

### Detection pipeline (eval/)

```
Input text
  → BiasDetector.detect_bias()
      ├── DEROGATION_PATTERNS (hardcoded, high-priority)
      ├── COUNTER_STEREOTYPE_PATTERNS (preserve, no correction)
      └── Lexicon rules (lexicon_{lang}_v3.csv)
            ├── ContextChecker (biographical/quote/statistical gates)
            ├── severity=replace → has_bias_detected=True, edit queued
            └── severity=warn   → informational only, never sets has_bias
  → BiasDetectionResult { has_bias_detected, detected_edits, warn_edits }
```

**Key files:**
- [eval/bias_detector.py](eval/bias_detector.py) — primary rules engine
- [eval/context_checker.py](eval/context_checker.py) — context gating (10 conditions)
- [eval/ngeli_tracker.py](eval/ngeli_tracker.py) — Swahili noun class tracking (wired but not yet gating possessives)
- [eval/hybrid_detector.py](eval/hybrid_detector.py) — rules (70%) + mT5-small (30%)
- [eval/models.py](eval/models.py) — Language, BiasLabel, StereotypeCategory, BiasDetectionResult

### Correction pipeline (api/)

```
POST /rewrite { id, lang, text, flags? }
  → apply_rules_on_spans() with ContextChecker
  → semantic preservation check (threshold 0.70)
  → ml_rewrite() fallback only when rules find nothing
  → audit log → audit_logs/rewrites.jsonl
  ← { original_text, rewrite, edits, confidence, source, semantic_score }
```

**Key file:** [api/main.py](api/main.py)

### Evaluation pipeline

```
run_evaluation.py
  → GroundTruthLoader → eval/ground_truth_{lang}_v5.csv (ki: v8)
  → BiasDetector per row
  → MetricsCalculator → F1, Precision, Recall
  → FairnessCalculator → DP, EO
  → eval/results/
```

### Lexicons (rules/)

| File | Entries | Status |
|---|---|---|
| `lexicon_en_v3.csv` | 538 | Production |
| `lexicon_sw_v3.csv` | 218 | Production (Bug 2 + Bug 3 fixed in Sprint 0) |
| `lexicon_fr_v3.csv` | 78 | Beta |
| `lexicon_ki_v3.csv` | 1,240 | Production |

**Lexicon `avoid_when` field must use pipe-separated ContextCondition enum values** — not prose.
Valid values: `quote|historical|proper_noun|biographical|statistical|medical|counter_stereotype|legal|artistic|organization`

### Ground truth files

| File | Rows | Human annotated | κ |
|---|---|---|---|
| `eval/ground_truth_en_v5.csv` | 66 | Yes (hand-curated) | N/A |
| `eval/ground_truth_sw_v5.csv` | 51,419 | **850 rows human-reviewed (ann_sw_v2), 269 candidates remaining** | Unmeasurable (2nd annotator needed) |
| `eval/ground_truth_fr_v5.csv` | 50 | Yes (hand-curated) | N/A |
| `eval/ground_truth_ki_v8.csv` | 11,848 | Partial | 14.3% overlap |

### Review UI (ui/)

Streamlit app — loads `audit_logs/rewrites.jsonl`, shows original vs rewrite, records decisions to `audit_logs/reviews.jsonl`. Full review form: approve / approve_with_edit / reject / flag. Stats panel shows F1/precision/recall/lexicon counts. Modular split: `ui/app.py` (layout) / `ui/data.py` (I/O) / `ui/components.py` (rendering).

---

## Swahili Dataset — Key Facts

- **51,419 rows**: Zenodo Swahili News (65.7%), HuggingFace AfriSenti (34.3%)
- **has_bias=true**: 1,915 rows (3.7%) — occupation (92.7%), capability (5.5%), pronoun (3%), family role (0.8%)
- **Implicit bias**: only 19 rows (0.04%) — AIBRIDGE requires ≥5%
- **Counter-stereotype**: <2% — AIBRIDGE requires ≥15%
- **region_dialect**: Tagged — kenya=18,008, tanzania=33,411. Sheng/Uganda=0 (gap).
- **domain**: 98.2% media — needs health, education, household
- **expected_correction**: ~950 of 1,915 bias=true rows still empty (down from 1,071; batches 001–017 in progress)

**Lexicon coverage gaps AfriLabs will probe first:**
- Proverbs: `mwanamke ni nyumba`, `mke mzuri ni utii`, `mwanamke ni shamba la baba`
- Sheng: `dame`, `msupa wa ofisi`, `mrembo job`
- Bride-price: `mahari`, `kuolea`
- Religious framing patterns
- Male stereotypes: only ~2 entries

---

## AIBRIDGE Framework

### Tier requirements

| Tier | Min Samples | Double Annotation | κ | F1 |
|---|---|---|---|---|
| Bronze | 1,200 | 10% | ≥0.70 | ≥0.75 |
| Silver | 5,000 | 20% | ≥0.75 | ≥0.80 |
| Gold | 10,000+ | 30% | ≥0.80 | ≥0.85 |

### Current tier status (honest)

| Language | Sample count | κ | F1 | Honest tier |
|---|---|---|---|---|
| English | 66 | N/A | 0.786 | Pre-Bronze |
| Swahili | 51,419 | Unmeasurable | 0.802 | Sample count: Gold. F1: Pre-Bronze (needs κ + recall ≥0.75 for Bronze) |
| French | 50 | N/A | 0.542 | Pre-Bronze |
| Kikuyu | 11,848 | Partial (14.3%) | 0.352 | Sample count: Bronze. F1: Pre-Bronze |

### AI BRIDGE session action items (Feb 13, 2026)

From Rebecca (AI Ethics & Gender Expert):
1. Fix correction layer bug — corrected text not applying ✅ Done (Sprint 0)
2. Add human feedback/flagging mechanism in UI ✅ Done (Sprint 1 — full review form)
3. Add plain-language explanations for flagged words ✅ Done (Sprint 1 — `reason` field)
4. Diversify beyond religious text; add livelihood + household domains ← Sprint 3
5. Document dialect/regional diversity (Sheng, Tanzanian, Coastal) ← Sprint 2+ (Tanzania tagged; Sheng=0)
6. Document annotator gender breakdown in Dataset Card ← Sprint 3
7. Update gender representation ratio with each dataset version ← ongoing
8. Update Model Card every time model is retrained ← ongoing
9. Research meaning preservation metrics ← Sprint 2 (SemanticPreservationMetrics exists in eval/)
10. Establish reporting practice: bias patterns found, changes made, before/after metrics ← ongoing
11. Complete Dataset Card for current Swahili version ← Sprint 3
12. Reach out to Richard to re-test with updated dataset + get his test parameters ← Done ✅

---

## Common Commands

```bash
# Evaluation
python3 run_evaluation.py                   # F1 across all languages
python3 eval/correction_evaluator.py        # Correction quality
python3 demo_live.py                        # Interactive demo

# Services
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
streamlit run review_ui/app.py --server.port 8501

# Tests
python3 tests/test_system.py
python3 tests/test_fairness_metrics.py
python3 tests/test_hitl_metrics.py

# Make shortcuts
make eval | make test | make run-api | make run-ui | make run | make format
```

---

## What Needs Cleaning (root-level clutter)

These files are untracked at root level — commit them to `docs/` or delete:
- `AIBRIDGE_ALIGNMENT_ASSESSMENT.md` — superseded by current CLAUDE.md
- `AIBRIDGE_QUICK_REFERENCE.md` — merge useful parts into docs/
- `FINAL_SUMMARY.md` — outdated (claims F1=1.000)
- `MIGRATION_COMPLETE.md` — one-time record, archive to docs/
- `MIGRATION_GUIDE.md` — useful, move to docs/
- `QUICK_START.md` — useful, move to docs/ or keep at root
- `DATA_COLLECTION_REPORT.md` — move to docs/

`eval/` has legacy ground truth versions (`ki_v5`, `ki_v6`, `ki_v7`) — keep v8 as current, others can be archived.

`rules/` has legacy lexicon files (`lexicon_ki_v2.csv`, `lexicon_ki_corpus.csv`, `lexicon_ki_transcripts.csv`, `kikuyu_purist_bias_lexicon_110_rows.csv`) — archive or delete.

---

## Important Constraints

1. **Precision must stay at 1.000 on replace-severity rules** — zero false positives on correction output
2. **Language independence** — each language has its own lexicon + ground truth
3. **Case preservation** — all replacements maintain original casing ("Chairman" → "Chairperson")
4. **Audit trail** — all API corrections logged to `audit_logs/rewrites.jsonl`
5. **No stdlib dependency in core eval** — `run_evaluation.py` must work with Python 3.12+ stdlib only
6. **`avoid_when` must be enum values** — never prose text (see Bug 3 above)
7. **`severity=warn` never sets `has_bias_detected=True`** — warn edits are informational only
