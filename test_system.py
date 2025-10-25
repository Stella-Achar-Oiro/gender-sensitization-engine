#!/usr/bin/env python3
"""
Quick system test to verify JuaKazi is working
"""
import sys
from pathlib import Path

def test_imports():
    """Test all core imports work"""
    try:
        from api.main import app, apply_rules_on_spans
        from api.ml_rewriter import ml_rewrite
        import pandas as pd
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_lexicon():
    """Test lexicon loading"""
    try:
        import pandas as pd
        en_lexicon = pd.read_csv('rules/lexicon_en_v2.csv')
        sw_lexicon = pd.read_csv('rules/lexicon_sw_v2.csv')
        print(f"✅ Lexicons loaded: {len(en_lexicon)} EN, {len(sw_lexicon)} SW rules")
        return True
    except Exception as e:
        print(f"❌ Lexicon loading failed: {e}")
        return False

def test_correction():
    """Test bias correction"""
    try:
        from api.main import apply_rules_on_spans
        
        test_cases = [
            ("The chairman met with the waitress.", "en"),
            ("Every businessman needs skills.", "en"),
        ]
        
        for text, lang in test_cases:
            result, edits, count = apply_rules_on_spans(text, lang)
            print(f"✅ '{text}' → '{result}' ({count} edits)")
        
        return True
    except Exception as e:
        print(f"❌ Correction failed: {e}")
        return False

def test_api_structure():
    """Test API can be created"""
    try:
        from api.main import app
        print(f"✅ FastAPI app created: {app.title}")
        return True
    except Exception as e:
        print(f"❌ API creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing JuaKazi System")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_lexicon, 
        test_correction,
        test_api_structure
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())