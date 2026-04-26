"""AIBRIDGE external Bias Detection API client.

Calls POST /detect to gate whether a sentence contains bias before running
the correction pipeline. Returns a typed result; never raises — all network
and HTTP errors are captured in AibridgeResult.error so callers can fall
through to the internal pipeline gracefully.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from config import (
    AIBRIDGE_BASE_URL,
    AIBRIDGE_CONFIDENCE_THRESHOLD,
    AIBRIDGE_ENABLED,
    AIBRIDGE_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Languages accepted by the external API (their exact string values)
SUPPORTED_LANGUAGES = frozenset({"hausa", "swahili", "zulu"})

# Our lang codes → external API language names
LANG_CODE_MAP: dict[str, str] = {
    "sw": "swahili",
}


@dataclass
class AibridgeResult:
    has_bias: bool
    confidence: float
    message: str
    error: Optional[str] = field(default=None)


def detect_bias(text: str, language: str, timeout: float = None) -> AibridgeResult:
    """
    Call the AIBRIDGE /detect endpoint and return an AibridgeResult.

    language: external API language string (e.g. "swahili"), NOT our lang code.
    On network error, HTTP error, or if AIBRIDGE_ENABLED=false, returns a result
    with error set — callers treat this as "fall through to internal pipeline".
    """
    if not AIBRIDGE_ENABLED:
        return AibridgeResult(has_bias=False, confidence=0.0, message="", error="aibridge_disabled")

    if language not in SUPPORTED_LANGUAGES:
        return AibridgeResult(
            has_bias=False,
            confidence=0.0,
            message="",
            error=f"language_not_supported:{language}",
        )

    try:
        import requests
    except ImportError:
        return AibridgeResult(has_bias=False, confidence=0.0, message="", error="requests_not_installed")

    url = f"{AIBRIDGE_BASE_URL}/detect"
    payload = {
        "text": text,
        "language": language,
        "confidence_threshold": AIBRIDGE_CONFIDENCE_THRESHOLD,
    }
    effective_timeout = timeout if timeout is not None else AIBRIDGE_TIMEOUT

    t0 = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=effective_timeout)
        latency_ms = int((time.time() - t0) * 1000)
        logger.debug(f"aibridge: status={resp.status_code} latency={latency_ms}ms lang={language}")

        if resp.status_code == 422:
            logger.warning(f"aibridge: 422 validation error — {resp.text[:200]}")
            return AibridgeResult(has_bias=False, confidence=0.0, message="", error=f"http_422")

        if resp.status_code != 200:
            return AibridgeResult(
                has_bias=False, confidence=0.0, message="", error=f"http_{resp.status_code}"
            )

        data = resp.json()
        return AibridgeResult(
            has_bias=bool(data.get("has_bias", False)),
            confidence=float(data.get("confidence", 0.0)),
            message=str(data.get("message", "")),
            error=None,
        )

    except Exception as exc:
        latency_ms = int((time.time() - t0) * 1000)
        logger.debug(f"aibridge: exception after {latency_ms}ms — {exc}")
        return AibridgeResult(has_bias=False, confidence=0.0, message="", error=str(exc))
