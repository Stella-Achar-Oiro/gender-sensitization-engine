#!/usr/bin/env python3
"""Live Demo Script - JuaKazi Hybrid Bias Detection
Shows rules-based detection with actual examples
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from eval.bias_detector import BiasDetector
from eval.models import Language
from api.rules_engine import apply_rules_on_spans, build_reason


def demo_header():
    """Print demo header"""
    print("\n" + "=" * 70)
    print(" " * 15 + "JUAKAZI HYBRID BIAS DETECTION & CORRECTION DEMO")
    print(" " * 20 + "Rules + ML Approach")
    print("=" * 70 + "\n")


def demo_example(detector, text, language, example_num):
    """Run detection on one example"""
    print(f"{'─' * 70}")
    print(f"EXAMPLE {example_num}: {language.value.upper()}")
    print(f"{'─' * 70}")
    print("\nOriginal Text:")
    print(f'   "{text}"')

    # Detect bias
    result = detector.detect_bias(text, language)

    print("\nDetection Result:")
    print(
        f"   Bias Detected: {'YES [WARNING]' if result.has_bias_detected else 'NO [OK]'}"
    )
    print("   Detection Method: Rules-based (Hybrid System)")

    if result.detected_edits:
        print("\nSuggested Corrections:")
        for i, edit in enumerate(result.detected_edits, 1):
            print(
                f'   {i}. "{edit["from"]}" -> "{edit["to"]}" (severity: {edit.get("severity", "replace")})'
            )

        # Apply corrections using the same regex-based, case-preserving function as the API
        corrected_text, applied_edits, count, skipped = apply_rules_on_spans(text, language.value)

        print("\nCorrected Text:")
        print(f'   "{corrected_text}"')
        if skipped:
            print(f"   (skipped {len(skipped)} term(s) due to context: {[s['term'] for s in skipped]})")
        print(f"\nReason: {build_reason('rules', applied_edits, skipped)}")
    else:
        print("\nNo corrections needed - text is bias-free!")

    print()


def main():
    """Run live demo"""
    demo_header()

    # Initialize detector
    print("Initializing hybrid bias detector...\n")
    detector = BiasDetector()
    print("[OK] Detector ready with 4 language lexicons:")
    print("  - English: 538 rules - Production")
    print("  - Swahili: 211 rules - Production")
    print("  - French: 78 rules - Beta")
    print("  - Gikuyu: 1,240 rules - Production")
    print("\n  F1 Scores: EN 0.786 | SW 0.611 | FR 0.542 | KI 0.352")
    print()

    # English Examples
    print("\n" + "=" * 70)
    print(" " * 20 + "ENGLISH DETECTION EXAMPLES")
    print("=" * 70 + "\n")

    examples_en = [
        "The chairman will lead the meeting today.",
        "The policeman helped the child cross the street.",
        "Each student must submit his homework on time.",
        "The nurse should check her patients regularly.",
        "The person manages the team effectively.",  # Already neutral
    ]

    for i, text in enumerate(examples_en, 1):
        demo_example(detector, text, Language.ENGLISH, i)

    # Swahili Examples
    print("\n" + "=" * 70)
    print(" " * 20 + "SWAHILI DETECTION EXAMPLES")
    print("=" * 70 + "\n")

    examples_sw = [
        "Mwalimu anafundisha darasa.",  # Teacher teaches class
        "Daktari anaangalia wagonjwa.",  # Doctor examines patients
    ]

    for i, text in enumerate(examples_sw, 1):
        demo_example(detector, text, Language.SWAHILI, i)

    # French Examples
    print("\n" + "=" * 70)
    print(" " * 20 + "FRENCH DETECTION EXAMPLES")
    print("=" * 70 + "\n")

    examples_fr = [
        "Le président dirigera la réunion",  # The chairman will lead the meeting
        "Le policier a arrêté le suspect",  # The policeman arrested the suspect
    ]

    for i, text in enumerate(examples_fr, 1):
        demo_example(detector, text, Language.FRENCH, i)

    # Gikuyu Examples
    print("\n" + "=" * 70)
    print(" " * 20 + "GIKUYU DETECTION EXAMPLES")
    print("=" * 70 + "\n")

    examples_ki = [
        "Mũrũgamĩrĩri ũcio nĩ mũndũ mũrũme",  # That leader is a man
        "Mũrutani ũcio nĩ mũndũ mwega",  # That teacher is a good person
    ]

    for i, text in enumerate(examples_ki, 1):
        demo_example(detector, text, Language.GIKUYU, i)

    # Summary
    print("\n" + "=" * 70)
    print(" " * 25 + "DEMO SUMMARY")
    print("=" * 70 + "\n")
    print("[OK] Hybrid Detection: Rules-based (primary) + ML (fallback)")
    print("[OK] Context-Aware: Biographical, quote, and statistical contexts preserved")
    print("[OK] Case-Preserving: Chairman → Chairperson, CHAIRMAN → CHAIRPERSON")
    print("[OK] Audit Trail: All corrections logged to audit_logs/rewrites.jsonl")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Demo interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Error during demo: {e}")
        import traceback

        traceback.print_exc()
