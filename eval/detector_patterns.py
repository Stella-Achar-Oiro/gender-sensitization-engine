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
        (r'\bbaba\b.{0,30}\b(analelea|analinda|anatunza|anasimamia)\s+watoto\s+peke\s+yake\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\bmama\b.+\b(anafanya\s+kazi\s+ofisi|ni\s+mkurugenzi|anaongoza)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\bmwanamke\b.+\b(mhandisi|rubani|fundi\s+wa\s+magari)',
         StereotypeCategory.PROFESSION, TargetGender.FEMALE),
        (r'\bmwanamume\b.+\b(muuguzi|mkunga|mlezi\s+wa\s+watoto)',
         StereotypeCategory.PROFESSION, TargetGender.MALE),
        # Girl in leadership role — challenge to norms
        (r'\bmsichana\b.{0,30}\b(ni\s+rais|ni\s+mkurugenzi|ni\s+kiongozi|anaongoza|ameongoza|amechaguliwa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Mwanamke in technical leadership
        (r'\bmwanamke\b.{0,30}\b(anaongoza\s+mradi|mkurugenzi\s+mkuu|rubani\s+mkuu|nahodha)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
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
        # Capability stereotypes
        (r'\bwanawake\b.{0,40}\b(hawafai|hawawezi|hawapaswi|si wazuri|si hodari|hana uwezo|hawana uwezo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bwanaume\b.{0,40}\b(hawafai|hawawezi|hawapaswi|si wazuri|hawana uwezo)\b.{0,30}\b(huduma|watoto|nyumba|familia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\bmsichana\b.{0,40}\b(hakuwepo|alitoroka|hakufika|alishindwa|hakuweza)\b.{0,30}\b(shule|darasa|mtihani|elimu)\b',
         StereotypeCategory.EDUCATION, TargetGender.FEMALE),
        # Appearance / body stereotypes
        (r'\b(mwanamke|msichana|mke)\b.{0,50}\b(mzuri|mrembo|mrefu|mfupi|nzuri|mvuto|mwili).{0,30}\b(lazima|anapaswa|sharti|inahitajika)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b.{0,30}\b(si mzuri|si mrembo|hana mvuto|mbaya|hana kitu)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Personality / emotion stereotypes
        (r'\bwanawake\b.{0,40}\b(wanaelewa|wanafikiri|wanajua|wanaweza).{0,20}\b(kidogo|tu|chini|zaidi ya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(wanaume|mwanaume)\b.{0,30}\b(hawalia|hawaonyeshi|usihisi|hisia|kilio)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # Domestic role prescription
        (r'\b(mwanamke|mke|mama)\b.{0,50}\b(anapaswa|lazima|sharti|inabidi)\b.{0,40}\b(kupika|kusafisha|kutunza|kubaki nyumbani|nyumbani)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\bsisi\s+wanaume\b.{0,60}\b(tunaongoza|tunalazimisha|tunaamua|tunapaswa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # Implicit surprise bias — 'hata' (even) before women encodes exceptionalism
        (r'\bhata\s+(wanawake|mwanamke|msichana)\b.{0,40}\b(wanaweza|anaweza|wanajeshi|kiongozi|daktari|mhandisi|rubani)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Comparative derogation — gender-qualifying achievement sets lower baseline
        (r'\balifanya\s+kazi\s+nzuri\s+kwa\s+(mwanamke|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bkwa\s+(mwanamke|msichana)\b.{0,20}\b(alifanya|alifanikiwa|alishinda|alimfaulu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Passive child-marriage — erases girl's agency
        (r'\b(aliozeshwa|alipozeshwa|waliozeshwa)\b.{0,30}\b(akiwa\s+na\s+miaka|mdogo|mchanga|kabla)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Religious prescriptive submission framing
        (r'\b(lazima|sharti|inabidi)\b.{0,20}\bamtii\s+mume\b.{0,30}\b(dini|mungu|biblia|quran|kanisa|msikiti)\b',
         StereotypeCategory.RELIGION_CULTURE, TargetGender.FEMALE),
        # Intersectional: rural women framed as uneducated
        (r'\bwanawake\s+wa\s+vijijini\b.{0,50}\b(hawana|hawajui|hawajasomea|hawana\s+elimu|hawajapata)\b',
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
    'dakt', 'muuguzi', 'mhand', 'dereva', 'rubani',
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
    # Health / service
    'muuguzi', 'wauguzi', 'daktari', 'madaktari',
    'mkunga', 'wakunga', 'mhudumu', 'wahudumu',
    'mwalimu', 'walimu', 'mkurugenzi', 'wakurugenzi',
    # Judicial / security
    'jaji', 'majaji', 'hakimu', 'mahakimu',
    'mwanasheria', 'wanasheria', 'mlinzi', 'walinzi',
    # Business / finance
    'mfanyabiashara', 'wafanyabiashara', 'mwekezaji', 'wawekezaji',
    'mhasibu', 'wahasibu',
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

# Suppressor for derogation patterns: biased language used rhetorically to CHALLENGE the bias
# e.g. "haileti maana kufikiri kuwa mwanamke hawezi..." (counter-stereotype framing)
SW_DEROGATION_COUNTER_SUPPRESSOR = re.compile(
    r'\b('
    r'haileti\s+maana\s+kufikiri\s+kuwa'   # "it doesn't make sense to think that"
    r'|siamini\s+(kuwa|kwamba)'             # "I don't believe that"
    r'|si\s+kweli\s+(kuwa|kwamba)'          # "it's not true that"
    r'|si\s+sahihi\s+(kuwa|kwamba)'         # "it's not correct that"
    r'|kupinga\s+dhana'                     # "opposing the notion"
    r'|tunapinga'                           # "we oppose"
    r'|hatukubaliani'                       # "we disagree"
    r'|hii\s+ni\s+dhuluma'                 # "this is oppression"
    r'|ni\s+udhalimu'                       # "this is injustice"
    r'|ni\s+ubaguzi'                        # "this is discrimination"
    r'|lazima\s+(tubadilishe|tuzuie|tuondoe)'  # "we must change/stop/remove this"
    r')',
    re.IGNORECASE,
)

SW_PROGRESS_CONTEXT = re.compile(
    r'\b('
    # Advocacy / rights / empowerment
    r'wa\s+kwanza|haki\s+za|usawa\s+wa\s+kijinsia|uwezeshaji|kuhamasisha'
    r'|haki\s+za\s+(mtoto|wanawake|binadamu)'
    r'|ulinzi\s+wa|sheria\s+(ya|inayolinda)|ajenda\s+ya'
    # Factual reporting verbs — "[occ] wa kike/kiume [verb]" = news report, not prescriptive
    r'|wameshinda|wamepiga|wameweza|wamefanikiwa|wamepewa|wamechaguliwa|wamejiunga'
    r'|wameimba|wamecheza|wamefanya|wameweka|wamewasili|wamejitokeza|wamekusanyika'
    r'|ameimba|amecheza|amefanikiwa|ameshinda|amepewa|amechaguliwa|ameweza'
    r'|wanafanya\s+kazi|wanaohusika|wanaohudumu|wanaoshiriki|wanaoimba|wanacheza'
    # Celebration/media reporting context
    r'|siku\s+ya\s+wanawake|maadhimisho|sherehe|tamasha|tuzo|zawadi'
    r'|ushindi|mafanikio|mchango|jitihada|nguvu\s+za'
    r')',
    re.IGNORECASE,
)



# Prescriptive-verb gate for mtoto/watoto wa kike/kiume.
# These phrases are neutral when used as factual gender references.
# Only flag as bias when a normative/prescriptive verb appears in context.
SW_CHILD_PRESCRIPTIVE = re.compile(
    r'\b(mtoto|watoto)\s+wa\s+(kike|kiume)\b.{0,120}'
    r'\b(anapaswa|wanapaswa|lazima|sharti|inabidi|inahitajika|inamaanisha|'
    r'apaswe|wapaswe|anatakiwa|wanatakiwa|anastahili|wanastahili|'
    r'kukaa\s+nyumbani|kubaki\s+nyumbani|kupika|kusafisha|kutunza\s+nyumba|'
    r'kuolewa|aolewe|hapaswi\s+kusoma|hana\s+haja\s+ya\s+elimu|'
    r'si\s+lazima\s+asomi|asifanye\s+kazi|akae\s+nyumbani)\b',
    re.IGNORECASE | re.DOTALL,
)

# Neutral contexts where mtoto/watoto wa kike/kiume is clearly a possessive biographical reference
# (e.g. "mtoto wake wa kike" = her daughter, not a prescriptive statement)
SW_CHILD_NEUTRAL_CONTEXT = re.compile(
    r'\b(mtoto|watoto)\s+(wake|wao|wangu|wenu)\s+wa\s+(kike|kiume)\b',
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
        # Suppress when biased language is used rhetorically to challenge the bias
        if language == Language.SWAHILI and SW_DEROGATION_COUNTER_SUPPRESSOR.search(text):
            return None
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

    def should_suppress_child_gender_term(self, text: str, biased_term: str) -> bool:
        """
        For mtoto/watoto wa kike/kiume lexicon entries: suppress only when
        clearly a biographical possessive or birth announcement (not prescriptive).
        Returns True if the match should be suppressed (not flagged as bias).
        """
        lower_term = biased_term.lower()
        if not any(x in lower_term for x in ('mtoto wa kike', 'mtoto wa kiume',
                                               'watoto wa kike', 'watoto wa kiume')):
            return False
        # Only suppress clear biographical/birth contexts
        return bool(SW_CHILD_NEUTRAL_CONTEXT.search(text))
