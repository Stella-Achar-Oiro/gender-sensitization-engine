
# Architecture (Correction Layer – Week 1)

## High-level
Detection layer flags biased spans → **Correction layer (this repo)** proposes inclusive rewrites →
**Human Review UI** validates → **Audit & metrics** report outcomes.

## Components
- **Lexicon v2**: CSV per language with linguistic + policy metadata.
- **Correction API (FastAPI)**:
  - Input: `{ id, lang, text }` (flags optional in Week 1)
  - Process: rules-based scan → policy apply (`replace` or `warn`)
  - Output: rewrite + detailed edits
  - Side-effect: append JSONL line to `audit_logs/rewrites.jsonl`
- **Review UI (Streamlit)**:
  - Loads items from `rewrites.jsonl`
  - Shows original, rewrite, and metadata (severity, tags, examples)
  - Records decisions in `audit_logs/reviews.jsonl`
- **Audit & Metrics**:
  - `rewrites.jsonl`: system events (what changed, when, why)
  - `reviews.jsonl`: human decisions (approve/reject/edit)
  - scripts/compute_metrics.py calculates **Rewrite Acceptance Rate**

## Data flow
Text → `/rewrite` → rules applied → response + system log → review UI →
decision appended → metrics → (later) export sanitized datasets.

## Extensibility
- Add ML rewrite layer behind rules for context-sensitive changes.
- Load language-specific morphology rules (e.g., Swahili `ngeli`) to auto-fix agreement.
- Expose batch `/rewrite/batch` and `/review/submit` endpoints later.
