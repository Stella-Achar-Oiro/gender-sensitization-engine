"""
Simplified data models for bias evaluation framework without external dependencies.

This module defines the data structures used throughout the evaluation system
using only standard library components.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


class BiasCategory(str, Enum):
    """Enumeration of bias categories for classification."""
    OCCUPATION = "occupation"
    PRONOUN_ASSUMPTION = "pronoun_assumption"
    PRONOUN_GENERIC = "pronoun_generic"
    HONORIFIC = "honorific"
    MORPHOLOGY = "morphology"
    NONE = "none"


class Language(str, Enum):
    """Supported languages for bias detection."""
    ENGLISH = "en"
    SWAHILI = "sw"
    HAUSA = "ha"
    YORUBA = "yo"
    IGBO = "ig"


@dataclass
class GroundTruthSample:
    """Single ground truth test case for evaluation."""
    text: str
    has_bias: bool
    bias_category: BiasCategory
    expected_correction: str


@dataclass
class BiasDetectionResult:
    """Result of bias detection on a single text sample."""
    text: str
    has_bias_detected: bool
    detected_edits: List[Dict[str, str]]


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for bias detection performance."""
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


@dataclass
class LanguageEvaluationResult:
    """Complete evaluation results for a single language."""
    language: Language
    overall_metrics: EvaluationMetrics
    category_metrics: Dict[BiasCategory, EvaluationMetrics]
    total_samples: int


@dataclass
class FailureCase:
    """Analysis of a failed prediction case."""
    failure_type: str
    input_text: str
    expected: bool
    predicted: bool
    category: BiasCategory
    diagnosis: str
    language: Language