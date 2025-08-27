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
    # newest first
    return list(reversed(items))

def save_review(audit_id, action, reviewer, comment="", edited_rewrite=None):
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
    with open(REVIEWS, "a", encoding="utf-8") as f:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")

st.title("JuaKazi Review UI (Week 1)")
rewrites = load_rewrites()

for item in rewrites[:50]:
    req, resp = item["request"], item["response"]
    audit_id = item.get("audit_id")
    st.markdown("---")
    st.write(f"**Audit ID:** {audit_id}")
    st.write(f"**Lang:** {req['lang']}")
    st.write("**Original:**", req["text"])
    st.write("**Suggested rewrite:**", resp["rewrite"])
    for e in resp["edits"]:
        st.write(f"- `{e['from']}` → `{e['to']}` | severity: **{e['severity']}**, tags: {e['tags']}")
        if e.get("example", {}).get("biased"):
            st.caption(f"ex: {e['example']['biased']} → {e['example']['neutral']}")
        if e.get("alternatives"):
            st.caption(f"alternatives: {', '.join([a for a in e['alternatives'] if a])}")

    with st.form(key=f"form-{audit_id}"):
        reviewer = st.text_input("Reviewer", value="pilot_user")
        decision = st.selectbox("Decision", ["approve", "approve_with_edit", "reject"])
        comment = st.text_area("Comment (optional)")
        edited = None
        if decision == "approve_with_edit":
            edited = st.text_area("Edited rewrite", value=resp["rewrite"])
        submitted = st.form_submit_button("Submit decision")
        if submitted:
            save_review(audit_id, decision, reviewer, comment, edited)
            st.success(f"Recorded {decision} for {audit_id}")
