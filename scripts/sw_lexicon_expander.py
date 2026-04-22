#!/usr/bin/env python3
"""
Swahili lexicon expander — uses Gemini to analyse SW false negatives and
suggest new lexicon entries to improve recall.

Targets the 197 SW FNs (107 stereotype, 72 occupation, 18 none) that the
rules-based layer currently misses.

Usage:
    python3 scripts/sw_lexicon_expander.py [--limit N] [--dry-run]

Output:
    scripts/sw_lexicon_suggestions.csv  (suggested new entries for human review)
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT_PATH = ROOT / "eval" / "ground_truth_sw_v5.csv"
LEXICON_PATH = ROOT / "rules" / "lexicon_sw_v3.csv"
OUT_PATH = ROOT / "scripts" / "sw_lexicon_suggestions.csv"

BATCH_SIZE = 20
SLEEP_BETWEEN = 0.4
MODEL = "gemini-2.0-flash"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are an expert linguist and gender bias annotator for the Swahili language (Kiswahili).

You will be given Swahili sentences that contain gender bias. Your task is to identify:
1. The specific biased term or short phrase (1-6 words) that signals the bias
2. A gender-neutral Swahili alternative
3. The bias category and stereotype category
4. Whether to replace or warn

Swahili gender bias patterns to look for:
- Gendered occupation markers: "daktari wa kiume/kike", "mwalimu wa kiume/kike" (implies gender is surprising)
- Male-default roles: occupations/leadership stated as male by default
- Prescriptive gender roles: "mwanamke anapaswa...", "mume lazima...", proverbs about women/men
- Appearance/body comments: body-shaming or appearance standards by gender
- Sexual violence framing: victim-blaming, normalising violence against women
- Marriage/family prescriptions: bride price framing, polygamy normalisation
- Capability doubts: implying women can't do jobs/roles ("hata mwanamke anaweza")
- Religious/cultural framing that restricts women's roles

Definition of has_bias=true (use these to calibrate):
- Expresses a stereotype about what a gender should/shouldn't do
- Reports gendered harm (FGM, forced marriage, school dropout by gender, sexual violence)
- Uses "wa kike/wa kiume" to imply the gender is surprising or limiting for that role
- Prescribes different standards/roles based on gender

Definition of has_bias=false (do NOT suggest entries for these):
- Factual reporting about a gender-neutral event
- Advocacy/policy statements promoting equality (e.g. "serikali inajenga vyoo kwa wanafunzi wa kike")
- Counter-stereotype sentences (e.g. "msichana alichaguliwa kuwa rais")
- Statistical reporting without bias framing

For each sentence, return JSON:
{
  "biased_term": "exact term or short phrase from the sentence (1-6 words)",
  "neutral_primary": "Swahili neutral alternative",
  "tags": "gender|occupation OR gender|stereotype OR gender|family_role OR pronoun|gender",
  "stereotype_category": one of ["profession","family_role","leadership","capability","appearance","emotion","sexuality","violence","daily_life","intersectional"],
  "explicitness": one of ["explicit","implicit","counter_stereotype"],
  "severity": one of ["replace","warn"],
  "confidence": one of ["high","medium","low"],
  "reason": "one sentence explaining the specific bias"
}

Only suggest entries where the biased_term is genuinely a lexicon entry (a term that reliably signals bias when seen).
If the bias is in the full sentence context and not capturable as a short term, return {"biased_term": "", "confidence": "low", "reason": "no extractable term"}.

Return a JSON array, one object per sentence."""


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
    """Load SW FN rows — has_bias=True rows the detector missed."""
    import pandas as pd
    from eval.bias_detector import BiasDetector
    from eval.data_loader import Language

    print("Loading SW ground truth and running detector to find FNs...")
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
            result = detector.detect_bias(text, Language.SWAHILI)

            if not result.has_bias_detected:
                fns.append({
                    "id": row.get("id", ""),
                    "text": text,
                    "bias_category": row.get("bias_category", ""),
                    "stereotype_category": row.get("stereotype_category", ""),
                })
        except Exception:
            pass

    print(f"  {len(fns)} false negatives found")
    return fns


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


