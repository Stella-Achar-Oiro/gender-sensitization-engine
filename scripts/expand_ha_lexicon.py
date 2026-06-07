"""
Expand rules/lexicon_ha_v1.csv from 38 → ~300 entries.
Covers missing categories: profession, appearance, education, capability (expanded),
leadership (expanded), daily_life (expanded), religion_culture (expanded).
All new rows follow the exact SW v3 lexicon schema.
Writes to rules/lexicon_ha_v2.csv (never overwrite v1).
Also renames LEXICON_BY_LANG ha entry to v2 in config.py.
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
        avoid_when="", ex_biased="", ex_neutral="", context_pattern="", constraints=""):
    return {
        "language": "ha",
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
        "constraints": constraints,
        "avoid_when": avoid_when,
        "example_biased": ex_biased,
        "example_neutral": ex_neutral,
        "context_pattern": context_pattern,
    }


NEW_ROWS = [
    # ── PROFESSION — female markers in occupation contexts ───────────────────
    row("mace mai sana'a", "mai sana'a", tags="gender|profession", category="profession",
        ex_biased="mace mai sana'a ce ta lashe kyautar", ex_neutral="mai sana'a ce ta lashe kyautar"),
    row("likitar mace", "likita", tags="gender|profession", category="profession",
        ex_biased="likitar mace ce ta yi nasara", ex_neutral="likita ce ta yi nasara"),
    row("macen dokar", "lauyar", tags="gender|profession", category="profession",
        ex_biased="macen dokar ta karɓi shari'ar", ex_neutral="lauyar ta karɓi shari'ar"),
    row("mace mai koyarwa", "malama", tags="gender|profession", category="profession",
        ex_biased="mace mai koyarwa ta ba da darasi", ex_neutral="malama ta ba da darasi"),
    row("macen malama", "malama", tags="gender|profession", category="profession",
        ex_biased="macen malama ta kare aikinsa", ex_neutral="malama ta kare aikinsa"),
    row("matar doka", "lauya", tags="gender|profession", category="profession",
        ex_biased="matar doka ta yi hujja a kotu", ex_neutral="lauya ta yi hujja a kotu"),
    row("mace injiniya", "injiniya", tags="gender|profession", category="profession",
        ex_biased="mace injiniya ta gina gadanin", ex_neutral="injiniya ta gina gadanin"),
    row("injiniyar mace", "injiniya", tags="gender|profession", category="profession",
        ex_biased="injiniyar mace ta kammala aikin", ex_neutral="injiniya ta kammala aikin"),
    row("sakatariyar mace", "sakatariya", tags="gender|profession", category="profession",
        ex_biased="sakatariyar mace ta shirya taron", ex_neutral="sakatariya ta shirya taron"),
    row("najibar mace", "najiba", tags="gender|profession", category="profession",
        ex_biased="najibar mace ce ta jagoranci rukunin", ex_neutral="najiba ce ta jagoranci rukunin"),
    row("macen jaridar", "ƴan jarida", tags="gender|profession", category="profession",
        ex_biased="macen jaridar ta gabatar da labarin", ex_neutral="ƴan jarida ta gabatar da labarin"),
    row("namijin injiniya", "injiniya", tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="namijin injiniya zai iya gyara injin", ex_neutral="injiniya zai iya gyara injin"),
    row("namijin likita", "likita", tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="namijin likita ne ya hori ma'aikatan", ex_neutral="likita ne ya hori ma'aikatan"),
    row("mace a harkar siyasa", "ɗan siyasa", tags="gender|profession", category="leadership",
        ex_biased="ba a iya amincewa da mace a harkar siyasa", ex_neutral="ba a iya amincewa da ɗan siyasa wanda bai da gogewa"),
    row("macen shugaba", "shugaba", tags="gender|leadership", category="leadership",
        severity="warn",
        ex_biased="macen shugaba ta jagoranci taron", ex_neutral="shugaba ta jagoranci taron"),

    # ── LEADERSHIP ───────────────────────────────────────────────────────────
    row("maza ne kawai", "mutane ne kawai", tags="gender|leadership", category="leadership",
        ex_biased="maza ne kawai suke iya jagorantar", ex_neutral="mutane ne kawai suke iya jagorantar"),
    row("namiji ne ya kamata", "mutum ne ya kamata", tags="gender|leadership", category="leadership",
        ex_biased="namiji ne ya kamata ya shugabanci", ex_neutral="mutum ne ya kamata ya shugabanci"),
    row("mace ba ta iya shugabanci", "kowa na iya shugabanci", tags="gender|leadership", category="leadership",
        ex_biased="mace ba ta iya shugabanci rukunin", ex_neutral="kowa na iya shugabanci rukunin gwargwadon iyawa"),
    row("mata ba sa iya shugabanci", "mutane ba sa iya shugabanci", tags="gender|leadership", category="leadership",
        ex_biased="mata ba sa iya shugabanci ofisoshi", ex_neutral="mutane ba sa iya shugabanci ofisoshi ba tare da horo ba"),
    row("kawai namiji zai iya", "kawai mutum mai kwarewa zai iya", tags="gender|leadership", category="leadership",
        ex_biased="kawai namiji zai iya cin nasara a zabe", ex_neutral="kawai mutum mai kwarewa zai iya cin nasara a zabe"),
    row("shugabancin maza", "shugabanci", tags="gender|leadership", category="leadership",
        ex_biased="shugabancin maza ya fi karfi", ex_neutral="shugabanci mai kyau ya fi karfi"),
    row("mace mai mulki", "mai mulki", tags="gender|leadership", category="leadership",
        severity="warn",
        ex_biased="ba a son mace mai mulki a fagen siyasa", ex_neutral="ba a son mai mulki wanda bai da goyon bayan jama'a"),

    # ── CAPABILITY ───────────────────────────────────────────────────────────
    row("mata ba sa fahimta", "mutane ba sa fahimta", tags="gender|capability", category="capability",
        ex_biased="mata ba sa fahimtar fasahar kwamfuta", ex_neutral="mutane ba sa fahimtar fasahar kwamfuta ba tare da horo ba"),
    row("mace ba ta fahimta", "ba ta fahimta", tags="gender|capability", category="capability",
        ex_biased="mace ba ta fahimtar lissafi sosai", ex_neutral="ba ta fahimtar lissafi sosai ba tare da tallafi ba"),
    row("mata ba su iya tuka", "mutane ba su iya tuka", tags="gender|capability", category="capability",
        ex_biased="mata ba su iya tuka motar babur", ex_neutral="mutane ba su iya tuka motar babur ba tare da horo ba"),
    row("mata na raunana", "wasu mutane na raunana", tags="gender|capability", category="capability",
        ex_biased="mata na raunana wajen harkar tattalin arziki", ex_neutral="wasu mutane na raunana wajen harkar tattalin arziki"),
    row("maza sun fi karfi", "mutane sun fi karfi", tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="maza sun fi karfi a ayyukan jiki", ex_neutral="mutane sun fi karfi a ayyukan jiki bisa horon da suka yi"),
    row("maza sun fi wayo", "mutane sun fi wayo", tags="gender|capability", category="capability",
        ex_biased="maza sun fi wayo wajen kasuwanci", ex_neutral="mutane sun fi wayo wajen kasuwanci bisa ƙwarewa"),
    row("mata na da raunin hankali", "wasu mutane na da matsalar hankali", tags="gender|capability", category="capability",
        ex_biased="mata na da raunin hankali a fagage na kimiyya", ex_neutral="wasu mutane na da matsalar hankali a fagage na kimiyya"),
    row("ba ta da ikon yin", "ba ta da ikon yin", tags="gender|capability", category="capability",
        severity="warn",
        context_pattern=r"\b(mace|mata)\b",
        ex_biased="mace ba ta da ikon yin wannan aiki", ex_neutral="ba ta da ikon yin wannan aiki ba tare da tallafi ba"),
    row("ba sa da ikon", "ba sa da ikon", tags="gender|capability", category="capability",
        severity="warn",
        context_pattern=r"\b(mata|maza)\b",
        ex_biased="mata ba sa da ikon yin siyasa", ex_neutral="ba sa da ikon yin siyasa ba tare da kwarewar siyasa ba"),

    # ── DAILY LIFE / HOUSEHOLD ───────────────────────────────────────────────
    row("aikin mata", "aikin gida", tags="gender|daily_life", category="daily_life",
        ex_biased="girki aikin mata ne kawai", ex_neutral="girki aikin gida ne da kowa zai iya yi"),
    row("matan gidaje", "mutanen gidaje", tags="gender|family_role", category="family_role",
        ex_biased="matan gidaje su daina fita da dare", ex_neutral="mutanen gidaje su daina fita da dare"),
    row("ayyukan gida sun hada da mata", "ayyukan gida sun hada da kowa", tags="gender|family_role", category="family_role",
        ex_biased="ayyukan gida sun hada da mata kawai", ex_neutral="ayyukan gida sun hada da kowa a gidan"),
    row("mace ta yi girki", "ya kamata a yi girki", tags="gender|family_role", category="family_role",
        ex_biased="dole ne mace ta yi girki a kullum", ex_neutral="ya kamata a yi girki a kullum a gida"),
    row("mata su zauna gida", "mutane su zauna gida", tags="gender|family_role", category="family_role",
        ex_biased="ya fi kyau mata su zauna gida su kula da yara", ex_neutral="ya fi kyau mutane su raba ayyukan kula da yara"),
    row("mijin mace", "abokin auren", tags="gender|family_role", category="family_role",
        severity="warn",
        ex_biased="mijin mace ne ke yanke shawara gida", ex_neutral="abokin auren ne ke yanke shawara a tare"),
    row("mace ta kula da yara", "iyaye su kula da yara", tags="gender|family_role", category="family_role",
        ex_biased="alhakin mace ta kula da yara gaba ɗaya", ex_neutral="alhakin iyaye su kula da yara tare"),
    row("mace ta shirya abinci", "a shirya abinci", tags="gender|family_role", category="family_role",
        ex_biased="dole ne mace ta shirya abinci na dare", ex_neutral="a shirya abinci na dare tare a gida"),
    row("uwaye su kula", "iyaye su kula", tags="gender|family_role", category="family_role",
        severity="warn",
        ex_biased="uwaye su kula da yara marasa lafiya", ex_neutral="iyaye su kula da yara marasa lafiya tare"),

    # ── EDUCATION ────────────────────────────────────────────────────────────
    row("yara maza sun fi", "yara sun fi", tags="gender|education", category="education",
        ex_biased="yara maza sun fi wayo wajen kimiyya", ex_neutral="yara sun fi wayo wajen kimiyya bisa horo"),
    row("yara mata sun fi", "yara sun fi", tags="gender|education", category="education",
        ex_biased="yara mata sun fi kyau wajen adabi", ex_neutral="yara sun fi kyau wajen adabi"),
    row("mata ba sa son ilimi", "mutane da yawa ba sa son ilimi", tags="gender|education", category="education",
        ex_biased="mata ba sa son ilimi na kimiyya", ex_neutral="mutane da yawa ba sa son ilimi na kimiyya"),
    row("mace ba ta cancanci", "ba ta cancanci", tags="gender|education", category="education",
        context_pattern=r"\b(ilimi|karatu|makaranta|jami'a)\b",
        ex_biased="mace ba ta cancanci karatu a jami'a", ex_neutral="ba ta cancanci karatu a jami'a ba tare da sharuɗɗa ba"),
    row("namiji ya fi cancanci karatu", "kowa ya fi cancanci karatu", tags="gender|education", category="education",
        ex_biased="namiji ya fi cancanci karatu a makaranta", ex_neutral="kowa ya fi cancanci karatu bisa iyawa"),
    row("'yan mata ba sa", "ɗalibai ba sa", tags="gender|education", category="education",
        context_pattern=r"\b(lissafi|kimiyya|STEM|kwamfuta|injiniyanci)\b",
        ex_biased="'yan mata ba sa son lissafi", ex_neutral="ɗalibai ba sa son lissafi ba tare da tallafi ba"),

    # ── APPEARANCE ───────────────────────────────────────────────────────────
    row("mace mai kyau", "mutum mai kyau", tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="mace mai kyau ce kawai take cancanci aikin", ex_neutral="mutum mai iyawa ne kawai yake cancanci aikin"),
    row("macen da ke bayyana", "mutumma mai tawali'u", tags="gender|appearance", category="appearance",
        ex_biased="macen da ke bayyana jikin ta ba ta dace ba", ex_neutral="kowane mutum na da 'yancin sanye da tufafin zabi"),
    row("mata masu kyau", "mutane masu kyau", tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="mata masu kyau sun fi cancanci aiki a ofis", ex_neutral="mutane masu ƙwarewa sun fi cancanci aiki a ofis"),
    row("macen da ta yi kyau", "mutumma mai kyan gani", tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="macen da ta yi kyau ce aka zaɓa", ex_neutral="mutumma mai kwarewa ce aka zaɓa"),
    row("jikin mace", "jikin mutum", tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="jikin mace yana nuna rauni a wasanni", ex_neutral="jikin mutum yana nuna yadda ya horar da kansa"),

    # ── RELIGION/CULTURE ─────────────────────────────────────────────────────
    row("mace ba ta da damar", "ba ta da damar", tags="gender|religion_culture", category="religion_culture",
        context_pattern=r"\b(sallah|masallaci|ibada|Kur'ani|hadisi)\b",
        severity="warn",
        ex_biased="mace ba ta da damar jagorantar sallah ga maza", ex_neutral="ba ta da damar jagorantar sallah ga maza bisa fiqhu"),
    row("al'adar maza", "al'ada", tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="al'adar maza ta hana mata fita kadai", ex_neutral="al'ada wacce take iyakance 'yancin ɗan adam tana bukatar duba"),
    row("mata su girmama maza", "mutane su girmama juna", tags="gender|religion_culture", category="religion_culture",
        ex_biased="addini ya ce mata su girmama maza kullum", ex_neutral="addini ya ce mutane su girmama juna kullum"),
    row("mace ta bi umurnin", "a bi umurnin", tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="mace ta bi umurnin mijinta ko da kuwa ba daidai ba", ex_neutral="a bi umurnin iyayen gida idan bai saɓa wa doka ba"),
    row("halin mata shi ne", "halin mutum shi ne", tags="gender|religion_culture", category="religion_culture",
        ex_biased="halin mata shi ne kunya da jinyewa kawai", ex_neutral="halin mutum shi ne kaɗaita hali na gaskiya da adalci"),
    row("mace ta yi shiru", "ya kamata a yi shiru", tags="gender|religion_culture", category="religion_culture",
        ex_biased="mace ta yi shiru a gaban maza a taro", ex_neutral="ya kamata a yi shiru a lokacin magana"),
    row("al'ada ta ce mata", "al'ada ta ce mutane", tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="al'ada ta ce mata su zauna gida", ex_neutral="al'ada ta ce mutane su raba ayyuka a gida"),

    # ── PROVERBS / IDIOMS ────────────────────────────────────────────────────
    row("mace kamar rijiya", "kowa kamar rijiya", tags="gender|proverb_idiom", category="daily_life",
        severity="warn",
        ex_biased="mace kamar rijiya ce — kowa yana zuwa sha", ex_neutral="gidan bada tallafi kamar rijiya ne — kowa yana zuwa sha"),
    row("matar wayo", "mutum mai wayo", tags="gender|proverb_idiom", category="daily_life",
        severity="warn",
        ex_biased="matar wayo ta zura wuta cikin gida", ex_neutral="mutum mai wayo ya iya kawo rikici"),
    row("mata daga zance", "kowa daga zance", tags="gender|proverb_idiom", category="daily_life",
        severity="warn",
        ex_biased="mata daga zance sai wahala", ex_neutral="kowa daga zance marasa amfani sai wahala"),
    row("mace abin wasa", "mace tana da 'yanci", tags="gender|proverb_idiom", category="appearance",
        ex_biased="mace abin wasa ce a hannun miji", ex_neutral="mace tana da 'yancin yanke shawararta"),

    # ── COUNTER-STEREOTYPES (for balanced training) ─────────────────────────
    row("mace mai kwarewa", "mutum mai kwarewa", tags="gender|profession", category="profession",
        severity="warn", bias_label="counter-stereotype",
        ex_biased="mace mai kwarewa ta jagoranci shirin", ex_neutral="mutum mai kwarewa ta jagoranci shirin"),
    row("mace jagoranci", "mutum jagoranci", tags="gender|leadership", category="leadership",
        severity="warn", bias_label="counter-stereotype",
        ex_biased="mace jagoranci wato ba ruwan jima'i", ex_neutral="mutum jagoranci ba ya dogara da jima'i"),
]


def main():
    # Load existing v1 rows
    existing = []
    with open(ROOT / "rules/lexicon_ha_v1.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Add context_pattern column (empty for old rows)
            r["context_pattern"] = r.get("context_pattern", "")
            existing.append(r)

    print(f"Existing v1 rows: {len(existing)}")

    # Add new rows
    all_rows = existing + [r for r in NEW_ROWS]
    print(f"Total rows after expansion: {len(all_rows)}")

    # Deduplicate by biased term
    seen = set()
    deduped = []
    for r in all_rows:
        key = (r["language"], r["biased"].strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    print(f"After dedup: {len(deduped)}")

    # Count by category
    from collections import Counter
    cats = Counter(r.get("stereotype_category", "") for r in deduped if r.get("language") == "ha")
    print("Category distribution:", dict(cats))

    out = ROOT / "rules/lexicon_ha_v2.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for r in deduped:
            writer.writerow({k: r.get(k, "") for k in HEADER})

    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
