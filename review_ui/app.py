import streamlit as st, json, uuid
from pathlib import Path
from datetime import datetime

REWRITES = Path("../audit_logs/rewrites.jsonl")
REVIEWS  = Path("../audit_logs/reviews.jsonl")
REVIEWS.parent.mkdir(parents=True, exist_ok=True)

def load_rewrites():
    items = []
    if REWRITES.exists():
        for line in REWRITES.read_text(encoding="utf-8").splitlines():
            try: items.append(json.loads(line))
            except: pass
    return list(reversed(items))  # newest first

def save_review(audit_id, action, reviewer, comment="", edited_rewrite=None, chosen_candidate=None):
    review = {
        "review_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "audit_id": audit_id,
        "action": action,
        "reviewer": reviewer,
        "comment": comment
    }
    if edited_rewrite:
        review["edited_rewrite"] = edited_rewrite
    if chosen_candidate:
        review["chosen_candidate"] = chosen_candidate
    with open(REVIEWS, "a", encoding="utf-8") as f:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")

st.title("JuaKazi Review UI (Week 2)")

rewrites = load_rewrites()
pending = [i for i in rewrites if i.get("response", {}).get("needs_review", True)]

st.write(f"Pending items: {len(pending)}")

for item in pending[:50]:
    audit_id = item.get("audit_id")
    req = item["request"]
    resp = item["response"]
    st.markdown("---")
    st.write(f"**Audit ID:** {audit_id} | **Source:** {resp.get('source')}")
    st.write("**Original:**", req.get("text"))
    st.write("**Suggested rewrite:**", resp.get("rewrite"))
    if item.get("model_info"):
        mi = item["model_info"]
        # Show ML candidates if present
        candidates = mi.get("candidates") if isinstance(mi, dict) else None
        if candidates:
            st.write("**ML candidates:**")
            for i, c in enumerate(candidates):
                st.write(f"{i+1}. {c}")
    for e in resp.get("edits", []):
        st.write(f"- `{e.get('from')}` → `{e.get('to')}` (severity: {e.get('severity')})")

    with st.form(key=f"form-{audit_id}"):
        reviewer = st.text_input("Reviewer", value="pilot_user")
        decision = st.selectbox("Decision", ["approve", "approve_with_edit", "reject"])
        comment = st.text_area("Comment (optional)")
        edited = None
        chosen_candidate = None
        if resp.get("source") == "ml" and item.get("model_info"):
            candidates = item["model_info"].get("candidates", [])
            if candidates:
                choice_idx = st.radio("Pick ML candidate (optional)", [f"{i+1}" for i in range(len(candidates))], index=0)
                chosen_candidate = candidates[int(choice_idx)-1]
                st.write("Selected:", chosen_candidate)
        if decision == "approve_with_edit":
            # default to chosen candidate or suggested rewrite
            default_text = chosen_candidate or resp.get("rewrite")
            edited = st.text_area("Edited rewrite", value=default_text)
        submitted = st.form_submit_button("Submit decision")
        if submitted:
            if decision == "approve":
                save_review(audit_id, "approve", reviewer, comment, chosen_candidate=chosen_candidate)
            elif decision == "reject":
                save_review(audit_id, "reject", reviewer, comment)
            else:
                save_review(audit_id, "approve_with_edit", reviewer, comment, edited_rewrite=edited)
            st.success(f"Recorded {decision} for {audit_id}")
            st.experimental_rerun()
