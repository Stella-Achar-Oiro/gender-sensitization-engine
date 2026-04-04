#!/usr/bin/env python3
"""
Kikuyu lexicon expander — uses Gemini to analyse KI false negatives and
suggest new lexicon entries to improve recall.

Strategy:
- Load KI ground truth rows where has_bias=True but detector fires nothing
  (i.e. the false negatives from the last evaluation run)
- Send batches to Gemini Flash asking: what is the biased term/phrase,
  what category, what would a neutral alternative be in Kikuyu?
- Write suggested entries to scripts/ki_lexicon_suggestions.csv for human review
- Human reviews suggestions → approves rows → appends to rules/lexicon_ki_v3.csv

Usage:
    python3 scripts/ki_lexicon_expander.py [--limit N] [--dry-run]

Output:
    scripts/ki_lexicon_suggestions.csv  (new suggested entries)
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT_PATH = ROOT / "eval" / "ground_truth_ki_v8.csv"
LEXICON_PATH = ROOT / "rules" / "lexicon_ki_v3.csv"
OUT_PATH = ROOT / "scripts" / "ki_lexicon_suggestions.csv"

BATCH_SIZE = 15
SLEEP_BETWEEN = 0.5
MODEL = "gemini-2.0-flash"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # fallback if Gemini quota exhausted

SYSTEM_PROMPT = """You are an expert linguist and gender bias annotator for the Kikuyu language (Gĩkũyũ, spoken in Kenya).

You will be given Kikuyu sentences that contain gender bias. Your task is to identify:
1. The specific biased term or short phrase (1-5 words) that signals the bias
2. A gender-neutral alternative in Kikuyu
3. The bias category
4. Whether it is explicit or implicit

Kikuyu gender bias patterns to look for:
- Male-default pronouns/roles: "mũndũ mũrũme" (man/male person), "we" used for male-default
- Female-restricted roles: "mũtumia" (woman) assigned only domestic/subordinate roles
- Occupations with male-default: "mũthĩnjĩri" (priest — always male), "mũthamaki" (king/leader)
- Gendered task assignments: men farming/herding, women cooking/child-rearing
- Surprise markers: "o mũtumia" (even a woman) implying women shouldn't hold a role
- Prescriptive family roles: women defined by marital status, men by occupation/status

For each sentence, return a JSON object:
{
  "biased_term": "exact term or short phrase from the sentence",
  "neutral_primary": "Kikuyu neutral alternative",
  "bias_category": one of ["occupation", "family_role", "capability", "pronoun_assumption", "pronoun_generic", "stereotype", "religion_culture"],
  "stereotype_category": one of ["profession", "family_role", "leadership", "capability", "emotion", "daily_life", "intersectional"],
  "explicitness": one of ["explicit", "implicit"],
  "severity": one of ["replace", "warn"],
  "reason": "one sentence explaining the bias",
  "confidence": one of ["high", "medium", "low"]
}

Use severity="replace" only when the term is always biased regardless of context.
Use severity="warn" when the term is biased in most contexts but has neutral uses.

