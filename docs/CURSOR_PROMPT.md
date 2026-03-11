# JuaKazi — Cursor Implementation Prompt
# Complete this project from current state to production-ready submission

---

## WHO YOU ARE

You are a staff engineer completing the JuaKazi Gender Sensitization Engine.
JuaKazi detects, corrects, and explains gender bias in African-language text
(Swahili, Kikuyu, English, French). It is the only tool in East Africa that
does detection + correction + explanation in one API call.

Read `CLAUDE.md` fully before touching any file. It is the single source of truth.

---

## HARD RULES — NEVER BREAK THESE

1. Every change must keep `python3 run_evaluation.py` passing — no crashes
2. Every lexicon change needs a before/after eval run — no regressions
3. `severity=warn` never sets `has_bias_detected=True` — ever
4. `avoid_when` must be pipe-separated ContextCondition enum values — never prose
5. `Precision ≥ 1.000` on replace-severity EN rules — test before adding any
6. No new files unless strictly required — edit existing files
7. Do not merge to main until `python3 tests/test_system.py` passes 5/5
8. Always work in branches — squash merge to main — never commit directly to main
9. Never push unless explicitly instructed
10. Never credit AI tools in commit messages

---

## CURRENT STATE (Mar 2026)

### What works
- Detection engine: `eval/bias_detector.py` — rules + ContextChecker (10 conditions)
- REST API: `POST /rewrite` on HuggingFace Spaces — FastAPI + Gradio via `gr.mount_gradio_app`
- Next.js frontend: `apps/web/` — scaffolded, wired to HF Spaces API, on Vercel
- ML Stage 2: `juakazike/sw-bias-classifier-v1` on HuggingFace (F1=0.854 val, warn-only)
- Ground truth: 64,723 Swahili rows, 11,848 Kikuyu, 66 English, 50 French
- Lexicons: sw=218 entries, ki=1240, en=538, fr=78
- Tests: `python3 tests/test_system.py` — 5/5 passing

### Current metrics
| Language | F1    | Precision | Recall | Samples |
|----------|-------|-----------|--------|---------|
| English  | 0.786 | 1.000     | 0.647  | 66      |
| Swahili  | 0.771 | 0.734     | 0.811  | 64,723  |
| French   | 0.542 | 1.000     | 0.371  | 50      |
| Kikuyu   | 0.352 | 0.926     | 0.217  | 11,848  |

### Known issues
- Low recall across all languages — primary F1 driver — root cause: lexicon coverage gaps
- SW precision 0.734 — `Watoto wa Kike`/`mtoto wa kike` (182+138 FPs) — ambiguous phrases
- Kikuyu F1 0.352 — recall 0.217 — lexicon underfires on real patterns
- Cohen's Kappa = 0 — 2nd annotator not yet recruited (AIBRIDGE Bronze blocker)
- `review_ui/` reference fixed → `ui/` — already in README and REPRODUCIBILITY.md

---

## WHAT TO BUILD — IN ORDER

### TASK 1 — Lexicon expansion (SW + KI) — biggest F1 impact

**Swahili — add these missing categories:**
- 5 proverbs: `mwanamke ni chombo`, `mke ni nguo mume ni nguo`, `mama ni nguzo ya nyumba`,
  `mwanamke hana akili`, `mkoba wa mwanamke ni mdomo wake`
- 10 Sheng terms: `dem`, `mresh`, `mami`, `babe`, `dame`, `gal`, `manzi`, `bibi mdogo`,
  `sponsor`, `sugardad`
- Bride-price patterns: `mahari`, `kuolea`, `kulipa mahari`, `bei ya bibi`, `ng'ombe za mahari`
- Religious framing: `mke mwema`, `mume ndiye kichwa`, `mwanamke atii mume`, `bwana wa nyumba`
- Male leadership default: `mkurugenzi wa kiume`, `mkuu wa kiume`, `bosi wa kiume`

For every new entry:
- `severity=replace` only if Precision stays 1.000 after eval run
- otherwise `severity=warn`
- `avoid_when` must use valid ContextCondition enum values from `eval/context_checker.py`
- Run `python3 run_evaluation.py` before and after — paste both results in commit message

**Kikuyu — the 0.217 recall is the biggest gap:**
- Mine `eval/ground_truth_ki_v8.csv` for `has_bias=true` rows that the detector misses
- Extract unmatched patterns — add to `rules/lexicon_ki_v3.csv`
- Target: recall ≥ 0.45 without dropping precision below 0.90

---

### TASK 2 — Fix SW precision FPs

`Watoto wa Kike` (182 FPs) and `mtoto wa kike` (138 FPs) fire in advocacy contexts.
Options (pick the safer one after testing):

