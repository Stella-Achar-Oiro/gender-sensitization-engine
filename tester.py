"""
JuaKazi Gender Bias Detection — External Tester
Clean interface for AI engineer testing and evaluation.

Run:  streamlit run tester.py
"""

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from eval.bias_detector import BiasDetector
from eval.models import Language
from api.rules_engine import apply_rules_on_spans, build_reason

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JuaKazi · Bias Tester",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .header-box {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 24px;
        color: white;
    }
    .header-box h1 { font-size: 2rem; margin: 0 0 4px 0; }
    .header-box p  { font-size: 0.95rem; margin: 0; opacity: 0.75; }

    .result-bias {
        background: #fff1f0;
        border-left: 5px solid #ff4d4f;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 16px;
    }
    .result-clean {
        background: #f6ffed;
        border-left: 5px solid #52c41a;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 16px;
    }
    .result-counter {
        background: #e6f7ff;
        border-left: 5px solid #1890ff;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 16px;
    }
    .verdict { font-size: 1.5rem; font-weight: 700; margin-bottom: 6px; }
    .subtext { font-size: 0.9rem; color: #555; }

    .edit-row {
        background: #fffbe6;
        border: 1px solid #ffe58f;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .warn-row {
        background: #f9f0ff;
        border: 1px solid #d3adf7;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .corrected-text {
        background: #f0f9ff;
        border: 1px solid #91d5ff;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 1rem;
        margin-top: 12px;
    }
    .history-item {
        border-bottom: 1px solid #f0f0f0;
        padding: 8px 0;
        font-size: 0.85rem;
    }
    .tag-bias    { background:#ff4d4f; color:white; border-radius:4px; padding:2px 8px; font-size:0.75rem; }
    .tag-clean   { background:#52c41a; color:white; border-radius:4px; padding:2px 8px; font-size:0.75rem; }
    .tag-counter { background:#1890ff; color:white; border-radius:4px; padding:2px 8px; font-size:0.75rem; }
    .tag-warn    { background:#fa8c16; color:white; border-radius:4px; padding:2px 8px; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)

# ── Cached detector ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading bias detection engine…")
def load_detector():
    return BiasDetector()

# ── Language mapping ──────────────────────────────────────────────────────────
LANG_OPTIONS = {
    "English":  Language.ENGLISH,
    "Swahili":  Language.SWAHILI,
    "French":   Language.FRENCH,
    "Gikuyu":   Language.GIKUYU,
}

LANG_STATS = {
    "English": {"rules": 538, "f1": 0.786, "tier": "Pre-Bronze", "status": "Production"},
    "Swahili": {"rules": 218, "f1": 0.611, "tier": "Gold (sample count)", "status": "Production"},
    "French":  {"rules": 78,  "f1": 0.542, "tier": "Pre-Bronze", "status": "Beta"},
    "Gikuyu":  {"rules": 1240,"f1": 0.352, "tier": "Bronze (sample count)", "status": "Production"},
}

EXAMPLE_SENTENCES = {
    "English": [
        "The chairman will lead the meeting today.",
        "Each student must submit his homework on time.",
        "The nurse should check her patients regularly.",
        "The female engineer designed the bridge.",
        "The person manages the team effectively.",
    ],
    "Swahili": [
        "Daktari wa kiume alipima mgonjwa.",
        "Mwalimu anafundisha darasa lake.",
        "Mwanamke ni nyumba.",
        "Mwanamke mhandisi alitengeneza daraja.",
    ],
    "French": [
        "Le président dirigera la réunion.",
        "Le policier a arrêté le suspect.",
        "Elle est une excellente infirmière.",
        "La directrice a pris la décision finale.",
    ],
    "Gikuyu": [
        "Mũrũgamĩrĩri ũcio nĩ mũndũ mũrũme.",
        "Mũrutani ũcio nĩ mũndũ mwega.",
    ],
}

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <h1>🔍 JuaKazi Gender Bias Tester</h1>
    <p>Enter any sentence to test whether the model detects gender bias — and see the suggested correction.</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    lang_name = st.selectbox("Language", list(LANG_OPTIONS.keys()))
    language = LANG_OPTIONS[lang_name]
    stats = LANG_STATS[lang_name]

    st.markdown("---")
    st.markdown("### 📊 Model Info")
    st.markdown(f"**Rules loaded:** {stats['rules']:,}")
    st.markdown(f"**F1 score:** {stats['f1']:.3f}")
    st.markdown(f"**AIBRIDGE tier:** {stats['tier']}")
    st.markdown(f"**Status:** {stats['status']}")

    st.markdown("---")
    st.markdown("### 💡 Try an example")
    for ex in EXAMPLE_SENTENCES[lang_name]:
        if st.button(ex[:55] + ("…" if len(ex) > 55 else ""), key=ex, use_container_width=True):
            st.session_state["prefill"] = ex

    st.markdown("---")
    st.markdown("### 📜 Test History")
    if st.session_state.history:
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
        for item in reversed(st.session_state.history[-20:]):
            tag_class = {
                "BIAS":    "tag-bias",
                "CLEAN":   "tag-clean",
                "COUNTER": "tag-counter",
                "WARN":    "tag-warn",
            }.get(item["verdict"], "tag-clean")
            st.markdown(
                f'<div class="history-item">'
                f'<span class="{tag_class}">{item["verdict"]}</span> '
                f'<b>[{item["lang"]}]</b> {item["text"][:60]}{"…" if len(item["text"]) > 60 else ""}'
                f'<br><small style="color:#999">{item["time"]}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No tests run yet.")

# ── Main panel ────────────────────────────────────────────────────────────────
detector = load_detector()

prefill = st.session_state.pop("prefill", "")
input_text = st.text_area(
    "Enter text to test",
    value=prefill,
    height=120,
    placeholder=f"Type a sentence in {lang_name}…",
    label_visibility="collapsed",
)

col_btn, col_clear = st.columns([1, 5])
with col_btn:
    run = st.button("▶ Run Test", type="primary", use_container_width=True)
with col_clear:
    if st.button("✕ Clear", use_container_width=False):
        st.session_state["prefill"] = ""
        st.rerun()

# ── Run detection ─────────────────────────────────────────────────────────────
if run and input_text.strip():
    text = input_text.strip()

    with st.spinner("Analysing…"):
        result = detector.detect_bias(text, language)
        corrected, applied_edits, matched_count, skipped = apply_rules_on_spans(
            text, language.value
        )
        reason = build_reason("rules", applied_edits, skipped)

    has_counter  = bool(result.counter_stereotype_detected) if hasattr(result, "counter_stereotype_detected") else False
    has_derog    = any(e.get("bias_label") == "derogation" for e in result.detected_edits)
    has_bias     = result.has_bias_detected
    has_warn     = bool(result.warn_edits)

    # Determine overall verdict
    if has_counter:
        verdict = "COUNTER"
    elif has_bias:
        verdict = "BIAS"
    elif has_warn:
        verdict = "WARN"
    else:
        verdict = "CLEAN"

    # ── Verdict card ─────────────────────────────────────────────────────────
    if verdict == "BIAS":
        box_class = "result-bias"
        icon = "⚠️"
        headline = "Gender bias detected"
        subtext = "This sentence contains gendered language that may reinforce stereotypes."
    elif verdict == "COUNTER":
        box_class = "result-counter"
        icon = "✅"
        headline = "Counter-stereotype detected"
        subtext = "This sentence challenges traditional gender roles — no correction applied."
    elif verdict == "WARN":
        box_class = "result-counter"
        icon = "ℹ️"
        headline = "Informational flag only"
        subtext = "Gendered language noted for awareness — no correction required."
    else:
        box_class = "result-clean"
        icon = "✅"
        headline = "No gender bias detected"
        subtext = "This sentence does not trigger any bias rules."

    st.markdown(
        f'<div class="{box_class}">'
        f'<div class="verdict">{icon} {headline}</div>'
        f'<div class="subtext">{subtext}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Edits ─────────────────────────────────────────────────────────────────
    if result.detected_edits:
        st.markdown("#### 🏷️ Flagged terms")
        for edit in result.detected_edits:
            cat  = edit.get("stereotype_category", edit.get("tags", "—"))
            sev  = edit.get("severity", "replace")
            st.markdown(
                f'<div class="edit-row">'
                f'<b>"{edit["from"]}"</b> → <b>"{edit["to"]}"</b>'
                f'&nbsp;&nbsp;<small>category: {cat} | severity: {sev}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if result.warn_edits:
        st.markdown("#### ℹ️ Advisory flags (no correction applied)")
        for edit in result.warn_edits:
            cat = edit.get("stereotype_category", edit.get("tags", "—"))
            st.markdown(
                f'<div class="warn-row">'
                f'<b>"{edit["from"]}"</b>'
                f'&nbsp;&nbsp;<small>category: {cat} | severity: warn only</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Correction ────────────────────────────────────────────────────────────
    if corrected != text:
        st.markdown("#### ✏️ Suggested correction")
        st.markdown(
            f'<div class="corrected-text">{corrected}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Reason: {reason}")
        if skipped:
            skipped_terms = [s["term"] for s in skipped]
            st.caption(f"Skipped (context-protected): {', '.join(skipped_terms)}")
    elif has_bias:
        st.info("Bias detected but no automatic correction available for this term. Manual review recommended.")

    # ── Metadata ──────────────────────────────────────────────────────────────
    with st.expander("🔬 Full detection details"):
        st.json({
            "language":          lang_name,
            "has_bias_detected": has_bias,
            "verdict":           verdict,
            "detected_edits":    result.detected_edits,
            "warn_edits":        result.warn_edits,
            "applied_correction": corrected if corrected != text else None,
            "matched_rules":     matched_count,
            "skipped_context":   skipped,
            "reason":            reason,
        })

    # ── Add to history ────────────────────────────────────────────────────────
    st.session_state.history.append({
        "text":    text,
        "lang":    lang_name,
        "verdict": verdict,
        "time":    datetime.now().strftime("%H:%M:%S"),
    })

elif run and not input_text.strip():
    st.warning("Please enter some text before running the test.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "JuaKazi Gender Sensitization Engine · Rules-based detection · "
    "EN F1=0.786 | SW F1=0.611 | FR F1=0.542 | KI F1=0.352"
)
