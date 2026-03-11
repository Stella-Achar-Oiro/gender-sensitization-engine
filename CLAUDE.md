# CLAUDE.md — JuaKazi Gender Sensitization Engine

This file is the single source of truth for Claude Code working in this repo.
It covers: what the project is, who is on the team, what agents exist, what is done, what is next, and how to execute.

---

## 1. Project Overview

**JuaKazi Gender Sensitization Engine** detects and corrects gender bias in African-language text.
We are the only tool in East Africa that does **detection + correction + plain-language explanation** in Swahili, Kikuyu, English, and French.

**What makes us different from every other team:**
- Other teams: detection only
- JuaKazi: detection → correction → reason → audit trail
- Integration plan: when AIBRIDGE says we are ready, wire other teams' detectors as Stage 1b, JuaKazi correction layer wraps all of them

**Current deployment:** HuggingFace Spaces (Gradio UI + FastAPI backend)
**Target deployment:** Next.js frontend (Vercel) + FastAPI backend (HF Spaces or Railway)

---

## 2. Team Structure & Roles

| Person | Role | Owns |
|---|---|---|
| **Project Lead** | Project Lead / Gender Expert | AIBRIDGE submission, AIBRIDGE contact relationship, annotator recruitment, Dataset Card, sprint decisions |
| **Engineer teammate** | Backend / Eval | run_evaluation.py, API, lexicon changes, eval pipeline, tests |
| **Data teammate** | Data / Annotation | ground truth expansion, annotation batches, sw-collect, sw-annotate, sw-lexicon |
| **Frontend teammate** | Product / Web | Next.js app, Vercel deploy, UI components (to be recruited or Project Lead does) |
| **Claude (AI)** | Staff Engineer | Executes all technical tasks via skills and agents — see Section 5 |

