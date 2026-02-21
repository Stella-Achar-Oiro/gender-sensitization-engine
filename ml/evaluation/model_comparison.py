"""
Model comparison utilities for bias detection.

Compares performance of:
- Rules-based detector only
- ML-based detector only
- Hybrid detector (rules + ML)
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

from eval.bias_detector import BiasDetector
from eval.ml_detector import MLBiasDetector
from eval.hybrid_detector import HybridBiasDetector
from eval.models import Language, GroundTruthSample, BiasDetectionResult
from eval.metrics_calculator import MetricsCalculator


@dataclass
class ModelMetrics:
    """Metrics for a single model."""

    model_name: str
    precision: float
    recall: float
    f1: float
    accuracy: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    samples_evaluated: int

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'model_name': self.model_name,
            'precision': self.precision,
            'recall': self.recall,
            'f1': f1,
            'accuracy': self.accuracy,
            'confusion_matrix': {
                'tp': self.true_positives,
                'fp': self.false_positives,
                'fn': self.false_negatives,
                'tn': self.true_negatives
            },
            'samples_evaluated': self.samples_evaluated
        }

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = [f"{self.model_name}:"]
        lines.append(f"  F1: {self.f1:.4f}")
        lines.append(f"  Precision: {self.precision:.4f}")
        lines.append(f"  Recall: {self.recall:.4f}")
        lines.append(f"  Accuracy: {self.accuracy:.4f}")
        lines.append(f"  Samples: {self.samples_evaluated}")
        return "\n".join(lines)


@dataclass
class ComparisonResult:
    """Results from comparing multiple models."""

    language: Language
    rules_metrics: ModelMetrics
    ml_metrics: ModelMetrics
    hybrid_metrics: ModelMetrics
    best_model: str  # Name of best performing model

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'language': self.language.value,
            'rules': self.rules_metrics.to_dict(),
            'ml': self.ml_metrics.to_dict(),
            'hybrid': self.hybrid_metrics.to_dict(),
            'best_model': self.best_model
        }

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = [f"Model Comparison ({self.language.value}):"]
        lines.append("")
        lines.append(self.rules_metrics.summary())
        lines.append("")
        lines.append(self.ml_metrics.summary())
        lines.append("")
        lines.append(self.hybrid_metrics.summary())
        lines.append("")
        lines.append(f"Best Model: {self.best_model}")
        return "\n".join(lines)


class ModelComparator:
    """Compare performance of different bias detection models."""

    def __init__(self):
        """Initialize comparator with all detector types."""
        self.rules_detector = BiasDetector()
        self.ml_detector = MLBiasDetector()
        self.hybrid_detector = HybridBiasDetector()
        self.calculator = MetricsCalculator()

    def compare_models(
        self,
        samples: List[GroundTruthSample],
        language: Language
    ) -> ComparisonResult:
        """
        Compare all three models on given samples.

        Args:
            samples: Ground truth samples to evaluate
            language: Language of samples

        Returns:
            ComparisonResult with metrics for each model
        """
        # Evaluate each model
        rules_results = [
            self.rules_detector.detect_bias(s.text, language)
            for s in samples
        ]

        ml_results = [
            self.ml_detector.detect_bias(s.text, language)
            for s in samples
        ]

        hybrid_results = [
            self.hybrid_detector.detect_bias(s.text, language)
            for s in samples
        ]

        # Calculate metrics for each
        rules_metrics = self._calculate_metrics(
            "Rules-based",
            samples,
            rules_results
        )

        ml_metrics = self._calculate_metrics(
            "ML-based",
            samples,
            ml_results
        )

        hybrid_metrics = self._calculate_metrics(
            "Hybrid (Rules+ML)",
            samples,
            hybrid_results
        )

        # Determine best model (by F1 score)
        best_model = self._get_best_model(
            rules_metrics,
            ml_metrics,
            hybrid_metrics
        )

        return ComparisonResult(
            language=language,
            rules_metrics=rules_metrics,
            ml_metrics=ml_metrics,
            hybrid_metrics=hybrid_metrics,
            best_model=best_model
        )

    def _calculate_metrics(
        self,
        model_name: str,
        samples: List[GroundTruthSample],
        results: List[BiasDetectionResult]
    ) -> ModelMetrics:
        """Calculate metrics for a model."""
        # Calculate confusion matrix
        tp = sum(1 for s, r in zip(samples, results)
                if s.has_bias and r.has_bias_detected)
        fp = sum(1 for s, r in zip(samples, results)
                if not s.has_bias and r.has_bias_detected)
        fn = sum(1 for s, r in zip(samples, results)
                if s.has_bias and not r.has_bias_detected)
        tn = sum(1 for s, r in zip(samples, results)
                if not s.has_bias and not r.has_bias_detected)

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)
        accuracy = (tp + tn) / len(samples) if samples else 0.0

        return ModelMetrics(
            model_name=model_name,
            precision=precision,
            recall=recall,
            f1=f1,
            accuracy=accuracy,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            samples_evaluated=len(samples)
        )

    def _get_best_model(
        self,
        rules: ModelMetrics,
        ml: ModelMetrics,
        hybrid: ModelMetrics
    ) -> str:
        """Determine best model by F1 score."""
        models = [
            (rules.f1, rules.model_name),
            (ml.f1, ml.model_name),
            (hybrid.f1, hybrid.model_name)
        ]

        # Sort by F1 (descending)
        models.sort(reverse=True)

        return models[0][1]

    def compare_on_language(self, language: Language) -> ComparisonResult:
        """
        Compare models on ground truth for a language.

        Args:
            language: Language to evaluate

        Returns:
            ComparisonResult
        """
        from eval.data_loader import GroundTruthLoader

        loader = GroundTruthLoader()
        samples = loader.load_ground_truth(language)

        if not samples:
            raise ValueError(f"No samples found for language: {language}")

        return self.compare_models(samples, language)

    def compare_all_languages(self) -> Dict[Language, ComparisonResult]:
        """
        Compare models across all languages.

        Returns:
            Dictionary mapping language to comparison results
        """
        languages = [
            Language.ENGLISH,
            Language.SWAHILI,
            Language.FRENCH,
            Language.GIKUYU
        ]

        results = {}
        for language in languages:
            try:
                result = self.compare_on_language(language)
                results[language] = result
            except ValueError:
                # No data for this language
                continue

        return results

    def generate_report(
        self,
        results: Dict[Language, ComparisonResult],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate comparison report.

        Args:
            results: Comparison results by language
            output_path: Optional path to save report

        Returns:
            Report as string
        """
        lines = ["=" * 70]
        lines.append("Model Comparison Report".center(70))
        lines.append("=" * 70)
        lines.append("")

        for language, result in results.items():
            lines.append(result.summary())
            lines.append("")
            lines.append("-" * 70)
            lines.append("")

        # Overall summary
        lines.append("=" * 70)
        lines.append("Overall Summary".center(70))
        lines.append("=" * 70)

        # Count best models
        best_counts = {}
        for result in results.values():
            best_counts[result.best_model] = best_counts.get(result.best_model, 0) + 1

        lines.append("Best model by language:")
        for model, count in sorted(best_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {model}: {count} language(s)")

        report = "\n".join(lines)

        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Report saved to: {output_path}")

        return report
