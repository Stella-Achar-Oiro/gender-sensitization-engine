"""JuaKazi UI — page layout only."""

import streamlit as st

from .components import (
    render_edits,
    render_header,
    render_meta,
    render_ml_candidates,
    render_review_form,
    render_skipped,
    render_stats_panel,
    render_text_comparison,
)
from .data import load_rewrites

st.set_page_config(page_title="JuaKazi", layout="wide")
st.title("JuaKazi")
render_stats_panel()

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
