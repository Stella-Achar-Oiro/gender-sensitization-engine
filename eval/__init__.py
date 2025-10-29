"""
JuaKazi Bias Evaluation Framework

A modular, maintainable framework for evaluating gender bias detection systems
in African languages.

Main Components:
- models: Core data structures and types
- data_loader: File I/O and data validation
- bias_detector: Bias detection services
- metrics_calculator: Evaluation metrics computation
- evaluator: Main orchestration and coordination

Usage:
    from eval.evaluator import BiasEvaluationOrchestrator
    
    orchestrator = BiasEvaluationOrchestrator()
    results = orchestrator.run_evaluation()
"""

from .models import (
    Language,
    BiasCategory,
    GroundTruthSample,
    BiasDetectionResult,
    EvaluationMetrics,
    LanguageEvaluationResult,
    FailureCase
)

from .evaluator import BiasEvaluationOrchestrator, EvaluationError
from .bias_detector import BiasDetector, BaselineDetector, BiasDetectionError
from .data_loader import GroundTruthLoader, RulesLoader, ResultsWriter, DataLoadError
from .metrics_calculator import MetricsCalculator, MetricsFormatter

__version__ = "1.0.0"
__author__ = "JuaKazi Team"

__all__ = [
    # Core models
    "Language",
    "BiasCategory", 
    "GroundTruthSample",
    "BiasDetectionResult",
    "EvaluationMetrics",
    "LanguageEvaluationResult",
    "FailureCase",
    
    # Main services
    "BiasEvaluationOrchestrator",
    "BiasDetector",
    "BaselineDetector",
    "GroundTruthLoader",
    "RulesLoader",
    "ResultsWriter",
    "MetricsCalculator",
    "MetricsFormatter",
    
    # Exceptions
    "EvaluationError",
    "BiasDetectionError", 
    "DataLoadError"
]