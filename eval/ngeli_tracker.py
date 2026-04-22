"""
Swahili noun class (ngeli) tracking module.

This module provides utilities for tracking and analyzing Swahili noun classes,
which is crucial for understanding agreement patterns and gender marking in Swahili.

Swahili has 18 noun classes organized into pairs:
- 1/2 (m-wa): People, animate beings (mtu/watu)
- 3/4 (m-mi): Plants, body parts (mti/miti)
- 5/6 (ji-ma): Fruits, paired items (jiwe/mawe)
- 7/8 (ki-vi): Things, diminutives (kitu/vitu)
- 9/10 (n-n): Animals, loanwords (ndege/ndege)
- 11/10 (u-n): Abstract nouns (ukuta/kuta)
- 15 (ku-): Infinitives (kukimbia)
- 16/17/18 (pa-ku-mu): Locatives (mahali)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class NounClass(Enum):
    """Swahili noun classes (ngeli)"""
    M_WA = "1/2"  # People, animate (mwalimu/walimu)
    M_MI = "3/4"  # Plants, natural objects (mti/miti)
    JI_MA = "5/6"  # Fruits, paired items (jiwe/mawe)
    KI_VI = "7/8"  # Things, diminutives (kitu/vitu)
    N_N = "9/10"   # Animals, loanwords (ndege/ndege)
    U_N = "11/10"  # Abstract nouns (ukuta/kuta)
    KU = "15"      # Infinitives (kukimbia)
    PA = "16"      # Locative (specific place)
    KU_LOC = "17"  # Locative (general)
    MU_LOC = "18"  # Locative (inside)
    MA = "6"       # Plural only (maji - water)


@dataclass
class NounClassInfo:
    """Information about a noun's class"""
    noun_class: NounClass
    number: str  # sg, pl, or both
    prefix_singular: str
    prefix_plural: str
    agreement_pattern: str
    examples: List[str]


