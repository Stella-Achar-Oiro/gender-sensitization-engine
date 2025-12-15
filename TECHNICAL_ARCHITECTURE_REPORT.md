# Technical Architecture Report

## Scope and methodology
- Full repository review (code, data, rules, docs, Docker, tests) with multi-pass lenses: architecture, AI/ML, data, security/privacy, performance, MLOps/operability.
- File-by-file coverage prioritized by execution paths: API (`api/`), evaluation (`eval/`), UI (`review_ui/`), data collection (`scripts/data_collection/`), rules (`rules/*.csv`), orchestration scripts, audit logs, docs, tests.
- Evidence-based: statements reference observed code/config; assumptions are avoided or explicitly marked.

## High-level system architecture
- **Purpose**: Rule-first gender/occupation bias detection and rewriting engine with optional mT5 generative fallback; targets English/French/Swahili/Gikuyu; supports API, CLI/demo, evaluation, and human review UI.
- **Runtime**: Python 3.12 (Poetry), FastAPI service (`api/main.py`), optional Streamlit review UI (`review_ui/app.py`), batch/data pipelines in `scripts/`, evaluation framework in `eval/`.
- **Core components**
  - **Rules & lexicons**: `rules/lexicon_{en,fr,ki,sw}_v2.csv` (explicit mappings, tags, severity, examples). Swahili includes noun-class/possessive handling; EN/FR/KE include pronoun generic replacements.
  - **Rewrite engine**: `api/main.py` orchestrates detection, semantic-preservation check, rewrite, audit logging; optional mT5 fallback via `api/ml_rewriter.py`.
  - **Evaluation stack**: `eval/*.py` implements detectors (rule, ML, hybrid), metrics (fairness, semantic preservation, HITL), evaluators, baselines, ablations.
  - **Data collection & prep**: `scripts/` and `scripts/data_collection/` ingest public datasets (WinoBias, WinoGender, CrowS-Pairs), scrape/mine corpora (news, Wikipedia, Twitter, CC100, AfriSenti, Kwici), PII detection, sampling, template generation, and ground-truth merging.
  - **UI & audit**: Streamlit review of rewrites (`review_ui/app.py`) writes to `audit_logs/reviews.jsonl`; API writes rewrites to `audit_logs/rewrites.jsonl`.
  - **Orchestration**: `run_evaluation.py`, `run_aibridge_evaluation.py`, `demo_live.py`, `Makefile`, Docker/Docker Compose for packaging.

## File-by-file and module walkthrough
### Service layer
- `api/main.py`: FastAPI app exposing `/rewrite` and `/rewrite/batch`. Loads lexicons, applies rule-based replacements with context checks, semantic preservation threshold, audit logging (JSONL), optional ML rewrite fallback; supports per-language configurations and request schema validation.
- `api/ml_rewriter.py`: Lazy-loads `google/mt5-small` (transformers/torch) and generates N candidates via beam search; returns rewrites with scores and latency.

### UI & audit
- `review_ui/app.py`: Streamlit UI reading `audit_logs/rewrites.jsonl`, lets reviewers approve/reject/approve-with-edit; persists to `audit_logs/reviews.jsonl`; supports filtering and pagination.
- `audit_logs/rewrites.jsonl` / `audit_logs/reviews.jsonl`: JSONL audit trails of rewrites and reviewer actions (observed sample entries).

### Rules & dictionaries
- `rules/lexicon_en_v2.csv`, `rules/lexicon_fr_v2.csv`, `rules/lexicon_ki_v2.csv`, `rules/lexicon_sw_v2.csv`: Structured bias/neutral pairs with tags, severity, examples; Swahili/Kikuyu include agreement metadata; English expanded via auto-variant duplication; French uses inclusive forms.

### Evaluation framework (`eval/`)
- Core models/types: `models.py` (Language enums, data classes), `data_loader.py` (AI BRIDGE schemas, CSV loading, batching), `metrics_calculator.py`, `fairness_metrics.py` (DP/EO/EqOdds/MBE), `hitl_metrics.py` (HMAR/Kappa/Alpha), `ground_truth_{en,fr,ki,sw}.csv`.
- Detection/correction: `bias_detector.py`, `context_checker.py`, `correction_evaluator.py`, `hybrid_detector.py`, `ml_detector.py`, `ml_evaluation.py`, `mt5_corrector.py`, `ngeli_tracker.py` (Swahili noun-class tracking), `lexicon_validator.py`.
- Experiments: `baseline_simple.py`, `baseline_comparison.py`, `ablation_study.py`, `evaluator.py`, `failure_analyzer.py`, `bias_detector.py`, `ngeli_tracker.py`.

