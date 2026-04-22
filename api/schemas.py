"""Pydantic request/response models for the correction API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Supported language codes (must match rules_engine and detector)
SUPPORTED_LANGS = ("en", "sw", "fr", "ki")
LangCode = Literal["en", "sw", "fr", "ki"]


class RewriteRequest(BaseModel):
    id: str
    lang: LangCode
    text: str = Field(..., min_length=1, max_length=5000)
    flags: Optional[list] = None
    region_dialect: Optional[str] = None  # "kenya" | "tanzania" | "uganda" | "sheng" | "coastal"


class BatchRewriteRequest(BaseModel):
    """Request body for POST /rewrite/batch. Validated so invalid items return 422."""

    items: list[RewriteRequest] = Field(..., min_length=1, max_length=100)


class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool
    source: str  # "rules" | "ml" | "preserved"
    reason: str
    semantic_score: Optional[float] = None
    skipped_context: Optional[list] = None
    has_bias_detected: bool = False
