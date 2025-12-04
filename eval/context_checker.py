"""
Context-Aware Correction Checker for Gender Bias Detection

This module implements context detection to prevent over-correction of legitimate
gender references. It checks for conditions where bias correction should be skipped:
- Quoted text (historical quotes, citations)
- Proper nouns (organization names, titles)
- Historical context (past references, dates)
- Biographical context (specific person references)
- Statistical context (factual gender-specific data)
- Medical context (biological/health accuracy)
- Counter-stereotypes (positive challenges to stereotypes)

Based on industry best practices from:
- MBIAS: Mitigating Bias While Retaining Context
- SC2: Content Preservation in Long Text Style Transfer
- Token-Level Disentanglement approaches
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ContextCondition(Enum):
    """Context conditions that may prevent correction."""
    QUOTE = "quote"
    HISTORICAL = "historical"
    PROPER_NOUN = "proper_noun"
    BIOGRAPHICAL = "biographical"
    STATISTICAL = "statistical"
    MEDICAL = "medical"
    COUNTER_STEREOTYPE = "counter_stereotype"
    LEGAL = "legal"
    ARTISTIC = "artistic"
    ORGANIZATION = "organization"


@dataclass
class ContextCheckResult:
    """Result of a context check."""
    should_correct: bool
    blocked_by: Optional[ContextCondition] = None
    reason: str = ""
    confidence: float = 1.0
    matched_pattern: str = ""


class ContextChecker:
    """
    Checks text context to determine if bias correction should be applied.

    This helps preserve meaning in cases where gender references are:
    - Historically accurate
    - Part of proper nouns/organization names
    - Quoting someone directly
    - Providing statistical facts
    - Medically/biologically necessary
    """

    # Context detection patterns organized by condition type
    # {term} placeholder is replaced with the actual biased term
    CONTEXT_PATTERNS: Dict[ContextCondition, List[str]] = {
        ContextCondition.QUOTE: [
            # Direct quotes - various quote styles (ASCII and Unicode)
            # Note: Using {{0,100}} to escape the braces from .format()
            r'"[^"]{{0,100}}{term}[^"]{{0,100}}"',           # "term"
            r"'[^']{{0,100}}{term}[^']{{0,100}}'",           # 'term'
            r'«[^»]{{0,100}}{term}[^»]{{0,100}}»',           # «term» French
            r'„[^"]{{0,100}}{term}[^"]{{0,100}}"',           # „term" German
            r'"[^"]{{0,100}}{term}[^"]{{0,100}}"',           # "term" smart quotes
            r'\"[^\"]{{0,100}}{term}[^\"]{{0,100}}\"',       # \"term\" escaped
            # Reported speech markers (Swahili & English)
            r'\b(alisema|anasema|walisema|said|says|stated|wrote|claimed)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(alisema|anasema|said|says)\b',
        ],

        ContextCondition.HISTORICAL: [
            # Year references (escape braces for .format())
            r'\b(mwaka\s+)?\d{{4}}\b.{{0,50}}{term}',        # "mwaka 1990" or "1990"
            r'{term}.{{0,50}}\b(mwaka\s+)?\d{{4}}\b',
            r'\bin\s+\d{{4}}\b.{{0,30}}{term}',              # "in 1990"
            # Historical markers (Swahili)
            r'\b(kihistoria|historia|zamani|kale|enzi)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(kihistoria|historia|zamani)\b',
            # Historical markers (English)
            r'\b(historically|history|ancient|traditional|formerly)\b.{{0,50}}{term}',
            # Past tense markers
            r'\b(ilikuwa|walikuwa|alikuwa|was|were|used\s+to)\b.{{0,30}}{term}',
        ],

        ContextCondition.PROPER_NOUN: [
            # Proper noun after term (e.g., "Mama Robert", "Baba Kanumba")
            # Must be preceded by word boundary, not sentence start (escape braces)
            r'(?<=[.!?]\s{{1,5}}|\A)(?![A-Z])\b{term}\s+[A-Z][a-z]+',  # Stricter: not at sentence start
            r'(?<=[a-z])\s+{term}\s+[A-Z][a-z]+',       # Mid-sentence "mama Robert"
            # Swahili naming convention: Mama/Baba + Name (very specific)
            r'\b[Mm]ama\s+[A-Z][a-z]{{2,}}',              # "Mama Robert" (min 3 char name)
            r'\b[Bb]aba\s+[A-Z][a-z]{{2,}}',              # "Baba Kanumba"
            # Capitalized title + term (not sentence start)
            r'(?<=[a-z.,;:]\s)[A-Z][a-z]+\s+{term}',    # "Chairman Mao" mid-sentence
            # Organization markers (Swahili)
            r'\b(Chama\s+cha|Shirika\s+la|Taasisi\s+ya|Kampuni\s+ya)\b.{{0,30}}{term}',
            # Organization markers (English)
            r'\b(Organization|Company|Association|Foundation|Institute)\s+.{{0,20}}{term}',
            r'{term}.{{0,20}}\b(Inc|Ltd|LLC|Corp|Foundation)\b',
            # Title patterns
            r'\b(Mheshimiwa|Dkt\.|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+.{{0,20}}{term}',
        ],

        ContextCondition.BIOGRAPHICAL: [
            # Specific person reference (Swahili) - escape braces
            r'\b(yeye|huyu|yule)\s+(ni|alikuwa|amekuwa).{{0,30}}{term}',
            r'{term}\s+wa\s+kwanza',                     # "first [role]"
            r'\baliyekuwa\b.{{0,20}}{term}',               # "who was [role]"
            r'\balikuwa\b.{{0,20}}{term}',                 # "alikuwa mke wa" pattern
            # Specific person reference (English)
            r'\b(she|he)\s+(is|was|became|served\s+as).{{0,30}}{term}',
            r'\bthe\s+first\s+(female|male|woman|man)\s+{term}',
            # Name + role pattern - REQUIRE two capitalized names (not IGNORECASE for names)
            # This is checked specially in _check_condition to avoid false positives
        ],

        ContextCondition.STATISTICAL: [
            # Percentage patterns - term can be before or after with any separator
            r'\d+(\.\d+)?%\s*.{{0,30}}{term}',             # "70% of women"
            r'\d+(\.\d+)?%.{{0,30}}{term}',                # "70%... women" (any chars)
            r'{term}.{{0,30}}\d+(\.\d+)?%',
            # Statistical markers (Swahili)
            r'\b(takwimu|idadi|asilimia|wastani)\b.{{0,30}}{term}',
            # Statistical markers (English)
            r'\b(statistics|data|survey|study|research|percent|majority|minority)\b.{{0,30}}{term}',
            # Numeric context
            r'\b\d+\s+(kati\s+ya|out\s+of|of\s+the)\s+\d+\b.{{0,30}}{term}',
        ],

        ContextCondition.MEDICAL: [
            # Pregnancy/birth (Swahili) - term can be before or after
            r'\b(mjamzito|ujauzito|uzazi|kujifungua|mimba)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(mjamzito|ujauzito|uzazi|kujifungua)\b',
            # "Mama mjamzito" pattern - very common in Swahili health contexts
            r'\b{term}\s+mjamzito\b',
            r'\bmjamzito.{{0,10}}{term}',
            # Pregnancy/birth (English)
            r'\b(pregnant|pregnancy|childbirth|maternal|obstetric|gynecolog)\b.{{0,50}}{term}',
            # Medical procedure context
            r'\b(saratani\s+ya\s+shingo|cervical\s+cancer|breast\s+cancer|prostate)\b.{{0,50}}{term}',
            # Healthcare setting markers
            r'\b(hospitali|clinic|daktari|nurse|doctor|hospital)\b.{{0,30}}{term}',
        ],

        ContextCondition.COUNTER_STEREOTYPE: [
            # Role reversal patterns (Swahili) - no term placeholder, no escaping needed
            r'\b(mwanamke|mama)\b.{0,30}\b(mhandisi|rubani|fundi|mkurugenzi|daktari)\b',
            r'\b(mwanamume|baba)\b.{0,30}\b(muuguzi|mkunga|mlezi|mpishi)\b',
            # Role reversal patterns (English)
            r'\b(female|woman|she)\b.{0,30}\b(engineer|pilot|mechanic|CEO|surgeon)\b',
            r'\b(male|man|he)\b.{0,30}\b(nurse|secretary|nanny|caregiver)\b',
            # "First female/male" achievements
            r'\b(wa\s+kwanza|first)\b.{0,20}\b(wa\s+kike|wa\s+kiume|female|male)\b',
        ],

        ContextCondition.LEGAL: [
            # Legal document markers (Swahili)
            r'\b(sheria|mahakama|kesi|mshtakiwa|mlalamikaji)\b.{{0,30}}{term}',
            # Legal document markers (English)
            r'\b(court|legal|plaintiff|defendant|witness|law|statute)\b.{{0,30}}{term}',
            # Official document context
            r'\b(hati|certificate|document|official|sworn)\b.{{0,30}}{term}',
        ],

        ContextCondition.ARTISTIC: [
            # Creative work markers
            r'\b(wimbo|filamu|kitabu|hadithi|mchezo)\b.{{0,30}}{term}',
            r'\b(song|film|movie|book|novel|play|poem|lyrics)\b.{{0,30}}{term}',
            # Character/role context
            r'\b(mhusika|character|role|actor|actress)\b.{{0,30}}{term}',
        ],

        ContextCondition.ORGANIZATION: [
            # Organization name patterns (Swahili)
            r'\b(TAWOMA|BAWATA|TAMWA|UWT)\b',           # Known women's orgs
            r'\bChama\s+cha\s+\w+\s+{term}',
            # Organization acronyms near term
            r'\b[A-Z]{{2,6}}\b.{{0,20}}{term}',
        ],
    }

    # Swahili-specific patterns for common false positive scenarios
    SWAHILI_PRESERVE_PATTERNS = [
        # "Mama [Name]" - common Swahili naming convention (teknonymn)
        r'\b[Mm]ama\s+[A-Z][a-z]+\b',
        # "Baba [Name]" - common Swahili naming convention
        r'\b[Bb]aba\s+[A-Z][a-z]+\b',
        # Religious/cultural titles
        r'\b(Bibi|Babu|Shangazi|Mjomba)\s+[A-Z][a-z]+\b',
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the context checker.

        Args:
            strict_mode: If True, any context match blocks correction.
                        If False, uses confidence scoring.
        """
        self.strict_mode = strict_mode
        self._compiled_patterns: Dict[ContextCondition, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        for condition, patterns in self.CONTEXT_PATTERNS.items():
            self._compiled_patterns[condition] = []
            for pattern in patterns:
                try:
                    # Patterns with {term} are templates, compile without term for now
                    if '{term}' not in pattern:
                        self._compiled_patterns[condition].append(
                            re.compile(pattern, re.IGNORECASE | re.UNICODE)
                        )
                except re.error:
                    continue

    def _get_pattern_for_term(self, pattern_template: str, term: str) -> Optional[re.Pattern]:
        """Create a compiled pattern with the specific term inserted."""
        try:
            pattern = pattern_template.format(term=re.escape(term))
            return re.compile(pattern, re.IGNORECASE | re.UNICODE)
        except (re.error, KeyError):
            return None

    def check_context(
        self,
        text: str,
        biased_term: str,
        avoid_when: str = "",
        constraints: str = ""
    ) -> ContextCheckResult:
        """
        Check if correction should be applied based on context.

        Args:
            text: Full text being analyzed
            biased_term: The specific biased term found
            avoid_when: Pipe-separated list of conditions from lexicon
            constraints: Additional constraints from lexicon

        Returns:
            ContextCheckResult indicating whether to proceed with correction
        """
        # Parse avoid_when conditions from lexicon
        conditions_to_check = self._parse_avoid_when(avoid_when)

        # If no specific conditions, check all common ones
        if not conditions_to_check:
            conditions_to_check = [
                ContextCondition.QUOTE,
                ContextCondition.PROPER_NOUN,
                ContextCondition.BIOGRAPHICAL,
            ]

        # Check each condition
        for condition in conditions_to_check:
            result = self._check_condition(text, biased_term, condition)
            if not result.should_correct:
                return result

        # Check Swahili-specific preservation patterns
        for pattern in self.SWAHILI_PRESERVE_PATTERNS:
            if re.search(pattern, text):
                # Check if the biased term is part of this preserved pattern
                full_match = re.search(pattern, text)
                if full_match and biased_term.lower() in full_match.group(0).lower():
                    return ContextCheckResult(
                        should_correct=False,
                        blocked_by=ContextCondition.PROPER_NOUN,
                        reason=f"Term is part of Swahili naming convention: {full_match.group(0)}",
                        confidence=0.9,
                        matched_pattern=pattern
                    )

        # All checks passed - proceed with correction
        return ContextCheckResult(
            should_correct=True,
            reason="No blocking context detected",
            confidence=1.0
        )

    def _parse_avoid_when(self, avoid_when: str) -> List[ContextCondition]:
        """Parse the avoid_when field into ContextCondition enums."""
        if not avoid_when or avoid_when.strip() == "":
            return []

        conditions = []
        for part in avoid_when.split('|'):
            part = part.strip().lower()
            try:
                conditions.append(ContextCondition(part))
            except ValueError:
                # Unknown condition, skip
                continue

        return conditions

    def _check_condition(
        self,
        text: str,
        term: str,
        condition: ContextCondition
    ) -> ContextCheckResult:
        """Check a specific context condition."""
        patterns = self.CONTEXT_PATTERNS.get(condition, [])

        for pattern_template in patterns:
            # Handle patterns with {term} placeholder
            if '{term}' in pattern_template:
                pattern = self._get_pattern_for_term(pattern_template, term)
                if pattern and pattern.search(text):
                    return ContextCheckResult(
                        should_correct=False,
                        blocked_by=condition,
                        reason=f"Detected {condition.value} context",
                        confidence=0.85,
                        matched_pattern=pattern_template
                    )
            else:
                # Pre-compiled pattern without term
                compiled = self._compiled_patterns.get(condition, [])
                for cp in compiled:
                    if cp.search(text):
                        return ContextCheckResult(
                            should_correct=False,
                            blocked_by=condition,
                            reason=f"Detected {condition.value} context",
                            confidence=0.85,
                            matched_pattern=cp.pattern
                        )

        # Special check for biographical: Name + term pattern (case-sensitive for names)
        if condition == ContextCondition.BIOGRAPHICAL:
            # Check for "FirstName LastName ... term" pattern (strict capitalization)
            name_pattern = re.compile(
                r'[A-Z][a-z]+\s+[A-Z][a-z]+.{0,30}' + re.escape(term),
                re.UNICODE  # NOT IGNORECASE - names must be capitalized
            )
            if name_pattern.search(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=condition,
                    reason=f"Detected {condition.value} context (name reference)",
                    confidence=0.85,
                    matched_pattern="[Name] + term"
                )

            # Check for "term + Name" pattern (e.g., "mke wa Nelson Mandela")
            term_name_pattern = re.compile(
                re.escape(term) + r'\s+(wa\s+)?[A-Z][a-z]+(\s+[A-Z][a-z]+)?',
                re.UNICODE  # NOT IGNORECASE
            )
            if term_name_pattern.search(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=condition,
                    reason=f"Detected {condition.value} context (name reference)",
                    confidence=0.85,
                    matched_pattern="term + [Name]"
                )

        # No match found for this condition
        return ContextCheckResult(
            should_correct=True,
            reason=f"No {condition.value} context detected",
            confidence=1.0
        )

    def is_in_quotes(self, text: str, term: str) -> bool:
        """Quick check if term appears within quotes."""
        quote_patterns = [
            r'"[^"]*' + re.escape(term) + r'[^"]*"',
            r"'[^']*" + re.escape(term) + r"[^']*'",
        ]
        for pattern in quote_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_proper_nouns(self, text: str) -> List[str]:
        """
        Extract potential proper nouns from text.

        Useful for preserving entities during ML fallback correction.
        """
        # Simple heuristic: capitalized words not at sentence start
        proper_nouns = []

        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)

        for sentence in sentences:
            words = sentence.split()
            for i, word in enumerate(words):
                # Skip first word (sentence start)
                if i == 0:
                    continue
                # Check if capitalized
                if word and word[0].isupper():
                    # Clean punctuation
                    clean_word = re.sub(r'[^\w]', '', word)
                    if clean_word and len(clean_word) > 1:
                        proper_nouns.append(clean_word)

        return list(set(proper_nouns))

    def get_preservation_entities(self, text: str) -> List[str]:
        """
        Get entities that should be preserved during correction.

        Combines proper nouns, organization names, and other key entities.
        """
        entities = set()

        # Add proper nouns
        entities.update(self.extract_proper_nouns(text))

        # Add organization patterns
        org_patterns = [
            r'\b[A-Z]{2,6}\b',  # Acronyms
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two-word names
        ]

        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        return list(entities)


