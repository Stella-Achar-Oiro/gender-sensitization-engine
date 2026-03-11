"""Re-export context checker from core so eval and api can share one implementation."""

from core.context_checker import (
    ContextCheckResult,
    ContextChecker,
    ContextCondition,
    should_apply_correction,
)

__all__ = [
    "ContextCheckResult",
    "ContextChecker",
    "ContextCondition",
    "should_apply_correction",
]
