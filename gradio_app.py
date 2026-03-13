"""
JuaKazi Gender Sensitization Engine — Gradio interface.
Deploy to HuggingFace Spaces (Gradio SDK).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from eval.bias_detector import BiasDetector
from eval.models import Language
from api.rules_engine import apply_rules_on_spans, build_reason

REGISTRY_PATH = Path(__file__).resolve().parent / "eval" / "results" / "model_registry.json"

RULES_DIR = Path(__file__).resolve().parent / "rules"
detector = BiasDetector(rules_dir=RULES_DIR, enable_ml_fallback=True, ml_threshold=0.56)

LANGS = {
    "English":  ("en", Language.ENGLISH),
    "Swahili":  ("sw", Language.SWAHILI),
    "French":   ("fr", Language.FRENCH),
    "Gikuyu":   ("ki", Language.GIKUYU),
}

METRICS = {
    "en": dict(f1=0.885, precision=1.000, recall=0.794, tier="Pre-Bronze", samples=66),
    "sw": dict(f1=0.816, precision=0.735, recall=0.918, tier="Gold (sample count)", samples=64_723),
    "fr": dict(f1=0.793, precision=1.000, recall=0.657, tier="Pre-Bronze", samples=50),
    "ki": dict(f1=0.368, precision=0.916, recall=0.231, tier="Bronze (sample count)", samples=11_848),
}

EXAMPLES = {
    "English": [
        "The chairman will lead the meeting today.",
        "Each student must submit his homework on time.",
        "Women cannot be good leaders.",
        "She is just a housewife — she wouldn't understand.",
        "The female engineer designed the bridge.",
        "The nurse checked her patients carefully.",
        "The fireman saved the cat.",
        "Ask the waitress for the menu.",
        "A working mother neglects her children.",
        "She was elected CEO by unanimous vote.",
        "The stay-at-home dad managed the household beautifully.",
        "The doctor examined the patient carefully.",
    ],
    "Swahili": [
        "Mwanamke ni nyumba.",
        "Msichana hawezi kuongoza timu.",
        "Daktari wa kiume alipima mgonjwa.",
        "Mwanamke mhandisi alitengeneza daraja.",
        "Mama wa nyumbani alipika chakula.",
        "Kijakazi alifanya kazi nzuri.",
    ],
    "French": [
        "Le président dirigera la réunion.",
        "Le policier a arrêté le suspect.",
        "La directrice a pris la décision finale.",
        "L'infirmière a soigné les patients.",
        "Le pompier a sauvé l'enfant.",
    ],
    "Gikuyu": [
        "Mũrũgamĩrĩri ũcio nĩ mũndũ mũrũme.",
        "Mwarimu ũcio nĩ mũtumia.",
        "Mũrutani ũcio nĩ mũndũ mwega.",
    ],
}


def analyse(text: str, lang_name: str) -> tuple[str, str, str]:
    if not text.strip():
        return "⚠️ Please enter some text.", "", ""

    lang_code, lang_enum = LANGS[lang_name]
    m = METRICS[lang_code]

    # Detection
    try:
        result = detector.detect_bias(text.strip(), lang_enum)
    except Exception as e:
        return f"❌ Detection error: {e}", "", ""

    # Correction
    try:
        corrected, edits, n_replaced, skipped = apply_rules_on_spans(text.strip(), lang_code)
        reason = build_reason(source="rules", edits=edits, skipped=skipped)
    except Exception as e:
        corrected, edits, n_replaced, skipped, reason = text, [], 0, [], str(e)

    # Verdict
    has_bias = result.has_bias_detected
    has_warn = len(result.warn_edits) > 0
    ml_edits = [e for e in result.warn_edits if e.get("severity") == "ml_fallback"]
    rules_warn = [e for e in result.warn_edits if e.get("severity") != "ml_fallback"]

    if has_bias:
        verdict = f"🔴 **Gender bias detected** — {len(result.detected_edits)} rule(s) matched"
    elif ml_edits:
        verdict = f"🟠 **Implicit bias detected (ML)** — {len(ml_edits)} pattern(s) flagged by sw-bias-classifier-v2"
    elif has_warn:
        verdict = f"🟡 **Advisory** — {len(rules_warn)} gendered term(s) noted (no correction applied)"
    else:
        verdict = "🟢 **No bias detected** — text passes all rules and ML classifier"

    # Detection detail
    detail_lines = []
    for edit in result.detected_edits:
        orig = edit.get("from", "?")
        repl = edit.get("to", "—")
        label = edit.get("bias_type", "stereotype")
        cat = edit.get("stereotype_category", "—")
        sev = edit.get("severity", "replace")
        reason_short = f"Use gender-neutral «{repl}»"
        detail_lines.append(f'• **"{orig}"** → **"{repl}"**  |  label: `{label}`  category: `{cat}`  severity: `{sev}`  \n  *Reason: {reason_short}*')
    for edit in rules_warn:
        orig = edit.get("from", "?")
        cat = edit.get("stereotype_category", "—")
        reason_w = edit.get("reason", "Advisory — review recommended")
        detail_lines.append(f'• **"{orig}"** (advisory, no replacement)  |  category: `{cat}`  \n  *Reason: {reason_w}*')
    for edit in ml_edits:
        score = edit.get("confidence", "—")
        reason_ml = edit.get("reason", "Implicit gender bias pattern detected by ML model")
        detail_lines.append(f'• 🤖 **ML classifier flagged this sentence**  |  confidence: `{score}`  needs_review: `true`  \n  *{reason_ml}*')
    if not detail_lines:
        detail_lines = ["No rules or ML patterns triggered."]

    detail_md = "\n".join(detail_lines)

    # Skipped context (when ContextChecker blocked correction)
    if skipped:
        skip_lines = [f"• «{s.get('term', '?')}» — {s.get('reason', 'context')}" for s in skipped]
        detail_md += "\n\n**Skipped (context):**\n" + "\n".join(skip_lines)

    # Correction output
    if n_replaced > 0 and corrected != text.strip():
        correction_md = f"**Corrected text:**\n\n> {corrected}\n\n✓ {n_replaced} replacement(s) applied"
        if reason:
            correction_md += f"\n\n*Reason: {reason}*"
    elif has_bias:
        correction_md = "Bias detected but no automatic correction available. Manual review recommended."
        if reason:
            correction_md += f"\n\n*Reason: {reason}*"
    else:
        correction_md = "No correction needed."
        if reason and (skipped or not has_bias):
            correction_md += f"\n\n*Reason: {reason}*"

    # Metrics footer
    metrics_md = (
        f"**Model metrics ({lang_name}):** "
        f"F1 `{m['f1']:.3f}` · Precision `{m['precision']:.3f}` · Recall `{m['recall']:.3f}` · "
        f"Samples `{m['samples']:,}` · Tier: **{m['tier']}**"
    )

    return f"{verdict}\n\n{metrics_md}", detail_md, correction_md


# --- REST API (mounted onto Gradio's FastAPI instance) ---

class _RewriteReq(BaseModel):
    id: str
    lang: str
    text: str
    region_dialect: str = None
    flags: list = None


def _rewrite_handler(req: _RewriteReq):
    rewritten, edits, matched, skipped = apply_rules_on_spans(
        req.text, req.lang, flags=req.flags or None
    )
    source = "rules"
    reason = build_reason(source, edits, skipped)
    has_bias_detected = any(e.get("severity") == "replace" for e in edits)
    confidence = 0.85 if edits else 0.95
    return {
        "id": req.id,
        "original_text": req.text,
        "rewrite": rewritten,
        "edits": edits,
        "confidence": confidence,
        "needs_review": len(edits) == 0,
        "source": source,
        "reason": reason,
        "semantic_score": None,
        "skipped_context": skipped or None,
        "has_bias_detected": has_bias_detected,
    }


def load_registry_table() -> tuple[list[list], str]:
    """Returns (rows_for_dataframe, last_updated_str)."""
    if not REGISTRY_PATH.exists():
        return [], "Registry not found"
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        reg = json.load(f)
    rows = []
    for v in reversed(reg.get("versions", [])):
        m = v.get("metrics", {})
        rows.append([
            v.get("tag", ""),
            v.get("timestamp", "")[:10],
            v.get("git_commit") or "—",
            f"{m.get('en', {}).get('f1', 0):.3f}",
            f"{m.get('sw', {}).get('f1', 0):.3f}",
            f"{m.get('fr', {}).get('f1', 0):.3f}",
            f"{m.get('ki', {}).get('f1', 0):.3f}",
            v.get("notes", ""),
        ])
    ts = reg["versions"][-1]["timestamp"][:16].replace("T", " ") if reg.get("versions") else "—"
    return rows, f"Last snapshot: {ts}"


def sidebar_metrics(lang_name: str) -> str:
    code = LANGS[lang_name][0]
    m = METRICS[code]
    bronze = 0.75
    f1_bar = min(int(m['f1'] / 1.0 * 10), 10)
    bar_filled = "█" * f1_bar + "░" * (10 - f1_bar)
    status_color = "#4ade80"
    return (
        f"<div style='"
        f"background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);"
        f"border:1px solid rgba(255,255,255,0.15);border-radius:12px;"
        f"padding:16px 18px;margin-top:8px;font-family:monospace;font-size:0.85rem;color:#e2e8f0'>"
        f"<div style='font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;"
        f"color:#94a3b8;margin-bottom:10px'>Model · {lang_name}</div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>F1</span>"
        f"<span style='color:{status_color};font-weight:700'>{m['f1']:.3f}</span></div>"
        f"<div style='font-size:0.75rem;color:#64748b;margin:2px 0'>{bar_filled}</div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>Precision</span>"
        f"<span style='color:#e2e8f0'>{m['precision']:.3f}</span></div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>Recall</span>"
        f"<span style='color:#e2e8f0'>{m['recall']:.3f}</span></div>"
        f"<div style='display:flex;justify-content:space-between;margin:6px 0 2px'>"
        f"<span style='color:#94a3b8'>Samples</span>"
        f"<span style='color:#e2e8f0'>{m['samples']:,}</span></div>"
        f"<div style='margin-top:8px;padding:4px 8px;border-radius:6px;"
        f"background:rgba(99,102,241,0.25);text-align:center;"
        f"font-size:0.75rem;color:#a5b4fc'>{m['tier']}</div>"
        f"</div>"
    )


CSS = """
/* JuaKazi · brand palette */
:root {
    --jk-bg:        #0d1117;
    --jk-surface:   rgba(255,255,255,0.06);
    --jk-border:    rgba(255,255,255,0.12);
    --jk-indigo:    #6366f1;
    --jk-indigo-lt: #818cf8;
    --jk-green:     #4ade80;
    --jk-red:       #f87171;
    --jk-amber:     #fbbf24;
    --jk-text:      #e2e8f0;
    --jk-muted:     #94a3b8;
}

