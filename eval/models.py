"""
Simplified data models for bias evaluation framework without external dependencies.

This module defines the data structures used throughout the evaluation system
using only standard library components.

AI BRIDGE Compliance: Implements bias constructs from the AI BRIDGE guidelines
including stereotype, counter-stereotype, derogation, and neutral classifications.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class BiasCategory(str, Enum):
    """Enumeration of bias categories for classification (detection mechanism)."""
    OCCUPATION = "occupation"
    PRONOUN_ASSUMPTION = "pronoun_assumption"
    PRONOUN_GENERIC = "pronoun_generic"
    HONORIFIC = "honorific"
    MORPHOLOGY = "morphology"
    NONE = "none"
    STEREOTYPE="stereotype"


class BiasLabel(str, Enum):
    """
    AI BRIDGE bias label classification.

    Defines the type of representational bias present in text:
    - stereotype: Reinforces common, often oversimplified beliefs about a group
    - counter_stereotype: Challenges or contradicts common stereotypes
    - derogation: Language that demeans or disparages a group
    - neutral: No bias or stereotype present
    """
    STEREOTYPE = "stereotype"
    COUNTER_STEREOTYPE = "counter-stereotype"
    DEROGATION = "derogation"
    NEUTRAL = "neutral"


class StereotypeCategory(str, Enum):
    """
    AI BRIDGE stereotype category classification.

    Thematic areas where gender stereotypes commonly manifest.
    """
    PROFESSION = "profession"
    FAMILY_ROLE = "family_role"
    LEADERSHIP = "leadership"
    EDUCATION = "education"
    RELIGION_CULTURE = "religion_culture"
    PROVERB_IDIOM = "proverb_idiom"
    DAILY_LIFE = "daily_life"
    APPEARANCE = "appearance"
    CAPABILITY = "capability"
    NONE = "none"


class TargetGender(str, Enum):
    """
    AI BRIDGE target gender classification.

    Who is being talked about, referenced, or implied in the text.
    """
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    NONBINARY = "nonbinary"
    UNKNOWN = "unknown"


class Explicitness(str, Enum):
    """
    AI BRIDGE explicitness classification.

    Whether the bias is directly stated or implied through context.
    """
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"


class Sentiment(str, Enum):
    """Emotional tone toward the gendered referent."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SafetyFlag(str, Enum):
    """Content safety classification."""
    SAFE = "safe"
    SENSITIVE = "sensitive"
    REJECT = "reject"


class QAStatus(str, Enum):
    """Quality assurance status for annotations."""
    GOLD = "gold"
    PASSED = "passed"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class Language(str, Enum):
    """Supported languages for bias detection."""
    ENGLISH = "en"
    SWAHILI = "sw"
    FRENCH = "fr"
    GIKUYU = "ki"


@dataclass
class GroundTruthSample:
    """
    Single ground truth test case for evaluation.

    Supports both legacy 4-field format and full AI BRIDGE 29-field format.
    """
    # Core required fields
    text: str
    has_bias: bool
    bias_category: BiasCategory
    expected_correction: str

    # AI BRIDGE extended fields (optional for backward compatibility)
    id: Optional[str] = None
    language: Optional[str] = None
    script: Optional[str] = None
    country: Optional[str] = None
    region_dialect: Optional[str] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    collection_date: Optional[str] = None
    translation: Optional[str] = None
    domain: Optional[str] = None
    topic: Optional[str] = None
    theme: Optional[str] = None
    sensitive_characteristic: Optional[str] = None

    # AI BRIDGE bias annotation fields
    target_gender: Optional[TargetGender] = None
    bias_label: Optional[BiasLabel] = None
    stereotype_category: Optional[StereotypeCategory] = None
    explicitness: Optional[Explicitness] = None
    bias_severity: Optional[int] = None  # 1-3 scale
    sentiment_toward_referent: Optional[Sentiment] = None
    device: Optional[str] = None  # metaphor, proverb, sarcasm, etc.

    # Quality and safety fields
    safety_flag: Optional[SafetyFlag] = None
    pii_removed: Optional[bool] = None
    annotator_id: Optional[str] = None
    qa_status: Optional[QAStatus] = None
    approver_id: Optional[str] = None
    cohen_kappa: Optional[float] = None
    notes: Optional[str] = None
    eval_split: Optional[str] = None  # train, validation, test


@dataclass
class BiasDetectionResult:
    """Result of bias detection on a single text sample."""
    text: str
    has_bias_detected: bool
    detected_edits: List[Dict[str, str]]

    # AI BRIDGE extended detection results
    bias_label: Optional[BiasLabel] = None
    stereotype_category: Optional[StereotypeCategory] = None
    target_gender: Optional[TargetGender] = None
    explicitness: Optional[Explicitness] = None
    confidence: Optional[float] = None

    # Informational warnings from severity=warn rules.
    # These do NOT indicate confirmed bias — they flag terms that may warrant
    # human review (e.g. occupation titles used in factual reporting).
    # has_bias_detected is never set True based on warn_edits alone.
    warn_edits: List[Dict[str, str]] = field(default_factory=list)

    # When detection is from an external team (AIBRIDGE integration), e.g. "external:TeamX".
    # UI can show "Detected by: TeamX · Corrected by: JuaKazi".
    detection_source: Optional[str] = None

    # When detection is from an external team (ExternalTeamDetector), set e.g. "external:TeamX"
    # so the UI can show "Detected by: Team X · Corrected by: JuaKazi".
    detection_source: Optional[str] = None


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