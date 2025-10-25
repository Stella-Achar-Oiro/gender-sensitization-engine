#!/usr/bin/env python3
"""
Main entry point for running bias detection evaluation.

This script provides a clean interface for running the refactored evaluation system.
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from eval.evaluator import main

if __name__ == "__main__":
    main()