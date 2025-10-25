"""
Metrics calculation service for bias detection evaluation.

This module provides clean interfaces for calculating evaluation metrics.
"""
from typing import List, Dict
from collections import defaultdict

from .models import (
    EvaluationMetrics, 
    LanguageEvaluationResult, 
    GroundTruthSample, 
    BiasDetectionResult,
    Language,
    BiasCategory
)


class MetricsCalculator:
    """
    Service for calculating evaluation metrics from predictions and ground truth.
    
    Provides methods for calculating precision, recall, F1 scores both overall
    and per-category.
    """
    
    def calculate_language_metrics(
        self, 
        ground_truth: List[GroundTruthSample],
        predictions: List[BiasDetectionResult],
        language: Language
    ) -> LanguageEvaluationResult:
        """
        Calculate comprehensive evaluation metrics for a language.
        
        Args:
            ground_truth: List of ground truth samples
            predictions: List of prediction results
            language: Language being evaluated
            
        Returns:
            LanguageEvaluationResult with overall and per-category metrics
            
        Raises:
            ValueError: If ground truth and predictions don't match in length
        """
        if len(ground_truth) != len(predictions):
            raise ValueError(
                f"Ground truth ({len(ground_truth)}) and predictions ({len(predictions)}) "
                f"must have the same length"
            )
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(ground_truth, predictions)
        
        # Calculate per-category metrics
        category_metrics = self._calculate_category_metrics(ground_truth, predictions)
        
        return LanguageEvaluationResult(
            language=language,
            overall_metrics=overall_metrics,
            category_metrics=category_metrics,
            total_samples=len(ground_truth)
        )
    
    def _calculate_overall_metrics(
        self,
        ground_truth: List[GroundTruthSample],
        predictions: List[BiasDetectionResult]
    ) -> EvaluationMetrics:
        """Calculate overall evaluation metrics."""
        tp = fp = fn = tn = 0
        
        for gt, pred in zip(ground_truth, predictions):
            if pred.has_bias_detected and gt.has_bias:
                tp += 1
            elif pred.has_bias_detected and not gt.has_bias:
                fp += 1
            elif not pred.has_bias_detected and gt.has_bias:
                fn += 1
            else:  # not pred.has_bias_detected and not gt.has_bias
                tn += 1
        
        return self._calculate_metrics_from_counts(tp, fp, fn, tn)
    
    def _calculate_category_metrics(
        self,
        ground_truth: List[GroundTruthSample],
        predictions: List[BiasDetectionResult]
    ) -> Dict[BiasCategory, EvaluationMetrics]:
        """Calculate per-category evaluation metrics."""
        # Group samples by category
        category_data = defaultdict(list)
        
        for gt, pred in zip(ground_truth, predictions):
            category_data[gt.bias_category].append((gt, pred))
        
        # Calculate metrics for each category
        category_metrics = {}
        
        for category, samples in category_data.items():
            if category == BiasCategory.NONE:
                continue  # Skip non-biased samples for category metrics
            
            tp = fp = fn = tn = 0
            
            for gt, pred in samples:
                if pred.has_bias_detected and gt.has_bias:
                    tp += 1
                elif pred.has_bias_detected and not gt.has_bias:
                    fp += 1
                elif not pred.has_bias_detected and gt.has_bias:
                    fn += 1
                else:
                    tn += 1
            
            category_metrics[category] = self._calculate_metrics_from_counts(tp, fp, fn, tn)
        
        return category_metrics
    
    def _calculate_metrics_from_counts(self, tp: int, fp: int, fn: int, tn: int) -> EvaluationMetrics:
        """Calculate metrics from confusion matrix counts."""
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn
        )


class MetricsFormatter:
    """
    Service for formatting evaluation metrics for display and export.
    
    Provides methods to convert metrics objects into various output formats.
    """
    
    def format_for_csv(self, results: List[LanguageEvaluationResult]) -> List[Dict[str, str]]:
        """
        Format evaluation results for CSV export.
        
        Args:
            results: List of language evaluation results
            
        Returns:
            List of dictionaries suitable for CSV writing
        """
        csv_rows = []
        
        for result in results:
            lang_name = result.language.value.upper()
            
            # Add overall metrics row
            csv_rows.append({
                'Language': lang_name,
                'Category': 'OVERALL',
                'Precision': f"{result.overall_metrics.precision:.3f}",
                'Recall': f"{result.overall_metrics.recall:.3f}",
                'F1_Score': f"{result.overall_metrics.f1_score:.3f}",
                'TP': str(result.overall_metrics.true_positives),
                'FP': str(result.overall_metrics.false_positives),
                'FN': str(result.overall_metrics.false_negatives),
                'TN': str(result.overall_metrics.true_negatives)
            })
            
            # Add category-specific metrics rows
            for category, metrics in result.category_metrics.items():
                csv_rows.append({
                    'Language': lang_name,
                    'Category': category.value,
                    'Precision': f"{metrics.precision:.3f}",
                    'Recall': f"{metrics.recall:.3f}",
                    'F1_Score': f"{metrics.f1_score:.3f}",
                    'TP': str(metrics.true_positives),
                    'FP': str(metrics.false_positives),
                    'FN': str(metrics.false_negatives),
                    'TN': str(metrics.true_negatives)
                })
        
        return csv_rows
    
    def format_for_console(self, results: List[LanguageEvaluationResult]) -> str:
        """
        Format evaluation results for console display.
        
        Args:
            results: List of language evaluation results
            
        Returns:
            Formatted string for console output
        """
        output_lines = ["Running bias detection evaluation..."]
        
        for result in results:
            lang_name = "English" if result.language == Language.ENGLISH else "Swahili"
            
            output_lines.extend([
                f"Evaluating {result.language.value}...",
                f"{lang_name} Results:",
                f"  Overall F1: {result.overall_metrics.f1_score:.3f}",
                f"  Precision: {result.overall_metrics.precision:.3f}",
                f"  Recall: {result.overall_metrics.recall:.3f}",
                ""
            ])
        
        return "\n".join(output_lines)