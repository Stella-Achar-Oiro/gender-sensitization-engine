"""
JuaKazi Gender Sensitization Engine — Gradio interface.
Deploy to HuggingFace Spaces (Gradio SDK).
"""

import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so 'core', 'api', 'eval' resolve on HF Space.
_app_dir = Path(__file__).resolve().parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))
os.chdir(str(_app_dir))  # ensure cwd = /app so relative file lookups work

_ML_MODEL_ID = os.environ.get("JUAKAZI_ML_MODEL", "juakazike/sw-bias-classifier-v2")
_ML_MODEL_SHORT = _ML_MODEL_ID.split("/")[-1]  # e.g. "sw-bias-classifier-v3"

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from eval.bias_detector import BiasDetector
from eval.models import Language
from api.rules_engine import apply_rules_on_spans, build_reason

REGISTRY_PATH = Path(__file__).resolve().parent / "eval" / "results" / "model_registry.json"

RULES_DIR = Path(__file__).resolve().parent / "rules"
detector_rules = BiasDetector(rules_dir=RULES_DIR, enable_ml_fallback=False)
_detector_ml = None  # lazy-loaded on first ML request

def _get_ml_detector():
    global _detector_ml
    if _detector_ml is None:
        _detector_ml = BiasDetector(rules_dir=RULES_DIR, enable_ml_fallback=True, ml_threshold=0.56)
    return _detector_ml

LANGS = {
    "English":  ("en", Language.ENGLISH),
    "Swahili":  ("sw", Language.SWAHILI),
    "French":   ("fr", Language.FRENCH),
    "Gikuyu":   ("ki", Language.GIKUYU),
    "Hausa":    ("ha", Language.HAUSA),
    "Zulu":     ("zu", Language.ZULU),
}

# Load live metrics from eval/metrics.json if available (written by eval/evaluator.py)
_METRICS_PATH = Path(__file__).parent / "eval" / "metrics.json"
_LIVE_METRICS: dict = {}
try:
    _LIVE_METRICS = json.loads(_METRICS_PATH.read_text())
except Exception:
    pass

def _m(code: str, field: str, fallback):
    return _LIVE_METRICS.get(code, {}).get(field, fallback)

# Known ML model metrics keyed by short model name.
# Add a new entry here whenever a new model version is pushed to HF.
_ML_KNOWN_METRICS = {
    "sw-bias-classifier-v1": {"f1": 0.854, "precision": 0.938, "recall": 0.784, "samples": 66_995},
    "sw-bias-classifier-v2": {"f1": 0.953, "precision": 0.940, "recall": 0.960, "samples": 66_995},
    "sw-bias-classifier-v3": {"f1": 0.871, "precision": 0.810, "recall": 0.942, "samples": 66_995},
}

def _ml_m(field: str, fallback):
    return _ML_KNOWN_METRICS.get(_ML_MODEL_SHORT, {}).get(field, fallback)