/* Page background — let Gradio theme handle bg, only tint slightly */
.gradio-container { background: #0f1117 !important; color: #e2e8f0 !important; }

/* Glass card helper */
.glass {
    background: var(--jk-surface);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--jk-border);
    border-radius: 14px;
    padding: 20px 22px;
}

/* Header */
.jk-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 60%, #1e3a5f 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 16px;
    padding: 28px 32px 22px;
    margin-bottom: 18px;
}
.jk-header h1 { font-size:1.9rem; color:#e2e8f0; margin:0 0 4px; font-weight:700; }
.jk-header p  { font-size:0.88rem; color:#94a3b8; margin:0; }

/* Verdict banners */
.verdict-bias    { border-left:4px solid #f87171; background:rgba(248,113,113,0.1);
                   border-radius:10px; padding:14px 18px; }
.verdict-clean   { border-left:4px solid #4ade80; background:rgba(74,222,128,0.08);
                   border-radius:10px; padding:14px 18px; }
.verdict-warn    { border-left:4px solid #fbbf24; background:rgba(251,191,36,0.08);
                   border-radius:10px; padding:14px 18px; }
.verdict-counter { border-left:4px solid #818cf8; background:rgba(129,140,248,0.1);
                   border-radius:10px; padding:14px 18px; }

/* Textbox */
textarea, input[type=text] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.13) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}
textarea:focus, input[type=text]:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* Primary / Analyse button */
button.primary, .analyse-btn button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: opacity 0.15s !important;
}
button.primary:hover, .analyse-btn button:hover { opacity: 0.88 !important; }

