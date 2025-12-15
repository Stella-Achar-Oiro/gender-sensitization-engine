"""
Human-in-the-Loop (HITL) metrics for bias detection evaluation.

This module implements AI BRIDGE HITL requirements:
- Human-Model Agreement Rate (HMAR): ≥0.80 threshold
- Cohen's Kappa (κ): ≥0.70 threshold for inter-annotator agreement
- Krippendorff's Alpha (α): ≥0.80 threshold for multi-annotator reliability

These metrics measure the quality of human validation and the reliability
of the bias detection system's alignment with human judgment.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class HITLMetrics:
    """
    Human-in-the-Loop evaluation metrics.

    Attributes:
        hmar: Human-Model Agreement Rate (0.0 to 1.0, ≥0.80)
        cohens_kappa: Inter-annotator agreement (0.0 to 1.0, ≥0.70)
        krippendorffs_alpha: Multi-annotator reliability (0.0 to 1.0, ≥0.80)
        annotator_count: Number of human annotators
        sample_count: Number of samples evaluated
        agreement_breakdown: Per-category agreement rates
    """
    hmar: float
    cohens_kappa: float
    krippendorffs_alpha: float
    annotator_count: int
    sample_count: int
    agreement_breakdown: dict[str, float]

    def passes_aibridge_requirements(self) -> bool:
        """Check if metrics meet AI BRIDGE HITL thresholds."""
        return (
            self.hmar >= 0.80
            and self.cohens_kappa >= 0.70
            and self.krippendorffs_alpha >= 0.80
        )


class HITLCalculator:
    """
    Calculate Human-in-the-Loop metrics for bias detection validation.

    Implements AI BRIDGE HITL requirements to ensure reliable human validation
    and measure model-human alignment.
    """

    def calculate_hmar(
        self,
        model_predictions: list[bool],
        human_labels: list[bool]
    ) -> float:
        """
        Calculate Human-Model Agreement Rate (HMAR).

        HMAR = (Number of agreements) / (Total samples)

        AI BRIDGE requirement: HMAR ≥ 0.80

        Args:
            model_predictions: Binary predictions from the model
            human_labels: Binary labels from human annotators (ground truth)

        Returns:
            Agreement rate (0.0 to 1.0)

        Example:
            model_predictions = [True, True, False, True, False]
            human_labels =      [True, False, False, True, True]
            agreements = [✓, ✗, ✓, ✓, ✗] = 3/5 = 0.60 (FAILS threshold)
        """
        if not model_predictions or len(model_predictions) != len(human_labels):
            return 0.0

        agreements = sum(1 for m, h in zip(model_predictions, human_labels) if m == h)
        hmar = agreements / len(model_predictions)

        return hmar

    def calculate_cohens_kappa(
        self,
        annotator1_labels: list[bool],
        annotator2_labels: list[bool]
    ) -> float:
        """
        Calculate Cohen's Kappa for inter-annotator agreement.

        κ = (p_o - p_e) / (1 - p_e)

        where:
        - p_o = observed agreement
        - p_e = expected agreement by chance

        AI BRIDGE requirement: κ ≥ 0.70

        Interpretation:
        - κ < 0.00: No agreement
        - 0.00 ≤ κ < 0.20: Slight agreement
        - 0.20 ≤ κ < 0.40: Fair agreement
        - 0.40 ≤ κ < 0.60: Moderate agreement
        - 0.60 ≤ κ < 0.80: Substantial agreement
        - 0.80 ≤ κ ≤ 1.00: Almost perfect agreement

        Args:
            annotator1_labels: First annotator's binary labels
            annotator2_labels: Second annotator's binary labels

        Returns:
            Cohen's Kappa (0.0 to 1.0)

        Example:
            annotator1 = [True, True, False, True, False]
            annotator2 = [True, True, False, False, False]

            Observed agreement: 4/5 = 0.80
            Expected agreement: p_e calculation below
            κ = (0.80 - p_e) / (1 - p_e)
        """
        if not annotator1_labels or len(annotator1_labels) != len(annotator2_labels):
            return 0.0

        n = len(annotator1_labels)

        # Calculate observed agreement (p_o)
        agreements = sum(1 for a1, a2 in zip(annotator1_labels, annotator2_labels) if a1 == a2)
        p_o = agreements / n

        # Calculate expected agreement by chance (p_e)
        # Count occurrences
        a1_true = sum(annotator1_labels)
        a1_false = n - a1_true
        a2_true = sum(annotator2_labels)
        a2_false = n - a2_true

        # Expected agreement for each category
        p_e_true = (a1_true / n) * (a2_true / n)
        p_e_false = (a1_false / n) * (a2_false / n)
        p_e = p_e_true + p_e_false

        # Cohen's Kappa
        if p_e >= 1.0:
            return 0.0

        kappa = (p_o - p_e) / (1 - p_e)

        return max(0.0, kappa)  # Clamp to non-negative

    def calculate_krippendorffs_alpha(
        self,
        annotations: list[list[bool]]
    ) -> float:
        """
        Calculate Krippendorff's Alpha for multi-annotator reliability.

        α = 1 - (D_o / D_e)

        where:
        - D_o = observed disagreement
        - D_e = expected disagreement by chance

        AI BRIDGE requirement: α ≥ 0.80

        Interpretation (same as Cohen's Kappa):
        - α ≥ 0.80: Acceptable for high-stakes decisions
        - α ≥ 0.67: Acceptable for tentative conclusions
        - α < 0.67: Not reliable

        Args:
            annotations: List of annotator lists, where each inner list contains
                        boolean labels from one annotator
                        Example: [[True, False, True], [True, True, True]]
                        means 2 annotators, 3 samples

        Returns:
            Krippendorff's Alpha (0.0 to 1.0)

        Example:
            annotations = [
                [True, True, False, True],   # Annotator 1
                [True, False, False, True],  # Annotator 2
                [True, True, False, False]   # Annotator 3
            ]

            Calculates disagreement across all annotator pairs.
        """
        if not annotations or len(annotations) < 2:
            return 0.0

        n_annotators = len(annotations)
        n_samples = len(annotations[0])

        # Validate all annotators have same number of samples
        if not all(len(ann) == n_samples for ann in annotations):
            return 0.0

        # Convert to matrix: samples x annotators
        # Missing values would be None in production
        matrix = [[annotations[j][i] for j in range(n_annotators)] for i in range(n_samples)]

        # Calculate observed disagreement (D_o)
        total_comparisons = 0
        total_disagreements = 0

        for sample in matrix:
            # For each sample, count disagreements between all annotator pairs
            valid_annotations = [a for a in sample if a is not None]
            if len(valid_annotations) < 2:
                continue

            for i in range(len(valid_annotations)):
                for j in range(i + 1, len(valid_annotations)):
                    total_comparisons += 1
                    if valid_annotations[i] != valid_annotations[j]:
                        total_disagreements += 1

        if total_comparisons == 0:
            return 0.0

        d_o = total_disagreements / total_comparisons

        # Calculate expected disagreement (D_e)
        # Count total occurrences of each category across all annotations
        all_values = [val for sample in matrix for val in sample if val is not None]
        if not all_values:
            return 0.0

        n_total = len(all_values)
        n_true = sum(all_values)
        n_false = n_total - n_true

        # Expected disagreement based on marginal distributions
        # For binary classification: P(disagree) = 2 * P(True) * P(False)
        p_true = n_true / n_total
        p_false = n_false / n_total
        d_e = 2 * p_true * p_false

        if d_e == 0:
            return 0.0

        # Krippendorff's Alpha
        alpha = 1 - (d_o / d_e)

        return max(0.0, min(1.0, alpha))  # Clamp to [0, 1]

    def calculate_hitl_metrics(
        self,
        model_predictions: list[bool],
        human_labels: list[bool],
        multi_annotator_data: Optional[list[list[bool]]] = None
    ) -> HITLMetrics:
        """
        Calculate comprehensive HITL metrics.

        Args:
            model_predictions: Binary predictions from the bias detection model
            human_labels: Binary labels from primary human annotator (ground truth)
            multi_annotator_data: Optional list of annotations from multiple annotators
                                 for Krippendorff's Alpha calculation

        Returns:
            HITLMetrics object with all HITL measures

        Example usage:
            calculator = HITLCalculator()

            # Model vs human agreement
            model_preds = [True, False, True, False]
            human_labels = [True, False, False, False]

            # Multiple annotators for reliability
            multi_annotator = [
                [True, False, False, False],  # Annotator 1
                [True, False, True, False],   # Annotator 2
                [True, True, False, False]    # Annotator 3
            ]

            metrics = calculator.calculate_hitl_metrics(
                model_preds, human_labels, multi_annotator
            )

            print(f"HMAR: {metrics.hmar:.3f}")
            print(f"Cohen's Kappa: {metrics.cohens_kappa:.3f}")
            print(f"Krippendorff's Alpha: {metrics.krippendorffs_alpha:.3f}")
        """
        # Calculate HMAR (model vs human)
        hmar = self.calculate_hmar(model_predictions, human_labels)

        # Calculate Cohen's Kappa (requires two annotators)
        cohens_kappa = 0.0
        if multi_annotator_data and len(multi_annotator_data) >= 2:
            # Use first two annotators for pairwise agreement
            cohens_kappa = self.calculate_cohens_kappa(
                multi_annotator_data[0],
                multi_annotator_data[1]
            )

        # Calculate Krippendorff's Alpha (multi-annotator)
        krippendorffs_alpha = 0.0
        if multi_annotator_data and len(multi_annotator_data) >= 2:
            krippendorffs_alpha = self.calculate_krippendorffs_alpha(
                multi_annotator_data
            )

        # Calculate per-category agreement (simplified for binary classification)
        agreement_breakdown: dict[str, float] = {
            "bias_detected": 0.0,
            "no_bias": 0.0
        }

        # Agreement for samples where human said "has bias"
        bias_indices = [i for i, label in enumerate(human_labels) if label]
        if bias_indices:
            bias_agreements = sum(
                1 for i in bias_indices
                if model_predictions[i] == human_labels[i]
            )
            agreement_breakdown["bias_detected"] = bias_agreements / len(bias_indices)

        # Agreement for samples where human said "no bias"
        no_bias_indices = [i for i, label in enumerate(human_labels) if not label]
        if no_bias_indices:
            no_bias_agreements = sum(
                1 for i in no_bias_indices
                if model_predictions[i] == human_labels[i]
            )
            agreement_breakdown["no_bias"] = no_bias_agreements / len(no_bias_indices)

        annotator_count = len(multi_annotator_data) if multi_annotator_data else 1
        sample_count = len(model_predictions)

        return HITLMetrics(
            hmar=hmar,
            cohens_kappa=cohens_kappa,
            krippendorffs_alpha=krippendorffs_alpha,
            annotator_count=annotator_count,
            sample_count=sample_count,
            agreement_breakdown=agreement_breakdown
        )


def format_hitl_report(metrics: HITLMetrics) -> str:
    """
    Format HITL metrics as a human-readable report.

    Args:
        metrics: HITL metrics to format

    Returns:
        Formatted string report
    """
    status = "✅ PASSES" if metrics.passes_aibridge_requirements() else "⚠️ FAILS"

    report = f"""
Human-in-the-Loop (HITL) Metrics Report
{'=' * 60}

AI BRIDGE Compliance: {status}

Core Metrics:
  Human-Model Agreement Rate (HMAR):  {metrics.hmar:.3f} (target: ≥0.80)
  Cohen's Kappa (κ):                  {metrics.cohens_kappa:.3f} (target: ≥0.70)
  Krippendorff's Alpha (α):           {metrics.krippendorffs_alpha:.3f} (target: ≥0.80)

Evaluation Context:
  Number of Annotators:               {metrics.annotator_count}
  Number of Samples:                  {metrics.sample_count}

Agreement Breakdown:
  Bias Detected Samples:              {metrics.agreement_breakdown.get('bias_detected', 0.0):.3f}
  No Bias Samples:                    {metrics.agreement_breakdown.get('no_bias', 0.0):.3f}

Interpretation:
  HMAR measures how well the model agrees with human judgment.
  Cohen's Kappa measures inter-annotator agreement (2 annotators).
  Krippendorff's Alpha measures multi-annotator reliability (2+ annotators).

{'=' * 60}
"""
    return report