# Per-model metrics: model_key -> lang_code -> metrics dict
MODEL_METRICS = {
    "rules": {
        "label": "Rules-based (lexicon)",
        "description": "Deterministic lexicon rules across all 6 languages. High precision, no GPU needed.",
        "en": dict(f1=_m("en","f1",1.000), precision=_m("en","precision",1.000), recall=_m("en","recall",1.000), tier="Pre-Bronze", samples=_m("en","samples",66)),
        "sw": dict(f1=_m("sw","f1",0.851), precision=_m("sw","precision",0.822), recall=_m("sw","recall",0.881), tier="Gold (sample count)", samples=_m("sw","samples",67_290)),
        "fr": dict(f1=_m("fr","f1",0.970), precision=_m("fr","precision",1.000), recall=_m("fr","recall",0.941), tier="Pre-Bronze", samples=_m("fr","samples",165)),
        "ki": dict(f1=_m("ki","f1",0.667), precision=_m("ki","precision",0.967), recall=_m("ki","recall",0.510), tier="Bronze (sample count)", samples=_m("ki","samples",11_622)),
        "ha": dict(f1=_m("ha","f1",0.043), precision=_m("ha","precision",1.000), recall=_m("ha","recall",0.022), tier="Initial (precision-first)", samples=_m("ha","samples",10_054)),
        "zu": dict(f1=_m("zu","f1",0.732), precision=_m("zu","precision",1.000), recall=_m("zu","recall",0.577), tier="Initial (morphological)", samples=_m("zu","samples",2_000)),
    },
    "ml_classifier": {
        "label": f"{_ML_MODEL_SHORT} (ML)",
        "description": f"AfroXLM-R fine-tuned on 67K Swahili rows ({_ML_MODEL_SHORT}). Swahili only — not trained on other languages.",
        "en": dict(f1=None, precision=None, recall=None, tier="N/A (ML is SW only)", samples=None),
        "sw": dict(
            f1=_ml_m("f1", 0.871), precision=_ml_m("precision", 0.810),
            recall=_ml_m("recall", 0.942), tier="Gold (sample count)",
            samples=_ml_m("samples", 67_290),
        ),
        "fr": dict(f1=None, precision=None, recall=None, tier="N/A (ML is SW only)", samples=None),
        "ki": dict(f1=None, precision=None, recall=None, tier="N/A (ML is SW only)", samples=None),
        "ha": dict(f1=None, precision=None, recall=None, tier="N/A (ML is SW only)", samples=None),
        "zu": dict(f1=None, precision=None, recall=None, tier="N/A (ML is SW only)", samples=None),
    },
}

# Default (rules) for backwards compat
METRICS = MODEL_METRICS["rules"]

MODEL_CHOICES = [v["label"] for v in MODEL_METRICS.values()]
MODEL_KEY_BY_LABEL = {v["label"]: k for k, v in MODEL_METRICS.items()}

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
    "Hausa": [
        "Matan gida suna girki kawai.",
        "Shugaban gari ya yanke hukunci.",
        "Uwargida ta kula da yara.",
        "Budurwar nan ba ta cancanci jagoranci ba.",
        "Likita namiji ya zo asibiti.",
    ],
    "Zulu": [
        "Umuntu wesifazane akanalo ilungelo lokuphatha.",
        "Owesifazane kumele ahlale ekhaya.",
        "Udokotela wesilisa weza esibhedlela.",
        "Umfazi kumele alalele indoda yakhe.",
        "Ingane yomfana izokhula ibe inhloko yomuzi.",
    ],
}


def _run_ollama_disambiguate(sentence: str) -> str | None:
    """Call local Ollama with llama3.2 for SW bias classification. Returns 'BIAS'/'NEUTRAL'/None."""
    try:
        import requests as _req
        prompt = (
            "You are a Swahili gender bias classifier. Decide if the sentence contains gender bias.\n"
            "Gender bias means the sentence PRESCRIBES, RESTRICTS, or STEREOTYPES a person based on gender.\n"
            f"Sentence: {sentence[:400]}\n"
            "Reply with exactly one word: BIAS or NEUTRAL.\nAnswer:"
        )
        resp = _req.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=8,
        )
        if resp.status_code == 200:
            import re
            text_out = resp.json().get("response", "").strip().upper()
            first = re.split(r'\W+', text_out)[0] if text_out else ""
            return first if first in ("BIAS", "NEUTRAL") else None
    except Exception:
        pass
    return None


def _run_hf_disambiguate(sentence: str) -> str | None:
    """Call HF router Llama 3.1 8B for SW bias classification."""
    try:
        from api.disambiguator import disambiguate
        result = disambiguate(sentence)
        if result is True:
            return "BIAS"
        if result is False:
            return "NEUTRAL"
    except Exception:
        pass
    return None