# Convenience function for quick context check
def should_apply_correction(
    text: str,
    biased_term: str,
    avoid_when: str = "",
    constraints: str = ""
) -> Tuple[bool, str]:
    """
    Quick check if correction should be applied.

    Args:
        text: Full text being analyzed
        biased_term: The biased term found
        avoid_when: Conditions from lexicon
        constraints: Additional constraints

    Returns:
        Tuple of (should_correct: bool, reason: str)
    """
    checker = ContextChecker()
    result = checker.check_context(text, biased_term, avoid_when, constraints)
    return result.should_correct, result.reason


if __name__ == "__main__":
    # Test examples
    checker = ContextChecker()

    test_cases = [
        # Should NOT correct - proper noun (Swahili naming)
        ("Mama Robert alisema watoto wapate elimu", "mama Robert", "proper_noun"),

        # Should NOT correct - historical quote
        ('"Mwanamke anapaswa kukaa nyumbani" alisema mtu zamani', "mwanamke anapaswa", "quote|historical"),

        # Should NOT correct - biographical
        ("Winnie Mandela alikuwa mke wa Nelson Mandela", "mke wa", "biographical"),

        # Should NOT correct - statistical
        ("70% ya wanawake wanafanya kazi", "wanawake", "statistical"),

        # Should NOT correct - medical
        ("Mama mjamzito anahitaji huduma", "mama", "medical"),

        # SHOULD correct - general stereotype
        ("Wanawake hawafai kuongoza", "wanawake", ""),

        # SHOULD correct - general bias
        ("Mwanamke anapaswa kupika", "mwanamke anapaswa", ""),
    ]

    print("Context Checker Test Results")
    print("=" * 60)

    for text, term, avoid_when in test_cases:
        result = checker.check_context(text, term, avoid_when)
        status = "SKIP" if not result.should_correct else "CORRECT"
        print(f"\n[{status}] Term: '{term}'")
        print(f"  Text: {text[:60]}...")
        print(f"  Reason: {result.reason}")
        if result.blocked_by:
            print(f"  Blocked by: {result.blocked_by.value}")
