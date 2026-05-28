# JuaKazi ML Rebuild Plan — TDD Spec-Driven

**Last updated:** 2026-05-28
**Goal:** Complete detection + correction pipeline for 6 languages using open-source
African NLP models. No LLMs. Runs on HuggingFace Spaces (CPU/T4).

---

## Target Pipeline (what we are building)

```
POST /analyse { text, lang }
        │
        ▼
┌──────────────────────────────────────────────────┐
│  STAGE 1: ML Detector                            │
│  Model: juakazike/{lang}-bias-classifier-v1      │
│  Base:  afro-xlmr-base  (HA / ZU / SW / EN / FR)│
│         afro-xlmr-large-76L (KI only)            │
│  → Output: { biased: bool, confidence: float }   │
└────────────────┬─────────────────────────────────┘
                 │ biased = false → return as-is
                 │ biased = true ↓
┌──────────────────────────────────────────────────┐
│  STAGE 2: Lexicon Rules (fast precision layer)   │
│  rules/lexicon_{lang}_v3.csv                     │
│  Word-level substitution + reason field          │
│  → Output: corrected_text (or None if no match)  │
└────────────────┬─────────────────────────────────┘
                 │ no lexicon match ↓
┌──────────────────────────────────────────────────┐
│  STAGE 3: ML Corrector (seq2seq)                 │
│  Model: juakazike/{lang}-bias-corrector-v1       │
│  Base:  castorini/afriteva_v2_base (HA/ZU/SW)   │
│         google/mt5-small (KI)                    │
│  Input: "correct bias: {biased_sentence}"        │
│  → Output: neutral rewrite                       │
└──────────────────────────────────────────────────┘
        │
        ▼
Response {
  original_text, corrected_text,
  detected: bool, confidence: float,
  source: "lexicon" | "ml-corrector" | "none",
  edits: [{ original, replacement, reason }],
  flag_for_human_review: bool
}
```

**Detection and correction are separate models.**
Stage 1 = classifier. Stage 2 = fast rules. Stage 3 = seq2seq corrector.

---

## Current State (honest)

| Lang | Classifier | Corrector | F1 | Recall | Blocker |
|------|-----------|-----------|-----|--------|---------|
| SW | ✅ v3 on HF | ✅ lexicon (1,586 pairs) | 0.851 | 0.881 | none |
| EN | ✅ v3 on HF | ✅ lexicon | 1.000 | 1.000 | GT too small (66 rows) |
| FR | ✅ v3 on HF | ✅ lexicon | 0.970 | 0.941 | GT too small (165 rows) |
| HA | ❌ no ML model | ❌ pairs unvalidated | 0.043 | 0.022 | no trained classifier |
| ZU | ❌ no ML model | ❌ pairs unvalidated | 0.732 | 0.577 | GT schema broken |
| KI | ❌ wrong base model | ✅ GT has corrections | 0.667 | 0.510 | base model wrong |

---

## Data Audit — What We Have

### Classification training data (for Stage 1)

| Language | File | Rows | Biased | Neutral | Usable? |
|----------|------|------|--------|---------|---------|
| SW | `eval/ground_truth_sw_v5.csv` | 67,290 | 1,586 | 65,704 | ✅ production |
| HA | `eval/ground_truth_ha_v1.csv` | 10,054 | 1,012 | 9,042 | ✅ accepted, no corrections |
| HA | `study-labs-non-synthetics-qa-approved-sentences-2026-04-27T09-23-46-234Z.csv` | 10,178 | 1,136 | 9,042 | ✅ all accepted, richer labels |
| HA | `v3_revised_hausa_bias_ds.csv` | 4,539 | 2,169 stereotype + 2,370 counter | 0 | ✅ stereotype/counter only, no neutral |
| ZU | `eval/ground_truth_zu_v1.csv` | 2,000 | 1,978 | 22 | ⚠️ 99% biased — broken balance |
| KI | `eval/ground_truth_ki_v8.csv` | 11,622 | 1,603 | 10,019 | ✅ all have expected_correction |

