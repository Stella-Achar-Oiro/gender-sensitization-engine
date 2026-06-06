"""
Generate English correction pairs for the Stage 3 corrector.

Sources:
  1. WinoBias (HuggingFace) — gendered pronoun coreference sentences
     type1_pro/anti + type2_pro/anti, both val+test splits
     Correction: she/her/he/him referring to occupation → they/them
  2. Rule-based expansion — gendered job titles, capability stereotypes,
     pronoun assumption patterns, expanded from templates

Output appended to data/training_data_correction.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

OUT_PATH = ROOT / "data" / "training_data_correction.csv"

# ── Pronoun substitution maps ─────────────────────────────────────────────────
# she/her/hers/herself → they/them/theirs/themselves
# he/him/his/himself   → they/them/their/themselves
_PRONOUN_MAP: dict[str, str] = {
    r"\bshe\b": "they",
    r"\bher\b": "them",          # object form: "asked her" → "asked them"
    r"\bhers\b": "theirs",
    r"\bherself\b": "themselves",
    r"\bhe\b": "they",
    r"\bhim\b": "them",
    r"\bhis\b": "their",
    r"\bhimself\b": "themselves",
    # possessive at start of clause: "Her report" → "Their report"
    r"\bHer\b": "Their",
    r"\bHis\b": "Their",
    r"\bShe\b": "They",
    r"\bHe\b": "They",
    r"\bHim\b": "Them",
}

# Gendered occupation terms → neutral
_TITLE_MAP: dict[str, str] = {
    r"\bchairman\b": "chair",
    r"\bchairmen\b": "chairs",
    r"\bChairman\b": "Chair",
    r"\bfireman\b": "firefighter",
    r"\bfiremen\b": "firefighters",
    r"\bFireman\b": "Firefighter",
    r"\bpoliceman\b": "police officer",
    r"\bpolicemen\b": "police officers",
    r"\bPoliceman\b": "Police officer",
    r"\bmailman\b": "mail carrier",
    r"\bmailmen\b": "mail carriers",
    r"\bMailman\b": "Mail carrier",
    r"\bdeliveryman\b": "delivery driver",
    r"\bdeliverymen\b": "delivery drivers",
    r"\bDeliveryman\b": "Delivery driver",
    r"\brepairman\b": "repair technician",
    r"\brepairmen\b": "repair technicians",
    r"\bRepairman\b": "Repair technician",
    r"\bhandyman\b": "maintenance worker",
    r"\bhandymen\b": "maintenance workers",
    r"\bHandyman\b": "Maintenance worker",
    r"\bgarbageman\b": "sanitation worker",
    r"\bgarbage man\b": "sanitation worker",
    r"\bGarbage man\b": "Sanitation worker",
    r"\bsalesman\b": "salesperson",
    r"\bsalesmen\b": "salespeople",
    r"\bSalesman\b": "Salesperson",
    r"\bsaleslady\b": "salesperson",
    r"\bSaleslady\b": "Salesperson",
    r"\bstewardess\b": "flight attendant",
    r"\bStewardess\b": "Flight attendant",
    r"\bwaitress\b": "server",
    r"\bWaitress\b": "Server",
    r"\bwaiter\b": "server",
    r"\bWaiter\b": "Server",
    r"\bseamstress\b": "tailor",
    r"\bSeamstress\b": "Tailor",
    r"\bweatherboy\b": "meteorologist",
    r"\bweathergirl\b": "meteorologist",
    r"\bWeathergirl\b": "Meteorologist",
    r"\bweatherman\b": "meteorologist",
    r"\bWeatherman\b": "Meteorologist",
    r"\banchorman\b": "news anchor",
    r"\bAnchorman\b": "News anchor",
    r"\bcameraman\b": "camera operator",
    r"\bCameraman\b": "Camera operator",
    r"\bsoundman\b": "sound technician",
    r"\bSoundman\b": "Sound technician",
    r"\bdoorman\b": "door attendant",
    r"\bDoorman\b": "Door attendant",
    r"\bcleaning lady\b": "cleaner",
    r"\bCleaning lady\b": "Cleaner",
    r"\bhousewife\b": "homemaker",
    r"\bHousewife\b": "Homemaker",
    r"\bbusinessman\b": "businessperson",
    r"\bbusinessmen\b": "businesspeople",
    r"\bBusinessman\b": "Businessperson",
    r"\bstatesman\b": "statesperson",
    r"\bStatesman\b": "Statesperson",
    r"\bsportsman\b": "athlete",
    r"\bSportsman\b": "Athlete",
    r"\bcraftsman\b": "craftsperson",
    r"\bCraftsman\b": "Craftsperson",
    r"\bworkman\b": "worker",
    r"\bWorkman\b": "Worker",
    r"\bcongressman\b": "representative",
    r"\bCongressman\b": "Representative",
    r"\bsalesman\b": "salesperson",
    r"\bclergyman\b": "clergy member",
    r"\bClergyman\b": "Clergy member",
    r"\bspokesman\b": "spokesperson",
    r"\bSpokesman\b": "Spokesperson",
    r"\bsportsmanship\b": "fair play",   # avoid false positive on this compound
}

# Gendered descriptor patterns → neutral rewrites (template-based)
# These handle attitudinal bias: "too emotional for X", "surprisingly good at Y"
_ATTITUDINAL_TEMPLATES: list[tuple[str, str, str]] = [
    # (biased_template, neutral_template, category)
    ("Women are too emotional for leadership", "Emotional intelligence is a leadership strength", "capability"),
    ("Women are too emotional for management", "Emotional intelligence is a management strength", "capability"),
    ("Women are not suited for engineering", "Engineering welcomes people of all genders", "capability"),
    ("Women are not good at mathematics", "Mathematical ability is not determined by gender", "capability"),
    ("Girls are not good at mathematics", "Mathematical ability is not determined by gender", "capability"),
    ("Girls are not as good as boys at science", "Science ability is not determined by gender", "capability"),
    ("Women are better suited for caregiving", "Caregiving ability is not determined by gender", "capability"),
    ("Men are better at decision making", "Decision-making ability is not determined by gender", "capability"),
    ("Men are better leaders than women", "Leadership ability is not determined by gender", "capability"),
    ("Men are naturally better at sports", "Athletic ability is not determined by gender", "capability"),
    ("Women are naturally better at cooking", "Cooking ability is not determined by gender", "capability"),
    ("Women should stay at home", "People of all genders can choose their roles", "family_role"),
    ("A woman's place is in the home", "People of all genders can choose their roles", "family_role"),
    ("Men are the breadwinners", "Financial responsibility is shared equally", "family_role"),
    ("He is the breadwinner of the family", "They are the primary earner in the family", "family_role"),
    ("She is just a housewife", "She manages the household", "family_role"),
    ("She is only a housewife", "She manages the household", "family_role"),
    ("Women belong in the kitchen", "People of all genders can cook", "family_role"),
    ("The female engineer struggled", "The engineer faced challenges", "profession"),
    ("The female doctor was surprised", "The doctor was surprised", "profession"),
    ("The female lawyer argued", "The lawyer argued", "profession"),
    ("A female pilot landed the plane", "A pilot landed the plane", "profession"),
    ("A male nurse tended the patient", "A nurse tended the patient", "profession"),
    ("The male secretary organized", "The secretary organized", "profession"),
    ("surprisingly good for a woman", "highly skilled", "capability"),
    ("surprisingly good for a girl", "highly skilled", "capability"),
    ("She is surprisingly competent", "She is competent", "capability"),
    ("She is surprisingly good at", "She is skilled at", "capability"),
    ("He is surprisingly good at nursing", "He is skilled at nursing", "capability"),
    ("Women are too sensitive for", "People of all genders handle", "capability"),
    ("Women can't handle pressure", "Pressure management is not gender-dependent", "capability"),
    ("Girls can't handle pressure", "Pressure management is not gender-dependent", "capability"),
]


def _apply_map(text: str, mapping: dict[str, str]) -> str:
    result = text
    for pattern, replacement in mapping.items():
        result = re.sub(pattern, replacement, result)
    return result


def _normalise(text: str) -> str:
    return " ".join(text.split()).strip(" .")


# ── Source 1: WinoBias ────────────────────────────────────────────────────────

def _winobias_pairs() -> list[dict]:
    try:
        from datasets import load_dataset
    except ImportError:
        print("  [SKIP] datasets not installed — skipping WinoBias")
        return []

    pairs = []
    configs = ["type1_pro", "type1_anti", "type2_pro", "type2_anti"]
    splits = ["test", "validation"]

    for config in configs:
        for split in splits:
            try:
                ds = load_dataset("wino_bias", config, split=split)
            except Exception as e:
                print(f"  [SKIP] wino_bias {config}/{split}: {e}")
                continue

            for row in ds:
                tokens = row["tokens"]
                sentence = " ".join(tokens)
                sentence = re.sub(r" \.", ".", sentence)
                sentence = re.sub(r" ,", ",", sentence)
                sentence = re.sub(r" '", "'", sentence)

                # Correction: replace gendered pronouns with they/them
                corrected = _apply_map(sentence, _PRONOUN_MAP)
                # Fix verb agreement: "they is" → "they are", "they was" → "they were"
                corrected = re.sub(r"\bthey is\b", "they are", corrected)
                corrected = re.sub(r"\bthey was\b", "they were", corrected)
                corrected = re.sub(r"\bThey is\b", "They are", corrected)
                corrected = re.sub(r"\bThey was\b", "They were", corrected)

                if corrected != sentence:
                    pairs.append({
                        "language": "en",
                        "input_text": _normalise(sentence),
                        "target_text": _normalise(corrected),
                        "source": "winobias",
                        "stereotype_category": "pronoun_assumption",
                    })

    print(f"  WinoBias raw pairs before dedup: {len(pairs)}")
    return pairs


# ── Source 2: Rule-based title + attitudinal expansion ───────────────────────

def _rulebased_pairs() -> list[dict]:
    pairs = []

    # 2a: Job title substitutions — generate varied sentences
    title_sentence_templates = [
        "The {title} arrived at the office.",
        "The {title} filed the report.",
        "The {title} handled the situation professionally.",
        "A {title} was needed for the job.",
        "We hired a new {title} last week.",
        "The {title} has ten years of experience.",
        "Ask the {title} for assistance.",
        "The {title} led the team meeting.",
        "Our {title} is very experienced.",
        "The {title} reviewed the documents.",
    ]

    gendered_titles = {
        "chairman": "chair",
        "fireman": "firefighter",
        "policeman": "police officer",
        "mailman": "mail carrier",
        "deliveryman": "delivery driver",
        "repairman": "repair technician",
        "handyman": "maintenance worker",
        "salesman": "salesperson",
        "weatherman": "meteorologist",
        "anchorman": "news anchor",
        "doorman": "door attendant",
        "congressman": "representative",
        "spokesman": "spokesperson",
        "craftsman": "craftsperson",
        "statesman": "statesperson",
        "businessman": "businessperson",
        "stewardess": "flight attendant",
        "waitress": "server",
        "salesgirl": "salesperson",
        "saleslady": "salesperson",
        "seamstress": "tailor",
        "cleaning lady": "cleaner",
        "housewife": "homemaker",
        "weathergirl": "meteorologist",
    }

    for biased_title, neutral_title in gendered_titles.items():
        for template in title_sentence_templates:
            inp = template.format(title=biased_title)
            tgt = template.format(title=neutral_title)
            if inp != tgt:
                pairs.append({
                    "language": "en",
                    "input_text": _normalise(inp),
                    "target_text": _normalise(tgt),
                    "source": "en_title_expansion",
                    "stereotype_category": "profession",
                })

    # 2b: Attitudinal/capability templates
    for biased, neutral, category in _ATTITUDINAL_TEMPLATES:
        pairs.append({
            "language": "en",
            "input_text": _normalise(biased),
            "target_text": _normalise(neutral),
            "source": "en_attitudinal_templates",
            "stereotype_category": category,
        })

    # 2c: Pronoun assumption patterns — his/her in generic professional contexts
    pronoun_templates = [
        ("Every doctor should update his records.", "Every doctor should update their records."),
        ("Every doctor should update her records.", "Every doctor should update their records."),
        ("Every nurse knows her patients.", "Every nurse knows their patients."),
        ("Every nurse knows his patients.", "Every nurse knows their patients."),
        ("Every teacher loves her students.", "Every teacher loves their students."),
        ("Every teacher loves his students.", "Every teacher loves their students."),
        ("Every employee must submit his timesheet.", "Every employee must submit their timesheet."),
        ("Every employee must submit her timesheet.", "Every employee must submit their timesheet."),
        ("Each manager should review his team.", "Each manager should review their team."),
        ("Each manager should review her team.", "Each manager should review their team."),
        ("Each engineer must complete his report.", "Each engineer must complete their report."),
        ("Each engineer must complete her report.", "Each engineer must complete their report."),
        ("The CEO gave his speech.", "The CEO gave their speech."),
        ("The CEO gave her speech.", "The CEO gave their speech."),
        ("The lawyer presented his case.", "The lawyer presented their case."),
        ("The lawyer presented her case.", "The lawyer presented their case."),
        ("Ask the manager about his decision.", "Ask the manager about their decision."),
        ("Ask the manager about her decision.", "Ask the manager about their decision."),
        ("The scientist published his findings.", "The scientist published their findings."),
        ("The scientist published her findings.", "The scientist published their findings."),
        ("The pilot landed his plane safely.", "The pilot landed their plane safely."),
        ("The pilot landed her plane safely.", "The pilot landed their plane safely."),
        ("The surgeon completed his operation.", "The surgeon completed their operation."),
        ("The surgeon completed her operation.", "The surgeon completed their operation."),
        ("Each businessperson should review his portfolio.", "Each businessperson should review their portfolio."),
        ("Each businessperson should review her portfolio.", "Each businessperson should review their portfolio."),
        ("Every student must hand in his assignment.", "Every student must hand in their assignment."),
        ("Every student must hand in her assignment.", "Every student must hand in their assignment."),
        ("The athlete proved his dedication.", "The athlete proved their dedication."),
        ("The athlete proved her dedication.", "The athlete proved their dedication."),
    ]

    for inp, tgt in pronoun_templates:
        pairs.append({
            "language": "en",
            "input_text": _normalise(inp),
            "target_text": _normalise(tgt),
            "source": "en_pronoun_templates",
            "stereotype_category": "pronoun_assumption",
        })

    print(f"  Rule-based: {len(pairs)} pairs (titles + attitudinal + pronouns)")
    return pairs


def main() -> None:
    print("Generating EN correction pairs...")

    wb_pairs = _winobias_pairs()
    rb_pairs = _rulebased_pairs()

    all_new = pd.DataFrame(wb_pairs + rb_pairs)
    all_new = all_new.drop_duplicates(subset=["input_text"])
    # Drop identical input/target
    all_new = all_new[all_new["input_text"] != all_new["target_text"]]

    print(f"\n  New EN pairs generated: {len(all_new)}")
    print(f"  By source: {all_new['source'].value_counts().to_dict()}")

    # Load existing and merge
    existing = pd.read_csv(OUT_PATH)
    en_existing = existing[existing["language"] == "en"]
    print(f"  Existing EN pairs: {len(en_existing)}")

    # Remove old EN rows, add all new ones
    non_en = existing[existing["language"] != "en"]
    combined = pd.concat([non_en, all_new], ignore_index=True)
    combined = combined.drop_duplicates(subset=["language", "input_text"])
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    combined.to_csv(OUT_PATH, index=False)

    print(f"\n{'='*50}")
    print(f"Total pairs now: {len(combined):,}")
    print(f"By language:\n{combined['language'].value_counts().to_string()}")
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
