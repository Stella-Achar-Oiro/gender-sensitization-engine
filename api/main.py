"""
JuaKazi Gender Bias Correction API (Hybrid Rules + ML)
"""

from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import pandas as pd, re, json, uuid, time, sys
from datetime import datetime

from .ml_rewriter import ml_rewrite

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from config import lexicon_filename
from eval.context_checker import should_apply_correction
from eval.correction_evaluator import SemanticPreservationMetrics

RULES_DIR = BASE / "rules"
AUDIT_FILE = BASE / "audit_logs" / "rewrites.jsonl"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

SEMANTIC_PRESERVATION_THRESHOLD = 0.70

app = FastAPI(title="JuaKazi Correction Engine (hybrid)", version="0.3")
semantic_metrics = SemanticPreservationMetrics()


def load_rules_v2(lang="en"):
    path = RULES_DIR / lexicon_filename(lang)
    if not path.exists():
        return []
    df = pd.read_csv(path, on_bad_lines="skip")
    return [{col: str(row.get(col, "")) for col in df.columns} for _, row in df.iterrows()]


RULES = {"en": load_rules_v2("en"), "sw": load_rules_v2("sw")}


class RewriteRequest(BaseModel):
    id: str
    lang: str
    text: str
    flags: list = None
    region_dialect: str = None  # "kenya" | "tanzania" | "uganda" | "sheng"


class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool
    source: str           # "rules" | "ml" | "preserved"
    reason: str           # why this decision was made
    semantic_score: float = None
    skipped_context: list = None


def preserve_case(orig: str, replacement: str) -> str:
    if orig.isupper():
        return replacement.upper()
    if orig[0].isupper():
        return replacement.capitalize()
    return replacement


def _make_edit(orig: str, replacement: str, rule: dict) -> dict:
    tags = rule.get("tags", "") or "occupation/role"
    severity = rule.get("severity", "replace")
    return {
        "from": orig,
        "to": replacement,
        "severity": severity,
        "tags": tags,
        "reason": f"'{orig}' is gender-biased ({tags}); use gender-neutral '{replacement}'",
    }


def _apply_rule(text: str, rule: dict) -> tuple[str, dict | None]:
    """Apply a single rule to text. Returns (new_text, edit_or_None)."""
    biased = rule["biased"]
    neutral = rule["neutral_primary"]
    severity = rule.get("severity", "replace")
    pattern = r"\b" + re.escape(biased) + r"\b"

    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return text, None

    orig = match.group(0)
    replacement = preserve_case(orig, neutral)
    edit = _make_edit(orig, replacement, rule)

    if severity == "warn":
        new_text = re.sub(pattern, lambda m: m.group(0) + f" [consider {replacement}]", text, flags=re.IGNORECASE)
    else:
        new_text = re.sub(pattern, lambda m: preserve_case(m.group(0), neutral), text, flags=re.IGNORECASE)

    return new_text, edit


def apply_rules_on_spans(text: str, lang: str, flags: list = None):
    """
    Apply lexicon rules to text, with context checking.
    Returns: (rewritten_text, edits, matched_count, skipped_context)
    """
    edits = []
    skipped = []
    new_text = text
    rules = RULES.get(lang, [])

    if not rules:
        return new_text, edits, 0, skipped

    # If flags given, restrict to those spans only
    if flags:
        matched = 0
        for f in flags:
            if "text" in f:
                span_text = f["text"]
            elif "span" in f:
                s, e = f["span"]
                span_text = text[s:e]
            else:
                continue

            for rule in rules:
                biased = rule["biased"]
                pattern = r"\b" + re.escape(biased) + r"\b"
                if not re.search(pattern, span_text, flags=re.IGNORECASE):
                    continue

                avoid_when = rule.get("avoid_when", "")
                constraints = rule.get("constraints", "")
                if avoid_when or constraints:
                    ok, ctx_reason = should_apply_correction(text, biased, avoid_when, constraints)
                    if not ok:
                        skipped.append({"term": biased, "reason": ctx_reason, "avoid_when": avoid_when})
                        continue

                new_text, edit = _apply_rule(new_text, rule)
                if edit:
                    edits.append(edit)
                    matched += 1
                break  # one rule per span flag

        return new_text, edits, matched, skipped

    # Global pass
    for rule in rules:
        biased = rule["biased"]
        pattern = r"\b" + re.escape(biased) + r"\b"
        if not re.search(pattern, new_text, flags=re.IGNORECASE):
            continue

        avoid_when = rule.get("avoid_when", "")
        constraints = rule.get("constraints", "")
        if avoid_when or constraints:
            ok, ctx_reason = should_apply_correction(text, biased, avoid_when, constraints)
            if not ok:
                skipped.append({"term": biased, "reason": ctx_reason, "avoid_when": avoid_when})
                continue

        new_text, edit = _apply_rule(new_text, rule)
        if edit:
            edits.append(edit)

    return new_text, edits, len(edits), skipped


