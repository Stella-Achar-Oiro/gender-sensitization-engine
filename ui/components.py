"""Streamlit render components — one function per UI section."""

import streamlit as st

from .data import save_review

SOURCE_BADGE = {
    "rules": "🟢 rules",
    "ml": "🟡 ml",
    "preserved": "🔵 preserved",
}


def render_header(item: dict) -> None:
    req = item["request"]
    source = item["response"].get("source", "unknown")
    region = req.get("region_dialect") or item.get("region_dialect") or "—"
    audit_id = item.get("audit_id", "")
    badge = SOURCE_BADGE.get(source, source)
    st.markdown(
        f"**{badge}** &nbsp;·&nbsp; `{audit_id[:8]}` "
        f"&nbsp;·&nbsp; lang: `{req.get('lang')}` "
        f"&nbsp;·&nbsp; region: `{region}`"
    )


def render_text_comparison(item: dict) -> None:
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


def render_edits(edits: list) -> None:
    if not edits:
        return
    st.caption("Edits:")
    for e in edits:
        icon = "⚠️" if e.get("severity") == "warn" else "✏️"
        st.markdown(f"- {icon} `{e.get('from')}` → `{e.get('to')}` *({e.get('severity')})*")
        if e.get("reason"):
            st.caption(f"\u00a0\u00a0\u00a0\u00a0{e['reason']}")


def render_skipped(skipped: list) -> None:
    if not skipped:
        return
    with st.expander(f"🔍 {len(skipped)} term(s) skipped (context preserved)"):
        for s in skipped:
            st.write(
                f"- `{s.get('term')}` — {s.get('reason', '')} "
                f"*(avoid_when: {s.get('avoid_when', '')})*"
            )


def render_ml_candidates(item: dict) -> None:
    if item.get("response", {}).get("source") != "ml":
        return
    candidates = (item.get("model_info") or {}).get("candidates", [])
    if not candidates:
        return
    with st.expander("🤖 ML candidates"):
        for i, c in enumerate(candidates):
            st.write(f"{i + 1}. {c}")


def render_meta(resp: dict) -> None:
    parts = []
    if resp.get("confidence") is not None:
        parts.append(f"confidence: {resp['confidence']:.0%}")
    if resp.get("semantic_score") is not None:
        parts.append(f"semantic preservation: {resp['semantic_score']:.0%}")
    if parts:
        st.caption(" · ".join(parts))


def render_review_form(item: dict) -> bool:
    """Render review form. Returns True when a decision is submitted."""
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
                placeholder="e.g. false positive — proper noun context",
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
