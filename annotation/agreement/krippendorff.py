"""Krippendorff's Alpha for inter-annotator agreement (2+ annotators).

Krippendorff's Alpha generalizes to any number of annotators and handles
missing data. It's more robust than Cohen's Kappa for multiple annotators.

AI BRIDGE requirement: α ≥ 0.80 for Gold tier
"""

from typing import List, Dict, Any
import numpy as np

from annotation.models import AnnotationSample


def calculate_krippendorff_alpha(
    annotations_by_annotator: Dict[str, List[AnnotationSample]],
) -> float:
    """Calculate Krippendorff's Alpha for multiple annotators.

    Args:
        annotations_by_annotator: Dict mapping annotator_id to their annotations.
                                  All annotation lists must have same texts in same order.

    Returns:
        Krippendorff's Alpha coefficient (0 to 1, higher is better)

    Raises:
        ValueError: If annotations don't match or less than 2 annotators
    """
    if len(annotations_by_annotator) < 2:
        raise ValueError(
            f"Need at least 2 annotators, got {len(annotations_by_annotator)}"
        )

    # Validate all annotators have same number of samples
    annotator_ids = list(annotations_by_annotator.keys())
    sample_counts = [len(annotations_by_annotator[aid]) for aid in annotator_ids]

    if len(set(sample_counts)) > 1:
        raise ValueError(
            f"Annotators have different sample counts: {dict(zip(annotator_ids, sample_counts))}"
        )

    n_samples = sample_counts[0]
    if n_samples == 0:
        raise ValueError("Cannot calculate Alpha with zero samples")

    # Build reliability matrix: rows are samples, columns are annotators
    # Value is 1 (has bias) or 0 (no bias), or None if missing
    reliability_matrix = []

    for sample_idx in range(n_samples):
        row = []
        for annotator_id in annotator_ids:
            annotation = annotations_by_annotator[annotator_id][sample_idx]
            value = 1 if annotation.has_bias else 0
            row.append(value)
        reliability_matrix.append(row)

    reliability_matrix = np.array(reliability_matrix)  # shape: (n_samples, n_annotators)

    # Calculate observed disagreement (D_o)
    d_o = calculate_observed_disagreement(reliability_matrix)

    # Calculate expected disagreement (D_e)
    d_e = calculate_expected_disagreement(reliability_matrix)

    # Krippendorff's Alpha
    if d_e == 0:
        return 1.0 if d_o == 0 else 0.0

    alpha = 1 - (d_o / d_e)
    return alpha


def calculate_observed_disagreement(matrix: np.ndarray) -> float:
    """Calculate observed disagreement from reliability matrix.

    Args:
        matrix: Reliability matrix (samples × annotators)

    Returns:
        Observed disagreement value
    """
    n_samples, n_annotators = matrix.shape
    total_disagreement = 0.0
    total_pairs = 0

    for sample_idx in range(n_samples):
        values = matrix[sample_idx]
        # Count pairwise disagreements
        for i in range(n_annotators):
            for j in range(i + 1, n_annotators):
                if values[i] != values[j]:
                    total_disagreement += 1.0
                total_pairs += 1

    if total_pairs == 0:
        return 0.0

    return total_disagreement / total_pairs


def calculate_expected_disagreement(matrix: np.ndarray) -> float:
    """Calculate expected disagreement by chance.

    Args:
        matrix: Reliability matrix (samples × annotators)

    Returns:
        Expected disagreement value
    """
    # Flatten to get all values
    all_values = matrix.flatten()

    # Calculate marginal distribution
    unique_values = np.unique(all_values)
    value_counts = {val: np.sum(all_values == val) for val in unique_values}
    total = len(all_values)

    # Expected disagreement is probability of picking different values
    expected_disagreement = 0.0
    for val1 in unique_values:
        for val2 in unique_values:
            if val1 != val2:
                p_val1 = value_counts[val1] / total
                p_val2 = value_counts[val2] / total
                expected_disagreement += p_val1 * p_val2

    return expected_disagreement