class NgeliTracker:
    """
    Tracks Swahili noun classes and agreement patterns.

    This class provides utilities for:
    - Identifying noun class from prefix
    - Tracking subject-verb agreement
    - Detecting possessive pronoun agreement
    - Analyzing gender marking patterns
    """

    # Noun class patterns
    NOUN_CLASS_PATTERNS = {
        NounClass.M_WA: NounClassInfo(
            noun_class=NounClass.M_WA,
            number="sg/pl",
            prefix_singular="m-, mw-, mu-",
            prefix_plural="wa-, w-",
            agreement_pattern="a-/wa- (subject), -ake/-ao (possessive)",
            examples=["mwalimu/walimu", "mtu/watu", "mkulima/wakulima"]
        ),
        NounClass.M_MI: NounClassInfo(
            noun_class=NounClass.M_MI,
            number="sg/pl",
            prefix_singular="m-, mw-",
            prefix_plural="mi-",
            agreement_pattern="u-/i- (subject), -ake/-ao (possessive)",
            examples=["mti/miti", "mkono/mikono"]
        ),
        NounClass.JI_MA: NounClassInfo(
            noun_class=NounClass.JI_MA,
            number="sg/pl",
            prefix_singular="ji-, j-, ø-",
            prefix_plural="ma-",
            agreement_pattern="li-/ya- (subject), -ake/-ao (possessive)",
            examples=["jiwe/mawe", "gari/magari"]
        ),
        NounClass.KI_VI: NounClassInfo(
            noun_class=NounClass.KI_VI,
            number="sg/pl",
            prefix_singular="ki-, ch-",
            prefix_plural="vi-, vy-",
            agreement_pattern="ki-/vi- (subject), -ake/-ao (possessive)",
            examples=["kitu/vitu", "kitabu/vitabu"]
        ),
        NounClass.N_N: NounClassInfo(
            noun_class=NounClass.N_N,
            number="sg/pl",
            prefix_singular="n-, ny-, m-, ø-",
            prefix_plural="n-, ny-, m-, ø-",
            agreement_pattern="i-/zi- (subject), -ake/-ao (possessive)",
            examples=["ndege/ndege", "nyumba/nyumba"]
        ),
        NounClass.MA: NounClassInfo(
            noun_class=NounClass.MA,
            number="pl",
            prefix_singular="",
            prefix_plural="ma-",
            agreement_pattern="ya- (subject), -ao (possessive)",
            examples=["maji (water)", "maziwa (milk)"]
        ),
    }

    # M-wa class prefixes (people/occupations - most relevant for gender bias)
    M_WA_PREFIXES = {
        'singular': ['m', 'mw', 'mu'],
        'plural': ['wa', 'w']
    }

    # Possessive pronoun patterns by class
    POSSESSIVE_PATTERNS = {
        NounClass.M_WA: {
            'singular': ['wake', 'wako', 'wangu', 'wetu', 'wenu', 'wao'],
            'plural': ['wao', 'wako', 'wangu', 'wetu', 'wenu', 'wao']
        },
        # Add other classes as needed
    }

    def __init__(self):
        """Initialize ngeli tracker"""
        self.tracked_nouns: Dict[str, NounClass] = {}

    def identify_class(self, noun: str) -> Optional[NounClass]:
        """
        Identify noun class from prefix.

        Args:
            noun: Swahili noun to analyze

        Returns:
            NounClass if identifiable, None otherwise
        """
        noun_lower = noun.lower().strip()

        # M-wa class (people) - most important for bias detection
        if any(noun_lower.startswith(prefix) for prefix in ['mw', 'mu', 'm']):
            # Check if it's likely a person noun (occupation, role)
            # This heuristic can be improved with corpus analysis
            if any(marker in noun_lower for marker in ['limu', 'kulima', 'andishi', 'fanya']):
                return NounClass.M_WA

        # Wa- prefix indicates plural m-wa class
        if any(noun_lower.startswith(prefix) for prefix in ['wa', 'w']):
            return NounClass.M_WA

        # Ma- prefix (class 6 plural or class 5/6)
        if noun_lower.startswith('ma'):
            return NounClass.JI_MA

        # Ki-/Vi- prefix (class 7/8)
        if noun_lower.startswith('ki') or noun_lower.startswith('ch'):
            return NounClass.KI_VI
        if noun_lower.startswith('vi') or noun_lower.startswith('vy'):
            return NounClass.KI_VI

        # N- prefix (class 9/10)
        if noun_lower.startswith('n') or noun_lower.startswith('ny'):
            return NounClass.N_N

        return None

    def is_m_wa_class(self, noun: str) -> bool:
        """
        Check if noun belongs to m-wa class (people).

        This is the most important class for gender bias detection
        as it includes all occupation and role nouns.

        Args:
            noun: Swahili noun to check

        Returns:
            True if noun is in m-wa class
        """
        noun_class = self.identify_class(noun)
        return noun_class == NounClass.M_WA

    def get_expected_agreement(self, noun: str, number: str = "sg") -> Optional[str]:
        """
        Get expected subject agreement prefix for a noun.

        Args:
            noun: Swahili noun
            number: 'sg' or 'pl'

        Returns:
            Expected agreement prefix (e.g., 'a-' for m-wa singular)
        """
        noun_class = self.identify_class(noun)

        if noun_class == NounClass.M_WA:
            return 'a-' if number == 'sg' else 'wa-'
        elif noun_class == NounClass.M_MI:
            return 'u-' if number == 'sg' else 'i-'
        elif noun_class == NounClass.JI_MA:
            return 'li-' if number == 'sg' else 'ya-'
        elif noun_class == NounClass.KI_VI:
            return 'ki-' if number == 'sg' else 'vi-'
        elif noun_class == NounClass.N_N:
            return 'i-' if number == 'sg' else 'zi-'

        return None

    def track_noun(self, noun: str, noun_class: Optional[NounClass] = None):
        """
        Track a noun and its class.

        Args:
            noun: Swahili noun to track
            noun_class: Optional explicit class (auto-detected if not provided)
        """
        if noun_class is None:
            noun_class = self.identify_class(noun)

        if noun_class:
            self.tracked_nouns[noun] = noun_class

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics on tracked nouns by class.

        Returns:
            Dictionary mapping class names to counts
        """
        stats = {}
        for noun_class in self.tracked_nouns.values():
            class_name = noun_class.value
            stats[class_name] = stats.get(class_name, 0) + 1

        return stats

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analyze text for noun class patterns.

        Args:
            text: Swahili text to analyze

        Returns:
            Dictionary with analysis results
        """
        words = text.split()
        m_wa_nouns = []
        other_nouns = []

        for word in words:
            # Remove punctuation
            word_clean = word.strip('.,!?;:')
            if len(word_clean) < 3:
                continue

            noun_class = self.identify_class(word_clean)
            if noun_class == NounClass.M_WA:
                m_wa_nouns.append(word_clean)
            elif noun_class:
                other_nouns.append((word_clean, noun_class.value))

        return {
            'm_wa_nouns': m_wa_nouns,
            'm_wa_count': len(m_wa_nouns),
            'other_nouns': other_nouns,
            'total_nouns': len(m_wa_nouns) + len(other_nouns)
        }


def get_noun_class_info(noun_class: NounClass) -> NounClassInfo:
    """
    Get detailed information about a noun class.

    Args:
        noun_class: NounClass enum value

    Returns:
        NounClassInfo with patterns and examples
    """
    tracker = NgeliTracker()
    return tracker.NOUN_CLASS_PATTERNS.get(noun_class)
