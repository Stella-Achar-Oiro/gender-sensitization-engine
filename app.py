"""
JuaKazi Gender Sensitization Engine — HuggingFace Spaces entry point.

Runs the real Python detection + correction engine (not a JS approximation).
Deploy to HuggingFace Spaces (Streamlit SDK) with requirements_hf.txt.

Local dev:  streamlit run app.py
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ── Import guard — surface errors in UI instead of silent crash ───────────────
_import_error = None
try:
    from eval.bias_detector import BiasDetector
    from eval.models import Language
    from api.rules_engine import apply_rules_on_spans, build_reason
except Exception as _e:
    _import_error = traceback.format_exc()

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JuaKazi · Gender Bias Tester",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

if _import_error:
    st.error("**Startup error — engine failed to load:**")
    st.code(_import_error)
    st.stop()

# ── Language map ──────────────────────────────────────────────────────────────
LANGS = {
    "English":  ("en", Language.ENGLISH),
    "Swahili":  ("sw", Language.SWAHILI),
    "French":   ("fr", Language.FRENCH),
    "Gikuyu":   ("ki", Language.GIKUYU),
}

# From run_evaluation.py (post–lexicon fixes: EN slim, SW+FR+KI additions)
METRICS = {
    "en": {"f1": 0.847, "precision": 1.000, "recall": 0.735, "tier": "Pre-Bronze",   "samples": 66},
    "sw": {"f1": 0.772, "precision": 0.732, "recall": 0.817, "tier": "Gold (sample count)", "samples": 64_723},
    "fr": {"f1": 0.571, "precision": 1.000, "recall": 0.400, "tier": "Pre-Bronze",   "samples": 50},
    "ki": {"f1": 0.352, "precision": 0.926, "recall": 0.217, "tier": "Bronze (sample count)", "samples": 11_848},
}

EXAMPLES = {
    "en": [
        "The chairman will lead the meeting today.",
        "Each student must submit his homework on time.",
        "Women cannot be good leaders.",
        "She is just a housewife — she wouldn't understand.",
        "The female engineer designed the bridge.",
        "The nurse checked her patients carefully.",
    ],
    "sw": [
        "Mwanamke ni nyumba.",
        "Msichana hawezi kuongoza timu.",
        "Daktari wa kiume alipima mgonjwa.",
        "Mwanamke mhandisi alitengeneza daraja.",
    ],
    "fr": [
        "Le président dirigera la réunion.",
        "Le policier a arrêté le suspect.",
        "La directrice a pris la décision finale.",
    ],
    "ki": [
        "Mũrũgamĩrĩri ũcio nĩ mũndũ mũrũme.",
        "Mwarimu ũcio nĩ mũtumia.",
        "Mũrutani ũcio nĩ mũndũ mwega.",
    ],
}

# ── Cached detector ───────────────────────────────────────────────────────────
RULES_DIR = Path(__file__).resolve().parent / "rules"

@st.cache_resource
def get_detector():
    return BiasDetector(rules_dir=RULES_DIR)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://i.postimg.cc/L5mk9h1P/juakazi.png", width=140)
    st.markdown("### JuaKazi · Bias Engine")
    st.caption("Detection & Correction · 4 Languages")
    st.divider()

    lang_name = st.radio("Language", list(LANGS.keys()), index=0)
    lang_code, lang_enum = LANGS[lang_name]
    m = METRICS[lang_code]

    st.divider()
    st.markdown("**Model metrics**")
    c1, c2 = st.columns(2)
    c1.metric("F1", f"{m['f1']:.3f}")
    c2.metric("Precision", f"{m['precision']:.3f}")
    c1.metric("Recall", f"{m['recall']:.3f}")
    c2.metric("Samples", f"{m['samples']:,}")
    st.caption(f"AIBRIDGE tier: **{m['tier']}**")
    st.divider()

    st.markdown("**Example sentences**")
    chosen_ex = None
    for ex in EXAMPLES[lang_code]:
        if st.button(ex[:55] + ("…" if len(ex) > 55 else ""), key=ex, use_container_width=True):
            chosen_ex = ex

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("""
<h2 style='margin:0 0 4px 0'>Gender Bias Detection & Correction</h2>
<p style='color:#6b7280;margin:0 0 24px 0'>
  Real Python engine · Rules-based · 2,059 lexicon rules · DEROGATION_PATTERNS
