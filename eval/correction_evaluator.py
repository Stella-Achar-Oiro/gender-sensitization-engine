#!/usr/bin/env python3
"""Enhanced Correction Evaluation Script - Advanced Metrics.

    This script evaluates bias correction effectiveness with:
    1. HarmonicScore combining detection quality and neutralization rate
    2. Token-level semantic preservation (BLEU/ROUGE-style + embedding similarity)
    3. Comprehensive per-category analysis
    4. Enhanced CLI outputs with all new metrics
"""

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from re import Match
from statistics import harmonic_mean
from typing import Any

from config import lexicon_filename

# Import existing evaluation components
from eval.bias_detector import BiasDetector
from eval.data_loader import GroundTruthLoader
from eval.models import BiasCategory, Language

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))




class SemanticPreservationMetrics:
    """Calculate token-level semantic preservation metrics."""

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Simple word tokenization."""
        return re.findall(r"\w+", text.lower())

    @staticmethod
    def calculate_bleu_score(original: str, corrected: str, n: int = 2) -> float:
        """Calculate BLEU-style score for n-grams.

        Why: Measures how much of the corrected text matches the original,
        indicating preservation of content and structure.

        Args:
            original: Original text
            corrected: Corrected text
            n: Maximum n-gram size (default: bigrams)

        Returns:
            BLEU score between 0 and 1
        """
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)

        if not orig_tokens or not corr_tokens:
            return 0.0

        scores = []
        for gram_size in range(1, n + 1):
            orig_ngrams = [
                tuple(orig_tokens[i : i + gram_size])
                for i in range(len(orig_tokens) - gram_size + 1)
            ]
            corr_ngrams = [
                tuple(corr_tokens[i : i + gram_size])
                for i in range(len(corr_tokens) - gram_size + 1)
            ]

            if not orig_ngrams or not corr_ngrams:
                continue

            matches = sum(1 for ng in corr_ngrams if ng in orig_ngrams)
            precision = matches / len(corr_ngrams) if corr_ngrams else 0.0
            scores.append(precision)

        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def calculate_rouge_l(original: str, corrected: str) -> float:
        """Calculate ROUGE-L score (longest common subsequence).

        Why: Measures the longest matching sequence of tokens,
        indicating structural preservation.

        Args:
            original: Original text
            corrected: Corrected text

        Returns:
            ROUGE-L F1 score between 0 and 1
        """
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)

        if not orig_tokens or not corr_tokens:
            return 0.0

        # Calculate LCS length using dynamic programming
        m, n = len(orig_tokens), len(corr_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if orig_tokens[i - 1] == corr_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        lcs_length = dp[m][n]

        # Calculate precision, recall, and F1
        precision = lcs_length / n if n > 0 else 0.0
        recall = lcs_length / m if m > 0 else 0.0

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        return f1

    @staticmethod
    def calculate_token_overlap(original: str, corrected: str) -> float:
        """Calculate simple token overlap ratio.

        Why: Quick measure of how many words are preserved.

        Args:
            original: Original text
            corrected: Corrected text

        Returns:
            Overlap ratio between 0 and 1
        """
        orig_tokens = set(SemanticPreservationMetrics.tokenize(original))
        corr_tokens = set(SemanticPreservationMetrics.tokenize(corrected))

        if not orig_tokens:
            return 1.0 if not corr_tokens else 0.0

        overlap = len(orig_tokens & corr_tokens)
        return overlap / len(orig_tokens)

    @staticmethod
    def calculate_edit_distance_ratio(original: str, corrected: str) -> float:
        """Calculate normalized Levenshtein distance at token level.

        Why: Measures how many edits were made, with 1.0 being identical.

        Args:
            original: Original text
            corrected: Corrected text

        Returns:
            Similarity ratio between 0 and 1 (1.0 = identical)
        """
        orig_tokens = SemanticPreservationMetrics.tokenize(original)
        corr_tokens = SemanticPreservationMetrics.tokenize(corrected)

        if not orig_tokens and not corr_tokens:
            return 1.0
        if not orig_tokens or not corr_tokens:
            return 0.0

        # Levenshtein distance
        m, n = len(orig_tokens), len(corr_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if orig_tokens[i - 1] == corr_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

        distance = dp[m][n]
        max_len = max(m, n)

        return 1.0 - (distance / max_len) if max_len > 0 else 1.0

    @staticmethod
    def calculate_composite_preservation_score(
        original: str, corrected: str
    ) -> dict[str, float]:
        """Calculate comprehensive semantic preservation metrics.

        Returns:
            Dictionary with BLEU, ROUGE-L, token overlap, edit distance,
            and composite score
        """
        bleu = SemanticPreservationMetrics.calculate_bleu_score(original, corrected)
        rouge_l = SemanticPreservationMetrics.calculate_rouge_l(original, corrected)
        token_overlap = SemanticPreservationMetrics.calculate_token_overlap(
            original, corrected
        )
        edit_sim = SemanticPreservationMetrics.calculate_edit_distance_ratio(
            original, corrected
        )

        # Composite score: weighted average favoring structural preservation
        composite = 0.3 * bleu + 0.3 * rouge_l + 0.2 * token_overlap + 0.2 * edit_sim

        return {
            "bleu_score": bleu,
            "rouge_l_score": rouge_l,
            "token_overlap": token_overlap,
            "edit_similarity": edit_sim,
            "composite_score": composite,
        }


class CorrectionEvaluator:
    """Evaluates bias correction effectiveness with enhanced metrics."""

    # Thresholds
    EFFECTIVE_REMOVAL_THRESHOLD = 0.7
    GOOD_HARMONIC_SCORE_THRESHOLD = 0.75
    GOOD_PRESERVATION_THRESHOLD = 0.85

    def __init__(self, rules_dir: Path = Path("rules")):
        """Initialize with bias detector and correction rules."""
        self.detector = BiasDetector(rules_dir)
        self.rules_dir = rules_dir
        self.rules_cache: dict[Language, list[dict[str, str]]] = {}
        self.semantic_metrics = SemanticPreservationMetrics()

    def load_correction_rules(self, language: Language) -> list[dict[str, str]]:
        """Load correction rules for a language with caching."""
        if language in self.rules_cache:
            return self.rules_cache[language]

        lang_code = language.value
        rules_file = self.rules_dir / lexicon_filename(lang_code)

        if not rules_file.exists():
            return []

        rules: list[dict[str, str]] = []
        try:
            with open(rules_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rules.append(
                        {
                            "biased": row.get("biased", ""),
                            "neutral_primary": row.get("neutral_primary", ""),
                            "severity": row.get("severity", "replace"),
                        }
                    )
        except (OSError, csv.Error) as e:
            print(f"Error reading rules file {rules_file}: {e}")
            return []

        self.rules_cache[language] = rules
        return rules

    def apply_corrections(self, text: str, language: Language) -> str:
        """Apply bias corrections to text using lexicon rules."""
        rules = self.load_correction_rules(language)
        corrected_text = text

        for rule in rules:
            if rule["severity"] == "replace":
                biased_term = rule["biased"]
                neutral_term = rule["neutral_primary"]

                pattern = r"\b" + re.escape(biased_term) + r"\b"

                def replace_func(match: Match[str]) -> str:
                    orig = match.group(0)
                    if orig.isupper():
                        return neutral_term.upper()
                    elif orig[0].isupper():
                        return neutral_term.capitalize()
                    else:
                        return neutral_term.lower()

                corrected_text = re.sub(
                    pattern, replace_func, corrected_text, flags=re.IGNORECASE
                )

        return corrected_text

    def _normalize_for_eval(self, text: str) -> str:
        """Normalize text for evaluation-only operations."""
        if text is None:
            return ""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
        text = text.replace("_", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def evaluate_correction_effectiveness(self, language: Language) -> dict[str, Any]:
        """Evaluate correction effectiveness with enhanced metrics.

        New metrics:
        - HarmonicScore: harmonic mean of pre-detection F1 and neutralization rate
        - Semantic preservation scores (BLEU, ROUGE-L, token overlap, edit distance)
        - Per-category harmonic scores
        - Enhanced quality metrics
        """
        # Load ground truth data
        loader = GroundTruthLoader(Path("eval"))
        try:
            ground_truth = loader.load_ground_truth(language)
        except Exception as e:
            print(f"Error loading ground truth for {language.value}: {e}")
            return self._empty_results(language)

        # Initialize results structure with new metrics
        results: dict[str, Any] = {
            "language": language.value,
            "total_samples": len(ground_truth),
            "biased_samples": sum(1 for gt in ground_truth if gt.has_bias),
            "overall_metrics": {
                "pre_correction": {
                    "tp": 0,
                    "fp": 0,
                    "tn": 0,
                    "fn": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                },
                "post_correction": {
                    "tp": 0,
                    "fp": 0,
                    "tn": 0,
                    "fn": 0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                },
                "bias_removal_rate": 0.0,
                "bias_removal_count": 0,
                "detected_and_removed": 0,
                "harmonic_score": 0.0,  # New: HarmonicScore
            },
            "semantic_preservation": {  # New: Token-level metrics
                "avg_bleu": 0.0,
                "avg_rouge_l": 0.0,
                "avg_token_overlap": 0.0,
                "avg_edit_similarity": 0.0,
                "avg_composite_score": 0.0,
                "samples_analyzed": 0,
            },
            "category_metrics": {},
            "correction_quality": {
                "meaning_preserved": 0,
                "over_corrections": 0,
                "successful_corrections": 0,
                "high_quality_corrections": 0,  # New: corrections with good preservation
            },
            "samples": [],
        }

        # Initialize category tracking with new metrics
        category_data = defaultdict(
            lambda: {
                "pre_tp": 0,
                "pre_fp": 0,
                "pre_tn": 0,
                "pre_fn": 0,
                "post_tp": 0,
                "post_fp": 0,
                "post_tn": 0,
                "post_fn": 0,
                "bias_removed": 0,
                "detected_count": 0,
                "preservation_scores": [],
            }
        )

        # Accumulate semantic preservation scores
        preservation_scores = []

        # Process each sample
        for gt_sample in ground_truth:
            text = gt_sample.text
            is_biased = gt_sample.has_bias
            category = gt_sample.bias_category

            eval_text = self._normalize_for_eval(text)

            # Pre-correction detection
            pre_detection = self.detector.detect_bias(eval_text, language)
            pre_detected = pre_detection.has_bias_detected

            # Apply correction
            corrected_text = self.apply_corrections(text, language)
            eval_corrected_text = self._normalize_for_eval(corrected_text)

            # Post-correction detection
            post_detection = self.detector.detect_bias(eval_corrected_text, language)
            post_detected = post_detection.has_bias_detected

            # Calculate semantic preservation for changed texts
            preservation_metrics = None
            if text != corrected_text:
                preservation_metrics = (
                    self.semantic_metrics.calculate_composite_preservation_score(
                        text, corrected_text
                    )
                )
                preservation_scores.append(preservation_metrics)

            # Update confusion matrices
            if pre_detected and is_biased:
                results["overall_metrics"]["pre_correction"]["tp"] += 1
            elif pre_detected and not is_biased:
                results["overall_metrics"]["pre_correction"]["fp"] += 1
            elif not pre_detected and is_biased:
                results["overall_metrics"]["pre_correction"]["fn"] += 1
            else:
                results["overall_metrics"]["pre_correction"]["tn"] += 1

            if post_detected and is_biased:
                results["overall_metrics"]["post_correction"]["tp"] += 1
            elif post_detected and not is_biased:
                results["overall_metrics"]["post_correction"]["fp"] += 1
            elif not post_detected and is_biased:
                results["overall_metrics"]["post_correction"]["fn"] += 1
            else:
                results["overall_metrics"]["post_correction"]["tn"] += 1

            # Track bias removal
            bias_removed = pre_detected and not post_detected
            if bias_removed and is_biased:
                results["overall_metrics"]["bias_removal_count"] += 1
                results["overall_metrics"]["detected_and_removed"] += 1

            # Update category-specific metrics
            if category != BiasCategory.NONE:
                cat_data = category_data[category]

                if pre_detected and is_biased:
                    cat_data["pre_tp"] += 1
                elif pre_detected and not is_biased:
                    cat_data["pre_fp"] += 1
                elif not pre_detected and is_biased:
                    cat_data["pre_fn"] += 1
                else:
                    cat_data["pre_tn"] += 1

                if post_detected and is_biased:
                    cat_data["post_tp"] += 1
                elif post_detected and not is_biased:
                    cat_data["post_fp"] += 1
                elif not post_detected and is_biased:
                    cat_data["post_fn"] += 1
                else:
                    cat_data["post_tn"] += 1

                if pre_detected:
                    cat_data["detected_count"] += 1
                if bias_removed and is_biased:
                    cat_data["bias_removed"] += 1

                if preservation_metrics:
                    cat_data["preservation_scores"].append(preservation_metrics)

            # Correction quality metrics
            if not is_biased and eval_text != eval_corrected_text:
                results["correction_quality"]["over_corrections"] += 1

            if is_biased and bias_removed:
                results["correction_quality"]["successful_corrections"] += 1

                # Check if it's a high-quality correction (good preservation)
                if (
                    preservation_metrics
                    and preservation_metrics["composite_score"]
                    >= self.GOOD_PRESERVATION_THRESHOLD
                ):
                    results["correction_quality"]["high_quality_corrections"] += 1

            if is_biased and eval_text != eval_corrected_text:
                results["correction_quality"]["meaning_preserved"] += 1

            # Store sample details with preservation metrics
            sample_data = {
                "original": text,
                "corrected": corrected_text,
                "is_biased": is_biased,
                "category": category.value,
                "pre_detected": pre_detected,
                "post_detected": post_detected,
                "bias_removed": bias_removed,
                "text_changed": text != corrected_text,
                "text_changed_eval": eval_text != eval_corrected_text,
                "pre_edits": pre_detection.detected_edits,
                "post_edits": post_detection.detected_edits,
            }

            if preservation_metrics:
                sample_data["preservation_metrics"] = preservation_metrics

            results["samples"].append(sample_data)

        # Calculate overall metrics
        results["overall_metrics"]["pre_correction"].update(
            self._calculate_metrics(results["overall_metrics"]["pre_correction"])
        )
        results["overall_metrics"]["post_correction"].update(
            self._calculate_metrics(results["overall_metrics"]["post_correction"])
        )

        # Calculate bias removal rate
        pre_detected = results["overall_metrics"]["pre_correction"]["tp"]
        if pre_detected > 0:
            results["overall_metrics"]["bias_removal_rate"] = (
                results["overall_metrics"]["bias_removal_count"] / pre_detected
            )

        # Calculate HarmonicScore
        pre_f1 = results["overall_metrics"]["pre_correction"]["f1_score"]
        removal_rate = results["overall_metrics"]["bias_removal_rate"]

        if pre_f1 > 0 and removal_rate > 0:
            results["overall_metrics"]["harmonic_score"] = harmonic_mean(
                [pre_f1, removal_rate]
            )
        else:
            results["overall_metrics"]["harmonic_score"] = 0.0

        # Calculate average semantic preservation scores
        if preservation_scores:
            results["semantic_preservation"]["samples_analyzed"] = len(
                preservation_scores
            )
            results["semantic_preservation"]["avg_bleu"] = sum(
                s["bleu_score"] for s in preservation_scores
            ) / len(preservation_scores)
            results["semantic_preservation"]["avg_rouge_l"] = sum(
                s["rouge_l_score"] for s in preservation_scores
            ) / len(preservation_scores)
            results["semantic_preservation"]["avg_token_overlap"] = sum(
                s["token_overlap"] for s in preservation_scores
            ) / len(preservation_scores)
            results["semantic_preservation"]["avg_edit_similarity"] = sum(
                s["edit_similarity"] for s in preservation_scores
            ) / len(preservation_scores)
            results["semantic_preservation"]["avg_composite_score"] = sum(
                s["composite_score"] for s in preservation_scores
            ) / len(preservation_scores)

        # Calculate category-specific metrics with harmonic scores
        for category, cat_data in category_data.items():
            pre_metrics = self._calculate_metrics(
                {
                    "tp": cat_data["pre_tp"],
                    "fp": cat_data["pre_fp"],
                    "tn": cat_data["pre_tn"],
                    "fn": cat_data["pre_fn"],
                }
            )
            post_metrics = self._calculate_metrics(
                {
                    "tp": cat_data["post_tp"],
                    "fp": cat_data["post_fp"],
                    "tn": cat_data["post_tn"],
                    "fn": cat_data["post_fn"],
                }
            )

            removal_rate = 0.0
            if cat_data["detected_count"] > 0:
                removal_rate = cat_data["bias_removed"] / cat_data["detected_count"]

            # Calculate category harmonic score
            cat_harmonic = 0.0
            if pre_metrics["f1_score"] > 0 and removal_rate > 0:
                cat_harmonic = harmonic_mean([pre_metrics["f1_score"], removal_rate])

            # Calculate category preservation scores
            cat_preservation = {}
            if cat_data["preservation_scores"]:
                pres_scores = cat_data["preservation_scores"]
                cat_preservation = {
                    "avg_composite": sum(s["composite_score"] for s in pres_scores)
                    / len(pres_scores),
                    "avg_bleu": sum(s["bleu_score"] for s in pres_scores)
                    / len(pres_scores),
                    "samples": len(pres_scores),
                }

            results["category_metrics"][category.value] = {
                "pre_correction": pre_metrics,
                "post_correction": post_metrics,
                "bias_removal_rate": removal_rate,
                "bias_removed_count": cat_data["bias_removed"],
                "detected_count": cat_data["detected_count"],
                "harmonic_score": cat_harmonic,
                "preservation": cat_preservation,
            }

        return results

    def _empty_results(self, language: Language) -> dict[str, Any]:
        """Return empty results structure for error cases."""
        return {
            "language": language.value,
            "total_samples": 0,
            "biased_samples": 0,
            "overall_metrics": {},
            "semantic_preservation": {},
            "category_metrics": {},
            "correction_quality": {},
            "samples": [],
        }

    def _calculate_metrics(self, confusion: dict[str, int]) -> dict[str, float]:
        """Calculate precision, recall, F1 from confusion matrix."""
        tp = confusion["tp"]
        fp = confusion["fp"]
        fn = confusion["fn"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {"precision": precision, "recall": recall, "f1_score": f1_score}

    def generate_comparison_report(self, results: dict[str, Any]) -> str:
        """Generate detailed human-readable comparison report with enhanced metrics."""
        lang = results["language"].upper()
        report = f"\n{'=' * 80}\n"
        report += f"ENHANCED CORRECTION EFFECTIVENESS REPORT - {lang}\n"
        report += f"{'=' * 80}\n\n"

        report += f"Dataset: {results['total_samples']} samples ({results['biased_samples']} biased)\n\n"

        # Overall pre-correction metrics
        pre = results["overall_metrics"]["pre_correction"]
        report += "PRE-CORRECTION DETECTION:\n"
        report += f"  Precision: {pre['precision']:.3f}\n"
        report += f"  Recall:    {pre['recall']:.3f}\n"
        report += f"  F1 Score:  {pre['f1_score']:.3f}\n"
        report += f"  Confusion: TP={pre['tp']}, FP={pre['fp']}, FN={pre['fn']}, TN={pre['tn']}\n\n"

        # Overall post-correction metrics
        post = results["overall_metrics"]["post_correction"]
        report += "POST-CORRECTION DETECTION:\n"
        report += f"  Precision: {post['precision']:.3f}\n"
        report += f"  Recall:    {post['recall']:.3f}\n"
        report += f"  F1 Score:  {post['f1_score']:.3f}\n"
        report += f"  Confusion: TP={post['tp']}, FP={post['fp']}, FN={post['fn']}, TN={post['tn']}\n\n"

        # Bias removal effectiveness with HarmonicScore
        removal_rate = results["overall_metrics"]["bias_removal_rate"]
        removal_count = results["overall_metrics"]["bias_removal_count"]
        harmonic_score = results["overall_metrics"]["harmonic_score"]

        report += "BIAS REMOVAL EFFECTIVENESS:\n"
        report += f"  Bias Removal Rate: {removal_rate:.1%}\n"
        report += (
            f"  Successfully Neutralized: {removal_count} / {pre['tp']} detected\n"
        )
        report += f"  HarmonicScore (F1 ⊗ Removal): {harmonic_score:.3f}\n"

        # Quality assessment
        if harmonic_score >= self.GOOD_HARMONIC_SCORE_THRESHOLD:
            report += f"  → Assessment: EXCELLENT (≥{self.GOOD_HARMONIC_SCORE_THRESHOLD:.2f})\n"
        elif harmonic_score >= 0.60:
            report += "  → Assessment: GOOD\n"
        elif harmonic_score >= 0.40:
            report += "  → Assessment: FAIR\n"
        else:
            report += "  → Assessment: NEEDS IMPROVEMENT\n"
        report += "\n"

        # Semantic preservation metrics
        if results["semantic_preservation"]["samples_analyzed"] > 0:
            pres = results["semantic_preservation"]
            report += "SEMANTIC PRESERVATION (Token-Level Analysis):\n"
            report += f"  Samples Analyzed: {pres['samples_analyzed']}\n"
            report += f"  BLEU Score:       {pres['avg_bleu']:.3f}\n"
            report += f"  ROUGE-L Score:    {pres['avg_rouge_l']:.3f}\n"
            report += f"  Token Overlap:    {pres['avg_token_overlap']:.3f}\n"
            report += f"  Edit Similarity:  {pres['avg_edit_similarity']:.3f}\n"
            report += f"  Composite Score:  {pres['avg_composite_score']:.3f}\n"

            if pres["avg_composite_score"] >= self.GOOD_PRESERVATION_THRESHOLD:
                report += "  → Assessment: EXCELLENT preservation\n"
            elif pres["avg_composite_score"] >= 0.70:
                report += "  → Assessment: GOOD preservation\n"
            else:
                report += "  → Assessment: Moderate preservation, review needed\n"
            report += "\n"

        # Correction quality with new metrics
        quality = results["correction_quality"]
        report += "CORRECTION QUALITY:\n"
        report += f"  Successful Corrections:     {quality['successful_corrections']}\n"
        report += (
            f"  High-Quality Corrections:   {quality['high_quality_corrections']}\n"
        )
        report += f"  Over-Corrections:           {quality['over_corrections']}\n"
        report += (
            f"  Meaning Preserved (manual): {quality['meaning_preserved']} samples\n\n"
        )

        # Category breakdown with harmonic scores
        if results["category_metrics"]:
            report += "CATEGORY BREAKDOWN:\n"
            report += f"{'Category':<15} {'Pre-F1':<8} {'Post-F1':<8} {'Removal%':<10} {'Harmonic':<10} {'Status':<12} {'Detd':<5} {'Cortd'}\n"
            report += "-" * 80 + "\n"

            for cat_name, cat_metrics in results["category_metrics"].items():
                pre_f1 = cat_metrics["pre_correction"]["f1_score"]
                post_f1 = cat_metrics["post_correction"]["f1_score"]
                removal_rate = cat_metrics["bias_removal_rate"]
                cat_harmonic = cat_metrics["harmonic_score"]
                removed = cat_metrics["bias_removed_count"]
                detected = cat_metrics["detected_count"]

                status = "✓ Effective" if cat_harmonic >= 0.70 else "⚠ Review"

                report += f"{cat_name:<15} {pre_f1:<8.3f} {post_f1:<8.3f} {removal_rate:<10.1%} {cat_harmonic:<10.3f} {status:<12} {detected:<5} {removed}\n"
            report += "\n"
        return report

    # save metrics to JSON
    def save_results_to_json(self, results: dict[str, Any], output_path: Path) -> None:
        """Save evaluation results to a JSON file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"Results saved to {output_path}")
        except OSError as e:
            print(f"Error saving results to {output_path}: {e}")

    # save report to markdown well formatted and readable
    def save_report_to_txt(self, report: str, output_path: Path) -> None:
        """Save evaluation report to a markdown file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {output_path}")
        except OSError as e:
            print(f"Error saving report to {output_path}: {e}")


if __name__ == "__main__":
    evaluator = CorrectionEvaluator()

    for lang in Language:
        print(f"Evaluating corrections for language: {lang.value}")
        results = evaluator.evaluate_correction_effectiveness(lang)
        report = evaluator.generate_comparison_report(results)
        print(report)

        # timestamp for unique file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(
            f"eval/results/correction_evaluation_{lang.value}_{timestamp}.json"
        )
        evaluator.save_results_to_json(results, output_file)

        report_file = Path(
            f"eval/results/correction_report_{lang.value}_{timestamp}.txt"
        )
        evaluator.save_report_to_txt(report, report_file)
