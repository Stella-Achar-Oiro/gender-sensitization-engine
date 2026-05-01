# JuaKazi × StudyLabs — Engine 2 Project Report

**Programme**: AI BRIDGE  
**Engine**: Engine 2 (Bias Detection: StudyLabs | Bias Correction: JuaKazi)  
**Submission date**: May 2026  
**Version**: 1.0

---

## 1. Executive Summary

JuaKazi is the bias correction module of Engine 2. It receives sentences that StudyLabs has flagged as gender-biased, applies deterministic lexicon rules to identify and replace biased terms, and returns a neutral rewrite with an explanation. The system covers six languages — Swahili, English, French, Gikuyu, Hausa, and Zulu — making it the broadest-coverage African-language gender correction system in the programme.

The system achieves zero false positives (Precision = 1.000) on English, French, Hausa, and Zulu. Swahili precision is 0.822 at 67,290 samples; the known FP cluster (contextually ambiguous phrases) is documented and managed. A semantic preservation check prevents rewrites that would alter sentence meaning.

---

## 2. System Architecture

### 2.1 Overview

Engine 2 is a two-stage pipeline:

```
[StudyLabs] -- POST /rewrite --> [JuaKazi API]
    |                                   |
    | (caller="studylabs")              v
    | bias confirmed upstream    Stage 0: skip re-detection gate
    |                                   |
    |                                   v
    |                            Stage 1: Lexicon rules
    |                            (lexicon_{lang}_v1/v3.csv)
    |                            + Context gating (avoid_when)
    |                            + Semantic preservation check
    |                                   |
    |                                   v
    |                            Stage 2: ML fallback (SW only)
    |                            juakazike/sw-bias-classifier-v3
    |                                   |
    |                                   v
    |                            { rewrite, edits, confidence,
    |                              source, reason, semantic_score }
```

### 2.2 Detection (StudyLabs)

StudyLabs runs the upstream bias detection model. When a sentence is flagged, their system POSTs to JuaKazi's `/rewrite` endpoint with `"caller": "studylabs"`. This tells JuaKazi to skip its own redundant re-detection and go directly to correction. If the caller field is absent, the pipeline still functions correctly — it just runs an internal detection check as well.

### 2.3 Correction (JuaKazi)

**Stage 1 — Lexicon rules (primary)**

Each language has a CSV lexicon mapping biased terms to gender-neutral replacements. Rules carry:
- `biased`: the term to match (word-boundary regex)
- `neutral_primary`: the replacement
- `severity`: `replace` (auto-correct) or `warn` (advisory only)
- `avoid_when`: pipe-separated context conditions that suppress the rule (e.g. `biographical|quote|statistical`)
- `bias_label`, `stereotype_category`, `tags`: metadata for the reason field

After substitution, a semantic preservation check computes a composite similarity score between the original and rewritten sentence. If the score falls below 0.70, the rewrite is discarded and the original is returned unchanged (`source=preserved`). This prevents meaning-altering corrections.

**Stage 2 — ML fallback (Swahili only)**

When no lexicon rule matches, `juakazike/sw-bias-classifier-v3` (afro-xlmr-base, fine-tuned on 67,290 SW rows) runs. It produces a warn-severity flag requiring human review. It never auto-corrects.

### 2.4 API contract

```
POST /rewrite
{
  "id": "sentence-001",
  "lang": "sw",              // en | sw | fr | ki | ha | zu
  "text": "...",
  "caller": "studylabs",     // optional — skips Stage 0 re-detection
  "flags": [...],            // optional — pre-identified spans
  "region_dialect": "kenya"  // optional — for dialect-aware rules
}
```

Response:
```json
{
  "id": "sentence-001",
  "original_text": "...",
  "rewrite": "...",
  "edits": [
    {
      "from": "biased term",
      "to": "neutral term",
      "severity": "replace",
      "tags": "occupation/role",
      "bias_type": "stereotype",
      "reason": "'biased term' is gender-biased (occupation/role); use gender-neutral 'neutral term'"
    }
  ],
  "confidence": 0.92,
  "needs_review": false,
  "source": "rules",
  "reason": "1 biased term(s) corrected: 'biased term'.",
  "semantic_score": 0.87,
  "has_bias_detected": true,
  "aibridge_detected": null,
  "aibridge_confidence": null
}
```

Batch endpoint: `POST /rewrite/batch` — accepts up to 100 sentences, returns a list of responses.

---

## 3. Languages and Lexicons

