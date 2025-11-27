#!/usr/bin/env python3
"""
Complete system demo showing all capabilities
"""
import time
from eval.bias_detector import BiasDetector
from eval.hybrid_detector import HybridBiasDetector
from eval.mt5_corrector import MT5BiasCorrector
from eval.models import Language

def demo_detection():
    """Demo bias detection capabilities"""
    print("🔍 BIAS DETECTION DEMO")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("The chairman will lead the meeting", Language.ENGLISH),
        ("Mwalimu mkuu atakuwa hapa", Language.SWAHILI),
        ("The nurse should check her patients", Language.ENGLISH)
    ]
    
    # Initialize detectors
    rules_detector = BiasDetector()
    hybrid_detector = HybridBiasDetector()
    
    for text, lang in test_cases:
        print(f"\n📝 Text: '{text}' ({lang.value})")
        
        # Rules-based detection
        rules_result = rules_detector.detect_bias(text, lang)
        print(f"   Rules: {'✅ BIAS' if rules_result.has_bias_detected else '❌ No bias'}")
        if rules_result.detected_edits:
            for edit in rules_result.detected_edits:
                print(f"     → {edit['from']} → {edit['to']}")
        
        # Hybrid detection
        hybrid_result = hybrid_detector.detect_bias(text, lang)
        print(f"   Hybrid: {'✅ BIAS' if hybrid_result.has_bias_detected else '❌ No bias'}")

def demo_correction():
    """Demo bias correction with MT5"""
    print("\n\n🔧 BIAS CORRECTION DEMO")
    print("=" * 50)
    
    try:
        corrector = MT5BiasCorrector()
        
        test_texts = [
            ("The chairman will announce the results", Language.ENGLISH),
            ("Every businessman should check his profits", Language.ENGLISH)
        ]
        
        for text, lang in test_texts:
            print(f"\n📝 Original: '{text}'")
            result = corrector.correct_bias(text, lang)
            print(f"   Corrected: '{result['best_correction']}'")
            print(f"   Model: {result['model']} ({result['latency_ms']}ms)")
            
            if len(result['candidates']) > 1:
                print("   Alternatives:")
                for i, candidate in enumerate(result['candidates'][1:], 2):
                    print(f"     {i}. {candidate}")
                    
    except ImportError:
        print("⚠️  MT5 correction requires: pip install transformers torch")

def demo_api_simulation():
    """Simulate API usage"""
    print("\n\n🌐 API SIMULATION DEMO")
    print("=" * 50)
    
    # Simulate API request/response
    api_request = {
        "id": "demo-001",
        "lang": "en", 
        "text": "The policeman arrested the suspect",
        "flags": None
    }
    
    print(f"📤 API Request:")
    print(f"   Text: '{api_request['text']}'")
    print(f"   Language: {api_request['lang']}")
    
    # Simulate processing
    detector = BiasDetector()
    result = detector.detect_bias(api_request['text'], Language.ENGLISH)
    
    api_response = {
        "id": api_request["id"],
        "original_text": api_request["text"],
        "rewrite": "The police officer arrested the suspect",
        "edits": result.detected_edits,
        "confidence": 0.85,
        "needs_review": False,
        "source": "rules"
    }
    
    print(f"\n📥 API Response:")
    print(f"   Rewrite: '{api_response['rewrite']}'")
    print(f"   Confidence: {api_response['confidence']}")
    print(f"   Source: {api_response['source']}")
    print(f"   Edits: {len(api_response['edits'])} changes")

def demo_evaluation_metrics():
    """Show evaluation results"""
    print("\n\n📊 EVALUATION METRICS DEMO")
    print("=" * 50)
    
    # Simulated F1 scores from actual evaluation
    metrics = {
        "English": {"f1": 0.764, "precision": 1.000, "recall": 0.618},
        "Swahili": {"f1": 0.681, "precision": 1.000, "recall": 0.516},
        "French": {"f1": 0.627, "precision": 1.000, "recall": 0.457},
        "Gikuyu": {"f1": 0.714, "precision": 1.000, "recall": 0.556}
    }
    
    print("Language    | F1    | Precision | Recall | Status")
    print("-" * 50)
    for lang, m in metrics.items():
        status = "Excellent" if m["f1"] > 0.9 else "Good" if m["f1"] > 0.7 else "Moderate"
        print(f"{lang:<11} | {m['f1']:.3f} | {m['precision']:.3f}     | {m['recall']:.3f}  | {status}")

def main():
    """Run complete demo"""
    print("🚀 JuaKazi Gender Sensitization Engine - Complete Demo")
    print("=" * 60)
    
    demo_detection()
    demo_correction()
    demo_api_simulation()
    demo_evaluation_metrics()
    
    print("\n\n✨ Demo Complete!")
    print("\nNext Steps:")
    print("• Start API: uvicorn api.main:app --reload")
    print("• Start UI: streamlit run review_ui/app.py")
    print("• Run evaluation: python3 eval/run_evaluation.py")

if __name__ == "__main__":
    main()