def analyse(text: str, lang_name: str, model_label: str | None = None) -> tuple[str, str, str]:
    if not text.strip():
        return "⚠️ Please enter some text.", "", ""

    model_key = MODEL_KEY_BY_LABEL.get(model_label or "", "rules")
    model_info = MODEL_METRICS[model_key]

    lang_code, lang_enum = LANGS[lang_name]
    m = model_info[lang_code]

    # ML classifier now supports all 6 languages (per-language models)
    # Falls back to rules if the language model is not yet trained/available
    ml_fallback_note = ""
    if model_key == "ml_classifier":
        from eval.ml_classifier import is_available
        from eval.models import Language as _Lang
        _lang_enum_check = LANGS.get(lang_name, (None, None))[1]
        if _lang_enum_check and not is_available(_lang_enum_check):
            ml_fallback_note = f"\n> ⚠️ **ML classifier not yet trained for {lang_name}** — using rules-based detection."
            model_key = "rules"
            model_info = MODEL_METRICS["rules"]
            m = model_info[lang_code]

    # Detection
    try:
        det = _get_ml_detector() if model_key == "ml_classifier" else detector_rules
        result = det.detect_bias(text.strip(), lang_enum)
    except Exception as e:
        return f"❌ Detection error: {e}", "", ""

    # Correction
    try:
        corrected, edits, n_replaced, skipped = apply_rules_on_spans(text.strip(), lang_code)
        reason = build_reason(source="rules", edits=edits, skipped=skipped)
    except Exception as e:
        corrected, edits, n_replaced, skipped, reason = text, [], 0, [], str(e)

    # LLM disambiguation for warn-only SW cases (hf_llm / ollama models)
    llm_verdict_note = ""
    warn_only = not result.has_bias_detected and len(result.warn_edits) > 0
    if warn_only and lang_code == "sw" and model_key in ("hf_llm", "ollama"):
        if model_key == "ollama":
            llm_result = _run_ollama_disambiguate(text.strip())
            llm_src = "Ollama/llama3.2"
        else:
            llm_result = _run_hf_disambiguate(text.strip())
            llm_src = "HF/Llama-3.1-8B"

        if llm_result == "BIAS":
            result.has_bias_detected = True
            llm_verdict_note = f" *(LLM confirmed by {llm_src})*"
        elif llm_result == "NEUTRAL":
            result.warn_edits = []
            llm_verdict_note = f" *(LLM cleared by {llm_src})*"
        else:
            llm_verdict_note = f" *(LLM inconclusive — {llm_src} unavailable)*"

    # Verdict
    has_bias = result.has_bias_detected
    has_warn = len(result.warn_edits) > 0
    ml_edits = [e for e in result.warn_edits if e.get("severity") == "ml_fallback"]
    rules_warn = [e for e in result.warn_edits if e.get("severity") != "ml_fallback"]

    model_badge = f" `[{model_info['label']}]`"
    confidence  = getattr(result, 'confidence', 0.0) or 0.0
    low_conf    = has_bias and confidence > 0 and confidence < 0.75

    if has_bias:
        conf_str = f" · confidence `{confidence:.0%}`" if confidence > 0 else ""
        flag_str = "\n\n⚠️ **Low confidence — flag for human review**" if low_conf else ""
        verdict = (
            f'<div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:8px">'
            f'🔴 <strong>Gender bias detected</strong> — '
            f'{len(result.detected_edits)} rule(s) matched{llm_verdict_note}'
            f'{conf_str}{model_badge}{flag_str}</div>'
        )
    elif ml_edits:
        verdict = (
            f'<div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:8px">'
            f'🟠 <strong>Implicit bias detected (ML)</strong> — '
            f'{len(ml_edits)} pattern(s) flagged{model_badge}'
            f'\n\n⚠️ **Low confidence — flag for human review**</div>'
        )
    elif has_warn:
        verdict = (
            f'<div style="background:#fffbeb;border:1.5px solid #fde68a;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:8px">'
            f'🟡 <strong>Advisory</strong> — '
            f'{len(rules_warn)} gendered term(s) noted (no correction applied)'
            f'{llm_verdict_note}{model_badge}</div>'
        )
    else:
        verdict = (
            f'<div style="background:#f0fdf4;border:1.5px solid #bbf7d0;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:8px">'
            f'🟢 <strong>No bias detected</strong> — '
            f'text passes all checks{llm_verdict_note}{model_badge}</div>'
        )

    verdict += ml_fallback_note

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
        correction_md = (
            "⚠️ **Bias detected — no automatic correction available.**\n\n"
            "This sentence needs human review. "
            "The bias pattern was identified but could not be automatically rewritten."
        )
        if reason:
            correction_md += f"\n\n*{reason}*"
    else:
        correction_md = "No correction needed."
        if reason and skipped:
            correction_md += f"\n\n*Reason: {reason}*"

    # Metrics footer (N/A when ML model and non-SW language)
    metrics_md = (
        f"**Model metrics ({lang_name}):** "
        f"F1 `{_fmt_metric(m['f1'])}` · Precision `{_fmt_metric(m['precision'])}` · Recall `{_fmt_metric(m['recall'])}` · "
        f"Samples `{_fmt_metric(m['samples'])}` · Tier: **{m['tier']}**"
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
            _fmt_metric(m.get('en', {}).get('f1')),
            _fmt_metric(m.get('sw', {}).get('f1')),
            _fmt_metric(m.get('fr', {}).get('f1')),
            _fmt_metric(m.get('ki', {}).get('f1')),
            v.get("notes", ""),
        ])
    ts = reg["versions"][-1]["timestamp"][:16].replace("T", " ") if reg.get("versions") else "—"
    return rows, f"Last snapshot: {ts}"