| Language | Lexicon file | Rules | Design approach |
|---|---|---|---|
| English | lexicon_en_v3.csv | 77 | Occupational titles, pronoun assumptions, role stereotypes |
| Swahili | lexicon_sw_v3.csv | 437 | Noun-class aware; 69 Sheng/informal terms added May 2026 |
| French | lexicon_fr_v3.csv | 117 | Gendered professional titles; French morphology |
| Gikuyu | lexicon_ki_v3.csv | 1,288 | Morphological patterns; religious/traditional role terms |
| Hausa | lexicon_ha_v1.csv | 36 | Precision-first initial lexicon; occupation + role terms |
| Zulu | lexicon_zu_v1.csv | 53 | Morphological gender suffix removal (wesifazane, wesilisa) |

**Context gating** — 11 suppression conditions prevent rules from firing in safe contexts:

| Condition | Suppresses rules when... |
|---|---|
| `biographical` | Named individuals (spouse, daughter references) |
| `quote` | Direct speech / attributed quotes |
| `statistical` | Statistical reporting contexts |
| `counter_stereotype` | Sentence already challenges the stereotype |
| `historical` | Historical/archival framing |
| `medical` | Clinical/medical contexts requiring gendered terms |
| `legal` | Legal instruments referencing statutory terms |
| `artistic` | Fiction, poetry, performance |
| `organization` | Formal organisation names |
| `proper_noun` | Named places, brands |
| `zu_neutral_profession` | Zulu celebratory/achievement sentences (e.g. "Kuyamangaza...") |

---

## 4. Performance Evaluation

### 4.1 Current metrics (May 2026)

Evaluation methodology: binary classification of has_bias against ground truth CSVs. Precision = true positives / flagged; Recall = true positives / all biased in ground truth; F1 = harmonic mean.

| Language | F1 | Precision | Recall | GT samples | Bias rows |
|---|---|---|---|---|---|
| English | 1.000 | 1.000 | 1.000 | 66 | ~30 |
| Swahili | 0.851 | 0.822 | 0.881 | 67,290 | ~1,600 |
| French | 0.970 | 1.000 | 0.941 | 165 | ~30 |
| Gikuyu | 0.667 | 0.967 | 0.510 | 11,622 | ~1,200 |
| Hausa | 0.043 | 1.000 | 0.022 | 10,054 | 1,012 |
| Zulu | 0.732 | 1.000 | 0.577 | 2,000 | 1,978 |

### 4.2 Iteration history (three cycles)

**Cycle 1 — Baseline (Feb 2026)**

| Language | F1 | Notes |
|---|---|---|
| English | 0.786 | Initial lexicon, occupational titles only |
| Swahili | 0.611 | Rules only, no ML fallback, no Sheng |
| French | 0.542 | Small lexicon (54 rules) |
| Gikuyu | 0.352 | Early morphological patterns |

**Cycle 2 — ML integration + GT expansion (Mar–Apr 2026)**

Changes: Added ML fallback (sw-bias-classifier-v3, F1=0.871 on external 9K set). Expanded SW ground truth to 67,290 rows. Added 28 recall-boosting derogation patterns. Added counter-stereotype and implicit bias rows (15.63% and 5.01% thresholds met). Expanded FR lexicon to 117 rules. Expanded KI to 1,288 rules.

| Language | F1 | Change |
|---|---|---|
| English | 1.000 | +0.214 |
| Swahili | 0.840 | +0.229 |
| French | 0.970 | +0.428 |
| Gikuyu | 0.667 | +0.315 |

**Cycle 3 — Hausa, Zulu, Sheng expansion (May 2026)**

Changes: Added Hausa support (36-rule precision-first lexicon, GT=10,054 rows from StudyLabs dataset). Added Zulu support (53-rule morphological lexicon with `zu_neutral_profession` context gating for zero FPs, GT=2,000 rows). Added 69 Sheng/informal Swahili terms covering objectification, harassment, body-shaming, and cyberbullying patterns. Merged 203 human-reviewed expected corrections into SW ground truth. Added `caller` field to skip redundant AIBRIDGE re-detection when StudyLabs sends pre-confirmed bias.

| Language | F1 | Precision | Recall |
|---|---|---|---|
| Hausa | 0.043 | 1.000 | 0.022 |
| Zulu | 0.732 | 1.000 | 0.577 |
| Swahili | 0.851 | 0.822 | 0.881 |

Hausa recall (0.022) is expected at this stage — the initial lexicon targets only high-confidence occupational and derogatory terms. The dominant Hausa bias categories in the StudyLabs GT (leadership, religion_culture, daily_life) require contextual/implicit understanding that word-level rules cannot reliably catch. Recall improvement requires an ML classifier fine-tuned on the 10,054-row Hausa GT.