**Option A — Demote to warn:**
Change severity from `replace` to `warn` for both entries.
Run eval — check SW F1 impact. Accept if F1 stays ≥ 0.77.

**Option B — Add counter-stereotype context:**
Add `counter_stereotype` to `avoid_when` for these entries.
Run eval — check if FP count drops without hurting recall.

Do NOT do both. Pick one, run eval, commit.

---

### TASK 3 — Next.js frontend completion (apps/web/)

Current state: scaffolded, TextAnalyzer + CorrectionPanel + LanguageSelector exist.
Missing: BiasSpans highlighted text, ReasonTooltip, batch CSV page, about page, mobile audit.

**Stack:** Next.js 14, TypeScript, Tailwind, Shadcn UI
**API:** `POST https://juakazike-gender-sensitization-engine.hf.space/rewrite`
**Brand colors:** deep green `#1a5c2e` (primary), `#38a169` (accent)
**Logo:** `https://i.postimg.cc/L5mk9h1P/juakazi.png`

**3a — BiasSpans component** (`apps/web/components/BiasSpans.tsx`)

Renders the original text with biased spans highlighted inline.
- Red highlight for `severity=replace` edits
- Yellow highlight for `severity=warn` edits
- Clicking a span shows a tooltip with `bias_type` + `reason`
- Props: `text: string`, `edits: Edit[]`

```tsx
// Approach: split text into segments, wrap matched spans in <mark>
// Use edit.from to find span positions via string indexOf
// replace-severity → bg-red-100 border-b-2 border-red-400
// warn-severity    → bg-yellow-100 border-b-2 border-yellow-400
```

**3b — ReasonTooltip** (`apps/web/components/ReasonTooltip.tsx`)

Shadcn `<Tooltip>` wrapper showing:
- Bias type (badge)
- Plain-language reason from API
- Severity badge (replace=red, warn=yellow)

**3c — CorrectionPanel enhancement**

Current `CorrectionPanel.tsx` exists but is basic. Enhance to:
- Show side-by-side: original (with BiasSpans highlights) | corrected text
- Show confidence score
- Show source label ("Detected by: rules" or "Detected by: ML")
- Show each edit as a card with reason + severity badge

**3d — Batch CSV page** (`apps/web/app/batch/page.tsx`)

- Upload a CSV file with a `text` column
- Call `/rewrite` for each row (with concurrency limit of 5)
- Show progress bar
- Download results CSV with added columns: `rewrite`, `has_bias_detected`, `reason`, `confidence`

```tsx
// Use Papa Parse for CSV parsing
// Use Promise pool pattern for concurrency (p-limit or manual)
// Stream results to table as they complete
```

**3e — About page** (`apps/web/app/about/page.tsx`)

- What JuaKazi detects (4 bias types with examples)
- AIBRIDGE tier table (Bronze/Silver/Gold requirements vs current status)
- Current metrics table (F1/P/R per language with honest tier labels)
- Link to GitHub + HuggingFace model

**3f — Landing page** (`apps/web/app/page.tsx`)

Hero with:
- JuaKazi logo
- One-line value prop: "Detect and correct gender bias in African-language text"
- Language pills: SW · EN · FR · KI
- CTA button → /analyze
- Three feature cards: Detect / Correct / Explain
- Footer: GitHub · HuggingFace · AIBRIDGE

**3g — Mobile responsiveness**

Audit all pages at 375px, 768px, 1280px.
TextAnalyzer textarea must be usable on mobile.
CorrectionPanel side-by-side must stack on mobile.

---

### TASK 4 — Gradio demo improvements (gradio_app.py)

Current: works but basic markdown output.

Add:
- Metrics footer updated to Mar 2026 values (SW F1=0.771, not 0.885)
- Show `reason` field in detection output
- Show `skipped_context` when ContextChecker fired
- Example sentences for all 4 languages (already in EXAMPLES dict — verify all work)

Do NOT change the FastAPI mounting pattern — `gr.mount_gradio_app` is working.

---

### TASK 5 — Evaluation pipeline hardening

**5a — Stale metrics in gradio_app.py**

Line 32: `"sw": dict(f1=0.885 ...)` — this is wrong, current is 0.771.
Fix:
```python
"sw": dict(f1=0.771, precision=0.734, recall=0.811, tier="Gold (sample count)", samples=64_723),
```

**5b — correction_evaluator.py — never been run**

Run `python3 eval/correction_evaluator.py` and paste output.
If it crashes, fix the crash. Do not rewrite the file — fix the minimal bug.

**5c — Fairness metrics**

Run `python3 tests/test_fairness_metrics.py` — confirm passing.
If any test fails, fix it.

