"""JuaKazi Correction API — HTTP routing only."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .audit import log as log_audit
from .schemas import BatchRewriteRequest, RewriteRequest, RewriteResponse
from .service import rewrite_text as service_rewrite

logger = logging.getLogger(__name__)

app = FastAPI(title="JuaKazi Correction Engine (hybrid)", version="0.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://*.hf.space",
        "https://huggingface.co",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


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
