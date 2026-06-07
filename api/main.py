"""JuaKazi Correction API — HTTP routing only."""

import io
import json
import logging
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .audit import log as log_audit
from .schemas import BatchRewriteRequest, RewriteRequest, RewriteResponse
from .service import rewrite_text as service_rewrite

logger = logging.getLogger(__name__)

_STATIC = Path(__file__).parent.parent / "static"

app = FastAPI(title="JuaKazi Correction Engine", version="0.4")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Serve Next.js static export — catch-all file serving
# Uses a path parameter to serve any file under /app/static/
if _STATIC.exists():
    from fastapi.responses import FileResponse as _FileResponse
    from starlette.responses import Response as _Response

    @app.get("/_next/{file_path:path}")
    async def serve_next_static(file_path: str):
        f = _STATIC / "_next" / file_path
        if f.exists() and f.is_file():
            return _FileResponse(str(f))
        return _Response(status_code=404)


@app.get("/")
def root():
    """Serve Next.js frontend."""
    index = _STATIC / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return {"service": "JuaKazi API", "docs": "/docs"}


@app.get("/favicon.ico")
def favicon():
    f = _STATIC / "favicon.ico"
    if f.exists():
        return FileResponse(str(f), media_type="image/x-icon")
    return Response(status_code=204)


@app.get("/languages")
def languages_page():
    """Serve Next.js languages page."""
    page = _STATIC / "languages" / "index.html"
    if page.exists():
        return FileResponse(str(page), media_type="text/html")
    index = _STATIC / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return {"service": "JuaKazi API"}


@app.get("/metrics")
def metrics_endpoint():
    """Return current evaluation metrics for all languages."""
    metrics_path = Path(__file__).parent.parent / "eval" / "metrics.json"
    if metrics_path.exists():
        return json.loads(metrics_path.read_text())
    return {}


@app.get("/health")
def health():
    """Health check — returns system status and loaded lexicon counts."""
    import csv
    from pathlib import Path
    lexicon_counts = {}
    for lang in ("en", "sw", "fr", "ki"):
        p = Path(f"rules/lexicon_{lang}_v3.csv")
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                lexicon_counts[lang] = sum(1 for _ in csv.DictReader(f))
        else:
            lexicon_counts[lang] = 0
    return {"status": "ok", "version": "0.3", "lexicon_entries": lexicon_counts}


@app.post("/rewrite", response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    """Validate, run rewrite service, log, return."""
    try:
        response, audit_info = service_rewrite(
            id=req.id,
            text=req.text,
            lang=req.lang,
            flags=req.flags,
            region_dialect=req.region_dialect,
            caller=req.caller,
        )
        log_audit({
            "request": req.model_dump(),
            "response": response.model_dump(),
            **audit_info,
        })
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("rewrite failed id=%s lang=%s", req.id, req.lang)
        raise HTTPException(
            status_code=500,
            detail="Rewrite failed; try again or contact support.",
        ) from e


@app.post("/rewrite/batch", response_model=list[RewriteResponse])
def rewrite_batch(body: BatchRewriteRequest):
    return [rewrite(item) for item in body.items]


_SENT_SPLIT = re.compile(r"(?<=[.!?؟。？！])\s+")
_MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


def _split_sentences(text: str) -> list[str]:
    parts = _SENT_SPLIT.split(text)
    return [s.strip() for s in parts if s.strip()]


@app.post("/rewrite/pdf", response_model=list[RewriteResponse])
async def rewrite_pdf(
    file: UploadFile = File(...),
    lang: str = "sw",
):
    """Extract text from a PDF, split into sentences, run bias detection on each."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted.")

    data = await file.read()
    if len(data) > _MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds 10 MB limit.")

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        full_text = " ".join(pages_text)
    except Exception as e:
        logger.exception("PDF extraction failed")
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {e}") from e

    sentences = _split_sentences(full_text)
    if not sentences:
        raise HTTPException(status_code=422, detail="No text found in PDF.")
    if len(sentences) > 200:
        sentences = sentences[:200]

    if lang not in ("en", "sw", "fr", "ki", "ha", "zu"):
        lang = "sw"

    items = [
        RewriteRequest(id=str(i), lang=lang, text=s)  # type: ignore[arg-type]
        for i, s in enumerate(sentences)
    ]
    return [rewrite(item) for item in items]
