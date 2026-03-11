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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
