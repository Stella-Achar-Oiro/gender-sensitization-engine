"""
Bias detection service for evaluating gender bias in text.

This module provides a clean interface for bias detection using rules-based matching.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import Language, BiasDetectionResult
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
    for evaluating text samples.
    """
    
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
        self.enable_ngeli_tracking = enable_ngeli_tracking
        self.ngeli_tracker = NgeliTracker() if enable_ngeli_tracking else None
    
    def detect_bias(self, text: str, language: Language) -> BiasDetectionResult:
        """
        Detect bias in a text sample.
        
        Args:
            text: Text to analyze for bias
            language: Language of the text
            
        Returns:
            BiasDetectionResult with detection results
            
        Raises:
            BiasDetectionError: If detection fails
        """
        try:
            rules = self._get_rules(language)
            patterns = self._get_compiled_patterns(language)
            
            detected_edits = []
            
            for rule, pattern in zip(rules, patterns):
                if pattern.search(text):
                    # Skip if biased == neutral (already gender-neutral term)
                    # These terms only need detection in pronoun/morphology contexts
                    if rule['biased'] == rule['neutral_primary']:
                        continue

                    edit = {
                        'from': rule['biased'],
                        'to': rule['neutral_primary'],
                        'severity': rule['severity']
                    }

                    # Add ngeli metadata for Swahili
                    if language == Language.SWAHILI and self.ngeli_tracker:
                        ngeli = rule.get('ngeli', '')
                        if ngeli:
                            edit['ngeli'] = ngeli
                            # Track noun for statistics
                            self.ngeli_tracker.track_noun(rule['biased'])

                    detected_edits.append(edit)

            # Analyze text for noun class patterns (Swahili only)
            ngeli_analysis = None
            if language == Language.SWAHILI and self.ngeli_tracker:
                ngeli_analysis = self.ngeli_tracker.analyze_text(text)

            result = BiasDetectionResult(
                text=text,
                has_bias_detected=len(detected_edits) > 0,
                detected_edits=detected_edits
            )

            # Attach ngeli analysis as metadata (not part of standard result)
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