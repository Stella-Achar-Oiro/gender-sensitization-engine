# api/main.py  (hybrid)
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import pandas as pd, re, json, uuid, time, os
from datetime import datetime

# import ML rewriter
from .ml_rewriter import ml_rewrite

BASE = Path(__file__).resolve().parent.parent
RULES_DIR = BASE / "rules"
AUDIT_FILE = BASE / "audit_logs" / "rewrites.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="JuaKazi Correction Engine (hybrid)", version="0.2")

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
    flags: list = None  # optional: list of flagged spans {start,end,type}

class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool
    source: str  # "rules" | "ml"

def preserve_case_replace(orig, replacement):
    if orig.isupper():
        return replacement.upper()
    if orig[0].isupper():
        return replacement.capitalize()
    return replacement

def apply_rules_on_spans(text: str, lang: str, flags: list = None):
    """
    If flags supplied, apply replacements ONLY to flagged spans that match rules.
    Else apply globally.
    Returns rewritten_text, edits, matched_rule_count
    """
    edits = []
    new_text = text
    rules = RULES.get(lang, [])
    if not rules:
        return new_text, edits, 0

    # If flags provided, limit replacements to flagged substrings
    if flags:
        # flags: list of {"start":int,"end":int,"text":str,"type":str} OR minimal {"span":[s,e]}
        matched_count = 0
        for f in flags:
            span_text = None
            if "text" in f:
                span_text = f["text"]
            elif "span" in f:
                s,e = f["span"]
                span_text = text[s:e]
            else:
                continue
            # apply rules only to this span_text
            for rule in rules:
                biased = rule["biased"]
                pattern = r"\b" + re.escape(biased) + r"\b"
                if re.search(pattern, span_text, flags=re.IGNORECASE):
                    # perform replacement in the whole new_text (only replaces this occurrence)
                    def repl(m):
                        orig = m.group(0)
                        replacement = preserve_case_replace(orig, rule["neutral_primary"])
                        edits.append({
                            "from": orig, "to": replacement, "severity": rule.get("severity", ""),
                            "tags": rule.get("tags", "")
                        })
                        return replacement if rule.get("severity", "") != "warn" else orig + f" [⚠ consider {replacement}]"
                    new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE, count=1)
                    matched_count += 1
                    break
        return new_text, edits, matched_count

    # No flags: do global application (as in Week1)
    for rule in rules:
        biased, neutral, severity = rule["biased"], rule["neutral_primary"], rule["severity"]
        pattern = r"\b" + re.escape(biased) + r"\b"
        def repl(match):
            orig = match.group(0)
            replacement = preserve_case_replace(orig, neutral)
            edits.append({"from": orig, "to": replacement, "severity": severity, "tags": rule.get("tags","")})
            if severity == "warn":
                return orig + f" [⚠ consider {replacement}]"
            return replacement
        new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE)
    return new_text, edits, len(edits)

def log_audit(entry: dict):
    entry['audit_id'] = str(uuid.uuid4())
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    t0 = time.time()
    rewritten, edits, matched_rules = apply_rules_on_spans(req.text, req.lang, flags=req.flags or None)
    source = "rules"
    ml_info = None
    latency_ms = int((time.time() - t0) * 1000)

    if matched_rules == 0:
        # fallback to ML
        ml_out = ml_rewrite(req.text, lang=req.lang, num_return_sequences=3)
        rewritten = ml_out["best"]
        # record candidates
        ml_info = ml_out
        source = "ml"
        latency_ms = ml_out.get("latency_ms", latency_ms)

        # append an edit entry indicating ML produced rewrite
        edits.append({"from": req.text, "to": rewritten, "severity": "ml_fallback", "tags": ""})

    needs_review = True if source == "ml" else (len(edits) == 0)
    confidence = 0.85 if source == "rules" else 0.6

    response = {
        "id": req.id,
        "original_text": req.text,
        "rewrite": rewritten,
        "edits": edits,
        "confidence": confidence,
        "needs_review": needs_review,
        "source": source
    }

    audit = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": req.dict(),
        "response": response,
        "model_info": ml_info if ml_info else {"model": "rulepack-v0.1"},
        "latency_ms": latency_ms
    }
    log_audit(audit)
    return response

# Batch endpoint
@app.post("/rewrite/batch")
def rewrite_batch(items: list):
    """
    Accepts list of {id,lang,text,flags?}
    Returns list of responses (same as /rewrite)
    """
    results = []
    for it in items:
        res = rewrite(RewriteRequest(**it))
        results.append(res)
    return results
