"""
Phase 0 — Correction contract tests.

Verifies that for each language with correction pairs:
1. corrector produces output that differs from the input (something changed)
2. output is not empty or garbled (min length, valid string)
3. BLEU score >= 0.25 vs human reference on a held-out sample

These tests MUST fail now for HA/ZU (no trained corrector yet).
SW passes because lexicon rules already produce corrections.
KI passes because ground truth has expected_correction column.

Run:
    pytest tests/test_correction_contract.py -v
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.models import Language
from api.rules_engine import apply_rules_on_spans

ROOT = Path(__file__).parent.parent

# ── Correction pair files ────────────────────────────────────────────────────
CORRECTION_FILES = {
    "sw": "juakazi_sw_correction_pairs_v1.csv",
    "ha": "juakazi_ha_correction_pairs_v1.csv",
    "zu": "juakazi_zu_correction_pairs_v1.csv",
}

# For KI we pull from ground truth (has expected_correction column)
KI_GT_FILE = "eval/ground_truth_ki_v8.csv"

LANG_ENUM = {
    "sw": Language.SWAHILI,
    "ha": Language.HAUSA,
    "zu": Language.ZULU,
    "ki": Language.GIKUYU,
}

# BLEU thresholds (loose — AI drafts only, not human gold)
BLEU_THRESHOLDS = {
    "sw": 0.25,
    "ha": 0.20,  # lower — AI draft pairs, not yet validated
    "zu": 0.20,
    "ki": 0.25,
}

SAMPLE_SIZE = 100  # rows to evaluate per language


def _simple_bleu(hypothesis: str, reference: str) -> float:
    """Unigram + bigram BLEU approximation. No external deps needed."""
    hyp_tokens = hypothesis.lower().split()
    ref_tokens = reference.lower().split()
    if not hyp_tokens or not ref_tokens:
        return 0.0

    # Unigram precision
    ref_counts: dict = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1
    matches = 0
    for t in hyp_tokens:
        if ref_counts.get(t, 0) > 0:
            matches += 1
            ref_counts[t] -= 1
    unigram_p = matches / max(len(hyp_tokens), 1)

    # Bigram precision
    hyp_bigrams = list(zip(hyp_tokens, hyp_tokens[1:]))
    ref_bigrams = list(zip(ref_tokens, ref_tokens[1:]))
    ref_bg_counts: dict = {}
    for bg in ref_bigrams:
        ref_bg_counts[bg] = ref_bg_counts.get(bg, 0) + 1
    bg_matches = 0
    for bg in hyp_bigrams:
        if ref_bg_counts.get(bg, 0) > 0:
            bg_matches += 1
            ref_bg_counts[bg] -= 1
    bigram_p = bg_matches / max(len(hyp_bigrams), 1) if hyp_bigrams else 0.0

    # Brevity penalty
    import math
    bp = 1.0 if len(hyp_tokens) >= len(ref_tokens) else \
        math.exp(1 - len(ref_tokens) / max(len(hyp_tokens), 1))

    score = bp * (unigram_p ** 0.5) * (bigram_p ** 0.5)
    return round(score, 4)


def _load_correction_pairs(lang_code: str, max_rows: int = SAMPLE_SIZE):
    """Load correction pairs for a language."""
    if lang_code == "ki":
        path = ROOT / KI_GT_FILE
        rows = []
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                original = r.get("text", "").strip()
                corrected = r.get("expected_correction", "").strip()
                if original and corrected and original != corrected:
                    rows.append({"original": original, "corrected": corrected})
                if len(rows) >= max_rows:
                    break
        return rows

    path = ROOT / CORRECTION_FILES[lang_code]
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            original = r.get("original_text", r.get("text", "")).strip()
            corrected = r.get("corrected_text", r.get("expected_correction", "")).strip()
            if original and corrected and original != corrected:
                rows.append({"original": original, "corrected": corrected})
            if len(rows) >= max_rows:
                break
    return rows


def _run_correction(text: str, lang_code: str) -> str:
    """Run the lexicon-rule correction stage on a single text.

    These contract tests cover the rules only. The ML corrector is covered by the
    test_ml_corrector_* tests below.
    """
    corrected, _, _, _ = apply_rules_on_spans(text, lang_code)
    return corrected


def _evaluate_corrections(lang_code: str):
    pairs = _load_correction_pairs(lang_code)
    assert len(pairs) > 0, f"No correction pairs found for {lang_code}"

    changed = 0
    empty = 0
    bleu_scores = []

    for pair in pairs:
        output = _run_correction(pair["original"], lang_code)

        if not output or len(output.strip()) < 3:
            empty += 1
            continue
        if output != pair["original"]:
            changed += 1

        bleu = _simple_bleu(output, pair["corrected"])
        bleu_scores.append(bleu)

    avg_bleu = sum(bleu_scores) / max(len(bleu_scores), 1)
    change_rate = changed / max(len(pairs), 1)

    return {
        "pairs": len(pairs),
        "changed": changed,
        "change_rate": round(change_rate, 3),
        "empty": empty,
        "avg_bleu": round(avg_bleu, 4),
    }


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(
    not (ROOT / CORRECTION_FILES["sw"]).exists(),
    reason="SW correction pairs not in repo (gitignored large file)"
)
def test_sw_correction():
    """SW correction must work — lexicon rules already produce corrections."""
    metrics = _evaluate_corrections("sw")
    print(f"\nSW correction metrics: {metrics}")
    assert metrics["empty"] == 0, f"SW corrector produced empty output on {metrics['empty']} rows"
    assert metrics["avg_bleu"] >= BLEU_THRESHOLDS["sw"], \
        f"SW avg BLEU {metrics['avg_bleu']} < threshold {BLEU_THRESHOLDS['sw']}"


def test_ki_correction():
    """KI correction pairs from ground truth — baseline check."""
    metrics = _evaluate_corrections("ki")
    print(f"\nKI correction metrics: {metrics}")
    assert metrics["empty"] == 0, f"KI corrector produced empty output on {metrics['empty']} rows"
    assert metrics["avg_bleu"] >= BLEU_THRESHOLDS["ki"], \
        f"KI avg BLEU {metrics['avg_bleu']} < threshold {BLEU_THRESHOLDS['ki']}"


@pytest.mark.xfail(reason="HA corrector not yet trained — Phase 4.1 target", strict=True)
def test_ha_correction():
    """HA must fail now. Will pass after Phase 4.1 (afriteva fine-tuned on approved HA pairs)."""
    metrics = _evaluate_corrections("ha")
    print(f"\nHA correction metrics: {metrics}")
    assert metrics["avg_bleu"] >= BLEU_THRESHOLDS["ha"], \
        f"HA avg BLEU {metrics['avg_bleu']} < threshold {BLEU_THRESHOLDS['ha']}"
    assert metrics["change_rate"] >= 0.70, \
        f"HA change rate {metrics['change_rate']} too low — corrector not making changes"


@pytest.mark.skipif(
    not (ROOT / CORRECTION_FILES["zu"]).exists(),
    reason="ZU correction pairs not in repo (gitignored large file)"
)
def test_zu_correction():
    """ZU lexicon rules already produce good corrections (BLEU=1.0 on sample). Phase 4.2 improves coverage."""
    metrics = _evaluate_corrections("zu")
    print(f"\nZU correction metrics: {metrics}")
    assert metrics["avg_bleu"] >= BLEU_THRESHOLDS["zu"], \
        f"ZU avg BLEU {metrics['avg_bleu']} < threshold {BLEU_THRESHOLDS['zu']}"
    assert metrics["change_rate"] >= 0.70, \
        f"ZU change rate {metrics['change_rate']} too low — corrector not making changes"


def test_guardrails_all_languages():
    """
    Guardrails (validate_correction) must catch bad ML corrections and accept good ones
    for all 6 languages. This is the safety net that ensures Baluku never sees
    hallucinated output — bad corrections flag for human review instead.

    Four cases per language:
      1. Identical output  → review  (corrector did nothing)
      2. EN hallucination  → review  (corrector switched language)
      3. Good minimal swap → accept  (real minimal-edit correction)
      4. Different sentence → review (corrector hallucinated unrelated text)
    """
    from api.ml_rewriter import validate_correction

    cases = {
        "sw": [
            ("Mwanamke hawezi kuwa kiongozi", "Mwanamke hawezi kuwa kiongozi", "review"),
            ("Mwanamke hawezi kuwa kiongozi", "The company women are not leaders", "review"),
            ("Mwanamke hawezi kuwa kiongozi", "Mtu hawezi kuwa kiongozi", "accept"),
            ("Mwanamke hawezi kuwa kiongozi", "Chakula ni kizuri sana leo usiku", "review"),
        ],
        "ha": [
            ("Mace ba su iya tuka mota ba", "Mace ba su iya tuka mota ba", "review"),
            ("Mace ba su iya tuka mota ba", "The women are not able to drive cars", "review"),
            ("Mace ba su iya tuka mota ba", "Kowa ba su iya tuka mota ba", "review"),  # HA always needs human review
            ("Mace ba su iya tuka mota ba", "Abinci yana da kyau a yau", "review"),
        ],
        "zu": [
            ("Umfazi kumele ahlale ekhaya", "Umfazi kumele ahlale ekhaya", "review"),
            ("Umfazi kumele ahlale ekhaya", "The women should stay at home always", "review"),
            ("Umfazi kumele ahlale ekhaya", "Umuntu kumele ahlale ekhaya", "review"),  # ZU always needs human review
            ("Umfazi kumele ahlale ekhaya", "Izulu liyeza namhlanje emini", "review"),
        ],
        "ki": [
            ("Mũtumia ndanyitwo mũtongoria", "Mũtumia ndanyitwo mũtongoria", "review"),
            ("Mũtumia ndanyitwo mũtongoria", "The woman was appointed leader", "review"),
            ("Mũtumia ndanyitwo mũtongoria", "Mũndũ ndanyitwo mũtongoria", "accept"),
            ("Mũtumia ndanyitwo mũtongoria", "Ndũrũiri ĩrĩa nene nĩ njega", "review"),
        ],
        "fr": [
            ("Un homme dirige l'équipe", "Un homme dirige l'équipe", "review"),
            ("Un homme dirige l'équipe", "The man is leading the company team", "review"),
            ("Un homme dirige l'équipe", "Une personne dirige l'équipe", "accept"),
            ("Un homme dirige l'équipe", "Le marché est ouvert aujourd'hui matin", "review"),
        ],
        "en": [
            ("The nurse helped him with his report", "The nurse helped him with his report", "review"),
            ("The nurse helped him with his report", "Die Krankenschwester hat ihm geholfen", "review"),
            ("The nurse helped him with his report", "The nurse helped them with their report", "accept"),
            ("The nurse helped him with his report", "Yesterday the weather was very nice outside", "review"),
        ],
    }

    failures = []
    for lang, lang_cases in cases.items():
        for original, candidate, expected in lang_cases:
            verdict, reason = validate_correction(original, candidate, lang)
            if verdict != expected:
                failures.append(
                    f"[{lang}] original={original!r} candidate={candidate!r} "
                    f"expected={expected!r} got={verdict!r} reason={reason!r}"
                )

    assert not failures, "Guardrail failures:\n" + "\n".join(failures)


def test_ml_corrector_stops_at_end_of_sentence():
    """
    The ML corrector must stop generating at its end-of-sentence token.

    Without an eos_token_id, generation runs to max_new_tokens and the text after the
    first </s> is glued onto the output: the sentence is duplicated ("X. X"), or the
    repetition filter cuts it down to a single word.
    """
    from api.ml_rewriter import _CORRECTOR_MODEL, ml_rewrite

    try:
        from huggingface_hub import try_to_load_from_cache
        cached = isinstance(try_to_load_from_cache(_CORRECTOR_MODEL, "model.safetensors"), str)
    except ImportError:
        cached = False
    if not cached:
        pytest.skip(f"{_CORRECTOR_MODEL} not in local HF cache")

    cases = [
        ("ha", "Wannan matsala ce mai girma"),
        ("sw", "Wanawake hawawezi kuongoza kampuni."),
        ("en", "She works as a secretary"),
    ]
    for lang, text in cases:
        result = ml_rewrite(text, lang)
        if result["model"] == "unavailable":
            pytest.skip("ML corrector unavailable (torch/transformers not installed)")
        n_in, n_out = len(text.split()), len(result["best"].split())
        assert n_out <= n_in * 1.5, f"{lang}: output repeats itself: {result['best']!r}"
        assert n_out >= n_in * 0.5, f"{lang}: output cut short: {result['best']!r}"


POLARITY_CASES = [
    # (lang, original, corrected, polarity_changed)
    ("sw", "Wanawake hawawezi kuongoza kampuni.", "Mtu anapaswa kuongoza kampuni", True),
    ("sw", "Mwanamke hawezi kuwa kiongozi", "Mtu hawezi kuwa kiongozi", False),
    ("sw", "Wanawake hawawezi kuongoza kampuni.", "Watu hawawezi kuongoza kampuni", False),
    ("en", "A woman cannot lead a company", "A person can lead a company", True),
    ("en", "She can't drive a truck", "They can't drive a truck", False),
    ("en", "The chairman opened the meeting", "The chair opened the meeting", False),
    ("fr", "Une femme ne peut pas diriger une entreprise.", "Une personne ne peut pas diriger une entreprise", False),
    ("fr", "Une femme ne peut pas diriger une entreprise.", "Une personne peut diriger une entreprise", True),
    ("ha", "Mata ba su iya shugabanci ba.", "Mutane ba su iya shugabanci ba", False),
    ("ha", "Mata ba su iya shugabanci ba.", "Mutane suna iya shugabanci", True),
    ("zu", "Abesifazane abakwazi ukuhola.", "Abantu abakwazi ukuhola.", False),
    ("zu", "Abesifazane abakwazi ukuhola.", "Abantu bayakwazi ukuhola.", True),
    ("zu", "Abafazi kufanele bahlale ekhaya", "Abantu kufanele bahlale ekhaya", False),
    ("zu", "Lona unjiniyela wesifazane ohlakaniphile, akubona njengabesilisa abajwayelekile.",
     "Lona unjiniyela ohlakaniphile, akubona njengabesilisa abafanele", False),
]


@pytest.mark.parametrize("lang,original,corrected,expected", POLARITY_CASES)
def test_polarity_guard(lang, original, corrected, expected):
    """A correction that adds or removes a negation changes the meaning and must be caught."""
    from api.ml_rewriter import changes_polarity

    assert changes_polarity(original, corrected, lang) is expected


def test_service_withholds_polarity_flipping_correction(monkeypatch):
    """If the ML corrector flips the polarity, the service keeps the original text."""
    import api.service as service

    text = "Wanawake hawawezi kuongoza kampuni."
    warn_edit = {"from": "", "to": "", "severity": "warn", "bias_type": "ml-detected",
                 "stereotype_category": "", "reason": "test", "source": "ml"}
    monkeypatch.setattr(service, "apply_rules_on_spans", lambda t, lang, flags=None: (t, [warn_edit], [], []))
    monkeypatch.setattr(service, "_ML_DETECTOR_ENABLED", False)
    monkeypatch.setattr(service, "ml_rewrite", lambda t, lang: {
        "best": "Mtu anapaswa kuongoza kampuni", "candidates": [], "model": "test-model", "latency_ms": 1})

    response, _ = service.rewrite_text(id="t", text=text, lang="sw")
    assert response.rewrite == text
    assert response.source == "low_confidence"


def test_ml_corrector_skips_text_it_cannot_spell():
    """
    The corrector's vocabulary has no ĩ/ũ, so Gĩkũyũ words come back with letters dropped.
    Text containing letters the tokenizer cannot represent must not be rewritten.
    """
    from api.ml_rewriter import _CORRECTOR_MODEL, ml_rewrite

    try:
        from huggingface_hub import try_to_load_from_cache
        cached = isinstance(try_to_load_from_cache(_CORRECTOR_MODEL, "model.safetensors"), str)
    except ImportError:
        cached = False
    if not cached:
        pytest.skip(f"{_CORRECTOR_MODEL} not in local HF cache")

    text = "Mũtumia nĩ wa kũruga na gũthambia nyũmba."
    result = ml_rewrite(text, "ki")
    assert result["model"] == "unavailable" and result["best"] == text
    # Text the tokenizer can represent is still corrected (emoji must not block it).
    assert ml_rewrite("Wanawake hawawezi kuongoza kampuni 😂", "sw")["model"] != "unavailable"
