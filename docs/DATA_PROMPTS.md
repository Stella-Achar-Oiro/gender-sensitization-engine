# Data work — exact prompts and commands

Use these when you have annotators ready or when doing data tasks yourself. Sprint 2 must complete before Sprint 3 (AIBRIDGE submission).

---

## 1. [Project Lead] Recruit 2nd Swahili annotator

**Blocking:** Cohen's Kappa cannot be measured without a 2nd annotator. κ ≥ 0.70 is required for AIBRIDGE Bronze.

**Prompt to run in Cursor:**

```
Use the recruit-annotator skill. Generate the Masakhane Slack post and the annotator onboarding package. Default: volunteer, 500 rows. If we have budget, say: use recruit-annotator with --budget "X USD" and --rows 500.
```

**What you do by hand:**

1. Post the generated message in **#swahili** and **#general** on masakhane.slack.com (join via masakhane.io if needed).
2. When someone replies: send them the briefing doc and the CSV from Step 2 below.

---

## 2. [Data / Engineer] Export rows for annotation (before annotators start)

**Run once** to create the overlap set, then export the same rows for Annotator B.

```bash
# From repo root. Creates data/analysis/kappa_overlap_ids.txt on first run.
python3 scripts/export_for_annotation.py --batch 500 --offset 0 > data/annotation_export/batch_for_annotator_A.csv
```

Then export the **same overlap set** for the 2nd annotator (so both annotate the same rows for κ):

```bash
python3 scripts/export_for_annotation.py --kappa-set > data/annotation_export/batch_for_annotator_B_kappa_overlap.csv
```

**Optional:** Export a second batch of unique rows for Annotator B so they also do 500 total (250 overlap + 250 unique). Adjust offset in a second export if needed.

**Deliver to annotators:** Share `batch_for_annotator_A.csv` (or existing ann_sw_v2 batches) to Annotator 1 for reference; give `batch_for_annotator_B_kappa_overlap.csv` to Annotator 2. Use Google Drive or Zenodo — do not commit ground truth CSV to git (size + PII).

---

## 3. [Annotators] What to fill in

**Columns to complete (2nd annotator):**

- **has_bias** — `true` or `false`
- **target_gender** — `female` | `male` | `neutral` | `mixed` (if biased)
- **stereotype_category** — e.g. `profession`, `family_role`, `capability` (if biased)
- **explicitness** — `explicit` | `implicit` (if biased)
- **expected_correction** — corrected sentence (if biased); leave empty if no bias

**Rules:** Follow the annotation guidelines in `docs/eval/schemas/ANNOTATION_GUIDELINES.md`. For overlapping rows, annotate independently (do not look at Annotator 1’s labels until after submission).

---

## 4a. [Engineer] Label Studio one-shot (optional path for κ)

**If you use Label Studio** instead of CSV handoff:

**1. Run setup (once):**
```bash
bash scripts/setup_label_studio.sh
```
- Fixes: script uses Python 3.11 if available (3.14 breaks Label Studio). CRLF in script was fixed; token is read from DB.
- When it finishes, it prints **Project ID** (a UUID) and **Export when done** command.

**2. If you don't see any project:** The API project create may have failed. Run:
```bash
LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite .ls_venv/bin/python scripts/create_label_studio_project.py
```
Then refresh http://localhost:8080 — you should see **JuaKazi — Swahili Kappa Overlap** with tasks.

**3. If ann1/ann2 logins fail:** The API creates users but does not set passwords. Run:
```bash
LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite .ls_venv/bin/python scripts/set_label_studio_passwords.py
```
This creates or updates ann1 and ann2 with the correct passwords.

**4. Annotate:** Open http://localhost:8080. Log in as **ann1@juakazi.ai** / **annotator1pass**, label all tasks. Then log in as **ann2@juakazi.ai** / **annotator2pass** and label the same tasks. (Or share the link + ann2 login with a Swahili speaker.)

**4a. If the labeling screen is blank** after clicking Label: the full label config (conditional visibility / inline styles) can crash the UI. Switch the project to a minimal config:
```bash
LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite .ls_venv/bin/python scripts/fix_label_studio_blank_screen.py
```
Then refresh the page and click Label again. New projects created with `create_label_studio_project.py` use the minimal config by default.

**4b. Optional — AI annotations (two models for κ):** You can fill both annotator slots with two different models, then export for Cohen's κ.

**One-time: token files (no pasting each time)**  
Create two files (one line each, the API token from Label Studio → Account & settings):
- `.label_studio_data/admin_token.txt` — admin's token  
- `.label_studio_data/ann2_token.txt` — ann2's token (log in as ann2@juakazi.ai to copy)

Then run the full flow:
```bash
bash scripts/run_label_studio_ai_flow.sh
```
This runs: (1) rules annotator, (2) ML annotator, (3) export and κ. If `ann2_token.txt` is missing, step 2 is skipped.

