# Audit Log Schema

We use **JSONL** files (one JSON object per line).

## System events: `audit_logs/rewrites.jsonl`
Each line is a completed rewrite attempt.

```json
{
  "audit_id": "uuid",
  "timestamp": "2025-08-27T12:34:56.000Z",
  "request": { "id": "sw1", "lang": "sw", "text": "..." },
  "response": {
    "id": "sw1",
    "original_text": "...",
    "rewrite": "...",
    "edits": [
      { "from": "x", "to": "y", "severity": "replace", "tags": "gender|...", "alternatives": ["..."], "example": {...} }
    ],
    "confidence": 0.85,
    "needs_review": false
  },
  "model": "rulepack-v0.1"
}
```

## Human decisions: `audit_logs/reviews.jsonl`
Each line is a reviewer decision referencing the audit_id.

```json
{
  "review_id": "uuid",
  "timestamp": "2025-08-27T12:40:00Z",
  "audit_id": "uuid-from-rewrites",
  "action": "approve | approve_with_edit | reject",
  "reviewer": "name-or-id",
  "comment": "optional",
  "edited_rewrite": "optional new text"
}
```
## Metrics

Rewrite Acceptance Rate = (approve + approve_with_edit) / total_reviews.

Compute via `scripts/compute_metrics.py.`

## Retention

Do not commit audit logs to public repos.

Rotate or compress logs periodically in production.