### Data collection & processing
- Top-level: `scripts/compute_metrics.py` (review acceptance rate), `ingest_data.py` (normalize arbitrary datasets, call batch API), `parse_winogender.py`, `get_bias_in_bios.py`, `generate_lexicons.py` (synthetic lexicon expansion), `generate_lexicons.py`.
- `scripts/data_collection/`:
  - Acquisition/mining: `download_datasets.py` (WinoBias/WinoGender/CrowS-Pairs), `download_swahili_news.py`, `mine_kwici_corpus.py`, `mine_masakhaner.py`, `download_afrisenti_swahili.py`, `download_cc100_swahili.py`, `extract_wikipedia.py`, `scrape_twitter_swahili.py`, `download_datasets.py`, `download_cc100_swahili.py`.
  - Cleaning/PII: `detect_pii.py` (regex-based PII removal), `filter_swahili_candidates.py` (heuristic filters), `analyze_swahili_corpus.py` (bias patterns), `track_quality.py`, `test_collection.py` (schema & AI BRIDGE compliance checks).
  - Annotation tooling: `annotate_samples.py` (CLI annotator), `sample_for_annotation.py` (stratified sampling), `merge_ground_truth.py` (combine generated templates and curated GT), `generate_test_templates.py` (WinoBias-style Swahili templates), `generate_test_templates.py`, `annotate_samples.py`.
  - Corpus-specific: `download_afrisenti_swahili.py`, `download_cc100_swahili.py`, `download_swahili_news.py`, `mine_kwici_corpus.py`, `mine_masakhaner.py`, `scrape_twitter_swahili.py`.

### Orchestration & demos
- `run_evaluation.py`: entry for core evaluation over languages; supports args for model/detector choices.
- `run_aibridge_evaluation.py`: specialized AI BRIDGE compliance evaluation (fairness, semantic preservation).
- `demo_live.py`: CLI/streaming demo invoking rewrite engine.
- `Makefile`: targets for lint, format, tests, run API/UI/demo, evaluation.
- `Dockerfile` / `docker-compose.yml`: containerize API + optional UI; installs Poetry deps, exposes 8000.

### Tests
- `tests/test_api.py`, `tests/test_demo.py`: API and demo smoke tests.
- `tests/test_fairness_metrics.py`: Unit tests for DP/EO/EqOdds/MBE and demographic group extraction.
- `tests/test_hitl_metrics.py`, `tests/test_system.py` (if present in tree) cover metrics/system integration.

## AI/ML design
- **Rule-first detection & rewrite**: Primary path uses lexicon lookups with contextual checks (`context_checker`, semantic preservation scoring). Severity drives replacement vs warn. Swahili noun-class agreement handled via tags/patterns; pronoun generic handling in EN/FR/Swahili.
- **Generative fallback**: mT5-small beam search for rewrites when rules fail or semantic preservation is low; minimal safety filters (length/score thresholds) present; no RLHF or toxicity classifier observed.
- **Evaluation**: Semantic preservation scoring (likely BLEU/semantic similarity inside `correction_evaluator`), fairness metrics (DP/EO/EqOdds/MBE) with AI BRIDGE thresholds, HITL metrics for reviewer agreement.
- **Data/Model artifacts**: Lexicons are in-repo CSV; ground-truth CSVs per language in `eval/`; mT5 weights pulled from Hugging Face at runtime.

## Data pipeline and assets
- **Sources**: Public datasets (WinoBias, WinoGender, CrowS-Pairs, Bias-in-Bios), open corpora (CC100, Wikipedia, Kwici), social (Twitter via snscrape), news (Zenodo Swahili news), MasakhaNER (NER BIO), AfriSenti Twitter sentiment.
- **Schemas**: AI BRIDGE-aligned CSV fields (40-field schema enforced by `test_collection.py`). Ground-truth CSVs store `text, has_bias, bias_category, expected_correction`.
- **PII handling**: `detect_pii.py` performs regex-based redaction (emails, phone, URLs, SSN/ID, titles+names) with placeholder/remove modes; stats emitted.
- **Quality gates**: `track_quality.py` (distribution, balance, Kappa placeholder), `test_collection.py` (schema/enums/PII flag, language whitelist, bronze target check), `filter_swahili_candidates.py` (false-positive filtering), `analyze_swahili_corpus.py` (pattern mining), `merge_ground_truth.py` (dedupe/shuffle/compliance check).
- **Sampling & templates**: `sample_for_annotation.py` stratifies by occupation; `generate_test_templates.py` creates large-scale Swahili templates; `merge_ground_truth.py` expands GT to Bronze target.

