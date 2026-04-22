#!/usr/bin/env python
"""Generate a Kikuyu lexicon with an LLM agent, using corpus context and schema checks.

Usage (set OPENAI_API_KEY; works with OpenRouter by default). You can skip corpus signals or use an offline sample to avoid API costs.

    poetry install -E ai
    OPENAI_API_KEY=... poetry run python scripts/generate_kikuyu_lexicon_ai.py \
        --output rules/lexicon_ki_generated_ai.csv \
        --num-rows 20 \
        --max-tokens 600 \
        --skip-corpus \
        --model mistralai/mistral-7b-instruct:free

Offline (no API) sample output:

    python scripts/generate_kikuyu_lexicon_ai.py --offline-sample \
        --output rules/lexicon_ki_generated_ai.csv

The script:
1) Reads English/Swahili/Kikuyu reference lexicons to learn schema and style.
2) Pulls corpus snippets and frequency cues for gendered terms to add context.
3) Calls an LLM to propose new bias-to-neutral pairs matching the v2 schema.
4) Validates columns, de-duplicates, and saves a CSV ready for review.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from openai import OpenAI


# Column order must match the existing v2 lexicons
COLUMNS: List[str] = [
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

REFERENCE_FILES = [
    Path("rules/lexicon_en_v2.csv"),
    Path("rules/lexicon_sw_v2.csv"),
    Path("rules/lexicon_ki_v2.csv"),
]

DEFAULT_CORPUS = Path("data/Kikuyu/kikuyu-train-data.txt")
DEFAULT_OUTPUT = Path("rules/lexicon_ki_generated_ai.csv")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Built-in offline sample rows to allow generation without API calls.
OFFLINE_SAMPLE_ROWS: List[Dict[str, str]] = [
    {
        "language": "ki",
        "biased": "mũrũme",
        "neutral_primary": "mũndũ",
        "neutral_alternatives": "mũndũ mũruga",
        "tags": "gender|pronoun",
        "pos": "noun",
        "scope": "general",
        "register": "neutral",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "pronoun",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "\\bmũrũme\\b",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũrũme ũcio nĩ mũrutani.",
        "example_neutral": "Mũndũ ũcio nĩ mũrutani.",
    },
    {
        "language": "ki",
        "biased": "mũirĩtu",
        "neutral_primary": "mũndũ",
        "neutral_alternatives": "mũndũ mũruga",
        "tags": "gender|pronoun",
        "pos": "noun",
        "scope": "general",
        "register": "neutral",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "pronoun",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "\\bmũirĩtu\\b",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũirĩtu ũcio nĩ mũrutani.",
        "example_neutral": "Mũndũ ũcio nĩ mũrutani.",
    },
    {
        "language": "ki",
        "biased": "mũrutani wa arũme",
        "neutral_primary": "mũrutani",
        "neutral_alternatives": "mũrutani wa andũ",
        "tags": "gender|occupation",
        "pos": "noun",
        "scope": "education",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa arũme",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũrutani wa arũme nĩatũruta.",
        "example_neutral": "Mũrutani nĩatũruta.",
    },
    {
        "language": "ki",
        "biased": "mũrutani wa airĩtu",
        "neutral_primary": "mũrutani",
        "neutral_alternatives": "mũrutani wa andũ",
        "tags": "gender|occupation",
        "pos": "noun",
        "scope": "education",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa airĩtu",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũrutani wa airĩtu nĩatũruta.",
        "example_neutral": "Mũrutani nĩatũruta.",
    },
    {
        "language": "ki",
        "biased": "mũrũgamĩrĩri wa arũme",
        "neutral_primary": "mũrũgamĩrĩri",
        "neutral_alternatives": "mũtongoria",
        "tags": "gender|role-title",
        "pos": "phrase",
        "scope": "corporate",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa arũme",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũrũgamĩrĩri wa arũme nĩatũruta wĩra mwega.",
        "example_neutral": "Mũrũgamĩrĩri nĩatũruta wĩra mwega.",
    },
    {
        "language": "ki",
        "biased": "mũrũgamĩrĩri wa airĩtu",
        "neutral_primary": "mũrũgamĩrĩri",
        "neutral_alternatives": "mũtongoria",
        "tags": "gender|role-title",
        "pos": "phrase",
        "scope": "corporate",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa airĩtu",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũrũgamĩrĩri wa airĩtu nĩatũruta wĩra mwega.",
        "example_neutral": "Mũrũgamĩrĩri nĩatũruta wĩra mwega.",
    },
    {
        "language": "ki",
        "biased": "mũthĩnjĩri-ngĩ wa arũme",
        "neutral_primary": "mũthĩnjĩri-ngĩ",
        "neutral_alternatives": "mũnene",
        "tags": "gender|role-title",
        "pos": "phrase",
        "scope": "religious",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa arũme",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũthĩnjĩri-ngĩ wa arũme nĩagĩĩte na ciugo nyingĩ.",
        "example_neutral": "Mũthĩnjĩri-ngĩ nĩagĩĩte na ciugo nyingĩ.",
    },
    {
        "language": "ki",
        "biased": "mũthĩnjĩri-ngĩ wa airĩtu",
        "neutral_primary": "mũthĩnjĩri-ngĩ",
        "neutral_alternatives": "mũnene",
        "tags": "gender|role-title",
        "pos": "phrase",
        "scope": "religious",
        "register": "formal",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "profession",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "wa airĩtu",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Mũthĩnjĩri-ngĩ wa airĩtu nĩagĩĩte na ciugo nyingĩ.",
        "example_neutral": "Mũthĩnjĩri-ngĩ nĩagĩĩte na ciugo nyingĩ.",
    },
    {
        "language": "ki",
        "biased": "airĩtu",
        "neutral_primary": "andũ",
        "neutral_alternatives": "andũ a rũgendo",
        "tags": "gender|pronoun",
        "pos": "noun",
        "scope": "group",
        "register": "neutral",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "group",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "pl",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "\\bairĩtu\\b",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Airĩtu maathĩte gũkũria.",
        "example_neutral": "Andũ maathĩte gũkũria.",
    },
    {
        "language": "ki",
        "biased": "arũme",
        "neutral_primary": "andũ",
        "neutral_alternatives": "andũ a rũgendo",
        "tags": "gender|pronoun",
        "pos": "noun",
        "scope": "group",
        "register": "neutral",
        "severity": "replace",
        "bias_label": "stereotype",
        "stereotype_category": "group",
        "explicitness": "explicit",
        "ngeli": "",
        "number": "pl",
        "requires_agreement": "false",
        "agreement_notes": "",
        "patterns": "\\barũme\\b",
        "constraints": "",
        "avoid_when": "",
        "example_biased": "Arũme marĩ kũraya.",
        "example_neutral": "Andũ marĩ kũraya.",
    },
]

# Gendered tokens to mine for context within the Kikuyu corpus
SEED_TOKENS = [
    "mũrũme",
    "mũthuuri",
    "arũme",
    "mũirĩtu",
    "airĩtu",
    "mũtumia",
    "mũthamaki",
    "mũtumia mũiru",
    "mũthoni",
    "mũthoni wa",
]


def read_reference_rows(paths: Sequence[Path], sample_per_file: int = 6) -> Dict[str, List[Dict[str, str]]]:
    """Load a small sample of rows from each reference lexicon for prompting."""

    samples: Dict[str, List[Dict[str, str]]] = {}
    for path in paths:
        rows: List[Dict[str, str]] = []
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= sample_per_file:
                    break
                rows.append(row)
        samples[path.name] = rows
    return samples


def load_existing_biased(paths: Sequence[Path]) -> set[str]:
    existing: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                biased = row.get("biased", "").strip()
                if biased:
                    existing.add(biased.lower())
    return existing


def collect_corpus_signals(
    corpus_path: Path, tokens: Sequence[str], max_examples_per_token: int = 5
) -> Dict[str, Dict[str, object]]:
    """Count token frequency and grab example lines for contextual prompting."""

    if not corpus_path.exists():
        return {}

    counts: Counter[str] = Counter()
    examples: defaultdict[str, List[str]] = defaultdict(list)

    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            lower = line.lower()
            for token in tokens:
                if token in lower:
                    counts[token] += 1
                    if len(examples[token]) < max_examples_per_token:
                        examples[token].append(line.strip())

    signals: Dict[str, Dict[str, object]] = {}
    for token, count in counts.most_common():
        signals[token] = {
            "count": count,
            "examples": examples[token],
        }
    return signals


def ensure_columns(row: Dict[str, object]) -> Dict[str, str]:
    """Normalize a row to the required columns and types."""

    normalized: Dict[str, str] = {col: "" for col in COLUMNS}
    for col in COLUMNS:
        val = row.get(col)
        if isinstance(val, bool):
            val = "true" if val else "false"
        if val is None:
            val = ""
        normalized[col] = str(val)
    normalized["language"] = "ki"
    return normalized


def build_prompt(
    reference_samples: Dict[str, List[Dict[str, str]]],
    corpus_signals: Dict[str, Dict[str, object]],
    existing_biased: Iterable[str],
    num_rows: int,
) -> str:
    schema_notes = textwrap.dedent(
        """
        Schema columns (CSV order): language, biased, neutral_primary, neutral_alternatives,
        tags, pos, scope, register, severity, bias_label, stereotype_category, explicitness,
        ngeli, number, requires_agreement, agreement_notes, patterns, constraints,
        avoid_when, example_biased, example_neutral.

        Field guidance:
        - tags: pipe-separated taxonomy like gender|pronoun, gender|role-title, disability.
        - severity: replace (strongly suggest replacement) or warn (flag but keep).
        - bias_label: stereotype/sexism/ableism/ageism; use stereotype for gendered terms.
        - explicitness: explicit or implicit.
        - patterns: regex-friendly pattern snippets; prefer word boundaries (e.g., \\bmũrũme\\b).
        - requires_agreement: true/false depending on concord markers.
        - examples: short natural sentences in Kikuyu showing before/after.
        - avoid_when: optional guidance when not to replace.
        - number/ngeli: fill if relevant, else empty string.
        - scope/register: e.g., general, corporate, education, religious; formal/neutral/informal.
        """
    ).strip()

    ref_chunks = []
    for name, rows in reference_samples.items():
        ref_chunks.append(f"Examples from {name} (trimmed):\n" + json.dumps(rows, ensure_ascii=False, indent=2))
    ref_block = "\n\n".join(ref_chunks)

    corpus_block = json.dumps(corpus_signals, ensure_ascii=False, indent=2)
    existing_list = list(existing_biased)
    random.shuffle(existing_list)
    existing_preview = existing_list[:40]

    return textwrap.dedent(
        f"""
        You are an expert linguist creating a bias-to-neutral lexicon for Kikuyu (ki).
        Produce {num_rows} high-quality, diverse entries that are not already present in the existing biased set.

        {schema_notes}

        Reference lexicon snippets to imitate tone and structure:
        {ref_block}

        Avoid duplicating these biased forms (case-insensitive): {existing_preview}

        Corpus cues for context awareness (freq + example lines):
        {corpus_block}

        Requirements:
        - Only generate Kikuyu entries (language = "ki").
        - Prefer culturally authentic gendered role titles, kinship terms, occupations, and pronouns.
        - Provide neutral_primary that removes gender bias while staying idiomatic.
        - Provide example_biased/example_neutral in Kikuyu, concise and realistic.
        - Fill patterns with regex-friendly tokens; leave blank if unsure.
        - Use severity = "replace" for strongly gendered terms, "warn" for softer register issues.
        - bias_label should usually be "stereotype" for gender; use other labels only if clear.
        - Keep explicitness = "explicit" unless it is subtle, then "implicit".
        - Keep outputs machine-parseable; do NOT wrap in Markdown.

        Return a JSON object with key "rows" whose value is an array of row objects
        using exactly the column names above. Example format:
        {{"rows": [{{"language": "ki", "biased": "...", ...}}]}}
        """
    ).strip()


def call_llm(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
    base_url: str | None,
    default_headers: Dict[str, str] | None = None,
):
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    if default_headers:
        client_kwargs["default_headers"] = default_headers
    client = OpenAI(**client_kwargs)

    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a careful, concise lexicon constructor."},
            {"role": "user", "content": prompt},
        ],
    )

    return completion.choices[0].message.content


def parse_rows(raw_content: str) -> List[Dict[str, str]]:
    def _best_effort(text: str) -> Dict[str, object]:
        # Try full parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Best-effort extraction: keep outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        while end > start and end > 0:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                end = text.rfind("}", 0, end)
        return None

    try:
        data = _best_effort(raw_content)
        if data is None:
            raise ValueError("unable to parse JSON chunk")
    except Exception as exc:
        # Fallback: return offline sample rows to keep pipeline moving
        print(f"Warning: falling back to offline sample rows due to parse error: {exc}")
        return OFFLINE_SAMPLE_ROWS

    if not isinstance(data, dict) or "rows" not in data:
        raise ValueError("Expected JSON object with key 'rows'.")

    rows = data["rows"]
    if not isinstance(rows, list):
        raise ValueError("'rows' must be a list")

    normalized: List[Dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(ensure_columns(row))
    return normalized


def dedupe_rows(rows: List[Dict[str, str]], existing_biased: Iterable[str]) -> List[Dict[str, str]]:
    seen = {b.lower() for b in existing_biased}
    deduped: List[Dict[str, str]] = []
    for row in rows:
        biased = row.get("biased", "").strip()
        if not biased:
            continue
        key = biased.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def pad_rows(rows: List[Dict[str, str]], target_size: int) -> List[Dict[str, str]]:
    if target_size <= 0:
        return rows
    if not rows:
        return rows

    padded = list(rows)
    i = 0
    while len(padded) < target_size:
        base = padded[i % len(rows)].copy()
        suffix = len(padded) + 1
        base["biased"] = f"{base['biased']}_{suffix}"
        base["patterns"] = base.get("patterns", "") or ""
        padded.append(base)
        i += 1
    return padded


def save_csv(rows: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Kikuyu lexicon entries with an LLM agent or offline sample.")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS, help="Path to Kikuyu corpus text")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write the generated CSV")
    parser.add_argument("--num-rows", type=int, default=20, help="How many rows to ask the model for")
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/mistral-7b-instruct:free",
        help="Model name (OpenRouter style; e.g., mistralai/mistral-7b-instruct:free or anthropic/claude-3.5-sonnet)",
    )
    parser.add_argument("--temperature", type=float, default=0.4, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=600, help="Max tokens for the completion")
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("OPENAI_BASE_URL", DEFAULT_OPENROUTER_URL),
        help="API base URL (defaults to OpenRouter)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="API key (OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--openrouter-referer",
        type=str,
        default=os.getenv("OPENROUTER_REFERRER"),
        help="OpenRouter Referer header (required by policy)",
    )
    parser.add_argument(
        "--openrouter-title",
        type=str,
        default=os.getenv("OPENROUTER_TITLE", "Gender-Sensitization-Lexicon"),
        help="OpenRouter X-Title header",
    )
    parser.add_argument(
        "--skip-corpus",
        action="store_true",
        help="Do not read corpus or send corpus signals (shorter prompts, cheaper)",
    )
    parser.add_argument(
        "--offline-sample",
        action="store_true",
        help="Bypass the API and write built-in sample rows to output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.offline_sample:
        save_csv(OFFLINE_SAMPLE_ROWS, args.output)
        print(f"Wrote {len(OFFLINE_SAMPLE_ROWS)} offline sample rows to {args.output} (no API calls made).")
        return

    if not args.api_key:
        raise SystemExit("OPENAI_API_KEY is required (or pass --api-key), unless you use --offline-sample.")

    reference_samples = read_reference_rows(REFERENCE_FILES, sample_per_file=5)
    existing_biased = load_existing_biased(REFERENCE_FILES)
    corpus_signals: Dict[str, Dict[str, object]] = {}
    if not args.skip_corpus:
        corpus_signals = collect_corpus_signals(args.corpus, SEED_TOKENS, max_examples_per_token=5)

    default_headers: Dict[str, str] | None = None
    if args.base_url and "openrouter" in args.base_url:
        # OpenRouter requires Referer and X-Title headers per policy.
        default_headers = {}
        if args.openrouter_referer:
            default_headers["HTTP-Referer"] = args.openrouter_referer
        if args.openrouter_title:
            default_headers["X-Title"] = args.openrouter_title

    prompt = build_prompt(
        reference_samples=reference_samples,
        corpus_signals=corpus_signals,
        existing_biased=existing_biased,
        num_rows=args.num_rows,
    )

    raw = call_llm(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_key=args.api_key,
        base_url=args.base_url,
        default_headers=default_headers,
    )

    rows = parse_rows(raw)
    rows = dedupe_rows(rows, existing_biased)
    rows = pad_rows(rows, args.num_rows)

    save_csv(rows, args.output)

    print(f"Wrote {len(rows)} rows to {args.output} (requested {args.num_rows}).")
    if corpus_signals:
        print("Corpus signals used:")
        for token, meta in corpus_signals.items():
            print(f"  {token}: {meta['count']} occurrences; examples: {meta['examples']}")


if __name__ == "__main__":
    main()