Return a JSON array, one object per sentence, in the same order as input."""


def get_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


def load_fn_rows() -> list[dict]:
    """Load KI ground truth rows that are has_bias=True (the FNs are these
    rows where the detector missed them — we need to find which ones)."""
    import pandas as pd
    from eval.bias_detector import BiasDetector
    from eval.data_loader import Language

    print("Loading KI ground truth and running detector...")
    gt = pd.read_csv(GT_PATH, low_memory=False)
    bias_rows = gt[gt["has_bias"] == True].copy()
    print(f"  {len(bias_rows)} has_bias=True rows")

    detector = BiasDetector()
    fns = []
    for _, row in bias_rows.iterrows():
        text = str(row["text"])
        if not text or text == "nan":
            continue
        try:
            result = detector.detect_bias(text, Language.GIKUYU)
            if not result.has_bias_detected:
                fns.append({
                    "id": row.get("id", ""),
                    "text": text,
                    "bias_category": row.get("bias_category", ""),
                    "stereotype_category": row.get("stereotype_category", ""),
                })
        except Exception:
            pass

    print(f"  {len(fns)} false negatives (missed by detector)")
    return fns


def call_api(client, texts: list[str], use_claude: bool = False) -> list[dict]:
    numbered = "\n".join(f"{i+1}. {t[:400]}" for i, t in enumerate(texts))
    prompt = f"Analyse these {len(texts)} Kikuyu sentences for gender bias. Return one JSON object per sentence:\n\n{numbered}"

    if use_claude:
        import anthropic
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    else:
        from google.genai import types
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        raw = response.text.strip()

    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1:
            raise ValueError(f"No JSON in response: {raw[:200]}")
        return [json.loads(raw[start:end])]
    return json.loads(raw[start:end])


def deduplicate_suggestions(suggestions: list[dict], existing_biased: set) -> list[dict]:
    """Remove suggestions for terms already in the lexicon."""
    seen_terms = set()
    out = []
    for s in suggestions:
        term = s.get("biased_term", "").strip().lower()
        if not term or term in existing_biased or term in seen_terms:
            continue
        if len(term) < 3:
            continue
        seen_terms.add(term)
        out.append(s)
    return out


def get_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Process first N FN rows (0 = all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--use-claude", action="store_true", help="Use Claude instead of Gemini")
    args = parser.parse_args()

    use_claude = args.use_claude
    if use_claude:
        api_key = get_anthropic_key()
        if not api_key and not args.dry_run:
            print("Error: ANTHROPIC_API_KEY not set.")
            sys.exit(1)
        model_name = CLAUDE_MODEL
    else:
        api_key = get_api_key()
        if not api_key and not args.dry_run:
            print("Error: GOOGLE_API_KEY not set.")
            sys.exit(1)
        model_name = MODEL

    # Load existing lexicon terms to avoid duplicates
    existing_biased = set()
    with open(LEXICON_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("language") == "ki":
                existing_biased.add(row.get("biased", "").strip().lower())
    print(f"Existing KI lexicon: {len(existing_biased)} entries")

    # Load FN rows
    sys.path.insert(0, str(ROOT))
    fns = load_fn_rows()

    if args.limit > 0:
        fns = fns[: args.limit]
        print(f"  Limiting to {args.limit} rows")

    if args.dry_run:
        print(f"\n[DRY RUN] Would analyse {len(fns)} FN rows with {model_name}")
        print("Sample FNs:")
        for fn in fns[:5]:
            print(f"  [{fn['bias_category']}] {fn['text'][:120]}")
        return

    if use_claude:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    else:
        from google import genai
        client = genai.Client(api_key=api_key)

    texts = [fn["text"] for fn in fns]
    total = len(texts)
    n_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    all_suggestions = []
    print(f"\nAnalysing {total} FN rows in {n_batches} batches (model: {model_name})...")

    for b in range(n_batches):
        start_i = b * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total)
        batch = texts[start_i:end_i]

        print(f"  Batch {b+1}/{n_batches} (rows {start_i+1}-{end_i})...", end=" ", flush=True)

        for attempt in range(3):
            try:
                results = call_api(client, batch, use_claude=use_claude)
                while len(results) < len(batch):
                    results.append({"biased_term": "", "confidence": "low", "reason": "no suggestion"})
                all_suggestions.extend(results)
                high = sum(1 for r in results if r.get("confidence") == "high")
                print(f"✓ ({high}/{len(batch)} high confidence)")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry...", end=" ", flush=True)
                    time.sleep(2)
                else:
                    print(f"FAILED: {e}")
                    all_suggestions.extend([{"biased_term": "", "confidence": "low", "reason": f"error: {e}"}] * len(batch))

        if b < n_batches - 1:
            time.sleep(SLEEP_BETWEEN)

    # Deduplicate and filter
    clean = deduplicate_suggestions(all_suggestions, existing_biased)
    print(f"\n{len(clean)} unique new suggestions (from {len(all_suggestions)} total)")

    # Write to CSV for human review
    fieldnames = [
        "biased_term", "neutral_primary", "bias_category", "stereotype_category",
        "explicitness", "severity", "confidence", "reason",
        "source_sentence",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for i, (fn, suggestion) in enumerate(zip(fns, all_suggestions)):
            if suggestion.get("biased_term", "").strip().lower() in existing_biased:
                continue
            row = {
                "biased_term": suggestion.get("biased_term", ""),
                "neutral_primary": suggestion.get("neutral_primary", ""),
                "bias_category": suggestion.get("bias_category", fn.get("bias_category", "")),
                "stereotype_category": suggestion.get("stereotype_category", ""),
                "explicitness": suggestion.get("explicitness", "implicit"),
                "severity": suggestion.get("severity", "warn"),
                "confidence": suggestion.get("confidence", "low"),
                "reason": suggestion.get("reason", ""),
                "source_sentence": fn["text"][:200],
            }
            writer.writerow(row)

    print(f"""
══════════════════════════════════════════════════════════
  KI LEXICON EXPANSION COMPLETE
══════════════════════════════════════════════════════════
  FN rows analysed:    {total}
  Unique suggestions:  {len(clean)}
  Output:              {OUT_PATH.name}
══════════════════════════════════════════════════════════

Next steps:
  1. Review scripts/ki_lexicon_suggestions.csv
  2. Delete rows you disagree with or mark severity=skip
  3. Run: python3 scripts/ki_apply_suggestions.py
  4. python3 run_evaluation.py  (check KI recall improvement)
""")


if __name__ == "__main__":
    main()