### 4.3 StudyLabs evaluation cross-reference

StudyLabs ran an independent evaluation on their own test sets (Apr 2026):

| Language | StudyLabs-reported F1 | JuaKazi eval F1 |
|---|---|---|
| Swahili | 0.710 | 0.851 |
| Hausa | 0.814 | 0.043 |

The SW difference (0.710 vs 0.851) reflects different test set composition — StudyLabs used a held-out set from their own corpus; JuaKazi evaluates on a broader 67,290-row GT. The HA difference (0.814 detection vs 0.043 correction) is expected: StudyLabs measures detection accuracy; JuaKazi measures correction recall — different tasks.

---

## 5. Integration Documentation

### 5.1 StudyLabs → JuaKazi call spec

```python
import requests

response = requests.post(
    "https://juakazike.hf.space/rewrite",
    json={
        "id": "your-sentence-id",
        "lang": "sw",          # or "ha", "zu", "en", "fr", "ki"
        "text": "sentence text here",
        "caller": "studylabs"  # tells JuaKazi bias is already confirmed
    }
)
result = response.json()
# result["rewrite"]    — corrected sentence
# result["edits"]      — list of {from, to, severity, reason}
# result["confidence"] — float 0–1
# result["source"]     — "rules" | "ml" | "preserved" | "disambiguated"
# result["reason"]     — human-readable explanation
```

### 5.2 Supported language codes

| Code | Language | Notes |
|---|---|---|
| `sw` | Swahili | Full support; ML fallback active |
| `en` | English | Full support |
| `fr` | French | Full support |
| `ki` | Gikuyu/Kikuyu | Partial — recall 0.510 |
| `ha` | Hausa | Precision-first; recall improvement planned |
| `zu` | Zulu | Morphological rules; precision 1.000 |

### 5.3 Error responses

| HTTP code | Meaning | Action |
|---|---|---|
| 200 | Success | Parse response normally |
| 422 | Invalid request (bad lang code, missing field) | Check request schema |
| 500 | Internal error | Retry once; contact JuaKazi team |

### 5.4 Batch usage

```python
response = requests.post(
    "https://juakazike.hf.space/rewrite/batch",
    json={
        "items": [
            {"id": "1", "lang": "sw", "text": "...", "caller": "studylabs"},
            {"id": "2", "lang": "ha", "text": "...", "caller": "studylabs"},
        ]
    }
)
results = response.json()  # list, same order as items
```

---

## 6. Pipeline Retraining Outputs (Iteration Logs)

### 6.1 ML model registry

| Model | Base | Val F1 | Val P | Val R | Status |
|---|---|---|---|---|---|
| sw-bias-classifier-v1 | afro-xlmr-base | 0.854 | 0.938 | 0.784 | Retired |
| sw-bias-classifier-v2 | afro-xlmr-base | 0.953 | 0.940 | 0.960 | Invalid (overfit) |
| sw-bias-classifier-v3 | afro-xlmr-base | 0.871 | 0.810 | 0.942 | **Deployed** |

v2 was invalidated: high val F1 (0.953) was caused by train/val leakage in the augmentation step (synthetic duplicates crossed the split boundary). v3 fixed the leakage with pre-split augmentation and achieved 0.871 on Richard's external 9,709-sample evaluation set.

v4 retraining was attempted (LoRA + afro-xlmr-mini) but failed the quality gate (internal F1=0.689 vs gate ≥0.837). Root causes: POS_WEIGHT cap set too low (5.0 vs required 7.0+ for the class imbalance ratio), MAX_LEN=128 truncating 22% of data, LR=5e-4 too high for LoRA. Config fixes identified; retraining queued for next sprint.

### 6.2 Lexicon iteration log

| Date | Language | Change | Before F1 | After F1 |
|---|---|---|---|---|
| Feb 2026 | SW | Initial 267 rules | — | 0.611 |
| Mar 2026 | SW | +28 derogation patterns (recall boost) | 0.611 | 0.816 |
| Mar 2026 | SW | ann_sw_v3 GT expansion (13,304 rows) | 0.816 | 0.819 |
| Apr 2026 | FR | Expanded 54→117 rules | 0.542 | 0.970 |
| Apr 2026 | KI | Expanded to 1,288 rules | 0.352 | 0.667 |
| Apr 2026 | SW | ML v3 integrated as Stage 2 fallback | 0.840 | 0.851 |
| May 2026 | SW | +69 Sheng/informal terms | 0.840 | 0.851 |
| May 2026 | HA | v1 lexicon (36 rules, precision-first) | — | 0.043 |
| May 2026 | ZU | v1 lexicon (53 morphological rules) | — | 0.732 |

