"""
Expand rules/lexicon_ki_v3.csv with semantic stereotype coverage for missing categories:
  appearance, character, emotion, sexuality, violence
  + depth in capability, leadership, profession, family_role, religion_culture

KI key vocabulary (from existing entries):
  mũndũ = person        andũ = people
  mũtumia = woman/wife  atumia = women
  mũthuri = man/husband athuri = men
  mũirĩtu = girl        airĩtu = girls
  mũriũ/mwariũ = boy    ariũ = boys
  mũrũ = child/son      airũ = children
  kiũme = male (adjective marker)
  ũtumia = female (adjective marker)
  mũtongoria = leader   atongoria = leaders
  wĩra = work           mũrũgamĩrĩri = manager
  nĩ = is/are           ndanĩ = not (negative)
  ti = not (negative)   angĩ = can/able to
  ndangĩ = cannot       nĩatĩ = why/how
  ũhoro = matter/issue
  mũgũnda = farm        mũciĩ = home
  mĩhĩrĩga = culture/clan

Writes to rules/lexicon_ki_v4.csv (never overwrite v3).
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEADER = [
    "language", "biased", "neutral_primary", "neutral_alternatives",
    "tags", "pos", "scope", "register", "severity",
    "bias_label", "stereotype_category", "explicitness",
    "ngeli", "number", "requires_agreement", "agreement_notes",
    "patterns", "constraints", "avoid_when",
    "example_biased", "example_neutral", "context_pattern",
]


def row(biased, neutral, neutral_alts="", tags="gender", pos="phrase",
        scope="general", register="general", severity="replace",
        bias_label="stereotype", category="profession", explicitness="explicit",
        avoid_when="", ex_biased="", ex_neutral="", context_pattern=""):
    return {
        "language": "ki",
        "biased": biased,
        "neutral_primary": neutral,
        "neutral_alternatives": neutral_alts,
        "tags": tags,
        "pos": pos,
        "scope": scope,
        "register": register,
        "severity": severity,
        "bias_label": bias_label,
        "stereotype_category": category,
        "explicitness": explicitness,
        "ngeli": "",
        "number": "",
        "requires_agreement": "",
        "agreement_notes": "",
        "patterns": "",
        "constraints": "",
        "avoid_when": avoid_when,
        "example_biased": ex_biased,
        "example_neutral": ex_neutral,
        "context_pattern": context_pattern,
    }


NEW_ROWS = [
    # ── PROFESSION — gendered occupation phrases ──────────────────────────────
    row("daktari wa kiũme", "daktari",
        tags="gender|profession", category="profession",
        ex_biased="Daktari wa kiũme nĩwe waraathimĩire mũndũ ũcio.",
        ex_neutral="Daktari nĩwe waraathimĩire mũndũ ũcio."),
    row("daktari wa ũtumia", "daktari",
        tags="gender|profession", category="profession",
        ex_biased="Daktari wa ũtumia nĩwe warĩa na mũndũ.",
        ex_neutral="Daktari nĩwe warĩa na mũndũ."),
    row("mũrũgamĩrĩri wa kiũme", "mũrũgamĩrĩri",
        tags="gender|profession", category="profession",
        ex_biased="Mũrũgamĩrĩri wa kiũme nĩwe mwega.",
        ex_neutral="Mũrũgamĩrĩri nĩwe mwega."),
    row("mũrũgamĩrĩri wa ũtumia", "mũrũgamĩrĩri",
        tags="gender|profession", category="profession",
        ex_biased="Mũrũgamĩrĩri wa ũtumia ndangĩathime wĩra ũcio.",
        ex_neutral="Mũrũgamĩrĩri ndangĩathime wĩra ũcio."),
    row("injinia wa kiũme", "injinia",
        tags="gender|profession", category="profession",
        ex_biased="Injinia wa kiũme nĩwe watũmĩire chuma ĩcio.",
        ex_neutral="Injinia nĩwe watũmĩire chuma ĩcio."),
    row("injinia wa ũtumia", "injinia",
        tags="gender|profession", category="profession",
        ex_biased="Injinia wa ũtumia ndangĩona ũhoro ũcio.",
        ex_neutral="Injinia ndangĩona ũhoro ũcio."),
    row("mwarimu wa kiũme", "mwarimu",
        tags="gender|profession", category="profession",
        ex_biased="Mwarimu wa kiũme nĩwe wĩra wa kũrutithia.",
        ex_neutral="Mwarimu nĩwe wĩra wa kũrutithia."),
    row("mwarimu wa ũtumia", "mwarimu",
        tags="gender|profession", category="profession",
        ex_biased="Mwarimu wa ũtumia ndangĩigua gĩthomo gĩo.",
        ex_neutral="Mwarimu ndangĩigua gĩthomo gĩo."),
    row("mwandĩki wa kiũme", "mwandĩki",
        tags="gender|profession", category="profession",
        ex_biased="Mwandĩki wa kiũme nĩwe watũmĩire barua ĩyo.",
        ex_neutral="Mwandĩki nĩwe watũmĩire barua ĩyo."),
    row("rũũrũ wa atumia", "rũũrũ",
        tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="Ndĩrathĩ rũũrũ wa atumia ta ũngĩkorwo.",
        ex_neutral="Ndĩrathĩ rũũrũ ta ũngĩkorwo."),

    # ── LEADERSHIP ────────────────────────────────────────────────────────────
    row("atongoria nĩo athuri",
        "atongoria nĩo andũ",
        tags="gender|leadership", category="leadership",
        ex_biased="Atongoria nĩo athuri gũkũ tũciĩ-inĩ twĩtũ.",
        ex_neutral="Atongoria nĩo andũ arĩa marĩ na ũhoti na ũgĩ."),
    row("mũtumia ndangĩtongoria",
        "mũndũ ndangĩtongoria",
        tags="gender|leadership", category="leadership",
        ex_biased="Mũtumia ndangĩtongoria bata bũrũri-inĩ.",
        ex_neutral="Mũndũ ndangĩtongoria bata bũrũri-inĩ ndangĩkorwo na ũhoti."),
    row("atumia matongorie",
        "andũ matongorie",
        tags="gender|leadership", category="leadership",
        severity="warn",
        ex_biased="Atumia matongorie mahotĩte kũtongoria?",
        ex_neutral="Andũ matongorie mahotĩte kũtongoria?"),
    row("mũtumia angĩtongoria",
        "mũndũ angĩtongoria",
        tags="gender|leadership", category="leadership",
        ex_biased="Mũtumia angĩtongoria ĩthĩ? No mũthuri nĩwe angĩtongoria.",
        ex_neutral="Mũndũ angĩtongoria nĩwe arĩa na ũhoti na ũgĩ."),
    row("mũtongoria wa kiũme nĩwe mwega",
        "mũtongoria nĩwe mwega",
        tags="gender|leadership", category="leadership",
        ex_biased="Mũtongoria wa kiũme nĩwe mwega na atĩĩ ngumo.",
        ex_neutral="Mũtongoria nĩwe mwega arĩa arĩ na ũgĩ."),
    row("athuri nĩo maweza kũtongoria",
        "andũ nĩo maweza kũtongoria",
        tags="gender|leadership", category="leadership",
        ex_biased="Athuri nĩo maweza kũtongoria kwa njĩra nzũri.",
        ex_neutral="Andũ nĩo maweza kũtongoria kwa njĩra nzũri na ũhoti."),

    # ── CAPABILITY ────────────────────────────────────────────────────────────
    row("atumia matihotĩte",
        "andũ matihotĩte",
        tags="gender|capability", category="capability",
        ex_biased="Atumia matihotĩte kũhota wĩra ũcio wa maũndũ-inĩ ma injinia.",
        ex_neutral="Andũ matihotĩte kũhota wĩra ũcio na ũhoti wĩragĩrwo."),
    row("mũtumia ndahotaga",
        "mũndũ ndahotaga",
        tags="gender|capability", category="capability",
        ex_biased="Mũtumia ndahotaga maũndũ ya thayari.",
        ex_neutral="Mũndũ ndahotaga maũndũ ya thayari ndangĩkornwo na ũhoti."),
    row("airĩtu matihotĩte",
        "airĩtu mahotĩte",
        tags="gender|capability", category="capability",
        context_pattern=r"\b(thayari|kora|wĩra|injinia|daktari)\b",
        ex_biased="Airĩtu matihotĩte ũgĩ wa thayari.",
        ex_neutral="Airĩtu mahotĩte ũgĩ wa thayari nĩ kũrĩrwa nzũri."),
    row("athuri nĩo mohotĩte",
        "andũ nĩo mohotĩte",
        tags="gender|capability", category="capability",
        ex_biased="Athuri nĩo mohotĩte kũhota wĩra ũcio wĩtĩkĩrĩtwo.",
        ex_neutral="Andũ nĩo mohotĩte kũhota wĩra ũcio arĩa marĩ na ũhoti."),
    row("mũtumia ndangĩona",
        "mũndũ ndangĩona",
        tags="gender|capability", category="capability",
        severity="warn",
        context_pattern=r"\b(ũhoro|kora|wĩra|ũgĩ)\b",
        ex_biased="Mũtumia ndangĩona ũhoro ũcio wa thayari.",
        ex_neutral="Mũndũ ndangĩona ũhoro ũcio na ũhoti wĩheo."),

    # ── FAMILY ROLE / HOUSEHOLD ───────────────────────────────────────────────
    row("mũciĩ nĩ wĩra wa atumia",
        "mũciĩ nĩ wĩra wa andũ othe",
        tags="gender|family_role", category="family_role",
        ex_biased="Mũciĩ nĩ wĩra wa atumia — mũthuri nĩ wa nja.",
        ex_neutral="Mũciĩ nĩ wĩra wa andũ othe a nyũmba."),
    row("kũhĩka nĩ wĩra wa mũtumia",
        "kũhĩka nĩ wĩra wa andũ othe",
        tags="gender|family_role", category="family_role",
        ex_biased="Kũhĩka nĩ wĩra wa mũtumia, si wa mũthuri.",
        ex_neutral="Kũhĩka nĩ wĩra wa andũ othe a nyũmba."),
    row("atumia nĩo a mũciĩ",
        "andũ othe nĩo a mũciĩ",
        tags="gender|family_role", category="family_role",
        ex_biased="Atumia nĩo a mũciĩ — athuri nĩo a nja.",
        ex_neutral="Andũ othe nĩo a mũciĩ na a nja."),
    row("mũtumia agĩũthie mũciĩ",
        "andũ agiũthie mũciĩ",
        tags="gender|family_role", category="family_role",
        ex_biased="Mũtumia agĩũthie mũciĩ na agĩrĩithie arĩĩ.",
        ex_neutral="Andũ agiũthie mũciĩ na agĩrĩithie arĩĩ."),
    row("ndĩwetwo nĩ mũtumia",
        "ndĩwetwo nĩ mũndũ",
        tags="gender|family_role", category="family_role",
        severity="warn",
        ex_biased="Ndĩwetwo nĩ mũtumia agĩkorwo kĩrĩkani.",
        ex_neutral="Ndĩwetwo nĩ mũndũ agĩkorwo kĩrĩkani."),

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    row("mũtumia mwega macio",
        "mũndũ mwega macio",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Mũtumia mwega macio nĩwe wahotĩrire wĩra ũcio.",
        ex_neutral="Mũndũ mwega macio nĩwe wahotĩrire wĩra ũcio na ũhoti."),
    row("atumia macio",
        "andũ macio",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Atumia macio nĩo mohotĩte kũhota wĩra ũcio.",
        ex_neutral="Andũ macio nĩo mohotĩte kũhota wĩra ũcio na ũhoti."),
    row("mũtumia ndamacio",
        "mũndũ ndamacio",
        tags="gender|appearance", category="appearance",
        ex_biased="Mũtumia ndamacio ndangĩkorwo na wĩra ũrĩa nzũri.",
        ex_neutral="Mũndũ ndamacio ndangĩkorwo na wĩra ũrĩa nzũri nĩ itĩkĩo rĩarĩa ritĩkĩrĩtwo."),
    row("mwirimu wa mũtumia",
        "mwirimu wa mũndũ",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Mwirimu wa mũtumia nĩ wa mwega wĩra ũcio.",
        ex_neutral="Mwirimu wa mũndũ ndwĩranaga na ũhoti wake wa wĩra."),
    row("mũtumia mwega mwiri",
        "mũndũ mwega mwiri",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Mũtumia mwega mwiri nĩwe agĩtorwo.",
        ex_neutral="Mũndũ mwega mwiri nĩwe agĩtorwo — nĩ mweri ũngĩhenia."),

    # ── CHARACTER ─────────────────────────────────────────────────────────────
    row("atumia nĩ oimba",
        "andũ nĩ oimba",
        tags="gender|character", category="character",
        ex_biased="Atumia nĩ oimba — matĩkarĩiganaga mĩhĩrĩga.",
        ex_neutral="Andũ nĩ oimba nĩ kũndĩ kũmwe gũtĩ na ũhoro."),
    row("mũtumia ndagũrĩagĩrwo",
        "mũndũ ndagũrĩagĩrwo",
        tags="gender|character", category="character",
        severity="warn",
        ex_biased="Mũtumia ndagũrĩagĩrwo ũhoro wa bata.",
        ex_neutral="Mũndũ ndagũrĩagĩrwo ũhoro wa bata ndangĩkorwo na ũhoti."),
    row("mũirĩtu ndũnena na ũheri",
        "mũndũ ndũnena na ũheri",
        tags="gender|character", category="character",
        ex_biased="Mũirĩtu ndũnena na ũheri — nĩ oimba.",
        ex_neutral="Mũndũ ndũnena na ũheri nĩ nĩ ũhoro wakĩrwo."),
    row("athuri nĩo arĩa oimba",
        "andũ nĩo arĩa oimba",
        tags="gender|character", category="character",
        ex_biased="Athuri nĩo arĩa oimba na matĩkarĩiganaga.",
        ex_neutral="Andũ nĩo arĩa oimba na matĩkarĩiganaga nĩ kũharo."),
    row("mũtumia arĩ wa ũtheri",
        "mũndũ arĩ wa ũtheri",
        tags="gender|character", category="character",
        severity="warn",
        ex_biased="Mũtumia arĩ wa ũtheri nĩ kĩhĩĩ kĩake.",
        ex_neutral="Mũndũ arĩ wa ũtheri nĩ kĩhĩĩ kĩake."),

    # ── EMOTION ───────────────────────────────────────────────────────────────
    row("mũtumia na ngoro ya ũhoro",
        "mũndũ na ngoro ya ũhoro",
        tags="gender|emotion", category="emotion",
        severity="warn",
        ex_biased="Mũtumia na ngoro ya ũhoro ndangĩhota kũrangĩra wĩra.",
        ex_neutral="Mũndũ na ngoro ya ũhoro ndangĩhota kũrangĩra wĩra nĩ itĩkĩo."),
    row("atumia nĩ a ngoro",
        "andũ nĩ a ngoro",
        tags="gender|emotion", category="emotion",
        ex_biased="Atumia nĩ a ngoro — matĩhotĩte kũrangĩra.",
        ex_neutral="Andũ nĩ a ngoro — nĩ ũhoro wa gũcaria ũhoti."),
    row("mũtumia ngĩrĩ",
        "mũndũ ngĩrĩ",
        tags="gender|emotion", category="emotion",
        ex_biased="Mũtumia ngĩrĩ — ndangĩhota kũrangĩra wĩra.",
        ex_neutral="Mũndũ ngĩrĩ nĩ arĩ na ũhoro wa kũtarithia."),
    row("airĩtu nĩo oimba",
        "andũ nĩo oimba",
        tags="gender|emotion", category="emotion",
        ex_biased="Airĩtu nĩo oimba kũnana na ariũ.",
        ex_neutral="Andũ nĩo oimba na nĩ ũhoro wa mĩhĩrĩga."),

    # ── SEXUALITY ─────────────────────────────────────────────────────────────
    row("mũirĩtu wa mĩhĩrĩga",
        "mũirĩtu",
        tags="gender|sexuality", category="sexuality",
        severity="warn",
        ex_biased="Mũirĩtu wa mĩhĩrĩga ndangĩkorwo na ũheri.",
        ex_neutral="Mũirĩtu ndangĩkorwo na ũheri nĩ itĩkĩo rĩarĩa."),
    row("mũtumia wa ngĩrĩ",
        "mũndũ",
        tags="gender|sexuality", category="sexuality",
        ex_biased="Mũtumia wa ngĩrĩ — oimba ta wa bũrũri.",
        ex_neutral="Mũndũ — oimba ta wa bũrũri arĩ na ũheri."),
    row("mwirimu wao nĩ wa kĩũme",
        "mwirimu wao",
        tags="gender|sexuality", category="sexuality",
        severity="warn",
        ex_biased="Mwirimu wao nĩ wa kĩũme — nĩ wĩra wao.",
        ex_neutral="Mwirimu wao nĩ wa kũhota wĩra wao."),

    # ── VIOLENCE / SAFETY ─────────────────────────────────────────────────────
    row("mũtumia oimba nĩ wake",
        "oimba nĩ ũhoro wa kũrangĩrirwo",
        tags="gender|violence", category="violence",
        ex_biased="Mũtumia oimba nĩ wake — ndũhĩrĩte thina.",
        ex_neutral="Oimba nĩ ũhoro wa kũrangĩrirwo — mũndũ othe ndagũrĩagĩrwo."),
    row("atumia nĩo kũhonokio",
        "andũ nĩo kũhonokio",
        tags="gender|violence", category="violence",
        ex_biased="Atumia nĩo kũhonokio nĩ kũrangĩra na athuri ao.",
        ex_neutral="Andũ nĩo kũhonokio nĩ kũrangĩrirwo."),
    row("mũtumia akorwo na ngoro ĩno",
        "mũndũ akorwo na ngoro ĩno",
        tags="gender|violence", category="violence",
        severity="warn",
        ex_biased="Mũtumia akorwo na ngoro ĩno — nĩwe oimba.",
        ex_neutral="Mũndũ akorwo na ngoro ĩno — nĩ ũhoro wa kũrangĩrirwo."),

    # ── RELIGION / CULTURE ────────────────────────────────────────────────────
    row("mĩhĩrĩga ĩgĩrĩria atumia",
        "mĩhĩrĩga ĩgĩrĩria andũ",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Mĩhĩrĩga ĩgĩrĩria atumia kũgarũra ĩtĩkĩo.",
        ex_neutral="Mĩhĩrĩga ĩgĩrĩria andũ kũgarũra ĩtĩkĩo nĩ ũhoro wa bata."),
    row("itĩkĩo rĩa atumia",
        "itĩkĩo rĩa andũ",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Itĩkĩo rĩa atumia nĩ rĩo rĩngĩkorwo na ũheri.",
        ex_neutral="Itĩkĩo rĩa andũ nĩ rĩo rĩngĩkorwo na ũheri."),
    row("akorwo mũtumia ahĩkĩte",
        "akorwo mũndũ ahĩkĩte",
        tags="gender|religion_culture", category="religion_culture",
        ex_biased="Akorwo mũtumia ahĩkĩte, nĩ wĩra wake gũtũngĩra mũciĩ.",
        ex_neutral="Akorwo mũndũ ahĩkĩte, nĩ wĩra wa mĩhĩrĩga gũtũngĩra mũciĩ."),
    row("Ngai agĩtũmĩra atumia",
        "Ngai agĩtũmĩra andũ",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Ngai agĩtũmĩra atumia kũhĩka na kũrĩithia.",
        ex_neutral="Ngai agĩtũmĩra andũ kũhĩka na kũrĩithia."),
]


def main():
    existing = []
    with open(ROOT / "rules/lexicon_ki_v3.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["context_pattern"] = r.get("context_pattern", "")
            existing.append(r)

    print(f"Existing v3 rows: {len(existing)}")

    all_rows = existing + NEW_ROWS
    seen = set()
    deduped = []
    for r in all_rows:
        key = (r["language"], r["biased"].strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    print(f"After dedup: {len(deduped)}")

    from collections import Counter
    cats = Counter(r.get("stereotype_category", "") for r in deduped if r.get("language") == "ki")
    print("Category distribution:", dict(cats.most_common()))

    out = ROOT / "rules/lexicon_ki_v4.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for r in deduped:
            writer.writerow({k: r.get(k, "") for k in HEADER})

    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
