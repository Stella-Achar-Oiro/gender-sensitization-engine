"""Pydantic data models for annotation system.

This module defines the data structures for AI BRIDGE-compliant annotations,
including all 24 required fields for comprehensive bias detection evaluation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ConfidenceLevel(str, Enum):
    """Annotator confidence in their annotation."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class BiasCategory(str, Enum):
    """Categories of gender bias."""

    OCCUPATION = "occupation"
    PRONOUN_ASSUMPTION = "pronoun_assumption"
    PRONOUN_GENERIC = "pronoun_generic"
    HONORIFIC = "honorific"
    MORPHOLOGY = "morphology"
    OTHER = "other"


class DemographicGroup(str, Enum):
    """Demographic groups for fairness analysis."""

    MALE_REFERENT = "male_referent"
    FEMALE_REFERENT = "female_referent"
    NEUTRAL_REFERENT = "neutral_referent"
    MIXED_REFERENT = "mixed_referent"


class GenderReferent(str, Enum):
    """Gender referent in the text."""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Severity level for bias instances."""

    REPLACE = "replace"  # Must be corrected
    WARN = "warn"  # Should be flagged but may be acceptable
    INFO = "info"  # Informational only


class AnnotatorInfo(BaseModel):
    """Information about an annotator."""

    annotator_id: str = Field(..., description="Unique identifier for annotator")
    name: Optional[str] = Field(None, description="Annotator name (optional)")
    email: Optional[str] = Field(None, description="Contact email")
    native_language: str = Field(..., description="Annotator's native language")
    expertise_level: str = Field(
        ..., description="Expertise level: novice, intermediate, expert"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(use_enum_values=True)


class AnnotationSample(BaseModel):
    """Single annotation sample with AI BRIDGE 24-field schema.

    This model follows the AI BRIDGE framework requirements for comprehensive
    bias detection evaluation, fairness metrics, and human-in-the-loop validation.
    """

    # =========================================================================
    # CORE FIELDS (Fields 1-4: Basic annotation data)
    # =========================================================================

    text: str = Field(..., description="Text to annotate", min_length=1)
    has_bias: bool = Field(..., description="Whether text contains gender bias")
    bias_category: Optional[BiasCategory] = Field(
        None, description="Category of bias if present"
    )
    expected_correction: Optional[str] = Field(
        None, description="Expected neutral correction"
    )

    # =========================================================================
    # ANNOTATION METADATA (Fields 5-8: Who, when, how confident)
    # =========================================================================

    annotator_id: str = Field(..., description="Unique identifier for annotator")
    confidence: ConfidenceLevel = Field(
        ..., description="Annotator confidence level"
    )
    annotation_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now, description="When annotation was created"
    )
    notes: Optional[str] = Field(
        None, description="Additional notes from annotator"
    )

    # =========================================================================
    # FAIRNESS METRICS (Fields 9-12: For demographic parity, equal opportunity)
    # =========================================================================

    demographic_group: DemographicGroup = Field(
        ..., description="Demographic group for fairness analysis"
    )
    gender_referent: GenderReferent = Field(
        ..., description="Gender referent in the text"
    )
    protected_attribute: Optional[str] = Field(
        None, description="Protected attribute being evaluated"
    )
    fairness_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Fairness score if computed"
    )

    # =========================================================================
    # CONTEXT & SEVERITY (Fields 13-15: Understanding the bias)
    # =========================================================================

    context_requires_gender: bool = Field(
        False, description="Whether gender is contextually required"
    )
    severity: SeverityLevel = Field(
        SeverityLevel.REPLACE, description="Severity level for this bias"
    )
    language_variant: Optional[str] = Field(
        None, description="Language variant (e.g., Kenya Swahili, Tanzania Swahili)"
    )

    # =========================================================================
    # HITL METRICS (Fields 16-19: Human-model agreement tracking)
    # =========================================================================

    ml_prediction: Optional[bool] = Field(
        None, description="ML model's prediction for has_bias"
    )
    ml_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML model's confidence score"
    )
    human_model_agreement: Optional[bool] = Field(
        None, description="Whether human and model agree"
    )
    correction_accepted: Optional[bool] = Field(
        None, description="Whether annotator accepted ML correction"
    )

    # =========================================================================
    # SOURCE TRACKING (Fields 20-23: Data lineage)
    # =========================================================================

    source_dataset: Optional[str] = Field(
        None, description="Source dataset (e.g., wikipedia, news, bible)"
    )
    source_url: Optional[str] = Field(None, description="Source URL if available")
    collection_date: Optional[datetime] = Field(
        None, description="When data was collected"
    )
    multi_annotator: bool = Field(
        False, description="Whether multiple annotators reviewed this sample"
    )

    # =========================================================================
    # VERSIONING (Field 24: Schema version tracking)
    # =========================================================================

    version: str = Field(
        "1.0", description="Annotation schema version"
    )

    model_config = ConfigDict(use_enum_values=True)

    @model_validator(mode='after')
    def validate_bias_fields(self):
        """Validate bias-related fields after model creation."""
        # Ensure expected_correction is provided when has_bias is True
        if self.has_bias and not self.expected_correction:
            raise ValueError(
                "expected_correction is required when has_bias is True"
            )

        # Ensure bias_category is provided when has_bias is True
        if self.has_bias and not self.bias_category:
            raise ValueError("bias_category is required when has_bias is True")

        # Auto-compute human_model_agreement if not provided
        if self.human_model_agreement is None:
            if self.ml_prediction is not None:
                self.human_model_agreement = self.ml_prediction == self.has_bias

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = self.model_dump()
        # Convert datetime to ISO format
        if self.annotation_timestamp:
            data["annotation_timestamp"] = self.annotation_timestamp.isoformat()
        if self.collection_date:
            data["collection_date"] = self.collection_date.isoformat()
        return data

    @classmethod
    def from_ground_truth(
        cls,
        text: str,
        has_bias: bool,
        annotator_id: str,
        bias_category: Optional[str] = None,
        expected_correction: Optional[str] = None,
        demographic_group: str = "neutral_referent",
        gender_referent: str = "neutral",
        **kwargs,
    ) -> "AnnotationSample":
        """Create AnnotationSample from ground truth CSV row.

        This factory method helps migrate existing ground truth data to the
        new 24-field AI BRIDGE schema.

        Args:
            text: Sample text
            has_bias: Whether bias is present
            annotator_id: Annotator ID
            bias_category: Optional bias category
            expected_correction: Optional correction
            demographic_group: Demographic group (default: neutral_referent)
            gender_referent: Gender referent (default: neutral)
            **kwargs: Additional optional fields

        Returns:
            AnnotationSample instance
        """
        return cls(
            text=text,
            has_bias=has_bias,
            bias_category=bias_category,
            expected_correction=expected_correction,
            annotator_id=annotator_id,
            confidence=kwargs.get("confidence", ConfidenceLevel.HIGH),
            demographic_group=demographic_group,
            gender_referent=gender_referent,
            severity=kwargs.get("severity", SeverityLevel.REPLACE),
            context_requires_gender=kwargs.get("context_requires_gender", False),
            **{k: v for k, v in kwargs.items() if k not in [
                "confidence", "severity", "context_requires_gender"
            ]},
        )


class AnnotationBatch(BaseModel):
    """A batch of annotations for processing."""

    batch_id: str = Field(..., description="Unique batch identifier")
    language: str = Field(..., description="Language code (en, sw, fr, ki)")
    samples: List[AnnotationSample] = Field(
        default_factory=list, description="List of annotation samples"
    )
    annotator_id: str = Field(..., description="Primary annotator for this batch")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    is_complete: bool = Field(False, description="Whether batch is fully annotated")

    model_config = ConfigDict(use_enum_values=True)

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate (0.0 to 1.0)."""
        if not self.samples:
            return 0.0
        completed = sum(1 for s in self.samples if s.annotation_timestamp is not None)
        return completed / len(self.samples)

    @property
    def agreement_rate(self) -> Optional[float]:
        """Calculate human-model agreement rate."""
        samples_with_ml = [
            s for s in self.samples if s.human_model_agreement is not None
        ]
        if not samples_with_ml:
            return None

        agreements = sum(1 for s in samples_with_ml if s.human_model_agreement)
        return agreements / len(samples_with_ml)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return {
            "batch_id": self.batch_id,
            "language": self.language,
            "samples": [s.to_dict() for s in self.samples],
            "annotator_id": self.annotator_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "is_complete": self.is_complete,
            "completion_rate": self.completion_rate,
            "agreement_rate": self.agreement_rate,
        }