### 6.3 Expert feedback integration

Expert feedback from AIBRIDGE review sessions drove the following changes:

- **Dataset schema compliance**: `target_gender=none` changed to `neutral` (49,868 rows), `stereotype_category` and `explicitness` filled on all `has_bias=true` rows, PII scrubbed (110 rows).
- **Counter-stereotype coverage**: Added rows from C4, Wikipedia, and MasakhaNews to reach 15.63% (requirement: ≥15%).
- **Implicit bias coverage**: Added 5.01% implicit rows (requirement: ≥5%).
- **Sheng coverage**: Added 69 Sheng lexicon terms following expert feedback on urban Swahili gap.
- **Region tagging**: All 67,290 SW rows tagged `kenya` or `tanzania`; bias_category/stereotype_category reconciled.

---

## 7. Known Limitations

| Language | Limitation | Severity | Mitigation |
|---|---|---|---|
| Hausa | Recall = 0.022 — lexicon catches only surface-form occupational terms; contextual/implicit bias missed | High | ML classifier fine-tune on 10K HA GT (next sprint) |
| Gikuyu | Recall = 0.510 — religious and traditional-leadership terms not yet in lexicon | Medium | Lexicon expansion with native KI speaker review |
| Swahili | P = 0.822 — `Watoto wa Kike` / `mtoto wa kike` FP cluster (~320 sentences) contextually ambiguous | Documented | Context gating partially applied; flagged for human review |
| Zulu | Recall = 0.577 — only morphological patterns covered; compound constructions missed | Medium | Extend lexicon; GT is only 2,000 rows |
| All | Binary gender framework — non-binary, intersectional bias not captured | Structural | Future annotation sprint |
| All | No real-time speech support | Out of scope | — |

---

## 8. Deployment Instructions

### 8.1 HuggingFace Space (live)

```
https://huggingface.co/spaces/juakazike/gender-sensitization-engine
```

Docker-based deployment. The Space auto-restarts on push to `hf-deploy` branch. Lexicons and rules are bundled in the image; GT files are not (too large for Space storage).

### 8.2 Local deployment

```bash
git clone <repo>
pip install -r requirements.txt

# Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# CLI demo
python3 demo_live.py

# Evaluation (all 6 languages)
python3 run_evaluation.py

# Smoke tests (must pass 5/5 before any merge)
python3 tests/test_system.py
```

### 8.3 Environment variables

| Variable | Default | Description |
|---|---|---|
| `JUAKAZI_ML_MODEL` | juakazike/sw-bias-classifier-v3 | SW Stage 2 ML model |
| `JUAKAZI_ML_THRESHOLD` | 0.56 | ML confidence threshold |
| `JUAKAZI_SEMANTIC_THRESHOLD` | 0.70 | Minimum semantic score to accept a rewrite |
| `AIBRIDGE_ENABLED` | false | Enable Stage 0 external detection gate |
| `AIBRIDGE_API_KEY` | — | Key for AIBRIDGE external API |

### 8.4 Makefile shortcuts

```bash
make run-api    # uvicorn on port 8000
make eval       # run_evaluation.py
make test       # tests/test_system.py
make run        # demo_live.py
```

---

## 9. Inter-Annotator Agreement

Cohen's κ = 0.8537 (Almost Perfect) computed on a 500-row overlap set (ann_sw_kappa_v2) between two annotators. Exceeds the AIBRIDGE Bronze threshold (κ ≥ 0.61).

English, French, and Kikuyu IAA not yet computed — single annotator, small sets. This is documented as an open limitation.

---

## 10. Next Steps

| Priority | Item | Owner | Blocker |
|---|---|---|---|
| High | HA ML classifier (fine-tune on 10K rows) — recall 0.022 → target ≥0.60 | JuaKazi engineer | None — data available |
| High | StudyLabs full integration test — end-to-end call with real sentences | Joint | StudyLabs to add `caller="studylabs"` |
| Medium | ZU lexicon expansion (compound constructions, idiomatic patterns) | JuaKazi engineer | Need ZU native speaker review |
| Medium | KI religious/leadership lexicon expansion | JuaKazi engineer | KI native speaker review |
| Medium | SW `Watoto wa Kike` FP cluster — narrow match patterns | JuaKazi engineer | None |
| Low | sw-bias-classifier-v4 retraining (LoRA config fixed) | JuaKazi engineer | None — config fix ready |
| Low | Non-news domains (health, livelihoods, household) for SW GT | Data team | Collection effort |

---

*JuaKazi Team — AI BRIDGE Engine 2 — May 2026*
