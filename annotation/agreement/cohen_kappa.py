"""Cohen's Kappa for inter-annotator agreement (2 annotators).

Cohen's Kappa measures agreement between two annotators while accounting for
chance agreement. It's used to validate annotation quality in the AI BRIDGE
framework (requirement: κ ≥ 0.70 for Bronze tier).

Formula: κ = (p_o - p_e) / (1 - p_e)
Where:
  p_o = observed agreement
  p_e = expected agreement by chance
"""

from typing import List, Tuple, Dict, Any
import numpy as np

from annotation.models import AnnotationSample


def calculate_cohen_kappa(
    annotations1: List[AnnotationSample],
    annotations2: List[AnnotationSample],
) -> float:
    """Calculate Cohen's Kappa between two annotators.

    Args:
        annotations1: Annotations from first annotator
        annotations2: Annotations from second annotator

    Returns:
        Cohen's Kappa coefficient (-1 to 1, higher is better)

    Raises:
        ValueError: If annotations don't match in length or texts don't match
    """
    if len(annotations1) != len(annotations2):
        raise ValueError(
            f"Annotation counts don't match: {len(annotations1)} vs {len(annotations2)}"
        )

    n = len(annotations1)
    if n == 0:
        raise ValueError("Cannot calculate Kappa with zero annotations")

    # Verify texts match
    for i, (a1, a2) in enumerate(zip(annotations1, annotations2)):
        if a1.text != a2.text:
            raise ValueError(
                f"Text mismatch at index {i}: '{a1.text}' vs '{a2.text}'"
            )

    # Extract has_bias labels (binary classification)
    labels1 = np.array([1 if a.has_bias else 0 for a in annotations1])
    labels2 = np.array([1 if a.has_bias else 0 for a in annotations2])

    # Calculate observed agreement (p_o)
    agreements = labels1 == labels2
    p_o = np.mean(agreements)

    # Calculate expected agreement by chance (p_e)
    # p_e = P(both say 1) + P(both say 0)
    p_1_annotator1 = np.mean(labels1)
    p_1_annotator2 = np.mean(labels2)
    p_0_annotator1 = 1 - p_1_annotator1
    p_0_annotator2 = 1 - p_1_annotator2

    p_e = (p_1_annotator1 * p_1_annotator2) + (p_0_annotator1 * p_0_annotator2)

    # Calculate Kappa
    if p_e == 1.0:
        # Perfect chance agreement (all same label)
        return 1.0 if p_o == 1.0 else 0.0

    kappa = (p_o - p_e) / (1 - p_e)
    return kappa


def calculate_weighted_kappa(
    annotations1: List[AnnotationSample],
    annotations2: List[AnnotationSample],
    weight_by_confidence: bool = True,
) -> float:
    """Calculate weighted Cohen's Kappa using confidence levels.

    Args:
        annotations1: Annotations from first annotator
        annotations2: Annotations from second annotator
        weight_by_confidence: If True, weight by annotator confidence

    Returns:
        Weighted Cohen's Kappa coefficient
    """
    if len(annotations1) != len(annotations2):
        raise ValueError("Annotation counts don't match")

    n = len(annotations1)
    if n == 0:
        raise ValueError("Cannot calculate Kappa with zero annotations")

    # Confidence weights (if enabled)
    confidence_map = {
        "very_low": 1,
        "low": 2,
        "medium": 3,
        "high": 4,
        "very_high": 5,
    }

    weights = []
    for a1, a2 in zip(annotations1, annotations2):
        if weight_by_confidence:
            w1 = confidence_map.get(str(a1.confidence), 3)
            w2 = confidence_map.get(str(a2.confidence), 3)
            weight = (w1 + w2) / 2 / 5  # Normalize to [0, 1]
        else:
            weight = 1.0
        weights.append(weight)

    weights = np.array(weights)
    weights = weights / np.sum(weights)  # Normalize to sum to 1

    # Extract labels
    labels1 = np.array([1 if a.has_bias else 0 for a in annotations1])
    labels2 = np.array([1 if a.has_bias else 0 for a in annotations2])

    # Weighted observed agreement
    agreements = (labels1 == labels2).astype(float)
    p_o = np.sum(weights * agreements)

    # Weighted expected agreement
    p_1_annotator1 = np.sum(weights * labels1)
    p_1_annotator2 = np.sum(weights * labels2)
    p_0_annotator1 = 1 - p_1_annotator1
    p_0_annotator2 = 1 - p_1_annotator2

    p_e = (p_1_annotator1 * p_1_annotator2) + (p_0_annotator1 * p_0_annotator2)

    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0

    kappa = (p_o - p_e) / (1 - p_e)
    return kappa