def _fmt_metric(v, fmt_num="{:.3f}", fmt_int="{:,}"):
    """Format a metric value for display; None -> 'N/A'."""
    if v is None:
        return "N/A"
    return (fmt_int if isinstance(v, int) else fmt_num).format(v)


def sidebar_metrics(lang_name: str, model_label: str | None = None) -> str:
    code = LANGS[lang_name][0]
    model_key = MODEL_KEY_BY_LABEL.get(model_label or "", "rules")
    model_info = MODEL_METRICS[model_key]
    m = model_info[code]
    f1_val = m["f1"]
    has_na = f1_val is None
    f1_bar = 0 if has_na else min(int(f1_val / 1.0 * 10), 10)
    bar_filled = "█" * f1_bar + "░" * (10 - f1_bar)
    status_color = "#94a3b8" if has_na else "#4ade80" if f1_val >= 0.75 else "#fbbf24" if f1_val >= 0.5 else "#f87171"
    desc = model_info["description"]
    return (
        f"<div style='"
        f"background:rgba(255,255,255,0.07);"
        f"border:1px solid rgba(255,255,255,0.15);border-radius:12px;"
        f"padding:16px 18px;margin-top:8px;font-family:monospace;font-size:0.85rem;color:#e2e8f0'>"
        f"<div style='font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;"
        f"color:#94a3b8;margin-bottom:6px'>Model · {lang_name}</div>"
        f"<div style='font-size:0.72rem;color:#64748b;margin-bottom:10px;font-family:sans-serif'>{desc}</div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>F1</span>"
        f"<span style='color:{status_color};font-weight:700'>{_fmt_metric(f1_val)}</span></div>"
        f"<div style='font-size:0.75rem;color:#64748b;margin:2px 0'>{bar_filled}</div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>Precision</span>"
        f"<span style='color:#e2e8f0'>{_fmt_metric(m['precision'])}</span></div>"
        f"<div style='display:flex;justify-content:space-between;margin:4px 0'>"
        f"<span style='color:#94a3b8'>Recall</span>"
        f"<span style='color:#e2e8f0'>{_fmt_metric(m['recall'])}</span></div>"
        f"<div style='display:flex;justify-content:space-between;margin:6px 0 2px'>"
        f"<span style='color:#94a3b8'>Samples</span>"
        f"<span style='color:#e2e8f0'>{_fmt_metric(m['samples'])}</span></div>"
        f"<div style='margin-top:8px;padding:4px 8px;border-radius:6px;"
        f"background:rgba(99,102,241,0.25);text-align:center;"
        f"font-size:0.75rem;color:#a5b4fc'>{m['tier']}</div>"
        f"</div>"
    )


_theme = gr.themes.Soft(primary_hue="indigo")