class AnnotationStats(BaseModel):
    """Statistics for an annotation session or batch."""

    total_samples: int = 0
    annotated_samples: int = 0
    bias_detected: int = 0
    bias_percentage: float = 0.0
    avg_confidence: float = 0.0
    agreement_rate: Optional[float] = None
    category_distribution: Dict[str, int] = Field(default_factory=dict)

    @classmethod
    def from_batch(cls, batch: AnnotationBatch) -> "AnnotationStats":
        """Compute statistics from an annotation batch."""
        total = len(batch.samples)
        annotated = sum(1 for s in batch.samples if s.annotation_timestamp)
        bias_detected = sum(1 for s in batch.samples if s.has_bias)

        # Category distribution
        category_dist: Dict[str, int] = {}
        for sample in batch.samples:
            if sample.bias_category:
                cat = str(sample.bias_category)
                category_dist[cat] = category_dist.get(cat, 0) + 1

        # Average confidence (numeric conversion)
        confidence_map = {
            "very_low": 1,
            "low": 2,
            "medium": 3,
            "high": 4,
            "very_high": 5,
        }
        confidences = [
            confidence_map.get(str(s.confidence), 3) for s in batch.samples
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return cls(
            total_samples=total,
            annotated_samples=annotated,
            bias_detected=bias_detected,
            bias_percentage=(bias_detected / total * 100) if total > 0 else 0.0,
            avg_confidence=avg_confidence,
            agreement_rate=batch.agreement_rate,
            category_distribution=category_dist,
        )
