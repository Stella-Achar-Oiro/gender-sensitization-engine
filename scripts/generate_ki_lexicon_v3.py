"""Generate a large Kikuyu gender-bias lexicon from transcript datasets.

This script mines frequent n-grams that contain gendered/role terms from the
provided Kikuyu transcript CSVs, then creates rewrite lexicon rows in the
project's standard schema.

Output: rules/lexicon_ki_v3.csv

Notes:
- This is a heuristic generator (data-driven) intended to produce a large
  starting lexicon (1000+ rows) from the corpus.
- It does NOT call external LLM APIs. It relies on the corpus + a small set of
  replacement rules and templates.
- You can iteratively refine the seed terms and normalization rules.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


# If an n-gram includes these tokens, it's more likely to be a stereotype-laden
# template (e.g., "X nĩ wa ...", "X ti ...", "X ndangĩ...") and should be flagged
# as a warning rather than a direct replacement.
WARN_CUES = {
    "nĩ",
    "wa",
    "ti",
    "ndangĩ",
    "ndũ",
    "no",
    "mũhaka",
    "nĩwe",
    "nĩ",
}


def classify_severity(tokens: Sequence[str]) -> str:
    # Warn if pattern resembles a stereotype assertion or normative claim.
    joined = " ".join(tokens)
    if " nĩ wa " in f" {joined} ":
        return "warn"
    if " no mũhaka " in f" {joined} ":
        return "warn"
    if any(t in {"ti", "ndangĩ"} for t in tokens):
        return "warn"
    return "replace"


SCHEMA: List[str] = [
    "language",
    "biased",
    "neutral_primary",
    "neutral_alternatives",
    "tags",
    "pos",
    "scope",
    "register",
    "severity",
    "bias_label",
    "stereotype_category",
    "explicitness",
    "ngeli",
    "number",
    "requires_agreement",
    "agreement_notes",
    "patterns",
    "constraints",
    "avoid_when",
    "example_biased",
    "example_neutral",
]


# Seed terms that (in this project) we treat as potentially gendering a referent.
# We mine n-grams containing these tokens.
SEED_TERMS = [
    "mũtumia",
    "atumia",
    "mũndũmũka",
    "mũndũrũme",
    "mũrũme",
    "arũme",
    "mũthuri",
    "mũka",
    "mũkaana",
    "mwanake",
    "nyina",
    "maitu",
    "mũhiki",
    "mũthoni",
]


# Simple token-level replacements to create neutral forms.
# (We keep this conservative to avoid creating ungrammatical outputs.)
TOKEN_REPLACEMENTS: Dict[str, str] = {
    "mũtumia": "mũndũ",
    "atumia": "andũ",
    "mũndũmũka": "mũndũ",
    "mũndũrũme": "mũndũ",
    "mũrũme": "mũndũ",
    "arũme": "andũ",
    "mũthuri": "mũndũ",
    # "mũka" is ambiguous in corpus (can be name fragments); treat as gendered role when standalone.
    "mũka": "mũndũ",
    "mũkaana": "mwana",
    "mwanake": "mwana",
    "nyina": "mũzazi",
    "maitu": "mũzazi mukuru",
    "mũhiki": "mũndũ wa ũhiki",
    "mũthoni": "mũndũ wa ũhoro wa ũhiki",
}


@dataclass(frozen=True)
class NgramCandidate:
    ngram: Tuple[str, ...]
    count: int
    example: str


def iter_transcript_sentences(data_dir: Path) -> Iterable[str]:
    for p in sorted(data_dir.glob("*_ki_transcripts_scripted.csv")):
        df = pd.read_csv(p)
        if "actualSentence" not in df.columns:
            continue
        for s in df["actualSentence"].dropna().astype(str).tolist():
            yield s


_TOKEN_RE = re.compile(r"[A-Za-zũĩũĩĩ’']+")


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def contains_seed(text_lower: str) -> bool:
    return any(st in text_lower for st in SEED_TERMS)


def mine_ngrams(
    sentences: Sequence[str],
    n_min: int,
    n_max: int,
    min_count: int,
) -> List[NgramCandidate]:
    counts: Counter[Tuple[str, ...]] = Counter()
    example: Dict[Tuple[str, ...], str] = {}

    for s in sentences:
        low = s.lower()
        if not contains_seed(low):
            continue
        toks = tokenize(s)
        if not toks:
            continue
        for n in range(n_min, n_max + 1):
            for i in range(len(toks) - n + 1):
                g = tuple(toks[i : i + n])
                if any(seed in " ".join(g) for seed in SEED_TERMS):
                    counts[g] += 1
                    if g not in example:
                        example[g] = s

    cands = [
        NgramCandidate(ngram=g, count=c, example=example[g])
        for g, c in counts.items()
        if c >= min_count
    ]
    cands.sort(key=lambda x: (-x.count, " ".join(x.ngram)))
    return cands


def is_warn_candidate(tokens: Sequence[str]) -> bool:
    return classify_severity(tokens) == "warn"


def choose_candidates_with_warn_mix(
    candidates: Sequence[NgramCandidate],
    *,
    target_rows: int,
    warn_ratio: float,
) -> List[NgramCandidate]:
    """Pick candidates to hit a warn/replace mix.

    We first take warn candidates (rarer) up to target_warn, then fill remaining
    slots with replace candidates.
    """

    warn_ratio = max(0.0, min(1.0, warn_ratio))
    target_warn = int(round(target_rows * warn_ratio))

    warn: List[NgramCandidate] = []
    replace: List[NgramCandidate] = []
    for c in candidates:
        if is_warn_candidate(c.ngram):
            warn.append(c)
        else:
            replace.append(c)

    picked: List[NgramCandidate] = []

    # Start with warn up to target_warn.
    picked.extend(warn[:target_warn])

    # Fill the rest with replace.
    remaining = target_rows - len(picked)
    if remaining > 0:
        picked.extend(replace[:remaining])

    # If we still didn't reach target_rows (possible if candidates are very few),
    # fall back to using whatever remains from either pool.
    if len(picked) < target_rows:
        used = set(picked)
        for pool in (warn, replace):
            for c in pool:
                if c in used:
                    continue
                picked.append(c)
                used.add(c)
                if len(picked) >= target_rows:
                    break
            if len(picked) >= target_rows:
                break

    return picked


def _oversample_count(target_rows: int, warn_ratio: float) -> int:
    """Heuristic: oversample more when warn_ratio is higher (warn patterns are rarer)."""
    # Base oversample 2x, and ramp to 3.5x as warn_ratio approaches 1.0.
    factor = 2.0 + 1.5 * max(0.0, min(1.0, warn_ratio))
    return int(max(target_rows, round(target_rows * factor)))


def neutralize_phrase(tokens: Sequence[str]) -> Optional[str]:
    # Replace any token that is exactly a known gendered token.
    out = []
    changed = False
    for t in tokens:
        if t in TOKEN_REPLACEMENTS:
            out.append(TOKEN_REPLACEMENTS[t])
            changed = True
        else:
            out.append(t)
    if not changed:
        return None
    return " ".join(out)


def guess_pos(tokens: Sequence[str]) -> str:
    # Heuristic: phrases for 2+ tokens, noun for 1 token.
    return "noun" if len(tokens) == 1 else "phrase"


def guess_tags(tokens: Sequence[str]) -> str:
    joined = " ".join(tokens)
    if "nyina" in joined or "maitu" in joined:
        return "gender|family_role"
    if "mũhiki" in joined or "mũthoni" in joined:
        return "gender|family_role"
    if "mũthuri" in joined or "mũka" in joined:
        return "gender|marital_role"
    return "gender"


def guess_avoid_when(tokens: Sequence[str], tags: str) -> str:
    # Keep this short and conservative; it becomes a reviewer hint.
    joined = " ".join(tokens)
    if "nyina" in joined or "maitu" in joined:
        return "when the specific maternal relation is central (e.g., clinical or legal context)"
    if "mũndũmũka" in joined or "mũndũrũme" in joined:
        return "when biological sex is medically relevant"
    if tags == "gender|marital_role":
        return "when the person/group self-identifies with the term"
    if "\"" in joined or "'" in joined:
        return "inside direct quotes where wording must be preserved"
    return ""


def guess_constraints(tokens: Sequence[str]) -> str:
    joined = " ".join(tokens)
    if "mũka" in joined:
        return "token 'mũka' can appear in names/compounds; prefer whole-word matches"
    return ""


def guess_agreement_notes(tokens: Sequence[str]) -> str:
    # We currently do token substitution only; agreement may break in longer phrases.
    if len(tokens) >= 4:
        return "check noun-class agreement after replacement"
    return ""


def make_row(
    biased: str,
    neutral: str,
    example_biased: str,
    example_neutral: str,
    *,
    pos: str,
    tags: str,
    severity: str,
    requires_agreement: str,
    agreement_notes: str,
    constraints: str,
    avoid_when: str,
) -> Dict[str, str]:
    return {
        "language": "ki",
        "biased": biased,
        "neutral_primary": neutral,
        "neutral_alternatives": "",
        "tags": tags,
        "pos": pos,
        "scope": "general",
        "register": "general",
        "severity": severity,
        "bias_label": "stereotype",
        "stereotype_category": "gender" if tags.startswith("gender") else "gender",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "",
        "requires_agreement": requires_agreement,
        "agreement_notes": agreement_notes,
        "patterns": "",
        "constraints": constraints,
        "avoid_when": avoid_when,
        "example_biased": example_biased,
        "example_neutral": example_neutral,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/Kikuyu", help="Directory with Kikuyu transcript CSVs")
    ap.add_argument("--out", default="rules/lexicon_ki_v3.csv", help="Output CSV path")
    ap.add_argument("--min-count", type=int, default=2, help="Minimum n-gram frequency")
    ap.add_argument("--n-min", type=int, default=2)
    ap.add_argument("--n-max", type=int, default=7)
    ap.add_argument("--target-rows", type=int, default=1200, help="Stop after generating this many rows")
    ap.add_argument(
        "--warn-ratio",
        type=float,
        default=0.25,
        help="Target fraction of rows that should be severity=warn (0..1).",
    )
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_path = Path(args.out)

    sentences = list(iter_transcript_sentences(data_dir))
    cands = mine_ngrams(sentences, n_min=args.n_min, n_max=args.n_max, min_count=args.min_count)

    # Choose a mix that intentionally includes more warn patterns.
    # We oversample because many candidates will be dropped during neutralization
    # and deduplication.
    picked = choose_candidates_with_warn_mix(
        cands,
        target_rows=_oversample_count(args.target_rows, args.warn_ratio),
        warn_ratio=args.warn_ratio,
    )

    rows: List[Dict[str, str]] = []
    seen: set[Tuple[str, str]] = set()

    for cand in picked:
        toks = list(cand.ngram)
        biased = " ".join(toks)
        neutral = neutralize_phrase(toks)
        if not neutral:
            continue
        key = (biased, neutral)
        if key in seen:
            continue
        seen.add(key)

        pos = guess_pos(toks)
        tags = guess_tags(toks)
        severity = classify_severity(toks)
        avoid_when = guess_avoid_when(toks, tags)
        constraints = guess_constraints(toks)
        agreement_notes = guess_agreement_notes(toks)
        requires_agreement = "true" if agreement_notes else "false"

        # Derive example_neutral by token-level substitution over the example sentence.
        ex_b = cand.example
        ex_n = ex_b
        for src, tgt in TOKEN_REPLACEMENTS.items():
            # word boundary-ish replacement for latin letters + diacritics
            ex_n = re.sub(rf"\b{re.escape(src)}\b", tgt, ex_n, flags=re.IGNORECASE)

        rows.append(
            make_row(
                biased=biased,
                neutral=neutral,
                example_biased=ex_b,
                example_neutral=ex_n,
                pos=pos,
                tags=tags,
                severity=severity,
                requires_agreement=requires_agreement,
                agreement_notes=agreement_notes,
                constraints=constraints,
                avoid_when=avoid_when,
            )
        )
        if len(rows) >= args.target_rows:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    if len(rows) < args.target_rows:
        print(
            f"Wrote {len(rows)} rows -> {out_path} (note: fewer than target_rows={args.target_rows}; consider lowering --min-count or increasing --n-max)"
        )
    else:
        print(f"Wrote {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