**Annotators (human, external):**
- ann_sw_v2 — Swahili annotator (batches 001–023, ~1,069 rows reviewed)
- ann_sw_v3 — AI annotation pass (13,304 rows annotated, Mar 2026)
- Human reviewer — batch_024 (274-row review, Mar 2026)
- 2nd Swahili annotator — **NOT YET RECRUITED** (blocker for Cohen's Kappa)
- Target: recruit via Masakhane community

---

## 3. Actual Performance Metrics (Mar 2026)

Run `python3 run_evaluation.py` to verify.

| Language | F1 | Precision | Recall | Samples | Honest tier |
|---|---|---|---|---|---|
| English | 0.786 | 1.000 | 0.647 | 66 | Pre-Bronze |
| **Swahili** | **0.771** | **0.734** | **0.811** | **64,723** | Sample count: Gold. IAA: unmeasured. |
| French | 0.542 | 1.000 | 0.371 | 50 | Pre-Bronze |
| Kikuyu | 0.352 | 0.926 | 0.217 | 11,848 | Sample count: Bronze. F1: Pre-Bronze |

**Qualifications (do not hide these):**
- Swahili/Kikuyu Gold/Bronze = sample count only. Cohen's Kappa unmeasurable — 2nd annotator not yet recruited.
- SW F1 updated after ann_sw_v3 pass (13,304 rows annotated). Precision drop 0.958→0.734 is honest signal: `Watoto wa Kike`/`mtoto wa kike`/`mtoto wa kiume` are genuinely ambiguous phrases (advocacy vs prescriptive). Root cause: lexicon over-fires on girls'-rights-advocacy contexts.
- Low recall = primary F1 driver across all languages. Root cause: lexicon coverage gaps.
- SW annotation passes complete: ann_sw_v2 (batches 001–023, ~1,069 rows), ann_sw_v3 (13,304 rows, AI pass), human review batch_024 (274 rows).

**ML Classifier (Stage 2):**
- Model: `juakazike/sw-bias-classifier-v1` (afro-xlmr-base fine-tuned, 3 epochs, T4 x2)
- Val metrics: P=0.938, R=0.784, F1=0.854, Loss=0.047
- **Retraining:** Run `scripts/stratified_split.py --language sw` then `python3 ml/train_classifier.py --use-splits --epochs 5`. Val F1/precision/recall are written to `output_dir/val_metrics.json`; update Model Card after each retrain.
- Activated via `JUAKAZI_ML_MODEL` env var in HF Space
- Stage 2 warn-only — never replaces text, never sets has_bias_detected=True directly

---

## 4. Architecture

### Detection pipeline

```
Input text
  → BiasDetector.detect_bias()
      ├── DEROGATION_PATTERNS (hardcoded, highest priority)
      ├── COUNTER_STEREOTYPE_PATTERNS (preserve — no correction)
      └── Lexicon rules (rules/lexicon_{lang}_v3.csv)
            ├── ContextChecker (10 conditions: quote|historical|proper_noun|biographical|statistical|medical|counter_stereotype|legal|artistic|organization)
            ├── severity=replace → has_bias_detected=True, edit queued
            └── severity=warn   → informational only, never sets has_bias_detected=True
  → BiasDetectionResult { has_bias_detected, detected_edits, warn_edits }

  Stage 2 (SW only, when JUAKAZI_ML_MODEL set):
  → MLBiasDetector.classify() → warn_edits only, threshold=0.75
```

### Correction pipeline

```
POST /rewrite { id, lang, text, flags?, region_dialect? }
  → apply_rules_on_spans() with ContextChecker
  → semantic preservation check (threshold 0.70)
  → ml_rewrite() fallback only when rules find nothing
  → audit log → audit_logs/rewrites.jsonl
  ← { original_text, rewrite, edits, confidence, source, reason, semantic_score }
```

### Evaluation pipeline

```
run_evaluation.py
  → GroundTruthLoader → eval/ground_truth_{lang}_v5.csv (ki: v8)
  → BiasDetector per row
  → MetricsCalculator → F1, Precision, Recall
  → FairnessCalculator → Demographic Parity, Equal Opportunity
  → eval/results/
```

### Key files

| File | Purpose |
|---|---|
| [eval/bias_detector.py](eval/bias_detector.py) | Primary rules engine |
| [eval/context_checker.py](eval/context_checker.py) | Context gating (10 conditions) |
| [eval/ngeli_tracker.py](eval/ngeli_tracker.py) | Swahili noun class tracking |
| [eval/ml_classifier.py](eval/ml_classifier.py) | afro-xlmr-base Stage 2 loader |
| [eval/hybrid_detector.py](eval/hybrid_detector.py) | Rules (70%) + ML (30%) hybrid |
| [eval/models.py](eval/models.py) | Language, BiasLabel, BiasDetectionResult |
| [api/main.py](api/main.py) | FastAPI routing only |
| [api/rules_engine.py](api/rules_engine.py) | apply_rules_on_spans, build_reason |
| [api/schemas.py](api/schemas.py) | RewriteRequest, RewriteResponse |
| [api/audit.py](api/audit.py) | JSONL audit logging |
| [ui/app.py](ui/app.py) | Streamlit layout (~30 lines) |
| [ui/data.py](ui/data.py) | load_rewrites, load_stats, save_review |
| [ui/components.py](ui/components.py) | render_stats_panel, render_edits, render_review_form |
| [config.py](config.py) | DataVersions, RegionDialects |
| [gradio_app.py](gradio_app.py) | Gradio public demo (HF Spaces) |
| [docs/UI_APPS.md](docs/UI_APPS.md) | Canonical list of UI entry points (Next.js, Streamlit, Gradio) |
| [run_evaluation.py](run_evaluation.py) | Main eval entry point |
| [demo_live.py](demo_live.py) | Interactive CLI demo |

### Lexicons

| File | Entries | Status |
|---|---|---|
| `rules/lexicon_en_v3.csv` | 538 | Production |
| `rules/lexicon_sw_v3.csv` | 218 | Production |
| `rules/lexicon_fr_v3.csv` | 78 | Beta |
| `rules/lexicon_ki_v3.csv` | 1,240 | Production |

**`avoid_when` must be pipe-separated ContextCondition enum values — never prose.**
Valid: `quote|historical|proper_noun|biographical|statistical|medical|counter_stereotype|legal|artistic|organization`

### Ground truth files

| File | Rows | Human annotated | κ |
|---|---|---|---|
| `eval/ground_truth_en_v5.csv` | 66 | Yes (hand-curated) | N/A |
| `eval/ground_truth_sw_v5.csv` | 64,723 | 1,069 rows (ann_sw_v2, batches 001–023) | Unmeasurable (2nd annotator needed) |
| `eval/ground_truth_fr_v5.csv` | 50 | Yes (hand-curated) | N/A |
| `eval/ground_truth_ki_v8.csv` | 11,848 | Partial | 14.3% overlap |

**Submission file:** `eval/ground_truth_sw_v5_submission_20260305.csv` (64,723 rows, 70.5 MB) — shares via Google Drive / Zenodo, not git (gitignored, too large + PII).

---

## 5. Claude Skills (Agents)

Every skill is invoked with `/skill-name` in Claude Code.
Each skill has a full briefing file in `.claude/skills/`.

| Skill | What it does | When to use |
|---|---|---|
| `/recruit-annotator` | Generates Masakhane Slack post, annotator onboarding package, export command, and κ verification steps | When Project Lead is ready to recruit the 2nd Swahili annotator (AIBRIDGE Bronze blocker) |
| `/sw-annotate` | Native Swahili annotator — fills target_gender, explicitness, stereotype_category, expected_correction, qa_status | After any new rows are added to ground truth with qa_status=needs_review |
| `/sw-lexicon` | Expands `lexicon_sw_v3.csv` from corpus evidence. Zero false positives hard constraint. | When adding new occupation/gender terms to Swahili lexicon |
| `/sw-collect` | Downloads + formats real Swahili text from open datasets (Wikipedia, MasakhaNews, C4, AfriSenti) into AIBRIDGE rows | When we need more ground truth data |
| `/data-expert-review` | Full AIBRIDGE compliance audit — schema, IAA, balance, traceability, privacy | Before any AIBRIDGE submission or milestone review |
| `/gender-expert-review` | Cultural validity + implicit bias stress test — East African context | Before AfriLabs expert testing session |
| `/pai-engineer-review` | Architecture + false positive root cause + gap to Claude Opus performance | Before any technical whiteboard session |
| `/techdebt-review` | Prioritised debt register — BLOCKING / HIGH / MEDIUM / LOW | Before sprint planning |
| `/aibridge-migrate` | Schema migration + gap analysis + validation | When migrating ground truth to canonical AIBRIDGE schema |
| `/senior-ai-engineer-review` | Production readiness: API, latency, error handling, security, test coverage | Before any public demo or handoff |

**How agents handle human-only tasks:**
When a skill identifies a task that requires a human (e.g. recruiting annotators, reaching out to AIBRIDGE contact, domain name registration), it outputs a clearly labelled `[HUMAN TASK]` block and stops. Claude does not attempt to do it.

---

## 6. Bugs — All Status

| Bug | Description | Status |
|---|---|---|
| Bug 1 | Correction not applying in demo | ✅ FIXED Sprint 0 |
| Bug 2 | Verbatim article paragraphs in SW lexicon (>80 char biased entries) | ✅ FIXED Sprint 0 |
| Bug 3 | `avoid_when` field had prose instead of enum values | ✅ FIXED Sprint 0 |
| Bug 4 | `config.py` GROUND_TRUTH version mismatch (v4 vs v5) | ✅ FIXED (config now reads v5) |
| Bug 5 | `local_files_only=True` in ml_classifier.py blocked HF Space model download | ✅ FIXED Mar 2026 |

---

## 7. AIBRIDGE Compliance Status

### Tier requirements

| Tier | Min Samples | Double Annotation | κ | F1 |
|---|---|---|---|---|
| Bronze | 1,200 | 10% | ≥0.70 | ≥0.75 |
| Silver | 5,000 | 20% | ≥0.75 | ≥0.80 |
| Gold | 10,000+ | 30% | ≥0.80 | ≥0.85 |

### What is done (Mar 2026)

| Check | Status |
|---|---|
| 24-column canonical AIBRIDGE schema | ✅ |
| target_gender=neutral on non-biased rows (49,868 rows fixed) | ✅ |
| stereotype_category filled on all has_bias=true rows | ✅ |
| explicitness filled on all has_bias=true rows | ✅ |
| PII scrubbed (110 rows, pii_removed=true) | ✅ |
| Counter-stereotype ≥15% | ✅ 15.63% (10,115 rows) |
| Implicit rows ≥5% | ✅ 5.01% (3,244 rows) |
| region_dialect tagged (SW) | ✅ kenya=18,008, tanzania=33,411 |
| Explainability (reason field) | ✅ |
| Human feedback UI | ✅ |
| Dataset Card v3 | ✅ |
| Model Card v2 | ✅ |
| expected_correction filled (batches 001–023) | ✅ 1,069 rows done |

### What is still missing (blockers)

| Check | Status | Blocker? |
|---|---|---|
| Cohen's Kappa (κ) | ❌ 0% — 2nd annotator not recruited | **BLOCKING for Bronze IAA** |
| Gold rows (qa_status=gold, 200 minimum) | ❌ 0 | Blocking for drift monitoring |
| Non-news domains (health, livelihoods, household) | ❌ 98.2% media | AIBRIDGE §7 |
| 100 minimal pairs (gender-swap variants) | ❌ 0 | AIBRIDGE §11 |
| CSVW JSON-LD metadata | ❌ | AIBRIDGE §13 |
| PROV lineage | ❌ | AIBRIDGE §13 |
| DVC tracking | ❌ | AIBRIDGE §13 |
| Sheng/Uganda rows | ❌ 0 | Coverage gap |
| Annotator gender breakdown documented | ❌ | AIBRIDGE §9 |
| Proverbs in lexicon (5 minimum) | ❌ 0 | Coverage gap |
| Sheng terms in lexicon (10 minimum) | ❌ 0 | Coverage gap |

### AI BRIDGE action items from AIBRIDGE contact (Feb 13, 2026)

| # | Item | Status |
|---|---|---|
| 1 | Fix correction layer bug | ✅ Done |
| 2 | Human feedback/flagging in UI | ✅ Done |
| 3 | Plain-language explanations | ✅ Done |
| 4 | Diversify beyond news — livelihoods + household | ← Sprint 3 |
| 5 | Document dialect/regional diversity | Partial (Tanzania tagged, Sheng=0) |
| 6 | Document annotator gender breakdown | ← Sprint 3 |
| 7 | Update gender representation ratio each version | Ongoing |
| 8 | Update Model Card every retraining | Ongoing |
| 9 | Research meaning preservation metrics | SemanticPreservationMetrics exists in eval/ |
| 10 | Establish reporting practice | Ongoing |
| 11 | Complete Dataset Card | Partial (v3, metrics need update) |
| 12 | Re-test with Richard | ✅ Done |

---

## 8. Sprint Plan

### ✅ Sprint 0 — Stabilise (COMPLETE)
All 3 bugs fixed. Tests passing. Merged to main.

### ✅ Sprint 1 — Explainability + Feedback (COMPLETE)
reason field, review UI, region_dialect, Dataset Card v3, Model Card v2.

### 🔴 Sprint 2 — Human Annotation + Real Metrics (IN PROGRESS — INCOMPLETE)

**Owner: Project Lead + Data teammate + Annotators**

| Task | Owner | Status | Effort |
|---|---|---|---|
| Recruit 2nd Swahili native speaker (Masakhane) | Project Lead | ❌ Not started | [HUMAN TASK] |
| Sample 500 rows with overlapping assignment | Data | ❌ Blocked on annotator | 2h once annotator ready |
| Annotation session (500 rows, 2 annotators) | Annotators | ❌ Blocked | 1 week |
| Compute Cohen's Kappa | Engineer | ❌ Blocked | 2h |
| Run correction_evaluator.py | Engineer | ❌ Not run yet | 2h |
| Add 5 Swahili proverbs to lexicon | Data / `/sw-lexicon` | ❌ Not started | 3h |
| Add 10 Sheng terms to lexicon | Data / `/sw-lexicon` | ❌ Not started | 3h |
| Update Model Card after correction eval | Project Lead | ❌ Blocked | 30m |
| ~~Fill expected_correction on missing rows~~ | Data | ✅ Done (ann_sw_v3 + human review) | — |
| ~~ann_sw_v3 AI annotation pass (13,304 rows)~~ | Claude | ✅ Done Mar 2026 | — |
| ~~Human review batch_024 (274 rows)~~ | Human reviewer | ✅ Done Mar 2026 | — |
| ~~Detector recall fix (occupation prefix expansion)~~ | Engineer | ✅ Done Mar 2026 | — |

**Sprint 2 cannot close until κ is measured.**

### 🟡 Sprint 3 — Dataset Balance + AIBRIDGE Submission (NOT STARTED)

**Start only after Sprint 2 closes.**
**Owner: Data teammate + Engineer + Project Lead**

| Task | Owner | Agent | Effort |
|---|---|---|---|
| Generate 100 minimal pairs | Data | `/sw-collect` | 1 week |
| Add health domain rows (200+ minimum) | Data | `/sw-collect` | 1 week |
| Add livelihoods domain rows (200+ minimum) | Data | `/sw-collect` | 1 week |
| Add household/care domain rows (200+ minimum) | Data | `/sw-collect` | 1 week |
| Add bride-price patterns to lexicon (mahari, kuolea) | Data | `/sw-lexicon` | 3h |
| Add religious framing patterns to lexicon | Data | `/sw-lexicon` | 3h |
| Add male stereotype entries (~13 more) | Data | `/sw-lexicon` | 3h |
| Create 200 gold rows (qa_status=gold) | Data / Annotators | `/sw-annotate` | 1 week |
| Tag Sheng/Uganda rows | Data | `/sw-collect` | 1 week |
| Document annotator gender breakdown | Project Lead | [HUMAN TASK] | 30m |
| CSVW JSON-LD metadata | Engineer | — | 4h |
| PROV lineage | Engineer | — | 4h |
| DVC tracking setup | Engineer | — | 4h |
| Update Dataset Card (metrics, domains, annotator breakdown) | Project Lead | — | 3h |
| Final eval run + confirm all metrics | Engineer | — | 2h |
| Run `/data-expert-review` before submission | Claude | `/data-expert-review` | 1h |
| Run `/gender-expert-review` before submission | Claude | `/gender-expert-review` | 1h |
| Submit to AIBRIDGE contact / AIBRIDGE | Project Lead | [HUMAN TASK] | — |

### 🟡 Sprint 4 — Web App (CAN RUN IN PARALLEL WITH SPRINT 3)

**Owner: Frontend teammate + Engineer**

**Goal:** Public-facing product. Anonymous users (no auth on launch). Swahili first, other languages work if selected. Mobile + desktop. HF Spaces backend (existing). Vercel frontend (new).

**Stack:** Next.js 14 (TypeScript, Tailwind, Shadcn UI) + existing FastAPI backend

**Architecture (from LLM engineering course patterns):**
```
apps/web/                          ← Next.js on Vercel
  app/
    page.tsx                       ← Landing page
    analyze/page.tsx               ← Main analyzer UI
    batch/page.tsx                 ← CSV batch upload
    about/page.tsx                 ← What we detect + AIBRIDGE tiers
  components/
    LanguageSelector.tsx           ← Swahili default, all 4 available
    TextAnalyzer.tsx               ← Input + results in one component
    BiasSpans.tsx                  ← Color-coded highlighted text
    CorrectionPanel.tsx            ← Side-by-side original/corrected
    ReasonTooltip.tsx              ← Plain-language explanation popup
    SeverityBadge.tsx              ← replace (red) / warn (yellow)
    SourceLabel.tsx                ← "Detected by: rules / ML / [Team X]"
  lib/
    api.ts                         ← Typed client for POST /rewrite
    types.ts                       ← RewriteRequest, RewriteResponse types
```

**External team integration (when AIBRIDGE ready):**
```
eval/external_detector.py          ← ExternalTeamDetector class
  → calls their REST API or loads their HF model
  → adapts their schema → our BiasDetectionResult
  → UI shows "Detected by: [Team X] · Corrected by: JuaKazi"
```

**Sprint 4 tasks:**

| Task | Owner | Effort |
|---|---|---|
| Scaffold Next.js app (Shadcn, Tailwind, TypeScript) | Frontend | 1 day |
| `/analyze` page — language selector + text input + results | Frontend | 2 days |
| BiasSpans component (color-coded highlights) | Frontend | 1 day |
| CorrectionPanel (side-by-side) | Frontend | 1 day |
| ReasonTooltip (reason field from API) | Frontend | 0.5 day |
| Deploy to Vercel (connect to existing HF Spaces API) | Frontend + Engineer | 1 day |
| `/batch` page (CSV upload + download) | Frontend | 2 days |
| `/about` page + AIBRIDGE tier badges | Frontend | 1 day |
| Mobile responsiveness audit | Frontend | 1 day |
| ExternalTeamDetector stub (wire when team ready) | Engineer | 2h |

---

## 9. Execution Rules (Hard — Never Break)

1. **One sprint at a time for AIBRIDGE work.** Sprint 3 starts only when Sprint 2 closes (κ measured).
2. **Sprint 4 (web app) can run in parallel** — it does not touch eval or ground truth.
3. **Every change must keep `python3 run_evaluation.py` passing** — no crashes.
4. **Precision ≥ 1.000 on replace-severity rules.** Never add a replace rule without passing precision test first.
5. **`avoid_when` must be pipe-separated ContextCondition enum values** — never prose text.
6. **`severity=warn` never sets `has_bias_detected=True`** — always informational only.
7. **No new files unless strictly required.** Edit existing files.
8. **Every lexicon change needs before/after eval run** to confirm no regression.
9. **Do not merge to main until `python3 tests/test_system.py` passes 5/5.**
10. **Always work in branches; squash merge to main.** Never commit directly to main.
11. **Never push unless explicitly asked.**
12. **Never credit Claude in commit messages.**
13. **Agents identify human tasks clearly** — output `[HUMAN TASK]` and stop, do not attempt to do it.
14. **Ground truth CSV is gitignored** (size + PII). Share via Google Drive / Zenodo only.

---

## 10. Common Commands

```bash
# Evaluation
python3 run_evaluation.py                    # F1 across all languages
python3 eval/correction_evaluator.py         # Correction quality
python3 demo_live.py                         # Interactive CLI demo

# Services
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
streamlit run ui/app.py --server.port 8501

# Tests
python3 tests/test_system.py
python3 tests/test_fairness_metrics.py
python3 tests/test_hitl_metrics.py

# Make shortcuts
make eval | make test | make run-api | make run-ui | make run | make format

# Annotation export
python3 scripts/export_for_annotation.py
```

---

## 11. Files to Clean Up (low priority — do not block sprints)

Root-level untracked files — move to `docs/` or delete:
- `AIBRIDGE_ALIGNMENT_ASSESSMENT.md` — superseded by this file
- `AIBRIDGE_QUICK_REFERENCE.md` — merge useful parts to docs/
- `FINAL_SUMMARY.md` — outdated (claims F1=1.000), delete
- `MIGRATION_COMPLETE.md` — archive to docs/
- `MIGRATION_GUIDE.md` — move to docs/
- `QUICK_START.md` — move to docs/ or keep at root
- `DATA_COLLECTION_REPORT.md` — move to docs/

Legacy eval files — keep only current versions:
- `eval/ground_truth_ki_v5.csv`, `v6`, `v7` → archive (keep v8)

Legacy lexicon files — archive or delete:
- `rules/lexicon_ki_v2.csv`
- `rules/lexicon_ki_corpus.csv`
- `rules/lexicon_ki_transcripts.csv`
- `rules/kikuyu_purist_bias_lexicon_110_rows.csv`

---

## 12. What Each Teammate Picks Up Next

### Project Lead (Project Lead)
**This week:**
1. Post in Masakhane Slack: recruit 2 Swahili native speakers for 500-row annotation (paid if possible). Share `scripts/export_for_annotation.py` output with them. [HUMAN TASK]
2. Confirm AIBRIDGE contact's next review date and what she needs to see. [HUMAN TASK]

**This week (Claude will do):**
- Run `/sw-lexicon` to add 5 proverbs + 10 Sheng terms
- Run `python3 eval/correction_evaluator.py` and paste results here
- Update MEMORY.md after each completed task

### Engineer teammate
**Pick up:**
1. Run `python3 run_evaluation.py` and confirm SW F1=0.771 (updated Mar 2026 after ann_sw_v3)
2. Run `python3 eval/correction_evaluator.py` — first time running, paste results
3. Once 2nd annotator recruited: compute Cohen's Kappa (script exists in `scripts/`)
4. Sprint 4: scaffold `apps/web/` Next.js app

### Data teammate
**Pick up:**
1. Run `/sw-collect` for health domain rows (target: 200+ sentences about health + gender)
2. Run `/sw-collect` for household/care domain rows (target: 200+)
3. Generate 100 minimal pairs (gender-swap: each occupation × male/female/neutral)

### Frontend teammate (to be recruited or Project Lead does)
**Pick up:**
1. Read Sprint 4 task list above
2. Scaffold `apps/web/` with Next.js 14 + Shadcn + Tailwind
3. Implement `/analyze` page first — wire to `POST /rewrite` on existing HF Spaces API
