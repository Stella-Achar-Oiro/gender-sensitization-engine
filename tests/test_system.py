#!/usr/bin/env python3
"""
Core system tests for JuaKazi — verifies the rules engine, API, and lexicons
work end-to-end. Must pass 4/4 before merging to main.
"""
import sys
from pathlib import Path

# Ensure project root is on path when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test all core imports work (ML dependencies are optional)."""
    try:
        from api.main import app
        from api.rules_engine import apply_rules_on_spans, build_reason
        print("API import OK")
    except Exception as e:
        print(f"Import failed: {e}")
        return False

    try:
        from api.ml_rewriter import ml_rewrite, _ML_AVAILABLE
        print(f"ml_rewriter import OK (ML available: {_ML_AVAILABLE})")
    except Exception as e:
        print(f"ml_rewriter import failed: {e}")
        return False

    try:
        from eval.bias_detector import BiasDetector
        from eval.models import Language
        print("eval imports OK")
    except Exception as e:
        print(f"eval import failed: {e}")
        return False

    return True


def test_lexicon():
    """Test current v3 lexicons load without errors."""
    try:
        import csv
        lexicons = {
            'en': 'rules/lexicon_en_v3.csv',
            'sw': 'rules/lexicon_sw_v3.csv',
        }
        for lang, path in lexicons.items():
            with open(path, newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            assert len(rows) > 0, f"{path} is empty"
            print(f"  {lang}: {len(rows)} rules loaded from {path}")
        return True
    except Exception as e:
        print(f"Lexicon loading failed: {e}")
        return False


def test_correction():
    """Test bias correction pipeline returns correct structure."""
    try:
        from api.rules_engine import apply_rules_on_spans

        test_cases = [
            ("The chairman met with the waitress.", "en"),
            ("Every businessman needs skills.", "en"),
        ]

        for text, lang in test_cases:
            # apply_rules_on_spans returns (rewritten_text, edits, matched_count, skipped_context)
            result, edits, count, skipped = apply_rules_on_spans(text, lang)
            print(f"  '{text[:50]}' → '{result[:50]}' ({count} edits, {len(skipped)} skipped)")

        return True
    except Exception as e:
        print(f"Correction failed: {e}")
        return False


def test_reason():
    """Test build_reason produces correct strings for each source type."""
    try:
        from api.rules_engine import apply_rules_on_spans, build_reason

        cases = [
            # (text, lang, expected_source, substring_in_reason)
            ("The chairman will lead.", "en", "rules", "1 biased term(s) corrected"),
            ("Hello world.", "en", "rules", "No gender bias detected"),
        ]

        for text, lang, source, expected_substr in cases:
            _, edits, _, skipped = apply_rules_on_spans(text, lang)
            reason = build_reason(source, edits, skipped)
            ok = expected_substr in reason
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] '{text[:40]}' → reason: {reason!r}")
            if not ok:
                return False

        # Test preserved and ml sources directly
        preserved_reason = build_reason("preserved", [], [])
        assert "preserved" in preserved_reason.lower(), f"Unexpected: {preserved_reason!r}"
        print(f"  [OK] preserved → {preserved_reason!r}")

        ml_reason = build_reason("ml", [], [])
        assert "ml" in ml_reason.lower() or "fallback" in ml_reason.lower(), f"Unexpected: {ml_reason!r}"
        print(f"  [OK] ml → {ml_reason!r}")

        return True
    except Exception as e:
        print(f"Reason test failed: {e}")
        return False


def test_api_validation():
    """Test API request validation: invalid lang, empty text, max length, batch shape."""
    try:
        from pydantic import ValidationError
        from api.schemas import RewriteRequest, BatchRewriteRequest

        # Valid request
        req = RewriteRequest(id="v1", lang="en", text="Hello world.")
        assert req.lang == "en" and len(req.text) <= 5000

        # Invalid lang → ValidationError
        try:
            RewriteRequest(id="x", lang="xx", text="Hi")
            print("  [FAIL] invalid lang should raise ValidationError")
            return False
        except ValidationError:
            print("  [OK] invalid lang → 422")

        # Empty text → ValidationError (min_length=1)
        try:
            RewriteRequest(id="x", lang="en", text="")
            print("  [FAIL] empty text should raise ValidationError")
            return False
        except ValidationError:
            print("  [OK] empty text → 422")

        # Text over 5000 chars → ValidationError
        try:
            RewriteRequest(id="x", lang="en", text="a" * 5001)
            print("  [FAIL] text over 5000 should raise ValidationError")
            return False
        except ValidationError:
            print("  [OK] text max_length=5000 → 422")

        # Batch: empty items → ValidationError
        try:
            BatchRewriteRequest(items=[])
            print("  [FAIL] empty items should raise ValidationError")
            return False
        except ValidationError:
            print("  [OK] batch empty items → 422")

        # Batch: valid shape
        batch = BatchRewriteRequest(items=[{"id": "b1", "lang": "en", "text": "Test"}])
        assert len(batch.items) == 1
        print("  [OK] batch valid shape accepted")
        return True
    except Exception as e:
        print(f"API validation test failed: {e}")
        return False


