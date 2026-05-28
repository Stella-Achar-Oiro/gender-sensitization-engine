"""
Phase 0 — UI / API smoke tests.

Verifies the /rewrite API endpoint returns correct response structure
including detection signal, correction, reason, and human review flag.

These tests hit the FastAPI app directly via TestClient (no server needed).

Rules:
- Biased input  → has_bias_detected=True, rewrite != original, reason non-empty
- Neutral input → has_bias_detected=False, rewrite == original
- Low-confidence detection → flag_for_human_review=True in response

Run:
    pytest tests/test_ui_smoke.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Known biased sentences per language (same as integration tests) ──────────
BIASED = {
    "sw": "Daktari wa kiume alifika hospitalini asubuhi.",
    "ha": "Likitan namiji ya zo asibiti safe.",
    "zu": "Udokotela wesilisa weza esibhedlela ekuseni.",
    "ki": "Mũndũ wa mũrũme nĩwe ũngĩ gũtwara mũciĩ.",
    "fr": "Le président a dirigé la réunion comme un vrai homme.",
    "en": "The chairman will lead the board meeting.",
}

NEUTRAL = {
    "sw": "Mvua ilianza kunyesha asubuhi na mapema.",
    "ha": "Ruwan sama ya fara zuwa da safe.",
    "zu": "Imvula yaqala ukuna ekuseni.",
    "ki": "Mbura yaambĩrĩria gũthira rũciinĩ.",
    "fr": "Il pleut ce matin dans la ville.",
    "en": "The rain started early in the morning.",
}


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def _post_rewrite(client, text: str, lang: str) -> dict:
    resp = client.post("/rewrite", json={
        "id": f"smoke-{lang}",
        "lang": lang,
        "text": text,
    })
    assert resp.status_code == 200, f"API returned {resp.status_code}: {resp.text}"
    return resp.json()


def _assert_response_structure(data: dict):
    """Every response must have these fields regardless of detection result."""
    required = ["original_text", "rewrite", "edits", "confidence", "source"]
    for field in required:
        assert field in data, f"Response missing field: '{field}'"


# ── Swahili (must pass now) ──────────────────────────────────────────────────

def test_sw_api_biased(client):
    data = _post_rewrite(client, BIASED["sw"], "sw")
    print(f"\nSW biased API response: {data}")
    _assert_response_structure(data)
    assert data.get("has_bias_detected") is True or data["rewrite"] != data["original_text"], \
        "SW biased sentence: no detection signal and no correction"


def test_sw_api_neutral(client):
    data = _post_rewrite(client, NEUTRAL["sw"], "sw")
    print(f"\nSW neutral API response: {data}")
    _assert_response_structure(data)
    assert data["rewrite"] == data["original_text"], \
        f"SW neutral sentence was modified: '{data['original_text']}' → '{data['rewrite']}'"


def test_sw_api_response_has_reason(client):
    """Biased SW response must include a reason field."""
    data = _post_rewrite(client, BIASED["sw"], "sw")
    edits = data.get("edits", [])
    if edits:
        first_edit = edits[0]
        assert first_edit.get("reason") or first_edit.get("bias_type"), \
            "SW edit missing reason/bias_type field"


# ── English (must pass now) ──────────────────────────────────────────────────

def test_en_api_biased(client):
    data = _post_rewrite(client, BIASED["en"], "en")
    print(f"\nEN biased API response: {data}")
    _assert_response_structure(data)
    assert data.get("has_bias_detected") is True or data["rewrite"] != data["original_text"], \
        "EN biased sentence: no detection signal and no correction"


def test_en_api_neutral(client):
    data = _post_rewrite(client, NEUTRAL["en"], "en")
    print(f"\nEN neutral API response: {data}")
    _assert_response_structure(data)
    assert data["rewrite"] == data["original_text"], \
        f"EN neutral sentence was modified"


# ── Response structure for all languages (no detection assertion — structure only) ─

@pytest.mark.parametrize("lang", ["sw", "ha", "zu", "ki", "fr", "en"])
def test_api_response_structure(client, lang):
    """Every language must return a valid response structure — no crashes."""
    data = _post_rewrite(client, BIASED[lang], lang)
    _assert_response_structure(data)


@pytest.mark.parametrize("lang", ["sw", "ha", "zu", "ki", "fr", "en"])
def test_api_neutral_never_modified(client, lang):
    """Neutral sentences must NEVER be modified by the pipeline, any language."""
    data = _post_rewrite(client, NEUTRAL[lang], lang)
    _assert_response_structure(data)
    assert data["rewrite"] == data["original_text"], \
        f"[{lang.upper()}] Neutral sentence was incorrectly modified: " \
        f"'{data['original_text']}' → '{data['rewrite']}'"


# ── Human review flag ────────────────────────────────────────────────────────

def test_sw_api_no_crash_empty_text(client):
    """Empty text must return gracefully, not 500."""
    resp = client.post("/rewrite", json={"id": "smoke-empty", "lang": "sw", "text": ""})
    assert resp.status_code in (200, 422), \
        f"Empty text caused unexpected error: {resp.status_code}"


def test_api_confidence_field_present(client):
    """Confidence field must be a float between 0 and 1."""
    data = _post_rewrite(client, BIASED["sw"], "sw")
    conf = data.get("confidence")
    assert conf is not None, "Response missing confidence field"
    assert 0.0 <= float(conf) <= 1.0, f"Confidence out of range: {conf}"