with gr.Blocks(title="JuaKazi · Gender Bias Detection", theme=_theme) as demo:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.HTML(
        '<div style="background:linear-gradient(135deg,#1e1b4b 0%,#0f172a 60%,#1e3a5f 100%);'
        'border:1px solid rgba(99,102,241,0.3);border-radius:16px;'
        'padding:28px 32px 22px;margin-bottom:18px;position:relative;z-index:0">'
        '<h1 style="font-size:1.9rem;color:#e2e8f0;margin:0 0 4px;font-weight:700">'
        'JuaKazi &middot; Gender Bias Detection &amp; Correction</h1>'
        '<p style="font-size:0.88rem;color:#94a3b8;margin:0">'
        'Rules-based &middot; 4 East African languages &middot; AIBRIDGE-compliant &middot; '
        '<a href="https://github.com/Stella-Achar-Oiro/gender-sensitization-engine" '
        'style="color:#818cf8">GitHub</a></p>'
        '</div>'
    )

    with gr.Row():

        # ── Sidebar ───────────────────────────────────────────────────────────
        with gr.Column(scale=1, min_width=220):
            lang_dd = gr.Dropdown(
                label="Language",
                choices=list(LANGS.keys()),
                value="English",
                interactive=True,
            )
            model_dd = gr.Dropdown(
                label="Model",
                choices=MODEL_CHOICES,
                value=MODEL_CHOICES[0],
                interactive=True,
            )
            metrics_html = gr.HTML(sidebar_metrics("English", MODEL_CHOICES[0]))

        # ── Main content ──────────────────────────────────────────────────────
        with gr.Column(scale=3):
            with gr.Tabs():

                # Tab 1 — Analyse (id for programmatic switch)
                with gr.Tab("Analyse"):
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
                    analyse_btn = gr.Button("Analyse", variant="primary", size="lg")

                    verdict_out = gr.HTML()

                    with gr.Row():
                        with gr.Column():
                            gr.HTML('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#94a3b8;margin-bottom:6px;font-weight:600">Detection detail</div>')
                            detect_out = gr.Markdown()
                        with gr.Column():
                            gr.HTML('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;color:#94a3b8;margin-bottom:6px;font-weight:600">Correction</div>')
                            correct_out = gr.Markdown()

                # Tab 2 — Model Versions
                with gr.Tab("Model Versions"):
                    with gr.Row():
                        refresh_btn = gr.Button("Refresh", size="sm")
                        registry_ts = gr.Markdown()

                    versions_table = gr.Dataframe(
                        headers=["Tag", "Date", "Commit", "EN F1", "SW F1", "FR F1", "KI F1", "Notes"],
                        datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                        interactive=False,
                        label="",
                        wrap=True,
                    )

                    trend_md = gr.Markdown()

    def _trend_md(rows):
        lines = ["**F1 by version**\n", "| Version | EN | SW | FR | KI |", "|---|---|---|---|---|"]
        for row in reversed(rows):
            lines.append(f"| {row[0]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |")
        return "\n".join(lines)

    def refresh_versions():
        rows, ts = load_registry_table()
        return rows, ts, _trend_md(rows)

    # ── Wire language change: update metrics and example sentences ────────────
    def on_lang_change(lang, model_label):
        new_exs = EXAMPLES.get(lang, [])
        return sidebar_metrics(lang, model_label), gr.update(choices=new_exs, value=None)

    lang_dd.change(
        fn=on_lang_change,
        inputs=[lang_dd, model_dd],
        outputs=[metrics_html, example_dd],
    )

    # ── Wire model change: update metrics panel ───────────────────────────────
    def on_model_change(model_label, lang):
        return sidebar_metrics(lang, model_label)

    model_dd.change(
        fn=on_model_change,
        inputs=[model_dd, lang_dd],
        outputs=metrics_html,
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
        inputs=[text_in, lang_dd, model_dd],
        outputs=[verdict_out, detect_out, correct_out],
    )
    text_in.submit(
        fn=analyse,
        inputs=[text_in, lang_dd, model_dd],
        outputs=[verdict_out, detect_out, correct_out],
    )

    # ── Load versions on startup + refresh button ─────────────────────────────
    demo.load(fn=refresh_versions, outputs=[versions_table, registry_ts, trend_md])
    refresh_btn.click(fn=refresh_versions, outputs=[versions_table, registry_ts, trend_md])

demo.launch(server_name="0.0.0.0", server_port=7860)