def calculate_kappa_with_details(
    annotations1: List[AnnotationSample],
    annotations2: List[AnnotationSample],
) -> Dict[str, Any]:
    """Calculate Cohen's Kappa with detailed statistics.

    Args:
        annotations1: Annotations from first annotator
        annotations2: Annotations from second annotator

    Returns:
        Dictionary with Kappa and additional statistics
    """
    kappa = calculate_cohen_kappa(annotations1, annotations2)

    # Calculate confusion matrix
    labels1 = np.array([1 if a.has_bias else 0 for a in annotations1])
    labels2 = np.array([1 if a.has_bias else 0 for a in annotations2])

    # Agreements and disagreements
    both_bias = np.sum((labels1 == 1) & (labels2 == 1))
    both_no_bias = np.sum((labels1 == 0) & (labels2 == 0))
    annotator1_only = np.sum((labels1 == 1) & (labels2 == 0))
    annotator2_only = np.sum((labels1 == 0) & (labels2 == 1))

    agreements = both_bias + both_no_bias
    disagreements = annotator1_only + annotator2_only
    total = len(annotations1)

    # Agreement rate
    agreement_rate = agreements / total if total > 0 else 0.0

    # Disagreement samples
    disagreement_indices = []
    for i, (a1, a2) in enumerate(zip(annotations1, annotations2)):
        if a1.has_bias != a2.has_bias:
            disagreement_indices.append(i)

    return {
        "kappa": kappa,
        "agreement_rate": agreement_rate,
        "total_samples": total,
        "agreements": agreements,
        "disagreements": disagreements,
        "both_bias": both_bias,
        "both_no_bias": both_no_bias,
        "annotator1_only": annotator1_only,
        "annotator2_only": annotator2_only,
        "disagreement_indices": disagreement_indices,
        "passes_aibridge_bronze": kappa >= 0.70,
        "passes_aibridge_silver": kappa >= 0.75,
        "passes_aibridge_gold": kappa >= 0.80,
    }


def interpret_kappa(kappa: float) -> str:
    """Interpret Cohen's Kappa value using Landis & Koch scale.

    Args:
        kappa: Kappa coefficient

    Returns:
        Interpretation string
    """
    if kappa < 0:
        return "Poor (less than chance agreement)"
    elif kappa < 0.20:
        return "Slight"
    elif kappa < 0.40:
        return "Fair"
    elif kappa < 0.60:
        return "Moderate"
    elif kappa < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


def format_kappa_report(
    details: Dict[str, Any],
    annotator1_id: str,
    annotator2_id: str,
) -> str:
    """Format Kappa results as human-readable report.

    Args:
        details: Kappa details from calculate_kappa_with_details()
        annotator1_id: First annotator ID
        annotator2_id: Second annotator ID

    Returns:
        Formatted report string
    """
    kappa = details["kappa"]
    interpretation = interpret_kappa(kappa)

    lines = [
        "\n" + "=" * 70,
        "Cohen's Kappa Inter-Annotator Agreement",
        "=" * 70,
        f"Annotator 1: {annotator1_id}",
        f"Annotator 2: {annotator2_id}",
        f"Total Samples: {details['total_samples']}",
        "",
        f"Cohen's Kappa: {kappa:.4f}",
        f"Interpretation: {interpretation}",
        "",
        "Agreement Statistics:",
        f"  Agreement rate:   {details['agreement_rate']:.1%}",
        f"  Agreements:       {details['agreements']} samples",
        f"  Disagreements:    {details['disagreements']} samples",
        "",
        "Confusion Matrix:",
        f"  Both bias:        {details['both_bias']}",
        f"  Both no bias:     {details['both_no_bias']}",
        f"  {annotator1_id} only:    {details['annotator1_only']}",
        f"  {annotator2_id} only:    {details['annotator2_only']}",
        "",
        "AI BRIDGE Requirements:",
        f"  Bronze (κ ≥ 0.70): {'✅ PASS' if details['passes_aibridge_bronze'] else '❌ FAIL'}",
        f"  Silver (κ ≥ 0.75): {'✅ PASS' if details['passes_aibridge_silver'] else '❌ FAIL'}",
        f"  Gold   (κ ≥ 0.80): {'✅ PASS' if details['passes_aibridge_gold'] else '❌ FAIL'}",
    ]

    if details["disagreements"] > 0 and len(details["disagreement_indices"]) <= 10:
        lines.append("")
        lines.append(f"Disagreement Indices: {details['disagreement_indices']}")

    lines.append("=" * 70 + "\n")

    return "\n".join(lines)