def calculate_alpha_with_details(
    annotations_by_annotator: Dict[str, List[AnnotationSample]],
) -> Dict[str, Any]:
    """Calculate Krippendorff's Alpha with detailed statistics.

    Args:
        annotations_by_annotator: Dict mapping annotator_id to annotations

    Returns:
        Dictionary with Alpha and additional statistics
    """
    alpha = calculate_krippendorff_alpha(annotations_by_annotator)

    annotator_ids = list(annotations_by_annotator.keys())
    n_annotators = len(annotator_ids)
    n_samples = len(annotations_by_annotator[annotator_ids[0]])

    # Calculate pairwise agreements
    pairwise_agreements = {}
    for i, aid1 in enumerate(annotator_ids):
        for j, aid2 in enumerate(annotator_ids):
            if i < j:
                anns1 = annotations_by_annotator[aid1]
                anns2 = annotations_by_annotator[aid2]
                labels1 = [1 if a.has_bias else 0 for a in anns1]
                labels2 = [1 if a.has_bias else 0 for a in anns2]
                agreement = sum(l1 == l2 for l1, l2 in zip(labels1, labels2)) / len(labels1)
                pairwise_agreements[f"{aid1}_vs_{aid2}"] = agreement

    # Overall agreement rate
    avg_pairwise = np.mean(list(pairwise_agreements.values()))

    return {
        "alpha": alpha,
        "n_annotators": n_annotators,
        "n_samples": n_samples,
        "annotator_ids": annotator_ids,
        "pairwise_agreements": pairwise_agreements,
        "avg_pairwise_agreement": avg_pairwise,
        "passes_aibridge_bronze": alpha >= 0.70,
        "passes_aibridge_silver": alpha >= 0.75,
        "passes_aibridge_gold": alpha >= 0.80,
    }


def interpret_alpha(alpha: float) -> str:
    """Interpret Krippendorff's Alpha value.

    Args:
        alpha: Alpha coefficient

    Returns:
        Interpretation string
    """
    if alpha < 0:
        return "Poor (worse than chance)"
    elif alpha < 0.67:
        return "Low (tentative conclusions)"
    elif alpha < 0.80:
        return "Moderate (acceptable for exploratory research)"
    else:
        return "High (suitable for production use)"


def format_alpha_report(details: Dict[str, Any]) -> str:
    """Format Alpha results as human-readable report.

    Args:
        details: Alpha details from calculate_alpha_with_details()

    Returns:
        Formatted report string
    """
    alpha = details["alpha"]
    interpretation = interpret_alpha(alpha)

    lines = [
        "\n" + "=" * 70,
        "Krippendorff's Alpha Inter-Annotator Agreement",
        "=" * 70,
        f"Annotators: {', '.join(details['annotator_ids'])}",
        f"Number of Annotators: {details['n_annotators']}",
        f"Number of Samples: {details['n_samples']}",
        "",
        f"Krippendorff's Alpha: {alpha:.4f}",
        f"Interpretation: {interpretation}",
        "",
        f"Avg Pairwise Agreement: {details['avg_pairwise_agreement']:.1%}",
    ]

    if len(details["pairwise_agreements"]) <= 10:
        lines.append("")
        lines.append("Pairwise Agreements:")
        for pair, agreement in sorted(details["pairwise_agreements"].items()):
            lines.append(f"  {pair:30s}: {agreement:.1%}")

    lines.extend([
        "",
        "AI BRIDGE Requirements:",
        f"  Bronze (α ≥ 0.70): {'✅ PASS' if details['passes_aibridge_bronze'] else '❌ FAIL'}",
        f"  Silver (α ≥ 0.75): {'✅ PASS' if details['passes_aibridge_silver'] else '❌ FAIL'}",
        f"  Gold   (α ≥ 0.80): {'✅ PASS' if details['passes_aibridge_gold'] else '❌ FAIL'}",
        "=" * 70 + "\n",
    ])

    return "\n".join(lines)
