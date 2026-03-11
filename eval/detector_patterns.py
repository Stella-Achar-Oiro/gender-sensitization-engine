"""
Pattern configuration and matchers for bias detection.

Holds all regex-based pattern data (counter-stereotype, derogation, Swahili
gendered-suffix) and compiled matchers. Used by BiasDetector so pattern config
is separate from lexicon matching and result building.
"""
import re
from typing import Dict, List, Any, Optional

from .models import Language, StereotypeCategory, TargetGender


# Counter-stereotype patterns by language (role reversals / challenges to norms)
COUNTER_STEREOTYPE_PATTERNS: Dict[Language, List[tuple]] = {
    Language.ENGLISH: [
        (r'\b(father|dad|husband)\b.*(caregiver|nurtur|cook|clean|homemaker|stay.at.home)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\b(mother|mom|wife)\b.*(breadwinner|provider|work.*(full.time|office)|career)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(female|woman|she)\b.*(engineer|mechanic|pilot|ceo|surgeon|firefighter)',
         StereotypeCategory.PROFESSION, TargetGender.FEMALE),
        (r'\b(male|man|he)\b.*(nurse|secretary|receptionist|kindergarten|nanny)',
         StereotypeCategory.PROFESSION, TargetGender.MALE),
        (r'\b(she|her|woman|female)\b.*(lead|command|chief|director|president|boss)',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
    ],
    Language.SWAHILI: [
        (r'\bbaba\b.+\b(anale[zl]a|anapika|anasafisha|anakaa\s+nyumbani)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\bmama\b.+\b(anafanya\s+kazi\s+ofisi|ni\s+mkurugenzi|anaongoza)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\bmwanamke\b.+\b(mhandisi|rubani|fundi\s+wa\s+magari)',
         StereotypeCategory.PROFESSION, TargetGender.FEMALE),
        (r'\bmwanamume\b.+\b(muuguzi|mkunga|mlezi\s+wa\s+watoto)',
         StereotypeCategory.PROFESSION, TargetGender.MALE),
    ],
}

# Derogation patterns - language that demeans or disparages
DEROGATION_PATTERNS: Dict[Language, List[tuple]] = {
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
        (r'\bni\s+tu\s+(mwanamke|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b\s+hawezi\b(?!\s+(?:kuzaa|kukoma|kupenda|kunifikia|kufikia|kukufikia|bila\s+kuwezeshwa))',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(kama\s+msichana|kama\s+mwanamke)\b.{0,30}\b(dhaifu|hawezi|haiwezi|hana nguvu|anapiga|analia)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
    ],
}

# Swahili gendered-suffix: "[occupation] wa kiume/wa kike" on any occupation
SW_GENDERED_SUFFIX_PATTERNS: List[tuple] = [
    (r'\b(\w+)\s+(wa\s+kiume)\b', 'wa kiume', TargetGender.MALE),
    (r'\b(\w+)\s+(wa\s+kike)\b', 'wa kike', TargetGender.FEMALE),
]

# Allowlist for preceding noun in SW suffix — only fire on occupation-like words
SW_OCCUPATION_PREFIXES = (
    'dakt', 'muuguzi', 'mhand', 'dereva', 'rubani', 'mwali',
    'polisi', 'askari', 'waziri', 'rais', 'mgomba', 'msema',
    'mwanas', 'mkuru', 'mhudumu', 'mkulima', 'mvuvi', 'mwimb',
    'meneja', 'mhasi', 'mpishi', 'mfanya', 'wakili', 'profes',
    'majaji', 'meya', 'mtend', 'mstaa', 'mzalis', 'mlezi',
    'fundi', 'kocha', 'mshauri', 'mcheza', 'mwandishi',
    'mchezaji', 'mbunifu', 'mwanasiasa', 'mbunge', 'gavana',
    'seneta', 'karani', 'nahodha', 'ofisa', 'afisa',
    'mkaguzi', 'msimamizi', 'mwenyekiti', 'mkurugenzi',
    'mwanasheria', 'mwanauchumi', 'mwanahabari', 'mhusika',
    'kiongozi', 'viongozi', 'denti', 'madent',
    'mgombea', 'wagombea', 'muwakilishi', 'wawakilishi',
    'mwakilishi', 'mwanamichezo', 'wanamichezo',
    'rapa', 'mwanaharakati', 'wanaharakati',
    'wasomi', 'mwanajeshi', 'wanajeshi',
    'mwanachama', 'wanachama', 'maskauti',
    'mwamuzi', 'wamuzi', 'mwangalizi',
    'muigizaji', 'waigizaji', 'mwanasanaa',
    'mfanyakazi', 'wafanyakazi', 'mtaalamu', 'wataalamu',
    'naibu', 'manaibu', 'kamanda', 'makomanda',
    'jenerali', 'majenerali', 'kanali', 'brigadie',
    'spika', 'waziri mkuu', 'makamu',
)

SW_NON_OCCUPATION_WORDS = frozenset({
    'wake', 'yake', 'zake', 'lake', 'chake', 'pake',
    'wao', 'yao', 'zao', 'lao', 'chao', 'pao',
    'wetu', 'yetu', 'zetu', 'letu', 'chetu',
    'wenu', 'yenu', 'zenu', 'lenu',
    'huyo', 'hao', 'hawa', 'hizi', 'hilo', 'hayo',
    'mmoja', 'wawili', 'watatu', 'wengi', 'wote', 'wengine',
    'pekee', 'bora', 'mwingine', 'hasa', 'zaidi', 'sana', 'tu', 'pia',
    'mzee', 'mdogo', 'mkubwa', 'mpya', 'mwisho',
    'mwana', 'mtoto', 'watoto', 'vijana', 'kijana',
    'mtu', 'watu', 'binadamu', 'rafiki', 'ndugu',
    'mwananchi', 'wananchi', 'raia', 'shahidi', 'mshtakiwa',
})

SW_PROGRESS_CONTEXT = re.compile(
    r'\b(wa\s+kwanza|haki\s+za|usawa\s+wa\s+kijinsia|uwezeshaji|kuhamasisha)\b',
    re.IGNORECASE,
)


class DetectorPatterns:
    """
    Holds compiled pattern config and exposes detect_* methods for
    derogation, counter-stereotype, and Swahili gendered-suffix.
    """

    def __init__(self) -> None:
        self._counter: Dict[Language, List[tuple]] = {}
        self._derogation: Dict[Language, List[tuple]] = {}
        self._sw_suffix: List[tuple] = []
        self._compile()

    def _compile(self) -> None:
        for lang, patterns in COUNTER_STEREOTYPE_PATTERNS.items():
            self._counter[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]
        for lang, patterns in DEROGATION_PATTERNS.items():
            self._derogation[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]
        self._sw_suffix = [
            (re.compile(p[0], re.IGNORECASE), p[1], p[2])
            for p in SW_GENDERED_SUFFIX_PATTERNS
        ]

    def detect_derogation(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """Detect derogatory language. Returns match dict or None."""
        for pattern, category, gender in self._derogation.get(language, []):
            if pattern.search(text):
                return {
                    'bias_label': 'derogation',
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': 'explicit',
                    'matched_pattern': pattern.pattern,
                }
        return None

    def detect_counter_stereotype(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """Detect counter-stereotype (preserve, do not correct). Returns match dict or None."""
        for pattern, category, gender in self._counter.get(language, []):
            if pattern.search(text):
                return {
                    'bias_label': 'counter-stereotype',
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': 'explicit',
                    'matched_pattern': pattern.pattern,
                }
        return None

    def detect_sw_gendered_suffix(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect Swahili '[occupation] wa kiume/wa kike'. Returns match dict or None."""
        for compiled, suffix, target_gender in self._sw_suffix:
            m = compiled.search(text)
            if not m:
                continue
            if SW_PROGRESS_CONTEXT.search(text):
                continue
            preceding_noun = m.group(1).lower()
            if preceding_noun.isdigit():
                continue
            if preceding_noun in SW_NON_OCCUPATION_WORDS:
                continue
            if not any(preceding_noun.startswith(p) for p in SW_OCCUPATION_PREFIXES):
                continue
            corrected = compiled.sub(lambda match: match.group(1), text).strip()
            corrected = re.sub(r'  +', ' ', corrected)
            cat = StereotypeCategory.FAMILY_ROLE if preceding_noun in {'mzazi', 'mlezi'} else StereotypeCategory.PROFESSION
            return {
                'from': m.group(0),
                'to': m.group(1),
                'suffix': suffix,
                'corrected_text': corrected,
                'target_gender': target_gender,
                'stereotype_category': cat,
            }
        return None
