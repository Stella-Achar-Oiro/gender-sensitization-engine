"""Pydantic request/response models for the correction API."""

from pydantic import BaseModel


class RewriteRequest(BaseModel):
    id: str
    lang: str
    text: str
    flags: list = None
    region_dialect: str = None  # "kenya" | "tanzania" | "uganda" | "sheng" | "coastal"


class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool
    source: str           # "rules" | "ml" | "preserved"
    reason: str
    semantic_score: float = None
    skipped_context: list = None
    has_bias_detected: bool = False
