# JuaKazi UI — one app

We use **one** primary UI: the Next.js app.

---

## Primary UI: Next.js

**Path:** `apps/web/`  
**Run:** `make run` (API + Next.js together) or `make run-web` (UI only)  
**URL:** http://localhost:3000

- Landing, **Analyse** (with sidebar history), **Batch** CSV, **About**.
- Talks to FastAPI `POST /rewrite` (dev proxy or `NEXT_PUBLIC_API_URL` in prod).
- Use this for product use, demos, and investor-facing UI.

---

## Other entry points (optional / legacy)

| File | Purpose | Keep? |
|------|---------|--------|
| **app.py** | Streamlit demo (HF Spaces or local) | Only if you host a Streamlit Space; otherwise redundant with Next.js. |
| **tester.py** | Streamlit “external tester” for engineers | Redundant with app.py and Next.js; safe to remove or archive. |
| **ui/app.py** | Review UI (audit_logs, accept/reject) | Keep until review is in Next.js; then deprecate. |
| **gradio_app.py** | Gradio demo for HF Spaces | Use **either** app.py **or** gradio_app.py for a Space, not both. |

**Recommendation:** Use **Next.js** as the only day-to-day UI. For HuggingFace Spaces, pick one of `app.py` (Streamlit) or `gradio_app.py` (Gradio) and ignore the other. Consider removing or archiving `tester.py`; use Next.js Analyse (or the single Streamlit/Gradio Space) for testing.