---

### TASK 6 — ExternalTeamDetector stub

For AIBRIDGE integration — when other teams' detectors are ready, JuaKazi wraps them.

Create `eval/external_detector.py`:

```python
"""
Stub for external team detector integration.
When AIBRIDGE signals readiness, implement the actual REST call or HF model load.
"""
from eval.models import BiasDetectionResult, Language

class ExternalTeamDetector:
    """
    Wraps an external team's bias detector and adapts their schema
    to JuaKazi's BiasDetectionResult.

    Usage:
        detector = ExternalTeamDetector(team_name="TeamX", endpoint="https://...")
        result = detector.detect(text, language)
        # result.source == "external:TeamX"
    """

    def __init__(self, team_name: str, endpoint: str = None, hf_model: str = None):
        self.team_name = team_name
        self.endpoint = endpoint
        self.hf_model = hf_model

    def detect(self, text: str, language: Language) -> BiasDetectionResult:
        # TODO: implement when AIBRIDGE signals readiness
        # Return empty result for now — stub only
        return BiasDetectionResult(
            has_bias_detected=False,
            detected_edits=[],
            warn_edits=[],
        )
```

Do not wire this into the main pipeline yet — stub only.

---

## DATA PLAN — HOW TO GET GOOD DATA AND STOP LOW F1

### Why F1 is low (root causes)

1. **Recall gap (primary):** lexicon does not cover many real bias patterns
   - Solution: expand lexicon with evidence from ground truth misses

2. **Label noise in ML training:** ann_sw_v3 AI-annotated 13,304 rows with some ambiguous labels
   - v1 (clean labels, 3 epochs) → F1=0.854
   - v3 (noisy labels, 5 epochs + oversampling) → F1=0.673
   - Solution: filter ML training to human-reviewed rows only (qa_status=gold or qa_status=passed)

3. **Class imbalance (98% neutral / 2% bias):** oversampling helped but noise hurt more
   - Solution: fix labels first, then oversample

4. **Domain imbalance:** 98.2% news text — model overfits to news language patterns
   - Solution: add health, livelihoods, household domain rows (Sprint 3)

### ML training data strategy for v4/v5

```python
# In kaggle_finetune_v4.ipynb — filter training rows:
# Only use rows where qa_status in ('gold', 'passed', 'human_reviewed')
# This reduces quantity but increases quality → better F1

df_clean = df[df['qa_status'].isin(['gold', 'passed', 'human_reviewed'])]
# Expected: ~2,000-5,000 rows — much smaller but cleaner

# Then oversample BIAS to 30% (not 25%)
# Use 3 epochs not 5 — v1 showed 3 was the sweet spot
# learning_rate=2e-5 (slightly higher — smaller dataset needs faster convergence)
```

### Ground truth improvement plan (to run before next ML training)

**Step 1 — Gold rows (200 minimum):**
- Take the 274-row human_review_batch_024 that was reviewed
- Mark rows where both annotator and auto-label agree as `qa_status=gold`
- Target: 200 gold rows minimum

**Step 2 — Clean the AI annotation pass:**
- ann_sw_v3 13,304 rows were AI-labelled — many are uncertain
- Filter to only rows where `annotator_confidence=high`
- Demote low-confidence rows to `qa_status=needs_review`

**Step 3 — Domain diversification (Sprint 3):**
- Run `/sw-collect` skill for health domain (200+ sentences about health + gender)
- Run `/sw-collect` for household/care domain (200+ sentences)
- These new domains will improve generalisation

**Step 4 — Retrain on clean data:**
- Use gold + high-confidence rows only
- 3 epochs, lr=2e-5, oversample BIAS to 30%
- Target: F1 ≥ 0.85

### Lexicon-driven recall improvement

The fastest path to better F1 is not ML retraining — it is lexicon expansion.
Each new correctly-scoped lexicon rule costs 10 minutes and can recover
multiple percentage points of recall.

Priority order:
1. Kikuyu recall (0.217 → target 0.45): mine ki_v8.csv false negatives
2. SW recall (0.811 → target 0.87): add proverbs + bride-price + Sheng
3. EN recall (0.647 → target 0.75): add generic masculine patterns
4. FR recall (0.371 → target 0.60): add French occupational patterns

---

## ML ENGINEERING PATTERNS TO USE

No external LLM API calls. We train our own models on our own data.
The pipeline is: rules engine (Stage 1) → fine-tuned afro-xlmr-base (Stage 2).
Stage 3 is a better fine-tuned model, not an API call.

### Pattern 1 — Evaluation-driven development (enforce strictly)

Before any change:
```bash
python3 run_evaluation.py  # record baseline
# make change
python3 run_evaluation.py  # compare
# only merge if F1 >= baseline
```