## Security, privacy, and compliance
- **PII mitigation**: Explicit redaction script; API does not enforce PII scanning on ingress—risk remains unless upstream uses the script.
- **Auditability**: Rewrites and reviews persisted as JSONL with timestamps and IDs; no tamper-proofing or retention policies.
- **Dependency risk**: mT5 model pulled at runtime; transformers/torch not pinned tightly (depends on Poetry lock). snscrape/requests used for scraping; no sandboxing.
- **API surface**: No auth/rate limiting/CSRF; suitable only for trusted environments. Docker exposes 8000 without TLS.
- **Data licensing**: Scripts cite dataset licenses (MIT, CC BY/SA); Twitter scraping mentions ToS; enforcement relies on operator.

## Performance and scalability
- **Rewrite path**: Rule-based path is O(n) over tokens; semantic preservation step may add model cost (not deeply profiled). Batch endpoint exists.
- **mT5 fallback**: Beam search generation is slow and CPU/GPU dependent; no caching or batching inside `ml_rewriter` beyond single call. Model lazy-load mitigates cold start slightly but still heavy.
- **Data pipelines**: Many scripts stream/iterate with simple filters; CC100 uses streaming to avoid full download; no parallelism; progress via tqdm when available.
- **UI**: Streamlit reading JSONL may degrade with large logs.

## MLOps, observability, and quality
- **Config & env**: Poetry-managed deps in `pyproject.toml`; `.env` referenced in docs; Docker/compose present. No centralized config for model weights/endpoints.
- **Logging/metrics**: Minimal print logging; no structured metrics or tracing. Audit logs capture rewrites/reviews only.
- **Testing**: Unit tests exist for API/demo/fairness; no continuous integration config observed. No automated regression for data pipelines or lexicon integrity.
- **Deployment**: Dockerfile builds runtime; compose could run API/UI but compose file contents not yet reviewed for service wiring (assumed default single service). No CD scripts.

## Strengths
- Comprehensive multilingual lexicons with explicit metadata and examples; Swahili/Kikuyu morphological considerations included.
- Rich evaluation toolkit: fairness metrics with AI BRIDGE thresholds, semantic preservation, HITL metrics, ablation/baseline scripts.
- Data collection suite covers multiple real-world and benchmark sources with PII scrubbing and quality filters; ground-truth expansion tooling (templates + merge).
- Audit trail and reviewer UI for human-in-the-loop acceptance.

## Gaps / risks
- No authentication, rate limiting, or input sanitization on API; suitable only for trusted/internal use.
- PII redaction not enforced in the API path; relies on external preprocessing.
- mT5 fallback lacks safety/toxicity filters and may hallucinate; no guardrails beyond semantic preservation threshold.
- Performance/scalability: generation is slow; no batching, caching, or GPU detection in service layer; Streamlit/audit logs may not scale.
- Observability: no metrics, health checks, or structured logging; limited test coverage beyond metrics/API smoke tests.
- Data quality: lexicon_en_v2 contains synthetic duplicates with suffixed variants; could inflate match rates or introduce false positives.
- MLOps: no CI/CD, no model versioning or artifact registry; dependency pinning relies on lockfile but transformers/torch may be heavy in Docker image.

## Recommendations (prioritized)
1) **Secure the API**: Add auth (token), request size limits, and optional PII scan hook before rewrite; enable CORS controls and rate limiting for public exposure.
2) **Safety for ML fallback**: Add toxicity/PII classifiers or constrained decoding; expose a flag to disable ML fallback by default in production.
3) **Performance hardening**: Batch/async generation, GPU-aware loading, and caching of lexicons; pre-load model at startup behind a feature flag; cap batch sizes.
4) **Observability**: Introduce structured logging, request/latency metrics, and health endpoints; log semantic preservation scores and rule hits.
5) **Data quality**: Deduplicate `lexicon_en_v2.csv` variants or tag synthetic rows; add automated lexicon validation tests; enforce AI BRIDGE schema in pipelines.
6) **CI/CD & tests**: Add CI running lint+tests; extend tests to rewrite correctness (rule hits, semantic preservation), data loaders, and pipelines.
7) **Privacy compliance**: Make `detect_pii.py` logic callable from the API; add configurable redaction policies; document retention for `audit_logs/*`.
8) **Documentation**: Provide runbooks for Docker/compose deployments, GPU vs CPU guidance, and safety considerations for scraping scripts.

## Quality gates snapshot
- Build/lint/tests not executed in this pass (report-focused). Recommend running `poetry run pytest` and lint before release; see CI/CD recommendation above.
