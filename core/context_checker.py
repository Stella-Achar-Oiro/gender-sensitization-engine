"""
Context-Aware Correction Checker for Gender Bias Detection.

Shared by api and eval. Conditions: quote, historical, proper_noun, biographical,
statistical, medical, counter_stereotype, legal, artistic, organization.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Swahili inanimate nouns whose possessives (yake/wake/zake/lake/chake) are
# NOT human-referent and must not trigger gender-bias possessive rules.
SW_INANIMATE_NOUNS: frozenset = frozenset({
    # Places / infrastructure
    'nyumba', 'ofisi', 'shule', 'duka', 'hospitali', 'kanisa', 'msikiti',
    'barabara', 'daraja', 'mlango', 'dirisha', 'chumba', 'jiko', 'paa',
    # Objects / documents
    'kadi', 'kitabu', 'barua', 'mkoba', 'mfuko', 'gari', 'ndege', 'basi',
    'simu', 'kompyuta', 'fedha', 'pesa', 'akaunti', 'hati', 'cheti',
    'risiti', 'ankara', 'stakabadhi', 'pasipoti', 'leseni',
    # Abstract / processes
    'kazi', 'elimu', 'afya', 'matibabu', 'biashara', 'mradi', 'mpango',
    'tatizo', 'suluhisho', 'maamuzi', 'hatua', 'matokeo', 'faida',
    'hasara', 'thamani', 'bei', 'gharama', 'mishahara', 'mapato',
    # Nature / food
    'mto', 'mlima', 'bahari', 'bonde', 'msitu', 'chakula', 'maji',
    'ardhi', 'shamba',
    # Organisations (not human)
    'shirika', 'kampuni', 'taasisi', 'chama', 'wizara', 'serikali',
    'benki', 'chuo',
    # Time
    'mwaka', 'mwezi', 'wiki', 'siku', 'saa', 'dakika',
})

# Human occupation nouns: possessives on these CAN indicate gender assumption
SW_HUMAN_OCCUPATION_NOUNS: frozenset = frozenset({
    'daktari', 'muuguzi', 'mwalimu', 'rubani', 'dereva', 'mhandisi',
    'wakili', 'mbunge', 'waziri', 'rais', 'mkurugenzi', 'meneja',
    'kocha', 'mwanasiasa', 'fundi', 'mpishi', 'mkulima', 'mvuvi',
    'mhasibu', 'mwandishi', 'mshauri', 'mchezaji', 'hakimu', 'jaji',
    'askari', 'polisi', 'afisa', 'ofisa', 'profesa', 'msomi',
})

# Title nouns: "Rais Magufuli" at sentence start is biographical; "kauli ya Rais John …"
# embeds the title after an attributive particle — bias may be in the quote, not the name line.
_SW_TITLE_AFTER_PARTICLE: frozenset = frozenset({
    'rais', 'waziri', 'mbunge', 'spika', 'balozi', 'jaji', 'hakimu',
})

_SW_POSSESSIVE_RE = re.compile(
    r'\b(\w+)\s+(?:yake|wake|zake|lake|chake)\b', re.IGNORECASE
)


def sw_possessive_has_human_referent(text: str) -> bool:
    """
    Return True only when a Swahili possessive (yake/wake/zake/lake/chake)
    is preceded by a known human-occupation noun.
    Used to suppress inanimate-noun false positives.
    """
    for m in _SW_POSSESSIVE_RE.finditer(text):
        noun = m.group(1).lower()
        if noun in SW_HUMAN_OCCUPATION_NOUNS:
            return True
    return False


def _sw_title_noun_embedded_after_particle(text: str, term_start: int) -> bool:
    """True when a title noun (e.g. rais) is immediately preceded by ya/wa/kwa/…."""
    if term_start <= 0:
        return False
    before = text[:term_start].rstrip()
    return bool(
        re.search(r"\b(ya|wa|kwa|cha|la|pa|na|za)\s+$", before, re.IGNORECASE)
    )


def sw_possessive_is_inanimate(text: str, possessive: str) -> bool:
    """
    Return True when the closest preceding noun before `possessive` is
    a known inanimate noun — meaning the possessive is NOT a gender marker.
    """
    pattern = re.compile(
        r'\b(\w+)\s+' + re.escape(possessive) + r'\b', re.IGNORECASE
    )
    for m in pattern.finditer(text):
        noun = m.group(1).lower()
        if noun in SW_INANIMATE_NOUNS:
            return True
        if noun in SW_HUMAN_OCCUPATION_NOUNS:
            return False
    return False


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
    """Checks text context to determine if bias correction should be applied."""

    CONTEXT_PATTERNS: Dict[ContextCondition, List[str]] = {
        ContextCondition.QUOTE: [
            r'"[^"]{{0,100}}{term}[^"]{{0,100}}"',
            r"'[^']{{0,100}}{term}[^']{{0,100}}'",
            r'«[^»]{{0,100}}{term}[^»]{{0,100}}»',
            r'„[^"]{{0,100}}{term}[^"]{{0,100}}"',
            r'\"[^\"]{{0,100}}{term}[^\"]{{0,100}}\"',
            r'\b(alisema|anasema|walisema|said|says|stated|wrote|claimed)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(alisema|anasema|said|says)\b',
        ],
        ContextCondition.HISTORICAL: [
            r'\b(mwaka\s+)?\d{{4}}\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(mwaka\s+)?\d{{4}}\b',
            r'\bin\s+\d{{4}}\b.{{0,30}}{term}',
            r'\b(kihistoria|historia|zamani|kale|enzi)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(kihistoria|historia|zamani)\b',
            r'\b(historically|history|ancient|traditional|formerly)\b.{{0,50}}{term}',
            r'\b(ilikuwa|walikuwa|alikuwa|was|were|used\s+to)\b.{{0,30}}{term}',
        ],
        ContextCondition.PROPER_NOUN: [
            r'(?<=[.!?]\s{{1,5}}|\A)(?![A-Z])\b{term}\s+[A-Z][a-z]+',
            r'(?<=[a-z])\s+{term}\s+[A-Z][a-z]+',
            r'\b[Mm]ama\s+[A-Z][a-z]{{2,}}',
            r'\b[Bb]aba\s+[A-Z][a-z]{{2,}}',
            r'(?<=[a-z.,;:]\s)[A-Z][a-z]+\s+{term}',
            r'\b(Chama\s+cha|Shirika\s+la|Taasisi\s+ya|Kampuni\s+ya)\b.{{0,30}}{term}',
            r'\b(Organization|Company|Association|Foundation|Institute)\s+.{{0,20}}{term}',
            r'{term}.{{0,20}}\b(Inc|Ltd|LLC|Corp|Foundation)\b',
            r'\b(Mheshimiwa|Dkt\.|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+.{{0,20}}{term}',
        ],
        ContextCondition.BIOGRAPHICAL: [
            r'\b(yeye|huyu|yule)\s+(ni|amekuwa).{{0,30}}{term}',
            r'{term}\s+wa\s+kwanza',
            r'\baliyekuwa\b.{{0,20}}{term}',
            r'\b(she|he)\s+(is|was|became|served\s+as).{{0,30}}{term}',
            r'\bthe\s+first\s+(female|male|woman|man)\s+{term}',
            # Family possession — possessives on family/relational nouns are biographical
            # Note: mke/mume excluded here — handled by their own lexicon avoid_when rules
            r'\b(bibi|babu|mama|baba|ndugu|kaka|dada|mtoto|mdogo|mkubwa|shangazi|mjomba)\s+{term}',
            # Family member + possessive + to-be verb + term (e.g. "Mama yake ni daktari wa kike")
            r'\b(mama|baba|bibi|babu|shangazi|mjomba|ndugu|kaka|dada)\s+(yake|wake|wao|wangu|wenu)\s+(ni|amekuwa)\b.{{0,40}}{term}',
            r'{term}\s+(wa\s+miaka|mwenye\s+umri)',
        ],
        ContextCondition.STATISTICAL: [
            r'\d+(\.\d+)?%\s*.{{0,30}}{term}',
            r'\d+(\.\d+)?%.{{0,30}}{term}',
            r'{term}.{{0,30}}\d+(\.\d+)?%',
            r'\b(takwimu|idadi|asilimia|wastani)\b.{{0,30}}{term}',
            r'\b(statistics|data|survey|study|research|percent|majority|minority)\b.{{0,30}}{term}',
            r'\b\d+\s+(kati\s+ya|out\s+of|of\s+the)\s+\d+\b.{{0,30}}{term}',
            # Bare count adjacent to term: "polisi wanawake 150" or "150 polisi wanawake"
            r'{term}\s+\d{{2,}}',
            r'\b\d{{2,}}\s+{term}',
        ],
        ContextCondition.MEDICAL: [
            r'\b(mjamzito|ujauzito|uzazi|kujifungua|mimba)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(mjamzito|ujauzito|uzazi|kujifungua)\b',
            r'\b{term}\s+mjamzito\b',
            r'\bmjamzito.{{0,10}}{term}',
            r'\b(pregnant|pregnancy|childbirth|maternal|obstetric|gynecolog)\b.{{0,50}}{term}',
            r'\b(saratani\s+ya\s+shingo|cervical\s+cancer|breast\s+cancer|prostate)\b.{{0,50}}{term}',
            r'\b(hospitali|clinic|daktari|nurse|doctor|hospital)\b.{{0,30}}{term}',
        ],
        ContextCondition.COUNTER_STEREOTYPE: [
            # Swahili role-reversal lines live in DetectorPatterns.COUNTER_STEREOTYPE_PATTERNS — they
            # trigger stage-1 counter_stereotype before lexicon; duplicating them here caused
            # document-wide matches to suppress mtoto/Watoto wa kike in unrelated sentences.
            r'\b(female|woman|she)\b.{0,30}\b(engineer|pilot|mechanic|CEO|surgeon)\b',
            r'\b(male|man|he)\b.{0,30}\b(nurse|secretary|nanny|caregiver)\b',
            r'\b(wa\s+kwanza|first)\b.{0,20}\b(wa\s+kike|wa\s+kiume|female|male)\b',
            # Debunking framing — term-anchored only (globals caused FNs when the same article
            # quoted biased policy and challenged bias in another clause).
            r'{term}.{{0,55}}\b(haileti\s+maana\s+kufikiri\s+kuwa|siamini\s+(kuwa|kwamba)|si\s+kweli\s+(kuwa|kwamba)|si\s+sahihi\s+(kuwa|kwamba)|kupinga\s+dhana|tunapinga|hatukubaliani|hii\s+ni\s+dhuluma|ni\s+udhalimu|ni\s+ubaguzi|lazima\s+(tubadilishe|tuzuie|tuondoe)|dhana\s+potofu\s+kuwa|kufuta\s+(usemi|dhana|imani)\s+wa)\b',
            r'\b(haileti\s+maana\s+kufikiri\s+kuwa|siamini\s+(kuwa|kwamba)|si\s+kweli\s+(kuwa|kwamba)|si\s+sahihi\s+(kuwa|kwamba)|kupinga\s+dhana|tunapinga|hatukubaliani|hii\s+ni\s+dhuluma|ni\s+udhalimu|ni\s+ubaguzi|lazima\s+(tubadilishe|tuzuie|tuondoe)|dhana\s+potofu\s+kuwa|kufuta\s+(usemi|dhana|imani)\s+wa)\b.{{0,55}}{term}',
            r'{term}.{{0,40}}\bwanawake\s+na\s+wanaume\s+wote\s+ni\s+sawa\b',
            r'\bwanawake\s+na\s+wanaume\s+wote\s+ni\s+sawa\b.{{0,40}}{term}',
            # Advocacy / rights framing — tight proximity patterns only
            # The keyword must be DIRECTLY adjacent to the gendered term (≤15 chars gap)
            # to avoid suppressing legitimate bias reports that mention rights/education elsewhere.
            # e.g. "haki za watoto wa kike" = advocacy (suppress)
            # vs "utumikishwaji wa watoto wa kike ... elimu ya" = bias report (do NOT suppress)
            r'\bhaki\s+za\s+(watoto|wasichana|wanawake)\s+wa\s+(kike|kiume)\b',
            # NOTE: Do not add a bare "haki za watoto" pattern — it matches anywhere in the
            # article and suppresses legitimate bias mentions of mtoto/Watoto wa kike elsewhere.
            r'\belimu\s+ya\s+(watoto|wasichana)\s+wa\s+kike\b',
            r'\belimu\s+ya\s+(watoto|wasichana)\b.{0,15}\bwa\s+kike\b',
            r'\b(uwezeshaji|ulinzi\s+wa)\s+(watoto|wasichana|wanawake)\s+wa\s+(kike|kiume)\b',
            r'\bkampeni\s+ya\s+(uwezeshaji|haki|ulinzi|elimu).{0,15}\b(wa\s+(kike|kiume)|wasichana)\b',
            r'\b(usawa\s+wa\s+kijinsia|haki\s+sawa).{0,12}\bwa\s+(kike|kiume)\b',
            r'\bwa\s+(kike|kiume).{0,12}\b(usawa\s+wa\s+kijinsia|haki\s+sawa)\b',
            # Keep {term}-anchored forms — tight windows so advocacy in one clause does not
            # suppress a gendered phrase in another.
            r'\b(haki\s+za\s+(wasichana|wanawake|watoto)|elimu\s+ya\s+(wasichana|watoto))\b.{{0,14}}{term}',
            r'{term}.{{0,14}}\b(haki\s+za\s+(wasichana|wanawake|watoto)|elimu\s+ya\s+(wasichana|watoto))\b',
            r'\b(uwezeshaji|kuhamasisha|ulinzi\s+wa|kampeni\s+ya)\b.{{0,18}}{term}',
            r'{term}.{{0,18}}\b(uwezeshaji|kuhamasisha|ulinzi\s+wa)\b',
            r'\b(usawa\s+wa\s+kijinsia|haki\s+sawa)\b.{{0,20}}{term}',
            r'{term}.{{0,20}}\b(usawa\s+wa\s+kijinsia|haki\s+sawa)\b',
            # Investment + girls framing (always advocacy)
            r'\b(milioni|bilioni|fedha|bajeti|pesa).{{0,28}}(watoto\s+wa\s+kike|wasichana).{{0,28}}\b(shule|elimu)\b',
            r'\b(shule|elimu).{{0,28}}(watoto\s+wa\s+kike|wasichana).{{0,28}}\b(milioni|bilioni|fedha|bajeti)\b',
            # Achievement / celebration framing — counter-stereotype (suppress)
            # "wasanii wa kike wanaofanya vizuri", "wachezaji wa kike walishinda", etc.
            r'{term}.{{0,22}}\b(wanaofanya\s+vizuri|wanafanya\s+vizuri|walishinda|wanapambana|wanajitahidi|wanatoa\s+huduma)\b',
            r'\b(wanaofanya\s+vizuri|wanafanya\s+vizuri|walishinda|wanapambana|wanajitahidi)\b.{{0,22}}{term}',
            r'{term}.{{0,22}}\b(wamefanikiwa|wameshinda|wamepata\s+mafanikio|wanaendelea\s+kufanya\s+kazi\s+nzuri)\b',
            r'\b(maadhimisho|sherehe|tuzo|zawadi|ushindi|mafanikio).{{0,22}}{term}',
            r'{term}.{{0,22}}\b(maadhimisho|sherehe|tuzo|zawadi|ushindi|mafanikio)\b',
            # News celebrating/profiling female/male in a role (listi ya, orodha ya = list of)
            r'\b(listi|orodha)\s+ya\s+{term}',
        ],
        ContextCondition.LEGAL: [
            r'\b(sheria|mahakama|kesi|mshtakiwa|mlalamikaji)\b.{{0,30}}{term}',
            r'\b(court|legal|plaintiff|defendant|witness|law|statute)\b.{{0,30}}{term}',
            r'\b(hati|certificate|document|official|sworn)\b.{{0,30}}{term}',
        ],
        ContextCondition.ARTISTIC: [
            r'\b(wimbo|filamu|kitabu|hadithi|mchezo)\b.{{0,30}}{term}',
            r'\b(song|film|movie|book|novel|play|poem|lyrics)\b.{{0,30}}{term}',
            r'\b(mhusika|character|role|actor|actress)\b.{{0,30}}{term}',
        ],
        ContextCondition.ORGANIZATION: [
            r'\b(TAWOMA|BAWATA|TAMWA|UWT)\b',
            r'\bChama\s+cha\s+\w+\s+{term}',
            r'\b[A-Z]{{2,6}}\b.{{0,20}}{term}',
        ],
    }

    SWAHILI_PRESERVE_PATTERNS = [
        r'\b[Mm]ama\s+[A-Z][a-z]+\b',
        r'\b[Bb]aba\s+[A-Z][a-z]+\b',
        r'\b(Bibi|Babu|Shangazi|Mjomba)\s+[A-Z][a-z]+\b',
    ]

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._compiled_patterns: Dict[ContextCondition, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for condition, patterns in self.CONTEXT_PATTERNS.items():
            self._compiled_patterns[condition] = []
            for pattern in patterns:
                try:
                    if '{term}' not in pattern:
                        self._compiled_patterns[condition].append(
                            re.compile(pattern, re.IGNORECASE | re.UNICODE)
                        )
                except re.error:
                    continue

    def _get_pattern_for_term(self, pattern_template: str, term: str) -> Optional[re.Pattern]:
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
        constraints: str = "",
    ) -> ContextCheckResult:
        # Gate: possessive pronouns (yake/wake/zake/lake/chake) on inanimate nouns
        # are not gender markers — suppress to avoid false positives.
        _possessives = {'yake', 'wake', 'zake', 'lake', 'chake'}
        if biased_term.lower() in _possessives:
            if sw_possessive_is_inanimate(text, biased_term):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=ContextCondition.STATISTICAL,
                    reason=f"Possessive '{biased_term}' on inanimate noun — not a gender marker",
                    confidence=0.95,
                    matched_pattern="inanimate_noun_gate",
                )
            if not sw_possessive_has_human_referent(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=ContextCondition.STATISTICAL,
                    reason=f"Possessive '{biased_term}': no human occupation referent in context",
                    confidence=0.85,
                    matched_pattern="human_referent_gate",
                )

        conditions_to_check = self._parse_avoid_when(avoid_when)
        if not conditions_to_check:
            conditions_to_check = [
                ContextCondition.QUOTE,
                ContextCondition.PROPER_NOUN,
                ContextCondition.BIOGRAPHICAL,
            ]
        for condition in conditions_to_check:
            result = self._check_condition(text, biased_term, condition)
            if not result.should_correct:
                return result
        for pattern in self.SWAHILI_PRESERVE_PATTERNS:
            if re.search(pattern, text):
                full_match = re.search(pattern, text)
                if full_match and biased_term.lower() in full_match.group(0).lower():
                    return ContextCheckResult(
                        should_correct=False,
                        blocked_by=ContextCondition.PROPER_NOUN,
                        reason=f"Term is part of Swahili naming convention: {full_match.group(0)}",
                        confidence=0.9,
                        matched_pattern=pattern
                    )
        return ContextCheckResult(should_correct=True, reason="No blocking context detected", confidence=1.0)

    def _parse_avoid_when(self, avoid_when: str) -> List[ContextCondition]:
        if not avoid_when or avoid_when.strip() == "":
            return []
        conditions = []
        for part in avoid_when.split('|'):
            part = part.strip().lower()
            try:
                conditions.append(ContextCondition(part))
            except ValueError:
                continue
        return conditions

    def _check_condition(
        self,
        text: str,
        term: str,
        condition: ContextCondition
    ) -> ContextCheckResult:
        patterns = self.CONTEXT_PATTERNS.get(condition, [])
        for pattern_template in patterns:
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
        if condition == ContextCondition.BIOGRAPHICAL:
            # term followed directly by a personal name — e.g. "Rais Magufuli" (title + name)
            # Gap must be ≤5 chars (whitespace only) to avoid firing on "Rais alikuwa..."
            for t in (term, term.lower(), term.capitalize()):
                term_name_pattern = re.compile(
                    re.escape(t) + r'\s{1,5}[A-Z][a-z]{2,}(\s+[A-Z][a-z]{2,})?',
                    re.UNICODE
                )
                match = term_name_pattern.search(text)
                if match:
                    if term.lower() in _SW_TITLE_AFTER_PARTICLE and _sw_title_noun_embedded_after_particle(
                        text, match.start()
                    ):
                        continue
                    return ContextCheckResult(
                        should_correct=False,
                        blocked_by=condition,
                        reason=f"Detected {condition.value} context (name reference)",
                        confidence=0.85,
                        matched_pattern="term + [Name]"
                    )
            # Two proper names (mixed-case only) in close proximity to the term (≤15 chars)
            # e.g. "Ken Kesey s'est inspiré de l'infirmière" — author referenced the role
            # Case-sensitive: ALL-CAPS bylines (e.g. "PENDO FUNDISHA") are excluded.
            # Tight gap prevents firing on general news articles with names far from the term.
            name_suffix = re.escape(term.lower())
            name_pattern = re.compile(
                r'[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}.{0,25}' + name_suffix,
                re.UNICODE  # No IGNORECASE — must be proper mixed-case name
            )
            if name_pattern.search(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=condition,
                    reason=f"Detected {condition.value} context (name reference)",
                    confidence=0.85,
                    matched_pattern="[Name Name] + term (tight)"
                )
        return ContextCheckResult(
            should_correct=True,
            reason=f"No {condition.value} context detected",
            confidence=1.0
        )

    def is_in_quotes(self, text: str, term: str) -> bool:
        quote_patterns = [
            r'"[^"]*' + re.escape(term) + r'[^"]*"',
            r"'[^']*" + re.escape(term) + r"[^']*'",
        ]
        for pattern in quote_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_proper_nouns(self, text: str) -> List[str]:
        proper_nouns = []
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            words = sentence.split()
            for i, word in enumerate(words):
                if i == 0:
                    continue
                if word and word[0].isupper():
                    clean_word = re.sub(r'[^\w]', '', word)
                    if clean_word and len(clean_word) > 1:
                        proper_nouns.append(clean_word)
        return list(set(proper_nouns))

    def get_preservation_entities(self, text: str) -> List[str]:
        entities = set()
        entities.update(self.extract_proper_nouns(text))
        org_patterns = [r'\b[A-Z]{2,6}\b', r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b']
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)
        return list(entities)


def should_apply_correction(
    text: str,
    biased_term: str,
    avoid_when: str = "",
    constraints: str = ""
) -> Tuple[bool, str]:
    """Quick check if correction should be applied. Returns (should_correct, reason)."""
    checker = ContextChecker()
    result = checker.check_context(text, biased_term, avoid_when, constraints)
    return result.should_correct, result.reason
