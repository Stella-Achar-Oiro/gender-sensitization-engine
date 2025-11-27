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
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Match, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing evaluation components
from eval.bias_detector import BiasDetector
from eval.models import Language, BiasCategory
from eval.data_loader import GroundTruthLoader, ResultsWriter


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
        self.rules_cache: dict[Language, list[dict[str, str]]] = {}

    def load_correction_rules(self, language: Language) -> list[dict[str, str]]:
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

        rules: list[dict[str, str]] = []
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
        language: Language
    ) -> dict[str, Any]:
        """
        Evaluate correction effectiveness for a language with detailed category breakdown.

        Why: Measures how well corrections remove bias without introducing
        new issues. This is the core evaluation for correction systems.

        Measures:
        - Pre-correction bias detection rate (overall and per-category)
        - Post-correction bias detection rate
        - Bias removal rate
        - Correction success rate
        - Per-category correction effectiveness

        Args:
            language: Language being evaluated

        Returns:
            Dictionary with comprehensive correction effectiveness metrics including:
            - language, total_samples, biased_samples
            - overall_metrics: aggregated pre/post detection and removal rates
            - category_metrics: per-category correction effectiveness
            - correction_quality: over-corrections, meaning preservation
            - confusion_matrices: detailed TP/FP/TN/FN for pre and post
            - samples: detailed per-sample results
        """
        # Load ground truth data
        loader = GroundTruthLoader(Path("eval"))
        try:
            ground_truth = loader.load_ground_truth(language)
        except Exception as e:
            print(f"Error loading ground truth for {language.value}: {e}")
            return self._empty_results(language)

        # Initialize results structure
        results: Dict[str, Any] = {
            'language': language.value,
            'total_samples': len(ground_truth),
            'biased_samples': sum(1 for gt in ground_truth if gt.has_bias),
            'overall_metrics': {
                'pre_correction': {
                    'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0,
                    'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0
                },
                'post_correction': {
                    'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0,
                    'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0
                },
                'bias_removal_rate': 0.0,
                'bias_removal_count': 0,
                'detected_and_removed': 0
            },
            'category_metrics': {},
            'correction_quality': {
                'meaning_preserved': 0,
                'over_corrections': 0,
                'successful_corrections': 0
            },
            'samples': []
        }

        # Initialize category tracking
        category_data = defaultdict(lambda: {
            'pre_tp': 0, 'pre_fp': 0, 'pre_tn': 0, 'pre_fn': 0,
            'post_tp': 0, 'post_fp': 0, 'post_tn': 0, 'post_fn': 0,
            'bias_removed': 0, 'detected_count': 0
        })

        # Process each sample
        for gt_sample in ground_truth:
            text = gt_sample.text
            is_biased = gt_sample.has_bias
            category = gt_sample.bias_category

            # Pre-correction detection
            pre_detection = self.detector.detect_bias(text, language)
            pre_detected = pre_detection.has_bias_detected

            # Apply correction
            corrected_text = self.apply_corrections(text, language)

            # Post-correction detection
            post_detection = self.detector.detect_bias(corrected_text, language)
            post_detected = post_detection.has_bias_detected

            # Update overall confusion matrices
            # Pre-correction matrix
            if pre_detected and is_biased:
                results['overall_metrics']['pre_correction']['tp'] += 1
            elif pre_detected and not is_biased:
                results['overall_metrics']['pre_correction']['fp'] += 1
            elif not pre_detected and is_biased:
                results['overall_metrics']['pre_correction']['fn'] += 1
            else:
                results['overall_metrics']['pre_correction']['tn'] += 1

            # Post-correction matrix
            if post_detected and is_biased:
                results['overall_metrics']['post_correction']['tp'] += 1
            elif post_detected and not is_biased:
                results['overall_metrics']['post_correction']['fp'] += 1
            elif not post_detected and is_biased:
                results['overall_metrics']['post_correction']['fn'] += 1
            else:
                results['overall_metrics']['post_correction']['tn'] += 1

            # Track bias removal
            bias_removed = pre_detected and not post_detected
            if bias_removed and is_biased:
                results['overall_metrics']['bias_removal_count'] += 1
                results['overall_metrics']['detected_and_removed'] += 1

            # Update category-specific metrics
            if category != BiasCategory.NONE:
                cat_data = category_data[category]

                # Pre-correction
                if pre_detected and is_biased:
                    cat_data['pre_tp'] += 1
                elif pre_detected and not is_biased:
                    cat_data['pre_fp'] += 1
                elif not pre_detected and is_biased:
                    cat_data['pre_fn'] += 1
                else:
                    cat_data['pre_tn'] += 1

                # Post-correction
                if post_detected and is_biased:
                    cat_data['post_tp'] += 1
                elif post_detected and not is_biased:
                    cat_data['post_fp'] += 1
                elif not post_detected and is_biased:
                    cat_data['post_fn'] += 1
                else:
                    cat_data['post_tn'] += 1

                if pre_detected:
                    cat_data['detected_count'] += 1
                if bias_removed and is_biased:
                    cat_data['bias_removed'] += 1

            # Correction quality metrics
            if not is_biased and text != corrected_text:
                results['correction_quality']['over_corrections'] += 1
            if is_biased and bias_removed:
                results['correction_quality']['successful_corrections'] += 1
            if is_biased and text != corrected_text:
                results['correction_quality']['meaning_preserved'] += 1

            # Store sample details
            results['samples'].append({
                'original': text,
                'corrected': corrected_text,
                'is_biased': is_biased,
                'category': category.value,
                'pre_detected': pre_detected,
                'post_detected': post_detected,
                'bias_removed': bias_removed,
                'text_changed': text != corrected_text,
                'pre_edits': pre_detection.detected_edits,
                'post_edits': post_detection.detected_edits
            })

        # Calculate overall metrics
        results['overall_metrics']['pre_correction'].update(
            self._calculate_metrics(results['overall_metrics']['pre_correction'])
        )
        results['overall_metrics']['post_correction'].update(
            self._calculate_metrics(results['overall_metrics']['post_correction'])
        )

        # Calculate bias removal rate
        pre_detected = results['overall_metrics']['pre_correction']['tp']
        if pre_detected > 0:
            results['overall_metrics']['bias_removal_rate'] = (
                results['overall_metrics']['bias_removal_count'] / pre_detected
            )

        # Calculate category-specific metrics
        for category, cat_data in category_data.items():
            pre_metrics = self._calculate_metrics({
                'tp': cat_data['pre_tp'], 'fp': cat_data['pre_fp'],
                'tn': cat_data['pre_tn'], 'fn': cat_data['pre_fn']
            })
            post_metrics = self._calculate_metrics({
                'tp': cat_data['post_tp'], 'fp': cat_data['post_fp'],
                'tn': cat_data['post_tn'], 'fn': cat_data['post_fn']
            })

            removal_rate = 0.0
            if cat_data['detected_count'] > 0:
                removal_rate = cat_data['bias_removed'] / cat_data['detected_count']

            results['category_metrics'][category.value] = {
                'pre_correction': pre_metrics,
                'post_correction': post_metrics,
                'bias_removal_rate': removal_rate,
                'bias_removed_count': cat_data['bias_removed'],
                'detected_count': cat_data['detected_count']
            }

        return results

    def _empty_results(self, language: Language) -> dict[str, Any]:
        """Return empty results structure for error cases."""
        return {
            'language': language.value,
            'total_samples': 0,
            'biased_samples': 0,
            'overall_metrics': {},
            'category_metrics': {},
            'correction_quality': {},
            'samples': []
        }

    def _calculate_metrics(self, confusion: dict[str, int]) -> dict[str, float]:
        """Calculate precision, recall, F1 from confusion matrix."""
        tp = confusion['tp']
        fp = confusion['fp']
        fn = confusion['fn']

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }

    def generate_comparison_report(self, results: dict[str, Any]) -> str:
        """Generate detailed human-readable comparison report with category breakdown."""
        lang = results['language'].upper()
        report = f"\n{'='*80}\n"
        report += f"CORRECTION EFFECTIVENESS REPORT - {lang}\n"
        report += f"{'='*80}\n\n"

        report += f"Dataset: {results['total_samples']} samples ({results['biased_samples']} biased)\n\n"

        # Overall pre-correction metrics
        pre = results['overall_metrics']['pre_correction']
        report += "PRE-CORRECTION DETECTION:\n"
        report += f"  Precision: {pre['precision']:.3f}\n"
        report += f"  Recall:    {pre['recall']:.3f}\n"
        report += f"  F1 Score:  {pre['f1_score']:.3f}\n"
        report += f"  Confusion Matrix: TP={pre['tp']}, FP={pre['fp']}, FN={pre['fn']}, TN={pre['tn']}\n\n"

        # Overall post-correction metrics
        post = results['overall_metrics']['post_correction']
        report += "POST-CORRECTION DETECTION:\n"
        report += f"  Precision: {post['precision']:.3f}\n"
        report += f"  Recall:    {post['recall']:.3f}\n"
        report += f"  F1 Score:  {post['f1_score']:.3f}\n"
        report += f"  Confusion Matrix: TP={post['tp']}, FP={post['fp']}, FN={post['fn']}, TN={post['tn']}\n\n"

        # Bias removal effectiveness
        removal_rate = results['overall_metrics']['bias_removal_rate']
        removal_count = results['overall_metrics']['bias_removal_count']
        report += "BIAS REMOVAL EFFECTIVENESS:\n"
        report += f"  Bias Removal Rate: {removal_rate:.1%}\n"
        report += f"  Successfully Neutralized: {removal_count} / {pre['tp']} detected\n\n"

        # Correction quality
        quality = results['correction_quality']
        report += "CORRECTION QUALITY:\n"
        report += f"  Successful Corrections: {quality['successful_corrections']}\n"
        report += f"  Over-Corrections: {quality['over_corrections']}\n"
        report += f"  Meaning Preserved: {quality['meaning_preserved']} samples\n\n"

        # Category breakdown
        if results['category_metrics']:
            report += "CATEGORY BREAKDOWN:\n"
            report += f"{'Category':<20} {'Pre-F1':<8} {'Post-F1':<8} {'Removal%':<10} {'Removed':<10}\n"
            report += "-" * 80 + "\n"

            for cat_name, cat_metrics in results['category_metrics'].items():
                pre_f1 = cat_metrics['pre_correction']['f1_score']
                post_f1 = cat_metrics['post_correction']['f1_score']
                removal_rate = cat_metrics['bias_removal_rate']
                removed = cat_metrics['bias_removed_count']
                detected = cat_metrics['detected_count']

                report += f"{cat_name:<20} {pre_f1:<8.3f} {post_f1:<8.3f} {removal_rate:<10.1%} {removed}/{detected}\n"
            report += "\n"

        # Example corrections
        report += "EXAMPLE CORRECTIONS:\n"
        examples = [s for s in results['samples'] if s['bias_removed']][:3]
        if examples:
            for i, ex in enumerate(examples, 1):
                report += f"\n  {i}. Original:  \"{ex['original']}\"\n"
                report += f"     Corrected: \"{ex['corrected']}\"\n"
                report += f"     Category:  {ex['category']}\n"
        else:
            report += "  No successful bias removal examples found.\n"

        return report


