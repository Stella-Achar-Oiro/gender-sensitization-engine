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
        from api.main import app, apply_rules_on_spans
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
        from api.main import apply_rules_on_spans

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


def test_detector():
    """Test BiasDetector directly — the core rules engine."""
    try:
        from eval.bias_detector import BiasDetector
        from eval.models import Language

        detector = BiasDetector()

        cases = [
            ("The chairman will lead the meeting.", Language.ENGLISH, True),
            ("The engineer arrived on time.", Language.ENGLISH, False),
        ]

        for text, lang, expect_bias in cases:
            result = detector.detect_bias(text, lang)
            status = "OK" if result.has_bias_detected == expect_bias else "FAIL"
            print(f"  [{status}] '{text[:50]}' → bias={result.has_bias_detected} (expected {expect_bias})")
            if result.has_bias_detected != expect_bias:
                return False

        print(f"FastAPI app title: {__import__('api.main', fromlist=['app']).app.title}")
        return True
    except Exception as e:
        print(f"Detector test failed: {e}")
        return False


def main():
    print("Testing JuaKazi System")
    print("=" * 40)

    tests = [
        ("Imports", test_imports),
        ("Lexicons", test_lexicon),
        ("Correction API", test_correction),
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
