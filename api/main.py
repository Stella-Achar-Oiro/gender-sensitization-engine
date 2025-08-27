from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import pandas as pd, re, json, uuid
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
RULES_DIR = BASE / "rules"
AUDIT_FILE = BASE / "audit_logs" / "rewrites.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="JuaKazi Correction Engine", version="0.1")

def load_rules_v2(lang="en"):
    path = RULES_DIR / f"lexicon_{lang}_v2.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    rules = []
    for _, row in df.iterrows():
        rules.append({col: str(row.get(col, "")) for col in df.columns})
    return rules

RULES = {"en": load_rules_v2("en"), "sw": load_rules_v2("sw")}

class RewriteRequest(BaseModel):
    id: str
    lang: str
    text: str

class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool

def preserve_case_replace(orig, replacement):
    if orig.isupper():
        return replacement.upper()
    if orig[0].isupper():
        return replacement.capitalize()
    return replacement

def apply_rules(text: str, lang: str):
    edits, new_text = [], text
    rules = RULES.get(lang, [])
    for rule in rules:
        biased, neutral, severity = rule["biased"], rule["neutral_primary"], rule["severity"]
        pattern = r"\b" + re.escape(biased) + r"\b"

        def repl(match):
            orig = match.group(0)
            replacement = preserve_case_replace(orig, neutral)
            edits.append({
                "from": orig,
                "to": replacement,
                "severity": severity,
                "tags": rule.get("tags", ""),
                "alternatives": rule.get("neutral_alternatives", "").split("|"),
                "example": {
                    "biased": rule.get("example_biased", ""),
                    "neutral": rule.get("example_neutral", "")
                }
            })
            if severity == "warn":
                return orig + f" [⚠ consider {replacement}]"
            return replacement

        new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE)
    return new_text, edits

def log_audit(entry: dict):
    entry['audit_id'] = str(uuid.uuid4())
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    rewritten, edits = apply_rules(req.text, req.lang)
    needs_review = len(edits) == 0
    confidence = 0.85 if edits else 0.5
    response = {
        "id": req.id,
        "original_text": req.text,
        "rewrite": rewritten,
        "edits": edits,
        "confidence": confidence,
        "needs_review": needs_review
    }
    log_audit({"timestamp": datetime.utcnow().isoformat(), "request": req.dict(), "response": response})
    return response
