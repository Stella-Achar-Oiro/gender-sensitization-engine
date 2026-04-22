"""
Fairness metrics calculation for bias detection evaluation.

This module implements AI BRIDGE fairness requirements:
- Demographic Parity (DP): ≤0.10 threshold
- Equal Opportunity (EO): ≤0.05 threshold
- Multilingual Bias Evaluation (MBE)

These metrics ensure the bias detection system performs equitably across
demographic groups and language varieties.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .models import Language, BiasCategory


class DemographicGroup(Enum):
    """Demographic groups for fairness analysis."""
    MALE_REFERENT = "male_referent"
    FEMALE_REFERENT = "female_referent"
    NEUTRAL_REFERENT = "neutral_referent"
    UNKNOWN = "unknown"


@dataclass
class FairnessMetrics:
    """
    Fairness evaluation metrics.

    Attributes:
        demographic_parity: Difference in positive prediction rates across groups (≤0.10)
        equal_opportunity: Difference in TPR across groups (≤0.05)
        equalized_odds: Difference in TPR and FPR across groups (≤0.05)
        mbe_score: Multilingual bias evaluation score (0.0 to 1.0, higher is better)
        group_metrics: Per-group performance breakdown
    """
    demographic_parity: float
    equal_opportunity: float
    equalized_odds: float
    mbe_score: float
    group_metrics: dict[str, dict[str, float]]

    def passes_aibridge_requirements(self) -> bool:
        """Check if metrics meet AI BRIDGE fairness thresholds."""
        return (
            self.demographic_parity <= 0.10
            and self.equal_opportunity <= 0.05
            and self.equalized_odds <= 0.05
            and self.mbe_score >= 0.85
        )


class FairnessCalculator:
    """
    Calculate fairness metrics for bias detection evaluation.

    Implements AI BRIDGE fairness requirements to ensure equitable performance
    across demographic groups and language varieties.
    """

    def calculate_demographic_parity(
        self,
        predictions: list[bool],
        groups: list[DemographicGroup]
    ) -> float:
        """
        Calculate Demographic Parity: max difference in positive prediction rates.

        DP = max|P(Ŷ=1|A=a) - P(Ŷ=1|A=b)| across all group pairs

        AI BRIDGE requirement: DP ≤ 0.10

        Args:
            predictions: List of binary predictions (True = bias detected)
            groups: List of demographic groups for each prediction

        Returns:
            Maximum absolute difference in positive rates (0.0 to 1.0)

        Example:
            predictions = [True, True, False, False, True]
            groups = [MALE, MALE, FEMALE, FEMALE, MALE]

            Male positive rate: 3/3 = 1.00
            Female positive rate: 0/2 = 0.00
            DP = |1.00 - 0.00| = 1.00 (FAILS threshold)
        """
        if not predictions or len(predictions) != len(groups):
            return 0.0

        # Calculate positive rate for each group
        group_rates: dict[DemographicGroup, float] = {}

        for group in set(groups):
            group_indices = [i for i, g in enumerate(groups) if g == group]
            if not group_indices:
                continue

            group_predictions = [predictions[i] for i in group_indices]
            positive_rate = sum(group_predictions) / len(group_predictions)
            group_rates[group] = positive_rate

        if len(group_rates) < 2:
            return 0.0

        # Find maximum pairwise difference
        rates = list(group_rates.values())
        max_diff = max(rates) - min(rates)

        return max_diff

    def calculate_equal_opportunity(
        self,
        predictions: list[bool],
        labels: list[bool],
        groups: list[DemographicGroup]
    ) -> float:
        """
        Calculate Equal Opportunity: max difference in True Positive Rates.

        EO = max|TPR(A=a) - TPR(A=b)| across all group pairs
        where TPR = TP / (TP + FN)

        AI BRIDGE requirement: EO ≤ 0.05

        Args:
            predictions: List of binary predictions (True = bias detected)
            labels: List of ground truth labels (True = has bias)
            groups: List of demographic groups for each sample

        Returns:
            Maximum absolute difference in TPR (0.0 to 1.0)

        Example:
            predictions = [True, True, False, True]
            labels = [True, True, True, True]
            groups = [MALE, MALE, FEMALE, FEMALE]

            Male TPR: 2/2 = 1.00
            Female TPR: 1/2 = 0.50
            EO = |1.00 - 0.50| = 0.50 (FAILS threshold)
        """
        if not predictions or len(predictions) != len(labels) or len(predictions) != len(groups):
            return 0.0

        # Calculate TPR for each group
        group_tprs: dict[DemographicGroup, float] = {}

        for group in set(groups):
            group_indices = [i for i, g in enumerate(groups) if g == group]
            if not group_indices:
                continue

            # Count true positives and false negatives for this group
            tp = sum(1 for i in group_indices if predictions[i] and labels[i])
            fn = sum(1 for i in group_indices if not predictions[i] and labels[i])

            if tp + fn == 0:
                continue

            tpr = tp / (tp + fn)
            group_tprs[group] = tpr

        if len(group_tprs) < 2:
            return 0.0

        # Find maximum pairwise difference
        tprs = list(group_tprs.values())
        max_diff = max(tprs) - min(tprs)

        return max_diff

    def calculate_equalized_odds(
        self,
        predictions: list[bool],
        labels: list[bool],
        groups: list[DemographicGroup]
    ) -> float:
        """
        Calculate Equalized Odds: max difference in TPR and FPR.

        EqOdds = max(TPR_diff, FPR_diff)

        AI BRIDGE requirement: EqOdds ≤ 0.05

        Args:
            predictions: List of binary predictions
            labels: List of ground truth labels
            groups: List of demographic groups

        Returns:
            Maximum of TPR difference and FPR difference
        """
        if not predictions or len(predictions) != len(labels) or len(predictions) != len(groups):
            return 0.0

        # Calculate TPR and FPR for each group
        group_metrics: dict[DemographicGroup, dict[str, float]] = {}

        for group in set(groups):
            group_indices = [i for i, g in enumerate(groups) if g == group]
            if not group_indices:
                continue

            # Calculate confusion matrix components
            tp = sum(1 for i in group_indices if predictions[i] and labels[i])
            fp = sum(1 for i in group_indices if predictions[i] and not labels[i])
            tn = sum(1 for i in group_indices if not predictions[i] and not labels[i])
            fn = sum(1 for i in group_indices if not predictions[i] and labels[i])

            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

            group_metrics[group] = {"tpr": tpr, "fpr": fpr}

        if len(group_metrics) < 2:
            return 0.0

        # Find maximum differences
        tprs = [m["tpr"] for m in group_metrics.values()]
        fprs = [m["fpr"] for m in group_metrics.values()]

        tpr_diff = max(tprs) - min(tprs)
        fpr_diff = max(fprs) - min(fprs)

        return max(tpr_diff, fpr_diff)

    def calculate_mbe_score(
        self,
        language_f1_scores: dict[Language, float],
        target_f1: float = 0.75
    ) -> float:
        """
        Calculate Multilingual Bias Evaluation (MBE) score.

        MBE measures consistency of performance across languages relative to target.

        MBE = 1 - (std_dev(F1_scores) / target_F1)

        Higher is better (1.0 = perfect consistency, 0.0 = high variance).
        AI BRIDGE target: MBE ≥ 0.85

        Args:
            language_f1_scores: F1 scores for each language
            target_f1: AI BRIDGE F1 target (default: 0.75)

        Returns:
            MBE score (0.0 to 1.0)

        Example:
            EN: 0.76, SW: 0.80, FR: 0.75, KI: 0.74
            Mean: 0.7625, StdDev: 0.025
            MBE = 1 - (0.025 / 0.75) = 0.967 (PASSES)
        """
        if not language_f1_scores or len(language_f1_scores) < 2:
            return 0.0

        scores = list(language_f1_scores.values())

        # Calculate standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # MBE score
        if target_f1 == 0:
            return 0.0

        mbe = 1.0 - (std_dev / target_f1)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, mbe))

    def calculate_fairness_metrics(
        self,
        predictions: list[bool],
        labels: list[bool],
        groups: list[DemographicGroup],
        language_f1_scores: Optional[dict[Language, float]] = None
    ) -> FairnessMetrics:
        """
        Calculate comprehensive fairness metrics.

        Args:
            predictions: Binary predictions (bias detected or not)
            labels: Ground truth labels
            groups: Demographic group for each sample
            language_f1_scores: Optional F1 scores by language for MBE

        Returns:
            FairnessMetrics object with all fairness measures
        """
        dp = self.calculate_demographic_parity(predictions, groups)
        eo = self.calculate_equal_opportunity(predictions, labels, groups)
        eq_odds = self.calculate_equalized_odds(predictions, labels, groups)

        # Calculate MBE if language scores provided
        mbe = 0.0
        if language_f1_scores:
            mbe = self.calculate_mbe_score(language_f1_scores)

        # Calculate per-group metrics
        group_metrics: dict[str, dict[str, float]] = {}
        for group in set(groups):
            group_indices = [i for i, g in enumerate(groups) if g == group]
            if not group_indices:
                continue

            group_preds = [predictions[i] for i in group_indices]
            group_labels = [labels[i] for i in group_indices]

            # Calculate F1 for this group
            tp = sum(1 for p, l in zip(group_preds, group_labels) if p and l)
            fp = sum(1 for p, l in zip(group_preds, group_labels) if p and not l)
            fn = sum(1 for p, l in zip(group_preds, group_labels) if not p and l)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            group_metrics[group.value] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "sample_count": len(group_indices)
            }

        return FairnessMetrics(
            demographic_parity=dp,
            equal_opportunity=eo,
            equalized_odds=eq_odds,
            mbe_score=mbe,
            group_metrics=group_metrics
        )


def extract_demographic_group(text: str, language: Language) -> DemographicGroup:
    """
    Extract demographic group from text based on gendered references.

    This is a simple heuristic - in production, you'd want more sophisticated
    analysis or explicit annotations in ground truth data.

    Args:
        text: Text sample
        language: Language of the text

    Returns:
        Demographic group classification
    """
    text_lower = " " + text.lower() + " "  # Add spaces for boundary matching

    if language == Language.ENGLISH:
        male_markers = [" he ", " his ", " him ", " man ", " men ", " boy ", " father ", " brother "]
        female_markers = [" she ", " her ", " woman ", " women ", " girl ", " mother ", " sister "]
        neutral_markers = [" they ", " their ", " them ", " person ", " people ", " individual "]

        has_male = any(marker in text_lower for marker in male_markers)
        has_female = any(marker in text_lower for marker in female_markers)
        has_neutral = any(marker in text_lower for marker in neutral_markers)

        if has_male and not has_female:
            return DemographicGroup.MALE_REFERENT
        elif has_female and not has_male:
            return DemographicGroup.FEMALE_REFERENT
        elif has_neutral and not has_male and not has_female:
            return DemographicGroup.NEUTRAL_REFERENT

    elif language == Language.SWAHILI:
        # Swahili is naturally gender-neutral (yeye = he/she)
        # Bias often appears through context, not pronouns
        male_markers = [" mwanamume ", " baba ", " kaka ", " ndugu "]
        female_markers = [" mwanamke ", " mama ", " dada "]

        has_male = any(marker in text_lower for marker in male_markers)
        has_female = any(marker in text_lower for marker in female_markers)

        if has_male and not has_female:
            return DemographicGroup.MALE_REFERENT
        elif has_female and not has_male:
            return DemographicGroup.FEMALE_REFERENT

    return DemographicGroup.UNKNOWN