**HA combined:** ground_truth_ha_v1 + StudyLabs file = ~15K unique rows (need dedup).
v3_revised_ha adds 2,169 stereotype rows but NO neutral rows — use only for corrector training.

**ZU problem:** 1,978 biased / 22 neutral = 99% biased. A classifier trained on this
will learn to always predict biased. We need more ZU neutral rows.

### Correction training data (for Stage 3)

| Language | File | Pairs | Approved | Notes |
|----------|------|-------|----------|-------|
| SW | `juakazi_sw_correction_pairs_v1.csv` | 1,586 | — (no qa_status col) | Production quality |
| HA | `juakazi_ha_correction_pairs_v1.csv` | 1,918 | 0 | AI-drafted, needs native speaker review |
| ZU | `juakazi_zu_correction_pairs_v1.csv` | 1,142 | 0 | AI-drafted, needs review |
| ZU | `zulu_retraining - zulu_retraining.csv.csv` | 2,000 | — | Instruction-tuning format (input/output pairs) — usable directly |
| KI | `eval/ground_truth_ki_v8.csv` | 11,622 | — (qa_status=passed) | All rows have expected_correction |

**ZU bonus:** The `zulu_retraining` file has 2,000 (biased→corrected) pairs in
instruction format. This is ready to use for AfriTeVa fine-tuning immediately.

---

## Data Inventory (updated 2026-05-28)

### What we now have (new files added)

| File | Lang | Rows | Labels | Usable for |
|------|------|------|--------|------------|
| `v4_revised_hausa_bias_ds.csv` | HA | 17,401 | neutral+stereotype+derogation+counter | HA classifier ← PRIMARY |
| `IsiZulu_Ithute_Dataset_Final.csv` | ZU | 9,570 | stereotype+derogation (all passed) | ZU classifier ← PRIMARY |
| `French Annotated - final (1).csv` | FR | 10,996 | neutral+stereotype+derogation+counter (10,648 gold) | FR classifier ← PRIMARY |
| `Umunthu Data - Swahili Annotated (3).csv` | SW | 10,741 | stereotype+neutral | SW supplement |
| `twitter-hausa-bias-*.csv` | HA | 1,608 | gender/no-bias (Twitter) | HA classifier supplement |
| `sheng_gender_tweets_clean.csv` | SW/Sheng | 46 | annotated | Sheng lexicon only |
| `zulu_retraining - zulu_retraining.csv.csv` | ZU | 2,000 | instruction pairs | ZU corrector (ready now) |

### Revised language status

| Lang | Classifier data | Corrector data | Remaining blocker |
|------|----------------|----------------|-------------------|
| HA | ~33K rows combined ✅ | 1,918 pairs (needs validation) | Native speaker review of pairs |
| ZU | 11,570 biased ✅ but ZERO neutral ❌ | 2,000 pairs ready ✅ | Neutral ZU sentences |
| FR | 10,996 rows ✅ | none yet | Correction pairs needed later |
| SW | 78K rows ✅ | 1,586 pairs ✅ | None |
| KI | 11,622 rows ✅ | 1,603 pairs (from GT) ✅ | None |

### Data still needed

| Priority | What | Language | Action |
|----------|------|----------|--------|
| 🔴 P0 | ~3,000 neutral ZU sentences | Zulu | **Generate via script** (see Phase 0.5) |
| 🔴 P0 | HA correction pairs reviewed ≥200 | Hausa | Gideon/Ibrahim to mark qa_status=approved |
| 🟡 P1 | ZU correction pairs reviewed ≥100 | Zulu | StudyLabs ZU team review |
| 🟡 P1 | FR correction pairs | French | Generate after FR classifier trains |

---

## Phases

---

### Phase 0.5 — Generate Neutral Zulu Sentences (unblocks Phase 2)

**Problem:** IsiZulu_Ithute has 9,570 biased rows but ZERO neutral rows.
A classifier trained with no neutral examples is useless.

