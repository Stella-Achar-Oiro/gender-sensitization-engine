"""
Expand rules/lexicon_fr_v3.csv by adding missing stereotype categories:
  religion_culture, character, emotion, sexuality, violence
  + more depth in capability, leadership, appearance, family_role
Writes to rules/lexicon_fr_v4.csv (never overwrite v3).
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
        "language": "fr",
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
    # ── LEADERSHIP (depth) ────────────────────────────────────────────────────
    row("les hommes font de meilleurs dirigeants",
        "les personnes font de bons dirigeants",
        tags="gender|leadership", category="leadership",
        ex_biased="On pense que les hommes font de meilleurs dirigeants.",
        ex_neutral="On pense que les personnes compétentes font de bons dirigeants."),
    row("les femmes ne sont pas faites pour diriger",
        "tout le monde peut diriger",
        tags="gender|leadership", category="leadership",
        ex_biased="Il croit que les femmes ne sont pas faites pour diriger.",
        ex_neutral="Il croit que tout le monde peut diriger avec la bonne formation."),
    row("une femme à la tête",
        "une personne à la tête",
        tags="gender|leadership", category="leadership",
        severity="warn",
        ex_biased="Avoir une femme à la tête de l'entreprise pose problème.",
        ex_neutral="Avoir une personne à la tête de l'entreprise nécessite des compétences."),
    row("les hommes sont naturellement des leaders",
        "les personnes peuvent être des leaders",
        tags="gender|leadership", category="leadership",
        ex_biased="Les hommes sont naturellement des leaders dans les entreprises.",
        ex_neutral="Les personnes peuvent être des leaders avec la formation appropriée."),
    row("trop émotive pour diriger",
        "pas suffisamment formée pour diriger",
        tags="gender|leadership|emotion", category="leadership",
        ex_biased="Elle est trop émotive pour diriger une équipe.",
        ex_neutral="Elle n'est pas suffisamment formée pour diriger cette équipe."),

    # ── CAPABILITY (depth) ────────────────────────────────────────────────────
    row("les femmes ne comprennent pas",
        "certaines personnes ne comprennent pas",
        tags="gender|capability", category="capability",
        context_pattern=r"\b(la technique|les chiffres|l.informatique|la finance|les math)\b",
        ex_biased="Les femmes ne comprennent pas les chiffres.",
        ex_neutral="Certaines personnes ne comprennent pas les chiffres sans formation."),
    row("les hommes sont plus logiques",
        "les personnes peuvent être logiques",
        tags="gender|capability", category="capability",
        ex_biased="Les hommes sont plus logiques que les femmes.",
        ex_neutral="Les personnes peuvent être logiques avec l'expérience."),
    row("les femmes sont moins rationnelles",
        "tout le monde peut être rationnel",
        tags="gender|capability", category="capability",
        ex_biased="Les femmes sont moins rationnelles dans les décisions d'affaires.",
        ex_neutral="Tout le monde peut être rationnel avec la bonne information."),
    row("les femmes ne savent pas conduire",
        "tout le monde peut conduire",
        tags="gender|capability", category="capability",
        ex_biased="On dit souvent que les femmes ne savent pas conduire.",
        ex_neutral="On dit souvent que tout le monde peut conduire avec de la pratique."),
    row("pas assez forte pour",
        "pas encore formée pour",
        tags="gender|capability", category="capability",
        severity="warn",
        context_pattern=r"\b(elle|femme|fille)\b",
        ex_biased="Elle n'est pas assez forte pour ce poste.",
        ex_neutral="Elle n'est pas encore formée pour ce poste."),

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    row("une femme séduisante",
        "une professionnelle compétente",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="On a choisi une femme séduisante pour représenter la marque.",
        ex_neutral="On a choisi une professionnelle compétente pour représenter la marque."),
    row("elle est trop vieille",
        "elle manque d'expérience récente",
        tags="gender|appearance|age", category="appearance",
        severity="warn",
        context_pattern=r"\b(poste|emploi|travail|chef|directrice)\b",
        ex_biased="Elle est trop vieille pour ce poste de direction.",
        ex_neutral="Elle manque d'expérience récente pour ce poste de direction."),
    row("soigne son apparence",
        "soigne sa présentation",
        tags="gender|appearance", category="appearance",
        severity="warn",
        context_pattern=r"\b(femme|elle|secrétaire|hôtesse)\b",
        ex_biased="La secrétaire doit soigner son apparence.",
        ex_neutral="La secrétaire doit soigner sa présentation professionnelle."),
    row("belle mais pas intelligente",
        "compétente",
        tags="gender|appearance", category="appearance",
        ex_biased="Elle est belle mais pas intelligente.",
        ex_neutral="Elle est compétente dans son domaine."),

    # ── FAMILY ROLE (depth) ───────────────────────────────────────────────────
    row("c'est le rôle de la femme",
        "c'est le rôle de chacun",
        tags="gender|family_role", category="family_role",
        ex_biased="S'occuper des enfants, c'est le rôle de la femme.",
        ex_neutral="S'occuper des enfants, c'est le rôle de chacun dans la famille."),
    row("les femmes devraient rester à la maison",
        "les parents peuvent choisir leur organisation",
        tags="gender|family_role", category="family_role",
        ex_biased="Les femmes devraient rester à la maison pour élever les enfants.",
        ex_neutral="Les parents peuvent choisir leur organisation familiale."),
    row("la cuisine est l'affaire des femmes",
        "la cuisine est l'affaire de tous",
        tags="gender|family_role", category="family_role",
        ex_biased="La cuisine est l'affaire des femmes dans notre culture.",
        ex_neutral="La cuisine est l'affaire de tous dans la famille."),
    row("le mari décide",
        "les deux partenaires décident",
        tags="gender|family_role", category="family_role",
        ex_biased="Dans cette famille, le mari décide de tout.",
        ex_neutral="Dans cette famille, les deux partenaires décident ensemble."),

    # ── RELIGION / CULTURE ────────────────────────────────────────────────────
    row("la religion interdit aux femmes",
        "certaines interprétations religieuses restreignent",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="La religion interdit aux femmes de diriger la prière.",
        ex_neutral="Certaines interprétations religieuses restreignent les rôles de genre."),
    row("la tradition veut que la femme",
        "certaines traditions attribuent à la femme",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="La tradition veut que la femme obéisse à son mari.",
        ex_neutral="Certaines traditions attribuent des rôles différents aux femmes et aux hommes."),
    row("selon nos coutumes, la femme",
        "selon certaines coutumes, les femmes",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Selon nos coutumes, la femme ne parle pas en public.",
        ex_neutral="Selon certaines coutumes, les femmes font face à des restrictions d'expression."),
    row("dieu a créé la femme pour",
        "certaines traditions enseignent que la femme",
        tags="gender|religion_culture", category="religion_culture",
        ex_biased="Dieu a créé la femme pour servir l'homme.",
        ex_neutral="Certaines traditions enseignent que la femme et l'homme ont des rôles complémentaires."),
    row("c'est la volonté de dieu",
        "c'est une interprétation culturelle",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        context_pattern=r"\b(femme|mari|soumission|obéir)\b",
        ex_biased="Que la femme obéisse, c'est la volonté de dieu.",
        ex_neutral="Que la femme obéisse, c'est une interprétation culturelle ancienne."),

    # ── CHARACTER ─────────────────────────────────────────────────────────────
    row("les femmes sont bavardes",
        "certaines personnes sont bavardes",
        tags="gender|character", category="character",
        ex_biased="Les femmes sont bavardes et ne savent pas garder un secret.",
        ex_neutral="Certaines personnes sont bavardes et ne savent pas garder un secret."),
    row("les hommes ne pleurent pas",
        "tout le monde peut exprimer ses émotions",
        tags="gender|character", category="character",
        ex_biased="Les hommes ne pleurent pas — c'est une règle.",
        ex_neutral="Tout le monde peut exprimer ses émotions librement."),
    row("typiquement féminin",
        "typique",
        tags="gender|character", category="character",
        severity="warn",
        ex_biased="Cette réaction est typiquement féminine.",
        ex_neutral="Cette réaction est typique dans cette situation."),
    row("les femmes sont trop sensibles",
        "certaines personnes sont sensibles",
        tags="gender|character", category="character",
        ex_biased="Les femmes sont trop sensibles pour ce métier.",
        ex_neutral="Certaines personnes sont sensibles, ce qui peut être un atout."),
    row("les hommes sont plus courageux",
        "tout le monde peut faire preuve de courage",
        tags="gender|character", category="character",
        ex_biased="Les hommes sont plus courageux que les femmes.",
        ex_neutral="Tout le monde peut faire preuve de courage selon la situation."),
    row("c'est une vraie femme",
        "c'est une personne",
        tags="gender|character", category="character",
        severity="warn",
        ex_biased="Elle est douce, c'est une vraie femme.",
        ex_neutral="Elle est douce, c'est une personne attentionnée."),
    row("comportement de femme",
        "comportement",
        tags="gender|character", category="character",
        ex_biased="Ce comportement de femme n'a pas sa place ici.",
        ex_neutral="Ce comportement n'a pas sa place dans ce contexte professionnel."),

    # ── EMOTION ───────────────────────────────────────────────────────────────
    row("trop émotive",
        "émotive dans cette situation",
        tags="gender|emotion", category="emotion",
        severity="warn",
        context_pattern=r"\b(elle|femme|fille|directrice)\b",
        ex_biased="Elle est trop émotive pour prendre des décisions importantes.",
        ex_neutral="Elle est émotive dans cette situation, ce qui est compréhensible."),
    row("elle prend tout à cœur",
        "il prend les retours au sérieux",
        tags="gender|emotion", category="emotion",
        severity="warn",
        ex_biased="Elle prend tout à cœur, c'est typique.",
        ex_neutral="Il prend les retours au sérieux et cherche à progresser."),
    row("hystérique",
        "très préoccupée",
        tags="gender|emotion", category="emotion",
        ex_biased="Elle est hystérique face à cette situation.",
        ex_neutral="Elle est très préoccupée face à cette situation."),
    row("drama de femme",
        "réaction émotionnelle",
        tags="gender|emotion", category="emotion",
        ex_biased="C'est encore un drama de femme.",
        ex_neutral="C'est une réaction émotionnelle à une situation difficile."),
    row("les femmes sont irrationnelles",
        "tout le monde peut manquer de recul",
        tags="gender|emotion", category="emotion",
        ex_biased="Les femmes sont irrationnelles sous la pression.",
        ex_neutral="Tout le monde peut manquer de recul sous la pression."),

    # ── SEXUALITY ─────────────────────────────────────────────────────────────
    row("elle a dû coucher pour",
        "elle a travaillé dur pour",
        tags="gender|sexuality", category="sexuality",
        ex_biased="Elle a dû coucher pour obtenir ce poste.",
        ex_neutral="Elle a travaillé dur pour obtenir ce poste."),
    row("une fille facile",
        "une personne",
        tags="gender|sexuality", category="sexuality",
        ex_biased="On dit que c'est une fille facile.",
        ex_neutral="On devrait respecter toutes les personnes."),
    row("elle se donne en spectacle",
        "elle s'exprime",
        tags="gender|sexuality", category="sexuality",
        severity="warn",
        ex_biased="Avec cette tenue, elle se donne en spectacle.",
        ex_neutral="Elle s'exprime librement dans sa façon de se vêtir."),
    row("les femmes utilisent leur charme",
        "les personnes utilisent leurs atouts",
        tags="gender|sexuality", category="sexuality",
        ex_biased="Les femmes utilisent leur charme pour avancer.",
        ex_neutral="Les personnes utilisent leurs atouts professionnels pour avancer."),

    # ── VIOLENCE / SAFETY ─────────────────────────────────────────────────────
    row("elle l'a provoqué",
        "il a commis une violence",
        tags="gender|violence", category="violence",
        ex_biased="Elle l'a provoqué, donc il a réagi.",
        ex_neutral="Il a commis une violence, indépendamment du comportement d'autrui."),
    row("elle portait une tenue provocante",
        "elle portait une tenue",
        tags="gender|violence", category="violence",
        ex_biased="Elle portait une tenue provocante lors de l'agression.",
        ex_neutral="Elle portait une tenue lors de l'agression, qui reste inexcusable."),
    row("les violences conjugales",
        "les violences conjugales",
        tags="gender|violence", category="violence",
        severity="warn",
        ex_biased="Les violences conjugales, c'est souvent des deux côtés.",
        ex_neutral="Les violences conjugales sont majoritairement exercées contre les femmes."),
    row("elle avait bu",
        "il a commis une agression",
        tags="gender|violence", category="violence",
        context_pattern=r"\b(agression|viol|harcèlement|violence)\b",
        ex_biased="Elle avait bu lors de l'agression.",
        ex_neutral="Il a commis une agression — le comportement de la victime n'est pas en cause."),
]


def main():
    existing = []
    with open(ROOT / "rules/lexicon_fr_v3.csv", newline="", encoding="utf-8") as f:
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
    cats = Counter(r.get("stereotype_category", "") for r in deduped if r.get("language") == "fr")
    print("Category distribution:", dict(cats.most_common()))

    out = ROOT / "rules/lexicon_fr_v4.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for r in deduped:
            writer.writerow({k: r.get(k, "") for k in HEADER})

    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
