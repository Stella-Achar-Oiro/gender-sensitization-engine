"""LLM-based disambiguation for borderline gender bias cases.

Uses HF Inference API (no local GPU needed). Called only when rules find
a warn-severity match — not on every sentence. Falls back gracefully if
HF API is unavailable.
"""

import os
import re
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Model for classification — Llama 3.1 8B via HF router (no local GPU needed)
_MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Cache token at module load
_HF_TOKEN: Optional[str] = None


def _get_token() -> Optional[str]:
    global _HF_TOKEN
    if _HF_TOKEN:
        return _HF_TOKEN
    # Try env var first, then HF cache file
    token = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")
    if not token:
        cache_path = os.path.expanduser("~/.cache/huggingface/token")
        try:
            with open(cache_path) as f:
                token = f.read().strip()
        except OSError:
            pass
    _HF_TOKEN = token or None
    return _HF_TOKEN


_PROMPT_TEMPLATE = """\
You are a Swahili gender bias classifier. Your task: decide if the sentence below contains gender bias.

Gender bias means the sentence PRESCRIBES, RESTRICTS, or STEREOTYPES a person based on gender — e.g. "girls should stay home", "only men can lead", "women are weak".

NOT bias: factual reporting about gender ("the female student won"), advocacy/counter-stereotype contexts ("we must support girls' education"), neutral mentions of gender.

Sentence: {sentence}

Reply with exactly one word: BIAS or NEUTRAL.
Answer:"""


def disambiguate(sentence: str, timeout: float = 3.0) -> Optional[bool]:
    """
    Returns True = bias confirmed, False = not bias, None = inconclusive/error.
    Only called for borderline warn-severity matches.
    """
    token = _get_token()
    if not token:
        logger.debug("disambiguate: no HF token — skipping")
        return None

    try:
        import requests
    except ImportError:
        return None

    prompt = _PROMPT_TEMPLATE.format(sentence=sentence[:400])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 5,
        "temperature": 0.01,
    }

    t0 = time.time()
    try:
        resp = requests.post(_API_URL, headers=headers, json=payload, timeout=timeout)
        latency_ms = int((time.time() - t0) * 1000)
        logger.debug(f"disambiguate: status={resp.status_code} latency={latency_ms}ms")

        if resp.status_code != 200:
            return None

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return None

        generated = choices[0].get("message", {}).get("content", "").strip().upper()
        first_word = re.split(r'\W+', generated)[0] if generated else ""
        if first_word == "BIAS":
            return True
        if first_word == "NEUTRAL":
            return False
        return None

    except Exception as e:
        logger.debug(f"disambiguate: exception {e}")
        return None