**Solution:** Use AfriTeVa / mT5 or a rule-based approach to generate neutral
Zulu sentences from the biased ones by removing the gender reference entirely.
Also pull from existing Zulu corpora (MasakhaNEWS ZU, Wikipedia ZU).

**Script:** `scripts/generate_neutral_zu.py`

Steps:
1. Download MasakhaNEWS Zulu split from HuggingFace (`masakhane/masakhanews`, lang=`zul`)
2. Filter to non-gender topics (sports, politics, economics, weather)
3. Label all as `has_bias=false, bias_label=neutral`
4. Write to `data/neutral_zu_v1.csv` (target: 3,000–5,000 rows)
5. Merge with `IsiZulu_Ithute_Dataset_Final.csv` for Phase 2 training

**Acceptance:** `data/neutral_zu_v1.csv` exists with ≥ 3,000 rows, all `bias_label=neutral`

---

### Phase 0 — Test Specs (no GPU, ~2 hours)

Write all tests before touching any model. Tests are the spec — they fail now
and must pass by the end of each phase. This is non-negotiable.

**0.1 Detection contract tests** — `tests/test_detection_contract.py`

Minimum thresholds per language. Tests MUST fail now for HA/ZU/KI:

```
ha: F1 ≥ 0.70, Precision ≥ 0.60, Recall ≥ 0.75
zu: F1 ≥ 0.68, Precision ≥ 0.60, Recall ≥ 0.65
ki: F1 ≥ 0.70, Precision ≥ 0.65, Recall ≥ 0.65
sw: F1 ≥ 0.85, Precision ≥ 0.80, Recall ≥ 0.85  ← must not regress
```

**0.2 Correction contract tests** — `tests/test_correction_contract.py`

For each language with correction pairs:
- corrected output != original input
- BLEU ≥ 0.30 vs human reference (loose — AI drafts only)
- output is not empty, not garbled

**0.3 Pipeline integration tests** — `tests/test_pipeline_integration.py`

One known biased + one known neutral sentence per language:
- Biased: `detected=true`, `corrected != original`, `reason` non-empty
- Neutral: `detected=false`, `corrected == original`

**0.4 UI smoke tests** — `tests/test_ui_smoke.py`

Submit known biased sentences via the API:
- Response contains `detected: true`
- Response contains visible detection signal (badge text, matched terms)
- If `confidence < 0.75` → `flag_for_human_review: true`

**Deliverable:** All test files written. `pytest tests/ -v` runs without import errors.
HA/ZU/KI contract tests fail (expected). SW passes.

---

### Phase 1 — Hausa Classifier

**Objective:** Train `juakazike/ha-bias-classifier-v1`
**Data available:** ~15K HA rows (ground_truth_ha_v1 + StudyLabs) + v3 stereotype rows
**Blocker:** None — data is ready

**1.1 Prepare training data**

Merge and deduplicate:
- `eval/ground_truth_ha_v1.csv` (10,054 rows, has_bias boolean)
- StudyLabs file (10,178 rows, bias_label categorical)
- Normalise labels → binary: stereotype/derogation = BIASED, neutral = NEUTRAL
- Exclude counter-stereotype rows from classifier training (they are NOT bias)
- Drop annotation_error rows if any

Expected after merge + dedup: ~14,000–15,000 unique rows
Class balance: ~10% BIASED / 90% NEUTRAL

**1.2 Training spec (locked before running)**

```
Base model:     Davlan/afro-xlmr-base
Task:           binary text-classification (BIASED / NEUTRAL)
Max seq len:    128 tokens
Epochs:         3
Batch size:     32
LR:             2e-5
POS_WEIGHT:     min(n_neutral / n_biased, 15)  ← hard cap — SW v2 failure lesson
Train/val/test: 80 / 10 / 10 (stratified)
Eval metric:    macro F1 on test set
Target:         BIAS Recall ≥ 0.75, BIAS Precision ≥ 0.60
Notebook:       train_ha_bias_v1.ipynb
HF model ID:    juakazike/ha-bias-classifier-v1
```

