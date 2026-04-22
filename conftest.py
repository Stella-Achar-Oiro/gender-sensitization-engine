"""Root conftest.py to configure pytest for the project.

This module configures pytest to properly import our multi-package structure
(eval, api, ml, scripts) without assertion rewriting conflicts.
"""
import sys
from pathlib import Path

# CRITICAL: Add project root to sys.path BEFORE pytest starts collecting tests
# This must happen at module import time, before pytest's assertion rewriting kicks in
# Following gojiberri's pattern: configure paths at module level
_project_root = Path(__file__).parent.resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest  # noqa: E402


def pytest_configure(config):
    """Pytest hook: Configure before test collection.

    This hook runs after paths are set but before tests are collected.
    Following gojiberri's pattern for consistent setup.
    """
    # Re-ensure project root is in path (defensive)
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))


# Optional: Add test markers if needed in future
# pytest.mark.slow, pytest.mark.integration, etc.
