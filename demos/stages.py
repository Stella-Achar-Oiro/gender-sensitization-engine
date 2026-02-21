"""Pipeline stages for end-to-end demo."""
from typing import List, Tuple
from dataclasses import dataclass, field
from eval.models import Language, BiasDetectionResult, GroundTruthSample
from eval.bias_detector import BiasDetector
from eval.data_loader import GroundTruthLoader


@dataclass
class StageResult:
    """Result from a pipeline stage."""
    stage_name: str
    success: bool
    samples_processed: int
    output_summary: str
    metrics: dict = field(default_factory=dict)


class DataCollectionStage:
    """
    Stage 1: Data Collection.

    For demo purposes, loads from ground truth.
    In production, this would call actual data collection scripts.
    """

    def run(self, language: Language, count: int) -> Tuple[StageResult, List[GroundTruthSample]]:
        """
        Collect data samples.

        Args:
            language: Target language
            count: Number of samples requested

        Returns:
            Tuple of (StageResult, list of samples)
        """
        try:
            loader = GroundTruthLoader()
            samples = loader.load_ground_truth(language)

            # Limit to requested count
            samples = samples[:count]

            return (
                StageResult(
                    stage_name="Data Collection",
                    success=True,
                    samples_processed=len(samples),
                    output_summary=f"Loaded {len(samples)} samples for {language.value}",
                    metrics={"source": "ground_truth", "language": language.value}
                ),
                samples
            )
        except Exception as e:
            return (
                StageResult(
                    stage_name="Data Collection",
                    success=False,
                    samples_processed=0,
                    output_summary=f"Failed: {str(e)}"
                ),
                []
            )


class BiasDetectionStage:
    """
    Stage 2: Bias Detection.

    Uses rules-based detection with optional ML fallback.
    """

    def __init__(self, enable_ml: bool = True):
        """
        Initialize detection stage.

        Args:
            enable_ml: Whether to enable ML fallback (for demo, doesn't change behavior yet)
        """
        self.detector = BiasDetector()
        self.enable_ml = enable_ml

    def run(self, texts: List[str], language: Language) -> Tuple[StageResult, List[BiasDetectionResult]]:
        """
        Run bias detection on texts.

        Args:
            texts: List of texts to analyze
            language: Target language

        Returns:
            Tuple of (StageResult, list of detection results)
        """
        try:
            results = []
            for text in texts:
                result = self.detector.detect_bias(text, language)
                results.append(result)

            bias_detected = sum(1 for r in results if r.has_bias_detected)
            detection_rate = bias_detected / len(texts) if texts else 0.0

            return (
                StageResult(
                    stage_name="Bias Detection",
                    success=True,
                    samples_processed=len(texts),
                    output_summary=f"Detected bias in {bias_detected}/{len(texts)} samples ({detection_rate:.1%})",
                    metrics={
                        "detection_rate": detection_rate,
                        "method": "rules+ml" if self.enable_ml else "rules-only",
                        "bias_detected": bias_detected,
                        "no_bias": len(texts) - bias_detected
                    }
                ),
                results
            )
        except Exception as e:
            return (
                StageResult(
                    stage_name="Bias Detection",
                    success=False,
                    samples_processed=0,
                    output_summary=f"Failed: {str(e)}"
                ),
                []
            )


class EvaluationStage:
    """
    Stage 3: Evaluation.

    Calculates precision, recall, F1, and confusion matrix metrics.
    """

    def run(self, ground_truth: List[GroundTruthSample],
            detection_results: List[BiasDetectionResult]) -> StageResult:
        """
        Evaluate detection results against ground truth.

        Args:
            ground_truth: Ground truth samples
            detection_results: Detection results to evaluate

        Returns:
            StageResult with evaluation metrics
        """
        try:
            if len(ground_truth) != len(detection_results):
                return StageResult(
                    stage_name="Evaluation",
                    success=False,
                    samples_processed=0,
                    output_summary=f"Mismatch: {len(ground_truth)} ground truth vs {len(detection_results)} results"
                )

            # Calculate confusion matrix
            tp = sum(1 for gt, r in zip(ground_truth, detection_results)
                    if gt.has_bias and r.has_bias_detected)
            fp = sum(1 for gt, r in zip(ground_truth, detection_results)
                    if not gt.has_bias and r.has_bias_detected)
            fn = sum(1 for gt, r in zip(ground_truth, detection_results)
                    if gt.has_bias and not r.has_bias_detected)
            tn = sum(1 for gt, r in zip(ground_truth, detection_results)
                    if not gt.has_bias and not r.has_bias_detected)

            # Calculate metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            return StageResult(
                stage_name="Evaluation",
                success=True,
                samples_processed=len(ground_truth),
                output_summary=f"F1: {f1:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}",
                metrics={
                    "f1": f1,
                    "precision": precision,
                    "recall": recall,
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn
                }
            )
        except Exception as e:
            return StageResult(
                stage_name="Evaluation",
                success=False,
                samples_processed=0,
                output_summary=f"Failed: {str(e)}"
            )
