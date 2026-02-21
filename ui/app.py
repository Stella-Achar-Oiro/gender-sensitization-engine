import streamlit as st
import json
import uuid
from pathlib import Path
from datetime import datetime

REWRITES = Path("../audit_logs/rewrites.jsonl")
REVIEWS = Path("../audit_logs/reviews.jsonl")
REVIEWS.parent.mkdir(parents=True, exist_ok=True)


# ── Data layer ────────────────────────────────────────────────────────────────

def load_rewrites() -> list:
    if not REWRITES.exists():
        return []
    items = []
    for line in REWRITES.read_text(encoding="utf-8").splitlines():
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return list(reversed(items))


def save_review(audit_id: str, action: str, reviewer: str, comment: str = "",
                edited_rewrite: str = None, chosen_candidate: str = None,
                flagged_reason: str = None):
    review = {
        "review_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "audit_id": audit_id,
        "action": action,
        "reviewer": reviewer,
        "comment": comment,
    }
    if edited_rewrite:
        review["edited_rewrite"] = edited_rewrite
    if chosen_candidate:
        review["chosen_candidate"] = chosen_candidate
    if flagged_reason:
        review["flagged_reason"] = flagged_reason
    with open(REVIEWS, "a", encoding="utf-8") as f:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")


# ── UI components ─────────────────────────────────────────────────────────────

def render_header(item: dict):
    resp = item["response"]
    req = item["request"]
    source = resp.get("source", "unknown")
    badge = {"rules": "🟢 rules", "ml": "🟡 ml", "preserved": "🔵 preserved"}.get(source, source)
    region = req.get("region_dialect") or item.get("region_dialect") or "—"
    audit_id = item.get("audit_id", "")

    st.markdown(
        f"**{badge}** &nbsp;·&nbsp; `{audit_id[:8]}` "
        f"&nbsp;·&nbsp; lang: `{req.get('lang')}` "
        f"&nbsp;·&nbsp; region: `{region}`"
    )


def render_text_comparison(item: dict):
    req = item["request"]
    resp = item["response"]
    original = req.get("text", "")
    rewrite = resp.get("rewrite", "")

    col_l, col_r = st.columns(2)
    with col_l:
        st.caption("Original")
        st.info(original)
    with col_r:
        st.caption("Suggested rewrite")
        if rewrite != original:
            st.success(rewrite)
        else:
            st.info(rewrite)

    reason = resp.get("reason") or item.get("reason")
    if reason:
        st.caption(f"ℹ️ {reason}")


def render_edits(edits: list):
    if not edits:
        return
    st.caption("Edits:")
    for e in edits:
        icon = "⚠️" if e.get("severity") == "warn" else "✏️"
        st.markdown(f"- {icon} `{e.get('from')}` → `{e.get('to')}` *({e.get('severity')})*")
        if e.get("reason"):
            st.caption(f"\u00a0\u00a0\u00a0\u00a0{e['reason']}")


def render_skipped(skipped: list):
    if not skipped:
        return
    with st.expander(f"🔍 {len(skipped)} term(s) skipped (context preserved)"):
        for s in skipped:
            st.write(f"- `{s.get('term')}` — {s.get('reason', '')} *(avoid_when: {s.get('avoid_when', '')})*")


def render_ml_candidates(item: dict):
    if item.get("response", {}).get("source") != "ml":
        return
    candidates = (item.get("model_info") or {}).get("candidates", [])
    if not candidates:
        return
    with st.expander("🤖 ML candidates"):
        for i, c in enumerate(candidates):
            st.write(f"{i+1}. {c}")


def render_meta(resp: dict):
    parts = []
    if resp.get("confidence") is not None:
        parts.append(f"confidence: {resp['confidence']:.0%}")
    if resp.get("semantic_score") is not None:
        parts.append(f"semantic preservation: {resp['semantic_score']:.0%}")
    if parts:
        st.caption(" · ".join(parts))


def render_review_form(item: dict) -> bool:
    """Renders the review form. Returns True if a decision was submitted."""
    audit_id = item.get("audit_id", "")
    resp = item["response"]
    source = resp.get("source", "rules")
    candidates = (item.get("model_info") or {}).get("candidates", [])

    with st.form(key=f"form-{audit_id}"):
        col_rev, col_dec = st.columns(2)
        with col_rev:
            reviewer = st.text_input("Reviewer", value="pilot_user")
        with col_dec:
            decision = st.selectbox("Decision", ["approve", "approve_with_edit", "reject", "flag"])

        comment = st.text_area("Comment (optional)")
        flagged_reason = None
        chosen_candidate = None
        edited = None

        if decision == "flag":
            flagged_reason = st.text_input(
                "Flag reason (required)",
                placeholder="e.g. false positive — proper noun context"
            )

        if source == "ml" and candidates:
            idx = st.radio("Pick ML candidate", [str(i + 1) for i in range(len(candidates))], index=0)
            chosen_candidate = candidates[int(idx) - 1]

        if decision == "approve_with_edit":
            edited = st.text_area("Edited rewrite", value=chosen_candidate or resp.get("rewrite", ""))

        submitted = st.form_submit_button("Submit")
        if not submitted:
            return False

        if decision == "flag" and not flagged_reason:
            st.error("Enter a flag reason before submitting.")
            return False

        save_review(
            audit_id, decision, reviewer, comment,
            edited_rewrite=edited,
            chosen_candidate=chosen_candidate,
            flagged_reason=flagged_reason,
        )
        st.success(f"Recorded **{decision}** for `{audit_id[:8]}`")
        return True


# ── Page ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="JuaKazi Review", layout="wide")
st.title("JuaKazi Review UI")

all_items = load_rewrites()
pending = [i for i in all_items if i.get("response", {}).get("needs_review", True)]

col_info, col_filter = st.columns([3, 1])
with col_info:
    st.write(f"**{len(pending)}** pending · {len(all_items)} total")
with col_filter:
    source_filter = st.selectbox("Filter", ["all", "rules", "ml", "preserved"])

if source_filter != "all":
    pending = [i for i in pending if i.get("response", {}).get("source") == source_filter]

for item in pending[:50]:
    st.markdown("---")
    render_header(item)
    render_text_comparison(item)
    render_edits(item.get("response", {}).get("edits", []))
    render_skipped(item.get("response", {}).get("skipped_context") or [])
    render_ml_candidates(item)
    render_meta(item.get("response", {}))
    if render_review_form(item):
        st.rerun()