Or run steps manually; tokens are read from those files if `--token` is not set:
```bash
python3 scripts/run_ai_annotations_label_studio.py --url http://localhost:8080 --project-id 1
python3 scripts/run_ai_annotations_label_studio.py --model ml --url http://localhost:8080 --project-id 1
python3 scripts/export_label_studio_annotations.py --url http://localhost:8080 --project-id 1 --output eval/results/kappa_label_studio.json
```
(Requires ML model for step 2: set `JUAKAZI_ML_MODEL` if using the fine-tuned classifier.)

**5. Export and get κ:** Get your admin token: Account & Settings in Label Studio UI, or from DB:
```bash
sqlite3 .label_studio_data/label_studio.sqlite3 "SELECT key FROM authtoken_token LIMIT 1;"
```
Then:
```bash
python3 scripts/export_label_studio_annotations.py \
  --url http://localhost:8080 \
  --token <paste-admin-token> \
  --project-id <UUID-from-setup-output> \
  --output eval/results/kappa_label_studio.json
```
Script prints Cohen's Kappa and saves CSVs per annotator. If κ ≥ 0.70, Sprint 2 closes.

---

## 4. [Engineer] After both annotators return CSVs — compute Cohen's Kappa

**When:** You have two files with the **same row IDs** (the kappa overlap set), each with a `has_bias` (or equivalent) column per annotator.

**Option A — if using `scripts/calculate_agreement.py`:**  
It expects JSON batch files from the `annotation` package. If your pipeline exports that format:

```bash
python3 scripts/calculate_agreement.py \
  --batch1 data/annotations/batch_annotator1.json \
  --batch2 data/annotations/batch_annotator2.json \
  --output reports/agreement.json
```

**Option B — ad‑hoc κ from two CSVs:**  
If you only have two CSVs with overlapping `id` and `has_bias` columns, compute agreement on the overlap rows (e.g. in a small script or notebook: load both CSVs, merge on `id`, compare `has_bias` for both, compute κ with `sklearn.metrics.cohen_kappa_score`). Target: **κ ≥ 0.70**.

**Record:** Put the κ value in the Dataset Card and in CLAUDE.md §7 (AIBRIDGE compliance). Sprint 2 closes when κ is measured and documented.

---

## 5. [Engineer] Run correction evaluator (no annotators needed)

**Do this anytime** to get correction-quality metrics. First-time run:

```bash
python3 eval/correction_evaluator.py
```

Paste the output into CLAUDE.md or a short report. Re-run after lexicon or rule changes.

---

## 6. [Data / Claude] Add 5 Swahili proverbs to lexicon

**Prompt:**

```
Use the sw-lexicon skill to add 5 Swahili proverbs to the lexicon. Zero false positives. Candidates from Model Card / CURSOR_PROMPT: mwanamke ni chombo, mke ni nguo mume ni nguo, mama ni nguzo ya nyumba, mwanamke ni shamba la baba, mke mzuri ni utii — or other culturally appropriate proverbs that imply gender bias. Add only after validating against corpus; no speculative entries.
```

**Constraint:** `avoid_when` must be pipe-separated enum values only (e.g. `quote|historical`). Run `python3 run_evaluation.py` after changes; no F1 regression.

---

## 7. [Data / Claude] Add 10 Sheng terms to lexicon

**Prompt:**

```
Use the sw-lexicon skill to add 10 Sheng terms for gender/gender roles to lexicon_sw_v3.csv. Zero false positives. Candidates (from CURSOR_PROMPT): dem, mresh, mami, babe, dame, gal, manzi, bibi mdogo, msupa wa ofisi, mrembo job — or other Sheng terms validated from corpus. Maintain precision; document source.
```

**Constraint:** Same as above; run eval after changes.

---

## 8. [Project Lead] Update Model Card after correction eval

**When:** After Engineer has run `correction_evaluator.py` and shared results.

**Prompt:**

```
Update docs/eval/model_card.md with the correction_evaluator results (precision, recall, semantic preservation if reported). Add a short "Correction quality" subsection with the latest run date and key metrics.
```

---

## Order summary

| Step | Who        | Blocked by     | Command / action |
|------|------------|----------------|-------------------|
| 1    | Project Lead | —            | Post in Masakhane; use recruit-annotator skill for text |
| 2    | Data/Engineer | —          | `export_for_annotation.py --batch 500` then `--kappa-set` |
| 3    | Annotators | Step 1+2      | Fill has_bias, target_gender, expected_correction, etc. |
| 4    | Engineer   | Step 3        | Compute κ from two annotation files; document κ ≥ 0.70 |
| 5    | Engineer   | —             | `python3 eval/correction_evaluator.py` (anytime) |
| 6–7  | Data/Claude | —            | `/sw-lexicon` for 5 proverbs + 10 Sheng |
| 8    | Project Lead | Step 5       | Update Model Card with correction metrics |

Sprint 2 is **done** when κ is measured and (if applicable) correction_evaluator and Model Card are updated. Then you can start Sprint 3 (dataset balance, 100 minimal pairs, domain rows, etc.).
