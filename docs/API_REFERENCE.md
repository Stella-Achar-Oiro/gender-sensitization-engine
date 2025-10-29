# API Reference (Week 1)

Base URL (local): `http://127.0.0.1:8000`

## POST /rewrite
Rewrite a single text according to lexicon policy.

### Request (JSON)
```json
{
  "id": "string",
  "lang": "en|sw|...",
  "text": "string"
}
```

### Response (JSON)
```json
{
  "id": "string",
  "original_text": "string",
  "rewrite": "string",
  "edits": [
    {
      "from": "string",
      "to": "string",
      "severity": "replace|warn",
      "tags": "string",
      "alternatives": ["string", "..."],
      "example": {"biased": "string", "neutral": "string"}
    }
  ],
  "confidence": 0.0,
  "needs_review": true|false
}
```
## Error codes
```
400 invalid payload

422 validation error (Pydantic)

500 internal error (check server logs)
S```