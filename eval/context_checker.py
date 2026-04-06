"""Re-export context checker from core so eval and api can share one implementation."""

import sys
import os

# HF Space runs from /app but doesn't always have /app on sys.path
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

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
