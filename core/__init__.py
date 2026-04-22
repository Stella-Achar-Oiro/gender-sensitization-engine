"""Core shared logic: semantic preservation, context checking, rule loading.

Used by api and eval; no dependency on eval in this package.
"""

from core.semantic_preservation import SemanticPreservationMetrics
from core.context_checker import should_apply_correction, ContextChecker, ContextCondition, ContextCheckResult
from core.rules_loader import load_rules

__all__ = [
    "SemanticPreservationMetrics",
    "should_apply_correction",
    "ContextChecker",
    "ContextCondition",
    "ContextCheckResult",
    "load_rules",
]
