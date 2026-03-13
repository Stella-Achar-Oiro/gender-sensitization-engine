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
            r'\b(yeye|huyu|yule)\s+(ni|alikuwa|amekuwa).{{0,30}}{term}',
            r'{term}\s+wa\s+kwanza',
            r'\baliyekuwa\b.{{0,20}}{term}',
            r'\balikuwa\b.{{0,20}}{term}',
            r'\b(she|he)\s+(is|was|became|served\s+as).{{0,30}}{term}',
            r'\bthe\s+first\s+(female|male|woman|man)\s+{term}',
        ],
        ContextCondition.STATISTICAL: [
            r'\d+(\.\d+)?%\s*.{{0,30}}{term}',
            r'\d+(\.\d+)?%.{{0,30}}{term}',
            r'{term}.{{0,30}}\d+(\.\d+)?%',
            r'\b(takwimu|idadi|asilimia|wastani)\b.{{0,30}}{term}',
            r'\b(statistics|data|survey|study|research|percent|majority|minority)\b.{{0,30}}{term}',
            r'\b\d+\s+(kati\s+ya|out\s+of|of\s+the)\s+\d+\b.{{0,30}}{term}',
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
            r'\b(mwanamke|mama)\b.{0,30}\b(mhandisi|rubani|fundi|mkurugenzi|daktari)\b',
            r'\b(mwanamume|baba)\b.{0,30}\b(muuguzi|mkunga|mlezi|mpishi)\b',
            r'\b(female|woman|she)\b.{0,30}\b(engineer|pilot|mechanic|CEO|surgeon)\b',
            r'\b(male|man|he)\b.{0,30}\b(nurse|secretary|nanny|caregiver)\b',
            r'\b(wa\s+kwanza|first)\b.{0,20}\b(wa\s+kike|wa\s+kiume|female|male)\b',
            # Advocacy / rights framing — narrow: only when canonical advocacy wording surrounds the term
            r'\b(haki\s+za\s+(wasichana|wanawake|watoto)|elimu\s+ya\s+(wasichana|watoto))\b.{{0,40}}{term}',
            r'{term}.{{0,40}}\b(haki\s+za\s+(wasichana|wanawake|watoto)|elimu\s+ya\s+(wasichana|watoto))\b',
            r'\b(uwezeshaji|kuhamasisha|ulinzi\s+wa|kampeni\s+ya)\b.{{0,40}}{term}',
            r'{term}.{{0,40}}\b(uwezeshaji|kuhamasisha|ulinzi\s+wa)\b',
            r'\b(usawa\s+wa\s+kijinsia|haki\s+sawa)\b.{{0,50}}{term}',
            r'{term}.{{0,50}}\b(usawa\s+wa\s+kijinsia|haki\s+sawa)\b',
            # Investment + girls framing (always advocacy)
            r'\b(milioni|bilioni|fedha|bajeti|pesa).{{0,40}}(watoto\s+wa\s+kike|wasichana).{{0,40}}\b(shule|elimu)\b',
            r'\b(shule|elimu).{{0,40}}(watoto\s+wa\s+kike|wasichana).{{0,40}}\b(milioni|bilioni|fedha|bajeti)\b',
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
            name_pattern = re.compile(
                r'[A-Z][a-z]+\s+[A-Z][a-z]+.{0,30}' + re.escape(term),
                re.UNICODE
            )
            if name_pattern.search(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=condition,
                    reason=f"Detected {condition.value} context (name reference)",
                    confidence=0.85,
                    matched_pattern="[Name] + term"
                )
            term_name_pattern = re.compile(
                re.escape(term) + r'\s+(wa\s+)?[A-Z][a-z]+(\s+[A-Z][a-z]+)?',
                re.UNICODE
            )
            if term_name_pattern.search(text):
                return ContextCheckResult(
                    should_correct=False,
                    blocked_by=condition,
                    reason=f"Detected {condition.value} context (name reference)",
                    confidence=0.85,
                    matched_pattern="term + [Name]"
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