def test_detector():
    """
    Test BiasDetector directly — rules engine, all languages, all major pattern categories.

    Each case: (text, language, expect_bias_detected, label)
    Covers: EN/SW/FR bias detection, counter-stereotype preservation,
    neutral pass-through, all SW pattern categories added in Sprint 3.
    Failure here means a regression in the core detection layer.
    """
    try:
        from eval.bias_detector import BiasDetector
        from eval.models import Language
        from pathlib import Path

        detector = BiasDetector(rules_dir=Path("rules"))
        failures = []

        cases = [
            # ── English ─────────────────────────────────────────────────────────
            ("The chairman will lead the meeting.", Language.ENGLISH, True,
             "EN: gendered occupation term 'chairman'"),
            ("The engineer arrived on time.", Language.ENGLISH, False,
             "EN: neutral occupation, no bias"),
            ("Women can't drive.", Language.ENGLISH, True,
             "EN: capability derogation"),
            ("The nurse did an excellent job.", Language.ENGLISH, False,
             "EN: neutral sentence"),

            # ── Swahili — occupation suffix (wa kiume / wa kike) ────────────────
            ("Daktari wa kiume alifika hospitalini.", Language.SWAHILI, True,
             "SW: gendered profession suffix 'wa kiume'"),
            ("Mhandisi wa kike alishinda tuzo.", Language.SWAHILI, True,
             "SW: gendered profession suffix 'wa kike'"),

            # ── Swahili — capability derogation ─────────────────────────────────
            ("Wanawake hawawezi kuongoza kwa sababu wana hisia nyingi.",
             Language.SWAHILI, True,
             "SW: capability — women can't lead"),
            ("Mwanamke hawezi kuwa rubani mzuri kwa sababu anaogopa hali ya hewa.",
             Language.SWAHILI, True,
             "SW: capability — woman can't be pilot (counter-stereotype fix)"),
            ("Mwanamke ni dhaifu, hawezi kufanya kazi ngumu.",
             Language.SWAHILI, True,
             "SW: capability — dhaifu assertion"),
            ("Msichana anadhani hawezi kubalika, anamkimbilia.",
             Language.SWAHILI, True,
             "SW: capability — self-doubt pattern"),

            # ── Swahili — appearance ─────────────────────────────────────────────
            ("Katika jamii ya kitanzania, binti wa kike kukaa utupu hadharani ni matusi kwake.",
             Language.SWAHILI, True,
             "SW: appearance — body shame"),
            ("Wasanii wa kike nchini kutumia makalio feki ili kuonekana warembo.",
             Language.SWAHILI, True,
             "SW: appearance — fake body parts stereotype"),
            ("Mavazi ya nusu utupu ambayo huwa yanavaliwa na baadhi ya wasanii wa kike.",
             Language.SWAHILI, True,
             "SW: appearance — appearance policing"),

            # ── Swahili — family role / domestic ────────────────────────────────
            ("Mwanamke hapaswi kubishana na mume wake kamwe.",
             Language.SWAHILI, True,
             "SW: family_role — wife must not argue"),
            ("Wanawake ni mama wa nyumbani, wana shughuli nyingi za kufua na kupika.",
             Language.SWAHILI, True,
             "SW: family_role — women as homemakers"),
            ("Mwanamke umekuja tu kuolewa, huna haki ya kurithi.",
             Language.SWAHILI, True,
             "SW: family_role — inheritance denial"),
            ("Usimwamini mke anayependa kununua chakula cha tayari badala ya kupika.",
             Language.SWAHILI, True,
             "SW: family_role — cooking duty stereotype"),
            ("Tuliomba mtoto wetu angekuwa wa kiume, tukimtabiria makubwa.",
             Language.SWAHILI, True,
             "SW: family_role — son preference"),

            # ── Swahili — violence / IPV normalisation ───────────────────────────
            ("Mke mkaidi anahitaji kupigwa kidogo ili arudi kwenye mstari.",
             Language.SWAHILI, True,
             "SW: violence — IPV normalisation"),
            ("Kibao kimoja si ukatili, ni njia ya kumrudisha mwanamke kwenye adabu.",
             Language.SWAHILI, True,
             "SW: violence — beating framed as discipline"),

            # ── Swahili — daily life / school / grooming ─────────────────────────
            ("Wanafunzi watakaopata ujauzito wakiwa shuleni hawataruhusiwa tena kurudi.",
             Language.SWAHILI, True,
             "SW: daily_life — pregnancy expulsion policy"),
            ("Shule ilianzisha mpango wa kuwapima bikira wanafunzi wa kike.",
             Language.SWAHILI, True,
             "SW: daily_life — virginity testing"),
            ("Ni rahisi kuwarubuni wanafunzi wa kike kwa zawadi ndogo.",
             Language.SWAHILI, True,
             "SW: daily_life — grooming female students"),
            ("Wanaume ndio tunaoongoza kulazimisha mtu asivae kinga.",
             Language.SWAHILI, True,
             "SW: daily_life — forced unprotected sex"),
            ("Rushwa ya ngono vyuoni hutokea walimu wanapotumia nafasi zao.",
             Language.SWAHILI, True,
             "SW: daily_life — sexual bribery"),

            # ── Swahili — male emotional suppression ────────────────────────────
            ("Mwanaume hapaswi kuonyesha udhaifu wala kulia mbele ya watu.",
             Language.SWAHILI, True,
             "SW: daily_life — male emotional suppression"),
            ("Kulia ni kazi ya wanawake; mwanaume ana moyo wa chuma.",
             Language.SWAHILI, True,
             "SW: daily_life — crying is for women"),

            # ── Swahili — counter-stereotype (must NOT fire as bias) ─────────────
            ("Mwanamke huyu ni rubani mzuri sana, ana uzoefu wa miaka kumi.",
             Language.SWAHILI, False,
             "SW counter-stereotype: woman IS a good pilot"),
            ("Baba huyu analela watoto wake peke yake na kupika kila siku.",
             Language.SWAHILI, False,
             "SW counter-stereotype: father does domestic work"),
            ("Msichana huyo ni mkurugenzi mkuu wa kampuni kubwa.",
             Language.SWAHILI, False,
             "SW counter-stereotype: girl in leadership"),

            # ── Swahili — neutral (must NOT fire) ───────────────────────────────
            ("Serikali imewapa wasichana nafasi za masomo ya nje ya nchi.",
             Language.SWAHILI, False,
             "SW neutral: government helping girls — no bias"),
            ("Wanafunzi wa kike wanaendelea vizuri katika masomo ya sayansi.",
             Language.SWAHILI, False,
             "SW neutral: female students doing well"),
            ("Daktari alifika hospitalini na kufanya kazi nzuri.",
             Language.SWAHILI, False,
             "SW neutral: doctor (no gender marker)"),

            # ── French ───────────────────────────────────────────────────────────
            ("Le président a ouvert la réunion.", Language.FRENCH, True,
             "FR: gendered occupation 'président'"),
            ("La réunion a bien commencé.", Language.FRENCH, False,
             "FR: neutral sentence"),
        ]

        for text, lang, expect_bias, label in cases:
            result = detector.detect_bias(text, lang)
            ok = result.has_bias_detected == expect_bias
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {label}")
            if not ok:
                direction = "expected BIAS but got neutral" if expect_bias else "expected NEUTRAL but got bias"
                print(f"         → {direction}: {repr(text[:80])}")
                failures.append(label)

        if failures:
            print(f"\n  {len(failures)} failure(s):")
            for f in failures:
                print(f"    - {f}")
            return False

        print(f"\n  All {len(cases)} detector cases passed.")
        print(f"  FastAPI app title: {__import__('api.main', fromlist=['app']).app.title}")
        return True
    except Exception as e:
        import traceback
        print(f"Detector test failed: {e}")
        traceback.print_exc()
        return False


def main():
    print("Testing JuaKazi System")
    print("=" * 40)

    tests = [
        ("Imports", test_imports),
        ("Lexicons", test_lexicon),
        ("Correction API", test_correction),
        ("Reason Generation", test_reason),
        ("API validation", test_api_validation),
        ("Bias Detector", test_detector),
    ]

    passed = 0
    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        if test_fn():
            passed += 1
            print(f"PASS")
        else:
            print(f"FAIL")

    print("\n" + "=" * 40)
    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("All systems operational — safe to merge.")
        return 0
    else:
        print("Fix failures before merging.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
