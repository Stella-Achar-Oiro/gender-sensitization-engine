"""Pydantic request/response models for the correction API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Supported language codes (must match rules_engine and detector)
# ha/zu: rules-based correction via lexicon_ha_v1 / lexicon_zu_v1
SUPPORTED_LANGS = ("en", "sw", "fr", "ki", "ha", "zu")
LangCode = Literal["en", "sw", "fr", "ki", "ha", "zu"]


class RewriteRequest(BaseModel):
    id: str
    lang: LangCode
    text: str = Field(..., min_length=1, max_length=5000)
    flags: Optional[list] = None
    region_dialect: Optional[str] = None  # "kenya" | "tanzania" | "uganda" | "sheng" | "coastal"
    caller: Optional[str] = None  # "aibridge" = skip detection gate (caller already confirmed bias)


class BatchRewriteRequest(BaseModel):
    """Request body for POST /rewrite/batch. Validated so invalid items return 422."""

    items: list[RewriteRequest] = Field(..., min_length=1, max_length=100)


SourceLiteral = Literal[
    "rules",
    "ml",
    "preserved",
    "disambiguated",
    "aibridge_preserved",
]


class RewriteResponse(BaseModel):
    id: str
    original_text: str
    rewrite: str
    edits: list
    confidence: float
    needs_review: bool
    source: SourceLiteral
    reason: str
    semantic_score: Optional[float] = None
    skipped_context: Optional[list] = None
    has_bias_detected: bool = False
    aibridge_confidence: Optional[float] = None   # Confidence from external classifier
    aibridge_detected: Optional[bool] = None      # True/False when AIBRIDGE ran cleanly; None when bypassed or errored