### Pattern 2 — Clean data beats more data

v1 (clean labels, 3 epochs) → F1=0.854
v3 (noisy AI labels, 5 epochs, oversampling) → F1=0.673

**Lesson:** filter training rows to `qa_status in ('gold', 'passed', 'human_reviewed')` before any retraining. Fewer clean rows outperform more noisy rows every time.

### Pattern 3 — Lexicon-first, ML-second

Each new lexicon rule recovers multiple % points of recall in 10 minutes.
ML retraining takes 75 minutes on T4 x2 and risks regression.
Always exhaust lexicon expansion before retraining.

Priority: lexicon → eval → retrain only if lexicon plateaus.

### Pattern 4 — Incremental fine-tuning strategy

For v4/v5 training:
- Start from v1 weights (not afro-xlmr-base) — warm start
- 3 epochs max — v1 proved this is the sweet spot
- lr=2e-5 (small dataset needs slightly faster convergence)
- Oversample BIAS to 30% — but only after labels are clean
- Evaluate every epoch — use early stopping on eval_f1

```python
# In kaggle_finetune_v4.ipynb:
# Load v1 as starting point instead of base model
MODEL_ID = 'juakazike/sw-bias-classifier-v1'  # warm start from v1
# Filter to clean rows only
df_clean = df[df['qa_status'].isin(['gold', 'passed', 'human_reviewed'])]
```

### Pattern 5 — Separate detection threshold tuning from training

After training, sweep threshold on val set:
```python
for threshold in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
    # compute F1, P, R at each threshold
    # pick threshold that maximises F1
    # default 0.75 may not be optimal after retraining
```

---

## FILE MAP — WHAT EACH FILE DOES

```
eval/bias_detector.py          ← Primary rules engine — DO NOT restructure
eval/context_checker.py        ← ContextCondition enum — valid avoid_when values
eval/ngeli_tracker.py          ← Swahili noun class tracking
eval/ml_classifier.py          ← afro-xlmr-base Stage 2 loader
eval/models.py                 ← Language, BiasLabel, BiasDetectionResult
api/main.py                    ← FastAPI routing only — no business logic here
api/rules_engine.py            ← apply_rules_on_spans, build_reason
api/schemas.py                 ← RewriteRequest, RewriteResponse
api/audit.py                   ← JSONL audit log writer
gradio_app.py                  ← HF Space entry point — FastAPI + Gradio
apps/web/                      ← Next.js frontend
rules/lexicon_{en,sw,fr,ki}_v3.csv  ← Production lexicons
eval/ground_truth_{lang}_v5.csv     ← Ground truth (gitignored for SW — too large)
run_evaluation.py              ← F1 eval entry point — must always pass
tests/test_system.py           ← 5/5 must pass before any merge
config.py                      ← DataVersions, RegionDialects
```

---

## AIBRIDGE COMPLIANCE CHECKLIST

Before any submission run these checks:

```bash
python3 run_evaluation.py          # F1 all languages — paste results
python3 tests/test_system.py       # 5/5 passing
python3 eval/correction_evaluator.py  # correction quality — first time
python3 tests/test_fairness_metrics.py
```

Current blockers for Bronze:
- [ ] Cohen's Kappa ≥ 0.70 — needs 2nd annotator [HUMAN TASK]
- [ ] 200 gold rows (qa_status=gold)
- [ ] Non-news domain rows (health, livelihoods, household)
- [ ] 100 minimal pairs
- [ ] CSVW JSON-LD metadata
- [ ] PROV lineage
- [ ] DVC tracking

---

## DEFINITION OF DONE

The project is complete when:

1. `python3 run_evaluation.py` shows:
   - SW F1 ≥ 0.85, Precision ≥ 0.85, Recall ≥ 0.85
   - EN F1 ≥ 0.80, Precision = 1.000
   - KI F1 ≥ 0.50
   - FR F1 ≥ 0.60

2. `python3 tests/test_system.py` → 5/5 passing

3. Next.js frontend on Vercel:
   - `/analyze` page works end-to-end with real API
   - BiasSpans highlights biased text inline
   - CorrectionPanel shows side-by-side diff
   - ReasonTooltip shows explanation on hover
   - `/batch` CSV upload/download works
   - Mobile-responsive at 375px

4. `POST /rewrite` on HF Spaces returns correct response within 3s

5. AIBRIDGE Bronze achieved:
   - κ ≥ 0.70 (needs 2nd annotator)
   - 200 gold rows
   - Dataset Card updated with final metrics

6. ML v4/v5 trained on clean labels: F1 ≥ 0.85 on validation set
