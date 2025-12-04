"""
Bias detection service for evaluating gender bias in text.

This module provides a clean interface for bias detection using rules-based matching.
Implements AI BRIDGE bias constructs: stereotype, counter-stereotype, derogation, neutral.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    Language, BiasDetectionResult, BiasLabel, StereotypeCategory,
    TargetGender, Explicitness
)
from .data_loader import RulesLoader, DataLoadError
from .ngeli_tracker import NgeliTracker, NounClass


# Set up module logger
logger = logging.getLogger(__name__)


class BiasDetectionError(Exception):
    """Custom exception for bias detection errors."""
    pass


class BiasDetector:
    """
    Service for detecting gender bias in text using rules-based approach.

    This class encapsulates the bias detection logic and provides a clean interface
    for evaluating text samples. Implements AI BRIDGE bias constructs.
    """

    # Counter-stereotype patterns by language
    # These indicate role reversals or challenges to traditional gender norms
    COUNTER_STEREOTYPE_PATTERNS = {
        Language.ENGLISH: [
            # Family role reversals
            (r'\b(father|dad|husband)\b.*(caregiver|nurtur|cook|clean|homemaker|stay.at.home)',
             StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
            (r'\b(mother|mom|wife)\b.*(breadwinner|provider|work.*(full.time|office)|career)',
             StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
            # Professional role reversals
            (r'\b(female|woman|she)\b.*(engineer|mechanic|pilot|ceo|surgeon|firefighter)',
             StereotypeCategory.PROFESSION, TargetGender.FEMALE),
            (r'\b(male|man|he)\b.*(nurse|secretary|receptionist|kindergarten|nanny)',
             StereotypeCategory.PROFESSION, TargetGender.MALE),
            # Leadership
            (r'\b(she|her|woman|female)\b.*(lead|command|chief|director|president|boss)',
             StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        ],
        Language.SWAHILI: [
            # Family role reversals (Swahili) - more specific patterns
            (r'\bbaba\b.+\b(anale[zl]a|anapika|anasafisha|anakaa\s+nyumbani)',
             StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
            (r'\bmama\b.+\b(anafanya\s+kazi\s+ofisi|ni\s+mkurugenzi|anaongoza)',
             StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
            # Professional role reversals - more specific
            (r'\bmwanamke\b.+\b(mhandisi|rubani|fundi\s+wa\s+magari)',
             StereotypeCategory.PROFESSION, TargetGender.FEMALE),
            (r'\bmwanamume\b.+\b(muuguzi|mkunga|mlezi\s+wa\s+watoto)',
             StereotypeCategory.PROFESSION, TargetGender.MALE),
        ],
    }

    # Derogation patterns - language that demeans or disparages
    DEROGATION_PATTERNS = {
        Language.ENGLISH: [
            (r'\b(just|only|merely)\s+a\s+(woman|girl|female|housewife)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(woman|women|female|girl).*(can\'t|cannot|unable|incapable|shouldn\'t|could\s+never)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(women|woman)\s+(cannot|can\'t)\s+be\s+(good|great|effective)',
             StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
            (r'\b(like\s+a\s+girl|throw.like.a.girl|cry.like)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(too\s+emotional|hysterical|overreact)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(real\s+men\s+don\'t|man\s+up|be\s+a\s+man)',
             StereotypeCategory.CAPABILITY, TargetGender.MALE),
        ],
        Language.SWAHILI: [
            (r'\b(tu|basi)\s+(mwanamke|msichana)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(mwanamke|msichana).*(hawezi|haiwezekani|dhaifu)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            (r'\b(kama\s+msichana|kama\s+mwanamke)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        ],
    }

    def __init__(self, rules_dir: Path = Path("rules"), enable_ngeli_tracking: bool = True):
        """
        Initialize the bias detector.

        Args:
            rules_dir: Directory containing bias detection rules
            enable_ngeli_tracking: Enable Swahili noun class tracking (default: True)
        """
        self.rules_loader = RulesLoader(rules_dir)
        self._rules_cache: Dict[Language, List[Dict[str, str]]] = {}
        self._compiled_patterns: Dict[Language, List[re.Pattern]] = {}
        self._counter_stereotype_patterns: Dict[Language, List[tuple]] = {}
        self._derogation_patterns: Dict[Language, List[tuple]] = {}
        self.enable_ngeli_tracking = enable_ngeli_tracking
        self.ngeli_tracker = NgeliTracker() if enable_ngeli_tracking else None

        # Compile counter-stereotype and derogation patterns
        self._compile_special_patterns()

    def _compile_special_patterns(self) -> None:
        """Compile counter-stereotype and derogation regex patterns."""
        for lang, patterns in self.COUNTER_STEREOTYPE_PATTERNS.items():
            self._counter_stereotype_patterns[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]

        for lang, patterns in self.DEROGATION_PATTERNS.items():
            self._derogation_patterns[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]

    def _detect_counter_stereotype(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """
        Detect counter-stereotype patterns in text.

        Counter-stereotypes challenge or contradict common gender stereotypes.
        These should be preserved, not corrected.
        """
        patterns = self._counter_stereotype_patterns.get(language, [])
        for pattern, category, gender in patterns:
            if pattern.search(text):
                return {
                    'bias_label': BiasLabel.COUNTER_STEREOTYPE,
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': Explicitness.EXPLICIT,
                    'matched_pattern': pattern.pattern
                }
        return None

    def _detect_derogation(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """
        Detect derogatory language patterns in text.

        Derogation is language that demeans or disparages a gender group.
        """
        patterns = self._derogation_patterns.get(language, [])
        for pattern, category, gender in patterns:
            if pattern.search(text):
                return {
                    'bias_label': BiasLabel.DEROGATION,
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': Explicitness.EXPLICIT,
                    'matched_pattern': pattern.pattern
                }
        return None

    def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
        """
        Detect bias in a text sample.

        Implements AI BRIDGE bias construct detection:
        - stereotype: Reinforces common gender beliefs
        - counter-stereotype: Challenges gender stereotypes (preserved, not corrected)
        - derogation: Language that demeans a gender group
        - neutral: No bias present

        Args:
            text: Text to analyze for bias
            language: Language of the text

        Returns:
            BiasDetectionResult with detection results and AI BRIDGE classifications

        Raises:
            BiasDetectionError: If detection fails
        """
        try:
            # First check for derogation (highest priority - most harmful)
            derogation_result = self._detect_derogation(text, language)
            if derogation_result:
                return BiasDetectionResult(
                    text=text,
                    has_bias_detected=True,
                    detected_edits=[{
                        'from': text,
                        'to': '[DEROGATORY - requires manual review]',
                        'severity': 'high',
                        'bias_type': 'derogation'
                    }],
                    bias_label=BiasLabel.DEROGATION,
                    stereotype_category=derogation_result['stereotype_category'],
                    target_gender=derogation_result['target_gender'],
                    explicitness=Explicitness.EXPLICIT,
                    confidence=0.9
                )

            # Check for counter-stereotype (should be preserved, not corrected)
            counter_result = self._detect_counter_stereotype(text, language)
            if counter_result:
                return BiasDetectionResult(
                    text=text,
                    has_bias_detected=False,  # Counter-stereotypes are not "bias" to correct
                    detected_edits=[],  # No edits needed - preserve the text
                    bias_label=BiasLabel.COUNTER_STEREOTYPE,
                    stereotype_category=counter_result['stereotype_category'],
                    target_gender=counter_result['target_gender'],
                    explicitness=Explicitness.EXPLICIT,
                    confidence=0.85
                )

            # Standard stereotype detection via lexicon rules
            rules = self._get_rules(language)
            patterns = self._get_compiled_patterns(language)

            detected_edits = []
            detected_categories = []
            detected_genders = []

            for rule, pattern in zip(rules, patterns):
                if pattern.search(text):
                    # Skip if biased == neutral (already gender-neutral term)
                    if rule['biased'] == rule['neutral_primary']:
                        continue

                    edit = {
                        'from': rule['biased'],
                        'to': rule['neutral_primary'],
                        'severity': rule['severity'],
                        'bias_type': rule.get('bias_label', 'stereotype'),
                        'stereotype_category': rule.get('stereotype_category', 'profession')
                    }

                    # Add ngeli metadata for Swahili
                    if language == Language.SWAHILI and self.ngeli_tracker:
                        ngeli = rule.get('ngeli', '')
                        if ngeli:
                            edit['ngeli'] = ngeli
                            self.ngeli_tracker.track_noun(rule['biased'])

                    detected_edits.append(edit)

                    # Track categories for result aggregation
                    cat = rule.get('stereotype_category', 'profession')
                    if cat:
                        detected_categories.append(cat)

            # Determine primary stereotype category
            primary_category = None
            if detected_categories:
                try:
                    primary_category = StereotypeCategory(detected_categories[0])
                except (ValueError, KeyError):
                    primary_category = StereotypeCategory.PROFESSION

            # Analyze text for noun class patterns (Swahili only)
            ngeli_analysis = None
            if language == Language.SWAHILI and self.ngeli_tracker:
                ngeli_analysis = self.ngeli_tracker.analyze_text(text)

            # Build result with AI BRIDGE fields
            has_bias = len(detected_edits) > 0
            result = BiasDetectionResult(
                text=text,
                has_bias_detected=has_bias,
                detected_edits=detected_edits,
                bias_label=BiasLabel.STEREOTYPE if has_bias else BiasLabel.NEUTRAL,
                stereotype_category=primary_category,
                target_gender=None,  # Would need deeper NLP for gender inference
                explicitness=Explicitness.EXPLICIT if has_bias else None,
                confidence=0.85 if has_bias else 0.7
            )

            # Attach ngeli analysis as metadata
            if ngeli_analysis:
                result._ngeli_analysis = ngeli_analysis

            return result

        except Exception as e:
            raise BiasDetectionError(f"Failed to detect bias in text: {e}") from e
    
    def _get_rules(self, language: Language) -> List[Dict[str, str]]:
        """Get rules for a language, loading and caching if necessary."""
        if language not in self._rules_cache:
            try:
                self._rules_cache[language] = self.rules_loader.load_rules(language)
            except DataLoadError as e:
                raise BiasDetectionError(f"Failed to load rules for {language}: {e}") from e
        
        return self._rules_cache[language]
    
    def _get_compiled_patterns(self, language: Language) -> List[re.Pattern]:
        """Get compiled regex patterns for a language, compiling and caching if necessary."""
        if language not in self._compiled_patterns:
            rules = self._get_rules(language)
            patterns = []

            for rule in rules:
                biased_term = rule['biased']
                pos = rule.get('pos', 'noun')

                # Different pattern strategies based on term type
                if ' ' in biased_term:
                    # Multi-word phrase: use word boundaries only at start/end
                    # Example: "wa kike" → r'\bwa kike\b'
                    pattern = r'\b' + re.escape(biased_term) + r'\b'
                elif pos == 'suffix' or len(biased_term) <= 4:
                    # Suffix or short term: match as substring with word boundaries
                    # Example: "zake" → r'\bzake\b' (matches "rekodi zake")
                    # This allows matching within longer phrases
                    pattern = r'\b' + re.escape(biased_term) + r'\b'
                else:
                    # Single-word term: strict word boundary matching
                    pattern = r'\b' + re.escape(biased_term) + r'\b'

                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    patterns.append(compiled_pattern)
                except re.error as e:
                    # Skip invalid patterns but log the issue
                    logger.warning(
                        "Invalid regex pattern for '%s': %s",
                        biased_term, e
                    )
                    continue

            self._compiled_patterns[language] = patterns

        return self._compiled_patterns[language]
    
    def get_ngeli_statistics(self) -> Optional[Dict[str, int]]:
        """
        Get noun class statistics from tracked Swahili nouns.

        Returns:
            Dictionary mapping noun class codes to counts, or None if tracking disabled
        """
        if self.ngeli_tracker:
            return self.ngeli_tracker.get_statistics()
        return None

    def clear_cache(self) -> None:
        """Clear the rules and patterns cache."""
        self._rules_cache.clear()
        self._compiled_patterns.clear()


class BaselineDetector:
    """
    Simple baseline detector for comparison purposes.
    
    Uses naive gendered term detection without sophisticated rules.
    """
    
    def __init__(self):
        """Initialize the baseline detector."""
        self.gendered_terms = {
            Language.ENGLISH: ['he', 'she', 'his', 'her', 'him', 'man', 'woman', 'male', 'female', 'boy', 'girl'],
            Language.SWAHILI: ['yeye', 'mwanaume', 'mwanamke', 'mvulana', 'msichana', 'baba', 'mama']
        }
    
    def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
        """
        Detect bias using simple gendered term matching.
        
        Args:
            text: Text to analyze
            language: Language of the text
            
        Returns:
            BiasDetectionResult with detection results
        """
        text_lower = text.lower()
        terms = self.gendered_terms.get(language, [])
        
        detected_terms = []
        for term in terms:
            if term in text_lower:
                detected_terms.append({
                    'from': term,
                    'to': '[gendered_term]',
                    'severity': 'baseline'
                })
        
        return BiasDetectionResult(
            text=text,
            has_bias_detected=len(detected_terms) > 0,
            detected_edits=detected_terms
        )