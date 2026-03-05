"""
Bias detection service for evaluating gender bias in text.

This module provides a clean interface for bias detection using rules-based matching.
Implements AI BRIDGE bias constructs: stereotype, counter-stereotype, derogation, neutral.

Enhanced with context-aware correction to preserve meaning when gender terms are used
for accuracy (biographical, historical, medical, etc.) rather than bias.
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
from .context_checker import ContextChecker, ContextCheckResult


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

    # Swahili gendered-suffix patterns — catch "[occupation] wa kiume/wa kike" on ANY occupation.
    # These are the highest-volume recall gap: 1,847 sentences in SW ground truth use this
    # construction with occupations not individually listed in the lexicon.
    # Correction: remove " wa kiume" / " wa kike" suffix, preserve the occupation term.
    # Pattern requires a Swahili word (m-wa class prefix likely) before the suffix.
    SW_GENDERED_SUFFIX_PATTERNS = [
        # wa kiume — male gender marker on occupation
        (r'\b(\w+)\s+(wa\s+kiume)\b', 'wa kiume', TargetGender.MALE),
        # wa kike — female gender marker on occupation
        (r'\b(\w+)\s+(wa\s+kike)\b', 'wa kike', TargetGender.FEMALE),
        # watoto wa kike / watoto wa kiume — children gendered (family_role not profession)
        # handled by same patterns above; stereotype_category set to profession by default,
        # overridden to family_role when "watoto" is the preceding noun
    ]
    # Compiled at init time by _compile_special_patterns
    _sw_gendered_suffix_compiled: list = []

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
            # Dismissive "ni tu mwanamke/msichana" = "s/he is just a woman"
            # Must be predicate construction (ni + tu), not bare "tu mwanamke" which is too broad
            (r'\bni\s+tu\s+(mwanamke|msichana)\b',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            # Direct derogation: "mwanamke/msichana hawezi" where hawezi is a direct predicate
            # Exclude medical contexts (kuzaa, kukoma, kupenda) and counter-stereotype quotations
            # (hawezi bila kuwezeshwa = quoting stereotype in order to reject it)
            (r'\b(mwanamke|msichana)\b\s+hawezi\b(?!\s+(?:kuzaa|kukoma|kupenda|kunifikia|kufikia|kukufikia|bila\s+kuwezeshwa))',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
            # Require "kama mwanamke/msichana" to be followed by a negative/derogatory term,
            # not just any noun phrase (e.g. "kama mwanamke wa imani" is biographical)
            (r'\b(kama\s+msichana|kama\s+mwanamke)\b.{0,30}\b(dhaifu|hawezi|haiwezi|hana nguvu|anapiga|analia)',
             StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        ],
    }

    def __init__(
        self,
        rules_dir: Path = Path("rules"),
        enable_ngeli_tracking: bool = True,
        enable_context_checking: bool = True,
        enable_ml_fallback: bool = True,
        ml_threshold: float = 0.75,
    ):
        """
        Initialize the bias detector.

        Args:
            rules_dir: Directory containing bias detection rules
            enable_ngeli_tracking: Enable Swahili noun class tracking (default: True)
            enable_context_checking: Enable context-aware correction (default: True)
            enable_ml_fallback: Run ML classifier when rules find nothing (default: True)
            ml_threshold: Minimum ML confidence to surface a warn edit (default: 0.75)
        """
        self.rules_loader = RulesLoader(rules_dir)
        self._rules_cache: Dict[Language, List[Dict[str, str]]] = {}
        self._compiled_patterns: Dict[Language, List[re.Pattern]] = {}
        self._counter_stereotype_patterns: Dict[Language, List[tuple]] = {}
        self._derogation_patterns: Dict[Language, List[tuple]] = {}
        self.enable_ngeli_tracking = enable_ngeli_tracking
        self.ngeli_tracker = NgeliTracker() if enable_ngeli_tracking else None

        # Context-aware correction to preserve meaning
        self.enable_context_checking = enable_context_checking
        self.context_checker = ContextChecker() if enable_context_checking else None

        # ML fallback — Stage 2 classifier for cases rules miss
        self.enable_ml_fallback = enable_ml_fallback
        self._ml_threshold = ml_threshold

        # Compile counter-stereotype and derogation patterns
        self._compile_special_patterns()

    def _compile_special_patterns(self) -> None:
        """Compile counter-stereotype, derogation, and SW gendered-suffix regex patterns."""
        for lang, patterns in self.COUNTER_STEREOTYPE_PATTERNS.items():
            self._counter_stereotype_patterns[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]

        for lang, patterns in self.DEROGATION_PATTERNS.items():
            self._derogation_patterns[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]

        self._sw_gendered_suffix_compiled = [
            (re.compile(p[0], re.IGNORECASE), p[1], p[2])
            for p in self.SW_GENDERED_SUFFIX_PATTERNS
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

    def _detect_sw_gendered_suffix(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect Swahili gendered occupation suffixes: 'wa kiume' / 'wa kike'.

        These appear on any occupation noun (daktari wa kike, profesa wa kiume,
        mbunge wa kike, etc.) and are the highest-volume recall gap in SW detection.
        Correction: remove the gender suffix, preserve the occupation term.
        """
        # Occupation nouns in Swahili follow m-wa noun class or are loanwords.
        # We require the preceding word to start with an occupation-class prefix
        # OR be an explicitly known occupation loanword.
        # This is an allowlist approach — only fire on words that look like occupations.
        OCCUPATION_PREFIXES = ('dakt', 'muuguzi', 'mhand', 'dereva', 'rubani', 'mwali',
                               'polisi', 'askari', 'waziri', 'rais', 'mgomba', 'msema',
                               'mwanas', 'mkuru', 'mhudumu', 'mkulima', 'mvuvi', 'mwimb',
                               'meneja', 'mhasi', 'mpishi', 'mfanya', 'wakili', 'profes',
                               'majaji', 'meya', 'mtend', 'mstaa', 'mzalis', 'mlezi',
                               'fundi', 'kocha', 'mshauri', 'mcheza', 'mwandishi',
                               'mchezaji', 'mbunifu', 'mwanasiasa', 'mbunge', 'gavana',
                               'seneta', 'karani', 'nahodha', 'ofisa', 'afisa',
                               'mkaguzi', 'msimamizi', 'mwenyekiti', 'mkurugenzi',
                               'mwanasheria', 'mwanauchumi', 'mwanahabari', 'mhusika')
        progress_ctx = re.compile(
            r'\b(wa\s+kwanza|haki\s+za|usawa\s+wa\s+kijinsia|uwezeshaji|kuhamasisha)\b',
            re.IGNORECASE
        )

        for compiled, suffix, target_gender in self._sw_gendered_suffix_compiled:
            m = compiled.search(text)
            if not m:
                continue

            # Suppress: progress/achievement reporting context
            if progress_ctx.search(text):
                continue

            preceding_noun = m.group(1).lower()

            # Suppress: pure digit strings (e.g. "100 wa kike")
            if preceding_noun.isdigit():
                continue

            # Only fire when preceding word looks like an occupation noun
            if not any(preceding_noun.startswith(p) for p in OCCUPATION_PREFIXES):
                continue

            # Build correction: remove the gender suffix span
            corrected = compiled.sub(lambda match: match.group(1), text).strip()
            corrected = re.sub(r'  +', ' ', corrected)

            cat = StereotypeCategory.FAMILY_ROLE if preceding_noun in {'mzazi', 'mlezi'} \
                else StereotypeCategory.PROFESSION

            return {
                'from': m.group(0),
                'to': m.group(1),
                'suffix': suffix,
                'corrected_text': corrected,
                'target_gender': target_gender,
                'stereotype_category': cat,
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

            # Swahili gendered-suffix pattern: "[occupation] wa kiume/wa kike"
            # Fires on any occupation — covers the 1,847-sentence recall gap
            if language == Language.SWAHILI:
                sw_suffix = self._detect_sw_gendered_suffix(text)
                if sw_suffix:
                    return BiasDetectionResult(
                        text=text,
                        has_bias_detected=True,
                        detected_edits=[{
                            'from': sw_suffix['from'],
                            'to': sw_suffix['to'],
                            'severity': 'replace',
                            'bias_type': 'stereotype',
                            'stereotype_category': sw_suffix['stereotype_category'].value
                            if hasattr(sw_suffix['stereotype_category'], 'value')
                            else str(sw_suffix['stereotype_category']),
                            'reason': f"Unnecessary gender marker '{sw_suffix['suffix']}' on occupation — "
                                      f"use the neutral occupation term instead.",
                        }],
                        bias_label=BiasLabel.STEREOTYPE,
                        stereotype_category=sw_suffix['stereotype_category'],
                        target_gender=sw_suffix['target_gender'],
                        explicitness=Explicitness.EXPLICIT,
                        confidence=0.95,
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

            # replace_edits: confirmed bias — set has_bias_detected=True, trigger correction
            # warn_edits: informational flags (severity=warn) — never set has_bias_detected
            replace_edits = []
            warn_edits = []
            detected_categories = []
            detected_genders = []
            skipped_edits = []  # Track edits skipped due to context

            for rule, pattern in zip(rules, patterns):
                if pattern.search(text):
                    # Skip if biased == neutral (already gender-neutral term)
                    if rule['biased'] == rule['neutral_primary']:
                        continue

                    biased_term = rule['biased']
                    severity = rule.get('severity', 'replace')
                    avoid_when = rule.get('avoid_when', '')
                    constraints = rule.get('constraints', '')

                    # Context-aware check: should we apply this correction?
                    if self.context_checker and (avoid_when or constraints):
                        context_result = self.context_checker.check_context(
                            text=text,
                            biased_term=biased_term,
                            avoid_when=avoid_when,
                            constraints=constraints
                        )

                        if not context_result.should_correct:
                            # Skip this edit - context indicates preservation needed
                            skipped_edits.append({
                                'term': biased_term,
                                'reason': context_result.reason,
                                'blocked_by': context_result.blocked_by.value if context_result.blocked_by else None,
                                'confidence': context_result.confidence
                            })
                            logger.debug(
                                "Skipped correction for '%s': %s",
                                biased_term, context_result.reason
                            )
                            continue

                    edit = {
                        'from': rule['biased'],
                        'to': rule['neutral_primary'],
                        'severity': severity,
                        'bias_type': rule.get('bias_label', 'stereotype'),
                        'stereotype_category': rule.get('stereotype_category', 'profession')
                    }

                    # Add ngeli metadata for Swahili
                    if language == Language.SWAHILI and self.ngeli_tracker:
                        ngeli = rule.get('ngeli', '')
                        if ngeli:
                            edit['ngeli'] = ngeli
                            self.ngeli_tracker.track_noun(rule['biased'])

                    # Route by severity: warn entries are informational only
                    if severity == 'warn':
                        warn_edits.append(edit)
                    else:
                        replace_edits.append(edit)
                        # Only track categories for confirmed-bias (replace) edits
                        cat = rule.get('stereotype_category', 'profession')
                        if cat:
                            detected_categories.append(cat)

            # Determine primary stereotype category from replace edits only
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

            # has_bias is True only when replace-severity edits are present.
            # warn_edits surface separately and never drive has_bias_detected.
            has_bias = len(replace_edits) > 0
            result = BiasDetectionResult(
                text=text,
                has_bias_detected=has_bias,
                detected_edits=replace_edits,
                warn_edits=warn_edits,
                bias_label=BiasLabel.STEREOTYPE if has_bias else BiasLabel.NEUTRAL,
                stereotype_category=primary_category,
                target_gender=None,  # Would need deeper NLP for gender inference
                explicitness=Explicitness.EXPLICIT if has_bias else None,
                confidence=0.85 if has_bias else 0.7
            )

            # Attach ngeli analysis as metadata
            if ngeli_analysis:
                result._ngeli_analysis = ngeli_analysis

            # Attach context-skipped edits for transparency
            if skipped_edits:
                result._skipped_edits = skipped_edits

            # Stage 2 — ML classifier fallback
            # Only runs when rules found nothing (has_bias=False, no warn_edits).
            # Produces warn-severity edits only — never replace. Precision preserved.
            if not has_bias and not warn_edits and self.enable_ml_fallback:
                try:
                    from .ml_classifier import classify as ml_classify
                    ml_score = ml_classify(text, language)
                    if ml_score >= self._ml_threshold:
                        ml_edit = {
                            "from": "",
                            "to": "",
                            "severity": "warn",
                            "reason": f"ML: possible gender bias detected (confidence {ml_score:.0%}) — review recommended",
                            "source": "ml",
                            "confidence": ml_score,
                        }
                        result.warn_edits = [ml_edit]
                        result.confidence = ml_score
                except Exception:
                    pass  # ML unavailable — rules result stands

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