/* Example buttons */
.example-btn button {
    background: rgba(99,102,241,0.12) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 8px !important;
    color: #c7d2fe !important;
    font-size: 0.8rem !important;
    text-align: left !important;
    padding: 6px 10px !important;
    margin: 3px 0 !important;
    transition: background 0.12s !important;
}
.example-btn button:hover {
    background: rgba(99,102,241,0.25) !important;
}

/* Tabs: avoid overriding .tab-nav so Gradio’s tab clicks work; style via theme only */

/* Dataframe */
table { background: transparent !important; }
th { background: rgba(99,102,241,0.18) !important; color: #c7d2fe !important; font-size:0.8rem !important; }
td { color: #e2e8f0 !important; font-size:0.82rem !important; border-bottom:1px solid rgba(255,255,255,0.06) !important; }

/* Section labels */
.section-label {
    font-size:0.72rem; text-transform:uppercase; letter-spacing:1px;
    color:#94a3b8; margin-bottom:6px; font-weight:600;
}
"""

_theme = gr.themes.Soft(primary_hue=gr.themes.colors.indigo)

with gr.Blocks(title="JuaKazi · Gender Bias Detection") as demo:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div class="jk-header">
        <h1>JuaKazi · Gender Bias Detection &amp; Correction</h1>
        <p>Rules-based · 4 East African languages · AIBRIDGE-compliant ·
           <a href="https://github.com/Stella-Achar-Oiro/gender-sensitization-engine"
              style="color:#818cf8">GitHub</a></p>
    </div>
    """)

    with gr.Row(equal_height=False):

        # ── Sidebar ───────────────────────────────────────────────────────────
        with gr.Column(scale=1, min_width=220):
            lang_dd = gr.Dropdown(
                label="Language",
                choices=list(LANGS.keys()),
                value="English",
                interactive=True,
            )
            metrics_html = gr.HTML(sidebar_metrics("English"))

        # ── Main content ──────────────────────────────────────────────────────
        with gr.Column(scale=3):
            with gr.Tabs() as tabs:

                # Tab 1 — Analyse (id for programmatic switch)
                with gr.Tab("Analyse", id="analyse"):
                    text_in = gr.Textbox(
                        lines=4,
                        placeholder="Type or paste a sentence to analyse…",
                        label="Input text",
                        show_label=False,
                    )
                    example_dd = gr.Dropdown(
                        choices=EXAMPLES["English"],
                        value=None,
                        label="Sample sentences (select to load)",
                        interactive=True,
                    )
                    analyse_btn = gr.Button("Analyse", variant="primary", size="lg", elem_classes=["analyse-btn"])

                    verdict_out = gr.Markdown()

                    with gr.Row():
                        with gr.Column():
                            gr.HTML('<div class="section-label">Detection detail</div>')
                            detect_out = gr.Markdown()
                        with gr.Column():
                            gr.HTML('<div class="section-label">Correction</div>')
                            correct_out = gr.Markdown()

                # Tab 2 — Model Versions
                with gr.Tab("Model Versions", id="versions"):
                    with gr.Row():
                        refresh_btn = gr.Button("Refresh", size="sm")
                        registry_ts = gr.Markdown()

                    versions_table = gr.Dataframe(
                        headers=["Tag", "Date", "Commit", "EN F1", "SW F1", "FR F1", "KI F1", "Notes"],
                        datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                        column_count=(8, "fixed"),
                        interactive=False,
                        label="",
                        wrap=True,
                    )

                    gr.HTML('<div class="section-label" style="margin-top:16px">F1 trend by version</div>')
                    trend_plot = gr.LinePlot(
                        value=None,
                        x="Version",
                        y="F1",
                        color="Language",
                        height=300,
                        label="F1 by version",
                    )

    # ── Helper: build trend dataframe ─────────────────────────────────────────
    def _trend_data(rows):
        import pandas as pd
        records = []
        for row in reversed(rows):  # rows are newest-first, reverse for chronological
            tag = row[0]
            for i, lang in enumerate(["EN", "SW", "FR", "KI"], start=3):
                try:
                    records.append({"Version": tag, "Language": lang, "F1": float(row[i])})
                except (ValueError, IndexError):
                    pass
        return pd.DataFrame(records) if records else pd.DataFrame(columns=["Version", "Language", "F1"])

    def refresh_versions():
        rows, ts = load_registry_table()
        return rows, ts, _trend_data(rows)

    # ── Wire language change: update metrics and example sentences ────────────
    def on_lang_change(lang):
        new_exs = EXAMPLES.get(lang, [])
        return sidebar_metrics(lang), gr.update(choices=new_exs, value=None)

    lang_dd.change(
        fn=on_lang_change,
        inputs=lang_dd,
        outputs=[metrics_html, example_dd],
    )

    # ── Wire example dropdown → populate textbox ──────────────────────────────
    example_dd.change(
        fn=lambda ex: ex or "",
        inputs=example_dd,
        outputs=text_in,
    )

    # ── Wire Analyse button and Enter in textbox ──────────────────────────────
    analyse_btn.click(
        fn=analyse,
        inputs=[text_in, lang_dd],
        outputs=[verdict_out, detect_out, correct_out],
    )
    text_in.submit(
        fn=analyse,
        inputs=[text_in, lang_dd],
        outputs=[verdict_out, detect_out, correct_out],
    )

    # ── Load versions on startup + refresh button ─────────────────────────────
    demo.load(fn=refresh_versions, outputs=[versions_table, registry_ts, trend_plot])
    refresh_btn.click(fn=refresh_versions, outputs=[versions_table, registry_ts, trend_plot])

# Mount /rewrite onto Gradio's own FastAPI app — no path conflicts
app = demo.app
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.post("/rewrite")(_rewrite_handler)

if __name__ == "__main__":
    import uvicorn
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=_theme, css=CSS)