def main():
    """Run correction evaluation for all JuaKazi languages."""
    evaluator = CorrectionEvaluator()

    # JuaKazi languages: English (production), Swahili (foundation), French & Gikuyu (beta)
    languages = [
        (Language.ENGLISH, 'en', 'English'),
        (Language.SWAHILI, 'sw', 'Swahili'),
        (Language.FRENCH, 'fr', 'French'),
        (Language.GIKUYU, 'ki', 'Gikuyu')
    ]

    all_results = []

    print("Running Correction Effectiveness Evaluation...")
    print("=" * 80)

    for language, lang_code, lang_name in languages:
        ground_truth_file = Path("eval") / f"ground_truth_{lang_code}.csv"

        if not ground_truth_file.exists():
            print(f"Skipping {lang_name}: ground truth file not found")
            continue

        print(f"\nEvaluating {lang_name}...")
        results = evaluator.evaluate_correction_effectiveness(language)

        # Print report
        report = evaluator.generate_comparison_report(results)
        print(report)

        # Remove detailed samples for summary JSON
        summary_results = {k: v for k, v in results.items() if k != 'samples'}
        all_results.append(summary_results)

    # Save results with detailed samples
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("eval") / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"correction_eval_{timestamp}.json"
    writer = ResultsWriter(output_dir)
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}\n")
    except (IOError, OSError) as e:
        print(f"\nError: Failed to save results to {output_file}: {e}")
        print(f"{'='*80}\n")

    # Generate summary table
    print("\nSUMMARY TABLE - Correction Effectiveness")
    print("=" * 80)
    print(f"{'Language':<12} {'Pre-F1':<10} {'Post-F1':<10} {'Removal%':<12} {'Status':<15}")
    print("-" * 80)

    EFFECTIVE_REMOVAL_THRESHOLD = 0.7

    for result in all_results:
        lang = result['language'].upper()

        pre_f1 = result['overall_metrics']['pre_correction']['f1_score']
        post_f1 = result['overall_metrics']['post_correction']['f1_score']
        removal_rate = result['overall_metrics']['bias_removal_rate']

        status = "Effective" if removal_rate > EFFECTIVE_REMOVAL_THRESHOLD else "Needs Work"

        print(f"{lang:<12} {pre_f1:<10.3f} {post_f1:<10.3f} {removal_rate:<12.1%} {status:<15}")

    print("=" * 80)


if __name__ == "__main__":
    main()