def _build_reason(source: str, edits: list, skipped: list) -> str:
    if source == "preserved":
        return "Original preserved — correction would damage meaning (semantic score below threshold)."
    if source == "ml":
        return "No lexicon rules matched; ML fallback applied. Human review required."
    if edits:
        terms = ", ".join(f"'{e['from']}'" for e in edits)
        return f"{len(edits)} biased term(s) corrected: {terms}."
    if skipped:
        terms = ", ".join(f"'{s['term']}'" for s in skipped)
        return f"Bias terms detected ({terms}) but skipped — biographical, quote, or statistical context."
    return "No gender bias detected."


def log_audit(entry: dict):
    entry["audit_id"] = str(uuid.uuid4())
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    t0 = time.time()
    rewritten, edits, matched_rules, skipped = apply_rules_on_spans(
        req.text, req.lang, flags=req.flags or None
    )
    source = "rules"
    ml_info = None
    semantic_score = None

    if rewritten != req.text:
        score = semantic_metrics.calculate_composite_preservation_score(req.text, rewritten)
        semantic_score = score["composite_score"]
        if semantic_score < SEMANTIC_PRESERVATION_THRESHOLD:
            rewritten, edits, source, semantic_score = req.text, [], "preserved", 1.0

    if matched_rules == 0 and source != "preserved":
        ml_out = ml_rewrite(req.text, lang=req.lang, num_return_sequences=3)
        ml_score = semantic_metrics.calculate_composite_preservation_score(req.text, ml_out["best"])
        if ml_score["composite_score"] < SEMANTIC_PRESERVATION_THRESHOLD:
            rewritten, source, semantic_score = req.text, "preserved", 1.0
        else:
            rewritten = ml_out["best"]
            source = "ml"
            semantic_score = ml_score["composite_score"]
            ml_info = ml_out
            edits.append({"from": req.text, "to": rewritten, "severity": "ml_fallback", "tags": "", "reason": "ML rewrite"})

    latency_ms = int((time.time() - t0) * 1000)
    confidence = {"rules": 0.85, "ml": 0.60, "preserved": 0.95}.get(source, 0.85)
    needs_review = source == "ml" or len(edits) == 0
    reason = _build_reason(source, edits, skipped)

    response = {
        "id": req.id,
        "original_text": req.text,
        "rewrite": rewritten,
        "edits": edits,
        "confidence": confidence,
        "needs_review": needs_review,
        "source": source,
        "reason": reason,
        "semantic_score": semantic_score,
        "skipped_context": skipped or None,
    }

    log_audit({
        "timestamp": datetime.utcnow().isoformat(),
        "request": req.dict(),
        "response": response,
        "model_info": ml_info or {"model": "rulepack-v0.3"},
        "latency_ms": latency_ms,
        "region_dialect": req.region_dialect or "unknown",
    })
    return response


@app.post("/rewrite/batch")
def rewrite_batch(items: list):
    return [rewrite(RewriteRequest(**it)) for it in items]
