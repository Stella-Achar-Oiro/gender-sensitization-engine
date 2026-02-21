"""Annotation package for human validation and expert review.

This package provides tools for annotating gender bias samples following
the AI BRIDGE framework requirements, including multi-annotator agreement
metrics and comprehensive annotation tracking.
"""

from annotation.models import (
    AnnotationSample,
    AnnotatorInfo,
    ConfidenceLevel,
    AnnotationBatch,
    AnnotationStats,
    BiasCategory,
    DemographicGroup,
    GenderReferent,
    SeverityLevel,
)
from annotation.interface import AnnotationInterface
from annotation.validator import AnnotationValidator, ValidationError
from annotation.schema import AIBRIDGESchemaEnforcer, validate_ai_bridge_compliance
from annotation.export import AnnotationExporter

__all__ = [
    "AnnotationSample",
    "AnnotatorInfo",
    "ConfidenceLevel",
    "AnnotationBatch",
    "AnnotationStats",
    "BiasCategory",
    "DemographicGroup",
    "GenderReferent",
    "SeverityLevel",
    "AnnotationInterface",
    "AnnotationValidator",
    "ValidationError",
    "AIBRIDGESchemaEnforcer",
    "validate_ai_bridge_compliance",
    "AnnotationExporter",
]