</p>
""", unsafe_allow_html=True)

default_text = chosen_ex or ""
text_input = st.text_area(
    "Enter text to analyse",
    value=default_text,
    height=120,
    placeholder=f"Type or paste a {lang_name} sentence…",
    label_visibility="collapsed",
)

col_a, col_b, _ = st.columns([1, 1, 5])
run_btn = col_a.button("Analyse", type="primary", use_container_width=True)
col_b.button("Clear", on_click=lambda: None, use_container_width=True)

if run_btn and text_input.strip():
    detector = get_detector()
    text = text_input.strip()

    # ── Detection ──────────────────────────────────────────────────────────────
    try:
        result = detector.detect_bias(text, lang_enum)
    except Exception as e:
        st.error(f"Detection error: {e}")
        st.stop()

    # ── Correction ─────────────────────────────────────────────────────────────
    try:
        corrected, edits, n_replaced, skipped = apply_rules_on_spans(text, lang_code)
        reason = build_reason(source="rules", edits=edits, skipped=skipped)
    except Exception as e:
        corrected, edits, n_replaced, skipped, reason = text, [], 0, [], str(e)

    # ── Verdict banner ─────────────────────────────────────────────────────────
    has_bias = result.has_bias_detected
    has_warn = len(result.warn_edits) > 0

    if has_bias:
        st.error(f"**Gender bias detected** — {len(result.detected_edits)} rule(s) matched")
    elif has_warn:
        st.warning(f"**Advisory** — {len(result.warn_edits)} gendered term(s) noted (no correction)")
    else:
        st.success("**No bias detected** — text passes all rules in the current lexicon")

    # ── Two-column result ──────────────────────────────────────────────────────
    det_col, cor_col = st.columns(2)

    with det_col:
        st.markdown("#### Detection")
        if result.detected_edits:
            for edit in result.detected_edits:
                orig = getattr(edit, "original", getattr(edit, "biased_term", "?"))
                repl = getattr(edit, "replacement", getattr(edit, "suggested_replacement", "—"))
                label = getattr(edit, "label", "stereotype")
                cat = getattr(edit, "stereotype_category", "—")
                sev = getattr(edit, "severity", "replace")
                with st.expander(f'"{orig}" → "{repl}"', expanded=True):
                    st.markdown(f"**Label:** `{label}`  \n**Category:** `{cat}`  \n**Severity:** `{sev}`")
        elif result.warn_edits:
            for edit in result.warn_edits:
                orig = getattr(edit, "original", getattr(edit, "biased_term", "?"))
                cat = getattr(edit, "stereotype_category", "—")
                with st.expander(f'"{orig}" (advisory)', expanded=True):
                    st.markdown(f"**Category:** `{cat}`  \n**Severity:** `warn` — no replacement")
        else:
            st.info("No rules triggered.")

    with cor_col:
        st.markdown("#### Correction")
        if n_replaced > 0 and corrected != text:
            st.success(corrected)
            st.caption(f"✓ {n_replaced} replacement(s) applied")
            if reason:
                st.caption(f"Reason: {reason}")
            st.code(corrected, language=None)
        elif has_bias:
            st.warning("Bias detected but no automatic correction available.  \nManual review recommended.")
        else:
            st.info("No correction needed.")

    # ── Debug detail ───────────────────────────────────────────────────────────
    with st.expander("Engine detail"):
        st.json({
            "language": lang_name,
            "has_bias_detected": result.has_bias_detected,
            "detected_edits": len(result.detected_edits),
            "warn_edits": len(result.warn_edits),
            "correction_replacements": n_replaced,
            "corrected_text": corrected,
            "f1": m["f1"],
            "tier": m["tier"],
        })

elif run_btn:
    st.warning("Please enter some text first.")
