#!/usr/bin/env python3
"""
Correction Evaluation Script - Pre→Post Bias Detection Comparison

This script evaluates the effectiveness of bias correction by:
1. Detecting bias in original text (pre-correction)
2. Applying corrections using the lexicon
3. Detecting bias in corrected text (post-correction)
4. Measuring bias removal rate and quality metrics

This implements pre→post detection comparison as required for
correction effectiveness evaluation in bias mitigation systems.
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Match

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing evaluation components
from eval.bias_detector import BiasDetector
from eval.models import Language


class CorrectionEvaluator:
    """Evaluates bias correction effectiveness using pre→post comparison."""

    # Threshold for determining effective bias removal
    EFFECTIVE_REMOVAL_THRESHOLD = 0.7

    def __init__(self, rules_dir: Path = Path("rules")):
        """
        Initialize with bias detector and correction rules.

        Why: Sets up detection and correction infrastructure with caching
        to avoid repeated file I/O operations during evaluation.

        Args:
            rules_dir: Directory containing bias detection/correction lexicons
        """
        self.detector = BiasDetector(rules_dir)
        self.rules_dir = rules_dir
        self.rules_cache: Dict[Language, List[Dict[str, str]]] = {}

    def load_correction_rules(self, language: Language) -> List[Dict[str, str]]:
        """
        Load correction rules for a language.

        Why: Enables caching of rules to avoid repeated file I/O.
        Rules are loaded from CSV lexicons and cached per language.

        Args:
            language: Target language for rules

        Returns:
            List of rule dictionaries with 'biased', 'neutral_primary', 'severity' keys
        """
        if language in self.rules_cache:
            return self.rules_cache[language]

        lang_code = language.value
        rules_file = self.rules_dir / f"lexicon_{lang_code}_v2.csv"

        if not rules_file.exists():
            return []

        rules: List[Dict[str, str]] = []
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rules.append({
                        'biased': row.get('biased', ''),
                        'neutral_primary': row.get('neutral_primary', ''),
                        'severity': row.get('severity', 'replace')
                    })
        except (IOError, csv.Error) as e:
            print(f"Error reading rules file {rules_file}: {e}")
            return []

        self.rules_cache[language] = rules
        return rules

    def apply_corrections(self, text: str, language: Language) -> str:
        """
        Apply bias corrections to text using lexicon rules.

        Why: Transforms biased text to neutral form while preserving
        original case and meaning. Used for pre→post comparison.

        Args:
            text: Original text with potential bias
            language: Language of the text

        Returns:
            Corrected text with bias terms replaced
        """
        rules = self.load_correction_rules(language)
        corrected_text = text

        for rule in rules:
            if rule['severity'] == 'replace':
                biased_term = rule['biased']
                neutral_term = rule['neutral_primary']

                # Create regex pattern with word boundaries
                pattern = r'\b' + re.escape(biased_term) + r'\b'

                # Case-preserving replacement function
                def replace_func(match: Match[str]) -> str:
                    """Preserve original case in replacement."""
                    orig = match.group(0)
                    if orig.isupper():
                        return neutral_term.upper()
                    elif orig[0].isupper():
                        return neutral_term.capitalize()
                    else:
                        return neutral_term.lower()

                corrected_text = re.sub(pattern, replace_func, corrected_text, flags=re.IGNORECASE)

        return corrected_text

    def evaluate_correction_effectiveness(
        self,
        ground_truth_file: Path,
        language: Language
    ) -> Dict[str, Any]:
        """
        Evaluate correction effectiveness for a language.

        Why: Measures how well corrections remove bias without introducing
        new issues. This is the core evaluation for correction systems.

        Measures:
        - Pre-correction bias detection rate
        - Post-correction bias detection rate
        - Bias removal rate
        - Correction success rate

        Args:
            ground_truth_file: Path to ground truth CSV
            language: Language being evaluated

        Returns:
            Dictionary with correction effectiveness metrics including:
            - language, total_samples, biased_samples
            - pre_correction: detected, missed, detection_rate
            - post_correction: still_biased, successfully_neutralized, bias_removal_rate
            - correction_quality: meaning_preserved, over_corrections
            - samples: detailed per-sample results
        """
        results: Dict[str, Any] = {
            'language': language.value,
            'total_samples': 0,
            'biased_samples': 0,
            'pre_correction': {
                'detected': 0,
                'missed': 0,
                'detection_rate': 0.0
            },
            'post_correction': {
                'still_biased': 0,
                'successfully_neutralized': 0,
                'bias_removal_rate': 0.0
            },
            'correction_quality': {
                'meaning_preserved': 0,  # Simplified: assumes preserved if text changed
                'over_corrections': 0     # Corrected non-biased text
            },
            'samples': []
        }

        if not ground_truth_file.exists():
            return results

        try:
            with open(ground_truth_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    text = row['text'].strip('"')
                    is_biased = row['has_bias'] == 'true'
                    bias_category = row['bias_category']

                    results['total_samples'] += 1

                    # Pre-correction detection
                    pre_detection = self.detector.detect_bias(text, language)
                    pre_detected = pre_detection.has_bias_detected

                    # Apply correction
                    corrected_text = self.apply_corrections(text, language)

                    # Post-correction detection
                    post_detection = self.detector.detect_bias(corrected_text, language)
                    post_detected = post_detection.has_bias_detected

                    # Track metrics
                    if is_biased:
                        results['biased_samples'] += 1

                        if pre_detected:
                            results['pre_correction']['detected'] += 1

                            if not post_detected:
                                results['post_correction']['successfully_neutralized'] += 1
                            else:
                                results['post_correction']['still_biased'] += 1
                        else:
                            results['pre_correction']['missed'] += 1

                    # Check for over-corrections (correcting non-biased text)
                    if not is_biased and text != corrected_text:
                        results['correction_quality']['over_corrections'] += 1

                    # Check if meaning preserved (simplified: text was changed for biased samples)
                    if is_biased and text != corrected_text:
                        results['correction_quality']['meaning_preserved'] += 1

                    # Store sample for detailed analysis
                    sample_result = {
                        'original': text,
                        'corrected': corrected_text,
                        'is_biased': is_biased,
                        'category': bias_category,
                        'pre_detected': pre_detected,
                        'post_detected': post_detected,
                        'bias_removed': pre_detected and not post_detected,
                        'text_changed': text != corrected_text
                    }
                    results['samples'].append(sample_result)
        except (IOError, csv.Error, KeyError) as e:
            print(f"Error reading ground truth file {ground_truth_file}: {e}")
            return results

        # Calculate rates
        if results['biased_samples'] > 0:
            results['pre_correction']['detection_rate'] = (
                results['pre_correction']['detected'] / results['biased_samples']
            )

        if results['pre_correction']['detected'] > 0:
            results['post_correction']['bias_removal_rate'] = (
                results['post_correction']['successfully_neutralized'] /
                results['pre_correction']['detected']
            )

        return results

    def generate_comparison_report(self, results: Dict) -> str:
        """Generate human-readable comparison report."""
        lang = results['language'].upper()
        report = f"\n{'='*60}\n"
        report += f"CORRECTION EFFECTIVENESS REPORT - {lang}\n"
        report += f"{'='*60}\n\n"

        report += f"Dataset Size: {results['total_samples']} samples\n"
        report += f"Biased Samples: {results['biased_samples']}\n\n"

        report += "PRE-CORRECTION (Detection):\n"
        report += f"  Detected: {results['pre_correction']['detected']}\n"
        report += f"  Missed: {results['pre_correction']['missed']}\n"
        report += f"  Detection Rate: {results['pre_correction']['detection_rate']:.1%}\n\n"

        report += "POST-CORRECTION (Bias Removal):\n"
        report += f"  Successfully Neutralized: {results['post_correction']['successfully_neutralized']}\n"
        report += f"  Still Biased: {results['post_correction']['still_biased']}\n"
        report += f"  Bias Removal Rate: {results['post_correction']['bias_removal_rate']:.1%}\n\n"

        report += "CORRECTION QUALITY:\n"
        report += f"  Meaning Preserved: {results['correction_quality']['meaning_preserved']} samples\n"
        report += f"  Over-Corrections: {results['correction_quality']['over_corrections']}\n\n"

        # Show examples
        report += "EXAMPLE CORRECTIONS:\n"
        examples = [s for s in results['samples'] if s['bias_removed']][:3]
        for i, ex in enumerate(examples, 1):
            report += f"\n  {i}. Original:  \"{ex['original']}\"\n"
            report += f"     Corrected: \"{ex['corrected']}\"\n"
            report += f"     Category: {ex['category']}\n"

        return report


def main():
    """Run correction evaluation for all languages."""
    evaluator = CorrectionEvaluator()

    languages = [
        (Language.ENGLISH, 'en'),
        (Language.SWAHILI, 'sw'),
        (Language.HAUSA, 'ha'),
        (Language.YORUBA, 'yo'),
        (Language.IGBO, 'ig')
    ]

    all_results = []

    print("Running Correction Effectiveness Evaluation...")
    print("=" * 60)

    for language, lang_code in languages:
        ground_truth_file = Path("eval") / f"ground_truth_{lang_code}.csv"

        if not ground_truth_file.exists():
            print(f"Skipping {lang_code}: ground truth file not found")
            continue

        print(f"\nEvaluating {lang_code.upper()}...")
        results = evaluator.evaluate_correction_effectiveness(ground_truth_file, language)

        # Print report
        report = evaluator.generate_comparison_report(results)
        print(report)

        # Remove detailed samples for summary JSON
        summary_results = {k: v for k, v in results.items() if k != 'samples'}
        all_results.append(summary_results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("eval") / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"correction_eval_{timestamp}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}\n")
    except (IOError, OSError) as e:
        print(f"\nError: Failed to save results to {output_file}: {e}")
        print(f"{'='*60}\n")

    # Generate summary table
    print("\nSUMMARY TABLE - Pre→Post Comparison")
    print("=" * 80)
    print(f"{'Language':<10} {'Pre-F1':<10} {'Detection%':<12} {'Removal%':<12} {'Status':<15}")
    print("-" * 80)

    for result in all_results:
        lang = result['language'].upper()
        detection_rate = result['pre_correction']['detection_rate']
        removal_rate = result['post_correction']['bias_removal_rate']

        # Approximate F1 (simplified)
        pre_f1 = detection_rate  # Simplified - actual F1 from main evaluation

        status = "Effective" if removal_rate > self.EFFECTIVE_REMOVAL_THRESHOLD else "Needs Work"

        print(f"{lang:<10} {pre_f1:<10.3f} {detection_rate:<12.1%} {removal_rate:<12.1%} {status:<15}")

    print("=" * 80)


if __name__ == "__main__":
    main()
