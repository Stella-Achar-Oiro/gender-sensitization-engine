"""Rules engine — applies corrections, builds edit/reason output. Uses core for rules and context."""

import re
from pathlib import Path

from core.context_checker import should_apply_correction
from core.rules_loader import load_rules as _load_rules

BASE = Path(__file__).resolve().parent.parent
RULES_DIR = BASE / "rules"

# Module-level cache — loaded once at import time
RULES: dict[str, list[dict]] = {
    "en": _load_rules("en", RULES_DIR),
    "sw": _load_rules("sw", RULES_DIR),
}


def _preserve_case(orig: str, replacement: str) -> str:
    if orig.isupper():
        return replacement.upper()
    if orig[0].isupper():
        return replacement.capitalize()
    return replacement


def _make_edit(orig: str, replacement: str, rule: dict) -> dict:
    tags = rule.get("tags", "") or "occupation/role"
    severity = rule.get("severity", "replace")
    bias_type = rule.get("bias_label", "stereotype")
    stereotype_category = rule.get("stereotype_category", "profession")
    return {
        "from": orig,
        "to": replacement,
        "severity": severity,
        "tags": tags,
        "bias_type": bias_type,
        "stereotype_category": stereotype_category,
        "reason": f"'{orig}' is gender-biased ({tags}); use gender-neutral '{replacement}'",
    }


def _apply_rule(text: str, rule: dict) -> tuple[str, dict | None]:
    """Apply one rule to text. Returns (new_text, edit) or (text, None) if no match."""
    biased = rule["biased"]
    neutral = rule["neutral_primary"]
    severity = rule.get("severity", "replace")
    pattern = r"\b" + re.escape(biased) + r"\b"

    if not re.search(pattern, text, flags=re.IGNORECASE):
        return text, None

    orig = re.search(pattern, text, flags=re.IGNORECASE).group(0)
    replacement = _preserve_case(orig, neutral)

    if severity == "warn":
        new_text = re.sub(
            pattern,
            lambda m: m.group(0) + f" [consider {replacement}]",
            text,
            flags=re.IGNORECASE,
        )
    else:
        new_text = re.sub(
            pattern,
            lambda m: _preserve_case(m.group(0), neutral),
            text,
            flags=re.IGNORECASE,
        )

    return new_text, _make_edit(orig, replacement, rule)


def apply_rules_on_spans(
    text: str, lang: str, flags: list = None
) -> tuple[str, list, int, list]:
    """
    Apply lexicon rules to text with context checking.
    Returns: (rewritten_text, edits, matched_count, skipped_context)
    """
    edits = []
    skipped = []
    new_text = text
    rules = RULES.get(lang, [])

    if not rules:
        return new_text, edits, 0, skipped

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
                break

        return new_text, edits, matched, skipped

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


def build_reason(source: str, edits: list, skipped: list) -> str:
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
