"""
JuaKazi Gender Sensitization Engine — Gradio interface.
Deploy to HuggingFace Spaces (Gradio SDK).
"""

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

RULES_DIR = Path(__file__).resolve().parent / "rules"
detector = BiasDetector(rules_dir=RULES_DIR)

LANGS = {
    "English":  ("en", Language.ENGLISH),
    "Swahili":  ("sw", Language.SWAHILI),
    "French":   ("fr", Language.FRENCH),
    "Gikuyu":   ("ki", Language.GIKUYU),
}

METRICS = {
    "en": dict(f1=0.786, precision=1.000, recall=0.647, tier="Pre-Bronze",   samples=66),
    "sw": dict(f1=0.885, precision=0.958, recall=0.823, tier="Gold (sample count)", samples=51_419),
    "fr": dict(f1=0.542, precision=1.000, recall=0.371, tier="Pre-Bronze",   samples=50),
    "ki": dict(f1=0.352, precision=0.926, recall=0.217, tier="Bronze (sample count)", samples=11_848),
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

    if has_bias:
        verdict = f"🔴 **Gender bias detected** — {len(result.detected_edits)} rule(s) matched"
    elif has_warn:
        verdict = f"🟡 **Advisory** — {len(result.warn_edits)} gendered term(s) noted (no correction applied)"
    else:
        verdict = "🟢 **No bias detected** — text passes all rules in the current lexicon"

    # Detection detail
    detail_lines = []
    for edit in result.detected_edits:
        orig = getattr(edit, "original", getattr(edit, "biased_term", "?"))
        repl = getattr(edit, "replacement", getattr(edit, "suggested_replacement", "—"))
        label = getattr(edit, "label", "stereotype")
        cat = getattr(edit, "stereotype_category", "—")
        sev = getattr(edit, "severity", "replace")
        detail_lines.append(f'• **"{orig}"** → **"{repl}"**  |  label: `{label}`  category: `{cat}`  severity: `{sev}`')
    for edit in result.warn_edits:
        orig = getattr(edit, "original", getattr(edit, "biased_term", "?"))
        cat = getattr(edit, "stereotype_category", "—")
        detail_lines.append(f'• **"{orig}"** (advisory, no replacement)  |  category: `{cat}`')
    if not detail_lines:
        detail_lines = ["No rules triggered."]

    detail_md = "\n".join(detail_lines)

    # Correction output
    if n_replaced > 0 and corrected != text.strip():
        correction_md = f"**Corrected text:**\n\n> {corrected}\n\n✓ {n_replaced} replacement(s) applied"
        if reason:
            correction_md += f"\n\n*Reason: {reason}*"
    elif has_bias:
        correction_md = "Bias detected but no automatic correction available. Manual review recommended."
    else:
        correction_md = "No correction needed."

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


with gr.Blocks(title="JuaKazi · Gender Bias Tester") as demo:
    gr.Markdown("# JuaKazi · Gender Bias Detection & Correction")
    gr.Markdown(
        "Real Python engine · Rules-based · 4 languages · AIBRIDGE-compliant · "
        "[GitHub](https://github.com/Stella-Achar-Oiro/gender-sensitization-engine)"
    )

    with gr.Row():
        with gr.Column(scale=1):
            lang_dd = gr.Dropdown(
                choices=list(LANGS.keys()),
                value="English",
                label="Language",
            )
            text_in = gr.Textbox(
                lines=4,
                placeholder="Type or paste a sentence to analyse…",
                label="Input text",
            )
            analyse_btn = gr.Button("Analyse", variant="primary")
            gr.Markdown("**Example sentences** (click to load):")
            example_dd = gr.Dropdown(
                choices=EXAMPLES["English"],
                value=None,
                label="",
                show_label=False,
            )

        with gr.Column(scale=2):
            verdict_out = gr.Markdown(label="Verdict")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Detection detail")
                    detect_out = gr.Markdown()
                with gr.Column():
                    gr.Markdown("#### Correction")
                    correct_out = gr.Markdown()

    lang_dd.change(
        fn=lambda lang: gr.Dropdown(choices=EXAMPLES.get(lang, []), value=None),
        inputs=lang_dd,
        outputs=example_dd,
    )
    example_dd.change(
        fn=lambda ex: ex or "",
        inputs=example_dd,
        outputs=text_in,
    )

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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.post("/rewrite")(_rewrite_handler)
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