**1.3 Notebook** — `train_ha_bias_v1.ipynb`

Adapt from `train_sw_bias_v3.ipynb`. Sections:
1. Load + audit merged HA data
2. Stratified train/val/test split
3. Tokenise (afro-xlmr-base tokenizer)
4. Fine-tune with weighted cross-entropy
5. Evaluate on test set → print classification report
6. Push to HF Hub as `juakazike/ha-bias-classifier-v1`
7. Update `eval/metrics.json`

**1.4 Wire into pipeline** — `eval/ml_classifier.py`

- Add `Language.HAUSA` to `_SUPPORTED`
- Per-language lazy-loaded model (separate `_pipe` per language)
- Add `JUAKAZI_HA_MODEL` env var (default: `juakazike/ha-bias-classifier-v1`)

**1.5 Acceptance gate**

```bash
pytest tests/test_detection_contract.py::test_ha_detection -v
```
Must pass: F1 ≥ 0.70, Recall ≥ 0.75.

---

### Phase 2 — Zulu Classifier

**Objective:** Train `juakazike/zu-bias-classifier-v1`
**Blocker:** Need ZU neutral sentences (DATA ITEM #1 above). Cannot train until resolved.

**2.1 Fix ZU ground truth balance**

Current: 1,978 biased / 22 neutral = broken.
Required: ≥500 neutral ZU sentences added to `eval/ground_truth_zu_v1.csv`.

Sources (in priority order):
1. Ask StudyLabs for neutral ZU sentences from their corpus
2. Download AfriHate ZU neutral rows (`afrihate/afrihate`, ZU split)
3. Scrape IOL Zulu news — non-gender topics (sport, weather, politics)

Target after fix: 2,000 biased / 1,000+ neutral

**2.2 Training spec**

```
Base model:     Davlan/afro-xlmr-base
POS_WEIGHT:     recalculate after balance fix
Train/val/test: 70 / 15 / 15  ← larger test set for small dataset
Target:         Recall ≥ 0.65, F1 ≥ 0.68
Notebook:       train_zu_bias_v1.ipynb
HF model ID:    juakazike/zu-bias-classifier-v1
```

**2.3 Acceptance gate**

```bash
pytest tests/test_detection_contract.py::test_zu_detection -v
```

---

### Phase 3 — Kikuyu Classifier

**Objective:** Train `juakazike/ki-bias-classifier-v1`
**Blocker:** None — 11,622 rows available, no balance issue
**Key change:** Switch base model from afro-xlmr-base → **afro-xlmr-large-76L**
This is the only model that covers Kikuyu. This alone should lift KI recall significantly.

**3.1 Training spec**

```
Base model:     Davlan/afro-xlmr-large-76L
Params:         ~560M — needs gradient checkpointing on T4
Batch size:     16 + gradient_accumulation_steps=2 (effective 32)
Epochs:         3
LR:             1e-5  ← lower LR for large model
Target:         Recall ≥ 0.65, F1 ≥ 0.70
Notebook:       train_ki_bias_v1.ipynb
HF model ID:    juakazike/ki-bias-classifier-v1
```

**3.2 Acceptance gate**

```bash
pytest tests/test_detection_contract.py::test_ki_detection -v
```

---

### Phase 4 — Correction Models (seq2seq)

**Objective:** When lexicon rules find no match, a trained seq2seq model rewrites
the biased sentence into a neutral one.

**4.1 Hausa corrector**

Blocker: Need ≥200 native-speaker-validated HA pairs (DATA ITEM #2).

```
Base model:     castorini/afriteva_v2_base (T5 encoder-decoder, covers HA)
Training data:  juakazi_ha_correction_pairs_v1.csv — approved rows only
Input format:   "correct bias: {biased_sentence}"
Output:         neutral rewrite
Epochs:         5
Eval metric:    BLEU vs held-out 100 human-validated pairs
Target:         BLEU ≥ 0.30
Notebook:       train_ha_corrector_v1.ipynb
HF model ID:    juakazike/ha-bias-corrector-v1
```

**4.2 Zulu corrector**

Two data sources available immediately (no blocker):
- `zulu_retraining - zulu_retraining.csv.csv` — 2,000 instruction-format pairs (ready now)
- `juakazi_zu_correction_pairs_v1.csv` — 1,142 AI-drafted pairs (review recommended)

```
Base model:     castorini/afriteva_v2_base
Training data:  zulu_retraining file (2,000 pairs) + validated ZU pairs
Input format:   "correct bias: {input}"
Target:         BLEU ≥ 0.28
Notebook:       train_zu_corrector_v1.ipynb
HF model ID:    juakazike/zu-bias-corrector-v1
```

**4.3 Kikuyu corrector**

Data available immediately — KI GT has 11,622 rows all with `expected_correction`.

```
Base model:     google/mt5-small (mT5 — afriteva does not cover Kikuyu)
Training data:  eval/ground_truth_ki_v8.csv (expected_correction column)
               Filter to has_bias=True rows only (1,603 rows)
Target:         BLEU ≥ 0.25
Notebook:       train_ki_corrector_v1.ipynb
HF model ID:    juakazike/ki-bias-corrector-v1
```

**4.4 Wire correctors into pipeline**

`eval/mt5_corrector.py` already exists — extend it:
- Add HAUSA, ZULU, KIKUYU language support
- Load correct model per language
- Expose `correct(text: str, language: Language) -> str`

`api/service.py` Stage 3:
- After lexicon finds no match AND `biased=true` from Stage 1
- Call `correct(text, lang)`
- If corrected == original → set `flag_for_human_review=True`

**4.5 Acceptance gate**

```bash
pytest tests/test_correction_contract.py -v
```

---

### Phase 5 — UI: Detection Signal

**Problem:** Demo feedback — correction shown but no visible detection signal.
Also: correction failures are silent.

**5.1 Detection badge**

`gradio_app.py` changes:
- Show detection result BEFORE correction
- 🔴 Red badge: "Gender bias detected" + confidence score + matched terms
- 🟢 Green badge: "No bias detected"
- 🟡 Yellow badge: "Possible bias — low confidence" (confidence < 0.75)
- ⚠️ "Human review recommended" flag when `flag_for_human_review=True`
- "Bias detected but no automatic correction available" when corrected == original

**5.2 Acceptance gate**

```bash
pytest tests/test_ui_smoke.py -v
```

Manual: submit a known biased sentence → red badge appears, then correction shown.

---

### Phase 6 — Non-regression Check

After all phases complete:

```bash
python3 run_evaluation.py
```

SW must still show F1 ≥ 0.85. If regression → rollback Phase 4/5 changes.

---

## Data Shopping List (bring this in)

### Blocking (cannot train without these)

| Priority | What | Volume | Format needed | Action |
|----------|------|--------|---------------|--------|
| 🔴 P0 | ZU neutral sentences | ≥3,000 rows | `text, has_bias=false, language=zu` | Ask StudyLabs to provide |
| 🔴 P0 | HA correction pairs reviewed | ≥200 rows | `qa_status=approved` in `juakazi_ha_correction_pairs_v1.csv` | Gideon/Ibrahim to review |

### Recommended (improves model quality)

| Priority | What | Volume | Format needed | Action |
|----------|------|--------|---------------|--------|
| 🟡 P1 | ZU correction pairs reviewed | ≥100 rows | `qa_status=approved` in `juakazi_zu_correction_pairs_v1.csv` | StudyLabs ZU team to review |
| 🟡 P1 | AfriHate ZU gender rows | ~500 rows | Download from HF `afrihate/afrihate` | Engineering task — script exists |
| 🟡 P1 | AfriSenti HA tweets | ~2K rows | Download from HF `HausaNLP/AfriSenti-Twitter` | Engineering task |

### Optional (AIBRIDGE compliance)

| Priority | What | Volume | Action |
|----------|------|--------|--------|
| 🟢 P2 | KI correction pairs human review | ≥200 rows | Kikuyu native speaker |
| 🟢 P2 | EN/FR expanded GT | 500+ rows each | Annotation session |

---

---

## Phase 7 — Production Deployment (GCP Cloud Run + Next.js)

**Reference:** Clar project at `/Users/stellaoiro/Projects/clar` — already live at
`https://clar-608805582585.us-central1.run.app` on the same GCP project (`stella-cyber-analyzer`).
Use Clar's infra as the exact template. Do not reinvent anything.

### Architecture (identical to Clar)

```
Browser
   │
   ▼
Next.js static export (served by FastAPI — one container, no separate frontend server)
   │  REST calls
   ▼
FastAPI (GCP Cloud Run v2)   ← same GCP project as Clar
   │
   ├── Stage 1: ML Classifier   (afro-xlmr-base, loaded at startup)
   ├── Stage 2: Lexicon Rules   (CSV files, in-memory)
   └── Stage 3: ML Corrector    (afriteva_v2_base, loaded at startup)
```

### Why one container (FastAPI serves static Next.js export)

Clar does this — 3-stage Dockerfile:
1. Node 20 Alpine → builds Next.js `out/` static export
2. Python 3.11 slim → installs Python deps
3. Runtime → copies both, FastAPI mounts `./static`, serves `index.html` at root

Result: single Cloud Run service, single domain, no CORS, no separate Vercel deploy needed.

### Cloud Run config (copy from Clar)

```
CPU:           1 vCPU  (upgrade to 2 if model inference is slow)
Memory:        2Gi     (upgrade to 4Gi — models need ~1.5GB RAM)
Min instances: 0       (scale to zero — saves cost when idle)
Max instances: 3       (caps runaway cost)
Region:        us-central1  (same as Clar)
GCP project:   stella-cyber-analyzer  (already set up, Artifact Registry exists)
```

### Cost estimate (real, based on Clar actuals)

| Component | Config | Cost |
|---|---|---|
| Cloud Run | 1 vCPU / 4Gi, min=0, max=3 | ~$0–8/month (scales to zero) |
| Artifact Registry | ~2GB image | ~$0.20/month |
| Secret Manager | 3 secrets | ~$0.18/month |
| **Total** | | **< $10/month** |

Min=0 means $0 when nobody is using it. The Gates Foundation demo runs,
then it scales back to zero. No wasted spend.

### CI/CD (copy Clar's .github/workflows/)

```
ci.yml  — on every PR:
  pytest (acceptance gates must pass)
  docker build --platform linux/amd64

cd.yml  — on merge to main:
  Build Next.js static export
  Build Docker image (3-stage, linux/amd64)
  Push to Artifact Registry (us-central1-docker.pkg.dev/stella-cyber-analyzer/juakazi/juakazi)
  Deploy to Cloud Run v2
  Smoke test /health
```

Auth: Workload Identity Federation (no long-lived keys — Clar already has this configured).

### Dockerfile (3-stage, adapt from `infra/docker/Dockerfile` in Clar)

```dockerfile
# Stage 1: Build Next.js static export
FROM node:20-alpine AS node-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Python deps + download HF models at build time
FROM python:3.11-slim AS python-builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt
# Pre-download models so cold start is fast
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    AutoTokenizer.from_pretrained('juakazike/sw-bias-classifier-v3'); \
    AutoModelForSequenceClassification.from_pretrained('juakazike/sw-bias-classifier-v3')"

# Stage 3: Runtime
FROM python:3.11-slim
COPY --from=python-builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY . .
COPY --from=node-builder /frontend/out ./static
RUN useradd -m juakazi && chown -R juakazi /app
USER juakazi
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend — Next.js

**Design system** (from `public/index.html` — already designed, port exactly):
```
--green: #00a651        primary brand
--sidebar: #111827      dark sidebar
--bg: #f8fafc           page background
--surface: #ffffff      cards
--text: #0f172a         body text
font: system font stack (same as Clar)
```

**Structure:** `frontend/` folder (same as Clar)

**Pages:**
- `/` — Analyse: language sidebar + textarea + detect+correct results
- `/languages` — Metrics dashboard: F1/P/R per language, model version
- `/about` — Project overview + AIBRIDGE compliance status

**Key UX (what Gates Foundation demo needs to show):**
1. Select language from sidebar
2. Type or paste a sentence
3. Click "Analyse"
4. 🔴 Detection result card appears first — BIASED/CLEAN + confidence + reason
5. Correction card appears — original sentence with biased phrase ~~struck~~ in red, corrected in green
6. If confidence < 0.75 → 🟡 "Low confidence — flag for human review" button

### Terraform (copy from Clar `infra/terraform/`)

Resources needed (all exist in `stella-cyber-analyzer` already):
- `google_cloud_run_v2_service` — juakazi service
- `google_artifact_registry_repository` — juakazi repo (or reuse clar's)
- `google_secret_manager_secret` — no secrets needed (no API keys in pipeline)

### Phase 7 tasks (start after Phase 5)

- [x] 7.1 Copy Clar's `infra/` structure → `infra/docker/Dockerfile` + `infra/terraform/`
- [x] 7.2 Scaffold `frontend/` (Next.js 14, Pages Router, TypeScript, Tailwind — same as Clar)
- [x] 7.3 Port `public/index.html` design system to Next.js components
- [x] 7.4 Detection badge component (red/green/amber) → `frontend/components/VerdictBadge.tsx`
- [x] 7.5 Diff highlight component (original vs corrected) → `frontend/components/DiffView.tsx`
- [x] 7.6 Language metrics dashboard page → `frontend/pages/languages.tsx`
- [x] 7.7 Copy Clar's `.github/workflows/ci.yml` + `cd.yml` → adapt for JuaKazi
- [ ] 7.8 `gcloud run deploy` smoke test — run after models trained + pushed to HF
- [x] 7.9 Update FastAPI to serve `./static` (Next.js export) at root + `/metrics` endpoint

---

## What We Are NOT Doing

- No LLMs (Claude, GPT, Llama) in the detection/correction pipeline
- No paid inference APIs
- No rewriting the lexicon rules engine — it stays as the precision layer (Stage 2)
- No changes to SW pipeline (it works — don't touch it)
- No new languages until HA/ZU/KI pass their acceptance gates

---

## Execution Order

```
NOW (no GPU, no data blocker)
  Phase 0 — Write all test specs (~2h)
  Phase 4.2 partial — ZU corrector notebook (zulu_retraining file is ready)
  Phase 4.3 — KI corrector notebook (KI GT already has corrections)

NEEDS DATA (ZU neutral rows from StudyLabs)
  Phase 2 — ZU classifier

NEEDS NATIVE SPEAKER REVIEW (HA pairs from Gideon/Ibrahim)
  Phase 4.1 — HA corrector

UNBLOCKED (data ready)
  Phase 1 — HA classifier (train_ha_bias_v1.ipynb)
  Phase 3 — KI classifier (train_ki_bias_v1.ipynb)

AFTER MODELS TRAINED
  Phase 4.4 — Wire correctors into pipeline
  Phase 5 — UI detection signal fix
  Phase 6 — Non-regression check
```

**Estimated GPU time:** ~12h T4 total (free Colab tier)
**Hard human blockers:** ZU neutral rows, HA/ZU pair validation
**Calendar estimate:** 1–2 weeks if blockers resolved this week

---

## Hard Rules

1. Write the test first. No model ships without a passing acceptance test.
2. Run `python3 run_evaluation.py` before AND after every pipeline change.
3. Train correction models on validated pairs only (`qa_status=approved`).
   Exception: ZU `zulu_retraining` file and KI GT — already validated.
4. One phase at a time. Phase N+1 starts only after Phase N acceptance gate passes.
5. Ground truth CSVs are read-only. Never overwrite — create a new version file.
6. Every training run updates `eval/metrics.json`.
7. Never push models or data files without explicit instruction.
