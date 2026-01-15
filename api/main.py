"""
JuaKazi Gender Bias Correction API (Hybrid Rules + ML)

Enhanced with:
- Context-aware correction to preserve meaning in biographical/historical contexts
- Semantic validation to reject over-aggressive corrections
"""

from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import pandas as pd, re, json, uuid, time, os, sys
from datetime import datetime

from .ml_rewriter import ml_rewrite

# Add project root to path for eval imports
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from eval.context_checker import ContextChecker, should_apply_correction
from eval.correction_evaluator import SemanticPreservationMetrics

RULES_DIR = BASE / "rules"
AUDIT_FILE = BASE / "audit_logs" / "rewrites.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Semantic preservation threshold - reject corrections below this
SEMANTIC_PRESERVATION_THRESHOLD = 0.70

app = FastAPI(title="JuaKazi Correction Engine (hybrid)", version="0.3")

# Initialize context checker for meaning preservation
context_checker = ContextChecker()
semantic_metrics = SemanticPreservationMetrics()

def load_rules_v2(lang="en"):
    path = RULES_DIR / f"lexicon_{lang}_v3.csv"
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
    source: str  # "rules" | "ml" | "preserved"
    semantic_score: float = None  # Preservation score when correction applied
    skipped_context: list = None  # Terms skipped due to context preservation

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

    Enhanced with context-aware correction:
    - Checks avoid_when field to skip corrections in biographical/historical contexts
    - Returns skipped_context list for transparency

    Returns: (rewritten_text, edits, matched_rule_count, skipped_context)
    """
    edits = []
    skipped_context = []
    new_text = text
    rules = RULES.get(lang, [])
    if not rules:
        return new_text, edits, 0, skipped_context

    # If flags provided, limit replacements to flagged substrings
    if flags:
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
                    # Context check: should we apply this correction?
                    avoid_when = rule.get("avoid_when", "")
                    constraints = rule.get("constraints", "")

                    if avoid_when or constraints:
                        should_correct, reason = should_apply_correction(
                            text, biased, avoid_when, constraints
                        )
                        if not should_correct:
                            skipped_context.append({
                                "term": biased,
                                "reason": reason,
                                "avoid_when": avoid_when
                            })
                            continue

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
        return new_text, edits, matched_count, skipped_context

    # No flags: do global application with context checking
    for rule in rules:
        biased, neutral, severity = rule["biased"], rule["neutral_primary"], rule["severity"]
        pattern = r"\b" + re.escape(biased) + r"\b"

        # Check if this term appears in text
        if not re.search(pattern, text, flags=re.IGNORECASE):
            continue

        # Context check: should we apply this correction?
        avoid_when = rule.get("avoid_when", "")
        constraints = rule.get("constraints", "")

        if avoid_when or constraints:
            should_correct, reason = should_apply_correction(
                text, biased, avoid_when, constraints
            )
            if not should_correct:
                skipped_context.append({
                    "term": biased,
                    "reason": reason,
                    "avoid_when": avoid_when
                })
                continue

        def repl(match):
            orig = match.group(0)
            replacement = preserve_case_replace(orig, neutral)
            edits.append({"from": orig, "to": replacement, "severity": severity, "tags": rule.get("tags","")})
            if severity == "warn":
                return orig + f" [⚠ consider {replacement}]"
            return replacement
        new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE)
    return new_text, edits, len(edits), skipped_context

def log_audit(entry: dict):
    entry['audit_id'] = str(uuid.uuid4())
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    t0 = time.time()
    rewritten, edits, matched_rules, skipped_context = apply_rules_on_spans(
        req.text, req.lang, flags=req.flags or None
    )
    source = "rules"
    ml_info = None
    semantic_score = None
    latency_ms = int((time.time() - t0) * 1000)

    # Calculate semantic preservation score if text was modified
    if rewritten != req.text:
        preservation = semantic_metrics.calculate_composite_preservation_score(
            req.text, rewritten
        )
        semantic_score = preservation['composite_score']

        # Semantic validation: reject correction if preservation is too low
        if semantic_score < SEMANTIC_PRESERVATION_THRESHOLD:
            # Revert to original - correction would damage meaning too much
            rewritten = req.text
            edits = []
            source = "preserved"
            semantic_score = 1.0  # Original preserved perfectly

    if matched_rules == 0 and source != "preserved":
        # fallback to ML
        ml_out = ml_rewrite(req.text, lang=req.lang, num_return_sequences=3)
        rewritten = ml_out["best"]

        # Validate ML output for semantic preservation
        ml_preservation = semantic_metrics.calculate_composite_preservation_score(
            req.text, rewritten
        )
        ml_semantic_score = ml_preservation['composite_score']

        if ml_semantic_score < SEMANTIC_PRESERVATION_THRESHOLD:
            # ML output damages meaning too much - keep original
            rewritten = req.text
            source = "preserved"
            semantic_score = 1.0
        else:
            # ML output is acceptable
            ml_info = ml_out
            source = "ml"
            semantic_score = ml_semantic_score
            latency_ms = ml_out.get("latency_ms", latency_ms)
            edits.append({"from": req.text, "to": rewritten, "severity": "ml_fallback", "tags": ""})

    needs_review = True if source == "ml" else (len(edits) == 0)
    confidence = 0.85 if source == "rules" else (0.6 if source == "ml" else 0.95)

    response = {
        "id": req.id,
        "original_text": req.text,
        "rewrite": rewritten,
        "edits": edits,
        "confidence": confidence,
        "needs_review": needs_review,
        "source": source,
        "semantic_score": semantic_score,
        "skipped_context": skipped_context if skipped_context else None
    }

    audit = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": req.dict(),
        "response": response,
        "model_info": ml_info if ml_info else {"model": "rulepack-v0.3-context-aware"},
        "latency_ms": latency_ms,
        "semantic_preservation": semantic_score,
        "context_preservations": skipped_context
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