def call_api(client, texts: list[str], use_claude: bool = False) -> list[dict]:
    numbered = "\n".join(f"{i+1}. {t[:400]}" for i, t in enumerate(texts))
    prompt = f"Analyse these {len(texts)} Swahili sentences for gender bias patterns. Return one JSON object per sentence:\n\n{numbered}"

    if use_claude:
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
            raise ValueError(f"No JSON: {raw[:200]}")
        return [json.loads(raw[start:end])]
    return json.loads(raw[start:end])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
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

    # Load existing SW lexicon terms
    existing_biased = set()
    with open(LEXICON_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("language") == "sw":
                existing_biased.add(row.get("biased", "").strip().lower())
    print(f"Existing SW lexicon: {len(existing_biased)} entries")

    sys.path.insert(0, str(ROOT))
    fns = load_fn_rows()

    if args.limit > 0:
        fns = fns[: args.limit]

    if args.dry_run:
        print(f"\n[DRY RUN] Would analyse {len(fns)} SW FNs with {model_name}")
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
    all_results = []

    print(f"\nAnalysing {total} SW FN rows in {n_batches} batches (model: {model_name})...")

    for b in range(n_batches):
        start_i = b * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total)
        batch = texts[start_i:end_i]
        print(f"  Batch {b+1}/{n_batches} ({start_i+1}-{end_i})...", end=" ", flush=True)

        for attempt in range(3):
            try:
                results = call_api(client, batch, use_claude=use_claude)
                while len(results) < len(batch):
                    results.append({"biased_term": "", "confidence": "low", "reason": "no suggestion"})
                all_results.extend(results)
                useful = sum(1 for r in results if r.get("biased_term", "").strip())
                print(f"✓ ({useful}/{len(batch)} with term)")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry...", end=" ", flush=True)
                    time.sleep(2)
                else:
                    print(f"FAILED: {e}")
                    all_results.extend([{"biased_term": "", "confidence": "low", "reason": f"error: {e}"}] * len(batch))

        if b < n_batches - 1:
            time.sleep(SLEEP_BETWEEN)

    # Write suggestions
    fieldnames = [
        "biased_term", "neutral_primary", "tags", "stereotype_category",
        "explicitness", "severity", "confidence", "reason", "source_sentence",
    ]
    written = 0
    seen_terms = set()
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for fn, r in zip(fns, all_results):
            term = r.get("biased_term", "").strip()
            if not term or len(term) < 3:
                continue
            if term.lower() in existing_biased or term.lower() in seen_terms:
                continue
            seen_terms.add(term.lower())
            writer.writerow({
                "biased_term": term,
                "neutral_primary": r.get("neutral_primary", ""),
                "tags": r.get("tags", "gender|stereotype"),
                "stereotype_category": r.get("stereotype_category", ""),
                "explicitness": r.get("explicitness", "implicit"),
                "severity": r.get("severity", "warn"),
                "confidence": r.get("confidence", "low"),
                "reason": r.get("reason", ""),
                "source_sentence": fn["text"][:200],
            })
            written += 1

    print(f"""
══════════════════════════════════════════════════
  SW LEXICON EXPANSION COMPLETE
══════════════════════════════════════════════════
  FN rows analysed:    {total}
  Unique suggestions:  {written}
  Output:              {OUT_PATH.name}
══════════════════════════════════════════════════

Next steps:
  1. Review scripts/sw_lexicon_suggestions.csv
  2. Delete rows you reject or set severity=skip
  3. Run: python3 scripts/sw_apply_suggestions.py
  4. python3 run_evaluation.py
""")


if __name__ == "__main__":
    main()
