"""Inter-annotator agreement metrics module.

This module provides Cohen's Kappa (2 annotators) and Krippendorff's Alpha
(2+ annotators) for measuring annotation quality in the AI BRIDGE framework.
"""

from annotation.agreement.cohen_kappa import (
    calculate_cohen_kappa,
    calculate_weighted_kappa,
    calculate_kappa_with_details,
    interpret_kappa,
    format_kappa_report,
)
from annotation.agreement.krippendorff import (
    calculate_krippendorff_alpha,
    calculate_alpha_with_details,
    interpret_alpha,
    format_alpha_report,
)

__all__ = [
    "calculate_cohen_kappa",
    "calculate_weighted_kappa",
    "calculate_kappa_with_details",
    "interpret_kappa",
    "format_kappa_report",
    "calculate_krippendorff_alpha",
    "calculate_alpha_with_details",
    "interpret_alpha",
    "format_alpha_report",
]
