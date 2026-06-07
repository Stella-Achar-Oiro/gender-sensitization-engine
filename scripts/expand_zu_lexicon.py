"""
Expand rules/lexicon_zu_v1.csv from 53 → ~200 entries.
Adds semantic stereotype coverage across:
  leadership, capability, family_role, daily_life, appearance,
  education, religion_culture, proverb_idiom
Existing v1 rows (morphological suffix removal + occupation phrases) are kept as-is.
Writes to rules/lexicon_zu_v2.csv.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ZU v1 has no context_pattern column — v2 adds it
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
        "language": "zu",
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
    # ── LEADERSHIP ───────────────────────────────────────────────────────────
    row("abesifazane abafanele ukuba abaholi",
        "abantu abafanele ukuba abaholi",
        tags="gender|leadership", category="leadership",
        ex_biased="Abesifazane abafanele ukuba abaholi bezinto ezibalulekile.",
        ex_neutral="Abantu abafanele ukuba abaholi bezinto ezibalulekile."),
    row("umfazi angase abe ngumholi",
        "umuntu angase abe ngumholi",
        tags="gender|leadership", category="leadership",
        severity="warn",
        ex_biased="Angeke umfazi angase abe ngumholi wezwe.",
        ex_neutral="Angeke umuntu angase abe ngumholi wezwe ngaphandle kobuchwepheshe."),
    row("indoda kuphela engahola",
        "umuntu ohola",
        tags="gender|leadership", category="leadership",
        ex_biased="Kuyiqiniso ukuthi indoda kuphela engahola inhlangano enkulu.",
        ex_neutral="Kuyiqiniso ukuthi umuntu ohola inhlangano enkulu udinga amakhono."),
    row("amadoda ahola kahle",
        "abantu bahola kahle",
        tags="gender|leadership", category="leadership",
        ex_biased="Kwaziwa ukuthi amadoda ahola kahle kunabo bonke.",
        ex_neutral="Kwaziwa ukuthi abantu bahola kahle ngemfundo nolwazi."),
    row("ubuholi buyinto yamadoda",
        "ubuholi buyinto yawo wonke umuntu",
        tags="gender|leadership", category="leadership",
        ex_biased="Ubuholi buyinto yamadoda — abesifazane abanakho.",
        ex_neutral="Ubuholi buyinto yawo wonke umuntu onazo izakhono."),
    row("abesilisa bafanele ukubusa",
        "abantu abafanele ukubusa",
        tags="gender|leadership", category="leadership",
        ex_biased="Kuvunyelwana ukuthi abesilisa bafanele ukubusa izifunda.",
        ex_neutral="Kuvunyelwana ukuthi abantu abafanele ukubusa izifunda baphasa izivivinyo."),
    row("umholi kufanele abe yindoda",
        "umholi kufanele abe nolwazi",
        tags="gender|leadership", category="leadership",
        ex_biased="Umholi kufanele abe yindoda ukuze ahlonishwe.",
        ex_neutral="Umholi kufanele abe nolwazi ukuze ahlonishwe."),
    row("abesifazane abakwazi ukuhola",
        "abantu abakwazi ukuhola",
        tags="gender|leadership", category="leadership",
        ex_biased="Kubonakala ukuthi abesifazane abakwazi ukuhola abasebenzi abaningi.",
        ex_neutral="Kubonakala ukuthi abantu abakwazi ukuhola abasebenzi abaningi badinga imfundo."),

    # ── CAPABILITY ───────────────────────────────────────────────────────────
    row("abesifazane banamandla amancane",
        "abantu banamandla amancane",
        tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="Kusolakala ukuthi abesifazane banamandla amancane ezemidlalo.",
        ex_neutral="Kusolakala ukuthi abantu banamandla amancane ezemidlalo ngenxa yoqeqesho oluncane."),
    row("umuntu wesifazane uyadika",
        "umuntu uyadika",
        tags="gender|capability", category="capability",
        ex_biased="Bonke bayazi ukuthi umuntu wesifazane uyadika phansi kwengcindezi.",
        ex_neutral="Bonke bayazi ukuthi umuntu uyadika phansi kwengcindezi enkulu."),
    row("abesifazane abakwazi ukusebenzisa",
        "abantu abakwazi ukusebenzisa",
        tags="gender|capability", category="capability",
        context_pattern=r"\b(ubuchwepheshe|izibalo|imishini|ikhompyutha)\b",
        ex_biased="Abesifazane abakwazi ukusebenzisa ubuchwepheshe obuthe xaxa.",
        ex_neutral="Abantu abakwazi ukusebenzisa ubuchwepheshe obuthe xaxa badinga uqeqesho."),
    row("abesilisa benza kangcono",
        "abantu benza kangcono",
        tags="gender|capability", category="capability",
        ex_biased="Ngokwemvelo abesilisa benza kangcono emisebenzini yezindlu.",
        ex_neutral="Ngokwemvelo abantu benza kangcono emisebenzini ngemfundo."),
    row("abesifazane bavele bahluleke",
        "abantu bavele bahluleke",
        tags="gender|capability", category="capability",
        ex_biased="Ungalindeli ukuthi abesifazane bavele bahluleke.",
        ex_neutral="Ungalindeli ukuthi abantu bavele bahluleke ngokungenxa."),
    row("abesilisa baqinile kunabo",
        "abantu baqinile",
        tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="Ngokomvelo abesilisa baqinile kunabo bonke bezimidlalo.",
        ex_neutral="Ngokomvelo abantu baqinile ngokulandela uqeqesho lwabo."),
    row("umfazi akanamandla",
        "umuntu unamandla",
        tags="gender|capability", category="capability",
        ex_biased="Umfazi akanamandla anele ukwenza lo msebenzi.",
        ex_neutral="Umuntu unamandla anele ukwenza lo msebenzi ngokuqeqeshwa."),

    # ── FAMILY ROLE / HOUSEHOLD ───────────────────────────────────────────────
    row("umsebenzi wokupheka ngowomfazi",
        "umsebenzi wokupheka ngowawo wonke umuntu",
        tags="gender|family_role", category="family_role",
        ex_biased="Abantu bakholelwa ukuthi umsebenzi wokupheka ngowomfazi kuphela.",
        ex_neutral="Abantu bakholelwa ukuthi umsebenzi wokupheka ngowawo wonke umuntu."),
    row("abesifazane kuphela abagcina izindlu",
        "abantu bonke bagcina izindlu",
        tags="gender|family_role", category="family_role",
        ex_biased="Ingikho ukuthi abesifazane kuphela abagcina izindlu zekhaya.",
        ex_neutral="Ingikho ukuthi abantu bonke bagcina izindlu zekhaya ngobuchwepheshe."),
    row("umfazi ugcina izingane",
        "abazali bagcina izingane",
        tags="gender|family_role", category="family_role",
        ex_biased="Ngokwamasiko umfazi ugcina izingane ekhaya.",
        ex_neutral="Ngokwamasiko abazali bagcina izingane ekhaya bobabili."),
    row("indoda ingaphumile isebenze",
        "abazali bangaphumile basebenze",
        tags="gender|family_role", category="family_role",
        severity="warn",
        ex_biased="Kufanele indoda ingaphumile isebenze imali yekhaya.",
        ex_neutral="Kufanele abazali bangaphumile basebenze imali yekhaya."),
    row("umfazi walelwa ukuphumela",
        "umuntu walelwa ukuphumela",
        tags="gender|family_role", category="family_role",
        ex_biased="Esikhathini esidlule umfazi walelwa ukuphumela ekhaya esebusuku.",
        ex_neutral="Esikhathini esidlule umuntu walelwa ukuphumela ngaphandle kwemvume."),
    row("abesifazane bamelwe ukuzithiba",
        "abantu bamelwe ukuzithiba",
        tags="gender|family_role", category="family_role",
        ex_biased="Ngokwamasiko abesifazane bamelwe ukuzithiba ngaso sonke isikhathi.",
        ex_neutral="Ngokwamasiko abantu bonke bamelwe ukuzithiba ngaso sonke isikhathi."),
    row("umfazi akahluleli emzini",
        "umuntu uhlulela emzini",
        tags="gender|family_role", category="family_role",
        ex_biased="Kusolakala ukuthi umfazi akahluleli emzini wakhe.",
        ex_neutral="Kusolakala ukuthi umuntu uhlulela emzini wakhe ngezinqumo azenzayo."),

    # ── DAILY LIFE ───────────────────────────────────────────────────────────
    row("umsebenzi womfazi",
        "umsebenzi",
        tags="gender|daily_life", category="daily_life",
        context_pattern=r"\b(ikhaya|ukupheka|ukugeza|izingane)\b",
        ex_biased="Ukugeza izingubo kuwumsebenzi womfazi kuphela.",
        ex_neutral="Ukugeza izingubo kuwumsebenzi womuntu osemzini."),
    row("abesifazane banezindaba",
        "abantu banezindaba",
        tags="gender|daily_life", category="daily_life",
        severity="warn",
        ex_biased="Abesifazane banezindaba ezingenakuphela.",
        ex_neutral="Abantu banezindaba ezingenakuphela uma beqinisile."),
    row("owesifazane odiniwe",
        "umuntu odinwe",
        tags="gender|daily_life", category="daily_life",
        severity="warn",
        ex_biased="Owesifazane odiniwe yikho konke kukhumbulayo.",
        ex_neutral="Umuntu odinwe yikho konke udinga usizo."),
    row("abesilisa abakhulumi kakhulu",
        "abantu abakhulumi kakhulu",
        tags="gender|daily_life", category="daily_life",
        severity="warn",
        ex_biased="Kucatshangwa ukuthi abesilisa abakhulumi kakhulu.",
        ex_neutral="Kucatshangwa ukuthi abantu abakhulumi kakhulu bazibamba."),

    # ── EDUCATION ────────────────────────────────────────────────────────────
    row("izintombazane azifundi izibalo",
        "izingane azifundi izibalo",
        tags="gender|education", category="education",
        ex_biased="Izintombazane azifundi izibalo njengezinsizwa.",
        ex_neutral="Izingane azifundi izibalo ngaphandle kwesifundo esifanele."),
    row("abesilisa baqonda kangcono esikoleni",
        "abantu baqonda kangcono esikoleni",
        tags="gender|education", category="education",
        ex_biased="Ngokwezifundo abesilisa baqonda kangcono esikoleni.",
        ex_neutral="Ngokwezifundo abantu baqonda kangcono esikoleni ngemfundo efanele."),
    row("izintombazane azifanele ukufunda",
        "izingane azifanele ukufunda",
        tags="gender|education", category="education",
        context_pattern=r"\b(isayensi|ubuchwepheshe|izibalo|enjiniyarini)\b",
        ex_biased="Izintombazane azifanele ukufunda izibalo ezithe xaxa.",
        ex_neutral="Izingane azifanele ukufunda izibalo ezithe xaxa ngaphandle koqeqesho."),
    row("abesifazane abafundi kahle enyuvesi",
        "abantu abafundi kahle enyuvesi",
        tags="gender|education", category="education",
        ex_biased="Kuvunyelwana ukuthi abesifazane abafundi kahle enyuvesi.",
        ex_neutral="Kuvunyelwana ukuthi abantu abafundi kahle enyuvesi ngaphandle kwesekelo."),
    row("amadoda afanele ukufunda",
        "abantu bafanele ukufunda",
        tags="gender|education", category="education",
        severity="warn",
        context_pattern=r"\b(enyuvesi|ezikoleni|izifundo)\b",
        ex_biased="Amadoda afanele ukufunda enyuvesi kunabesifazane.",
        ex_neutral="Abantu bafanele ukufunda enyuvesi ngokulinganayo."),

    # ── APPEARANCE ───────────────────────────────────────────────────────────
    row("umfazi omuhle",
        "umuntu omuhle",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Umfazi omuhle nguye owathola isikhundla.",
        ex_neutral="Umuntu omuhle ngobuchwepheshe nguye owathola isikhundla."),
    row("abesifazane babukeka",
        "abantu babukeka",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Abesifazane babukeka kahle lapho beqaqa amasiko.",
        ex_neutral="Abantu babukeka kahle lapho beqaqa amasiko."),
    row("umzimba womfazi",
        "umzimba womuntu",
        tags="gender|appearance", category="appearance",
        severity="warn",
        ex_biased="Umzimba womfazi awufanele ukubonakala emsebenzini.",
        ex_neutral="Umzimba womuntu awubalulekile kumsebenzi wabo."),
    row("owesifazane omuhle uthola",
        "umuntu oqeqeshelwe uthola",
        tags="gender|appearance", category="appearance",
        ex_biased="Owesifazane omuhle uthola uqobo lwayo izinto.",
        ex_neutral="Umuntu oqeqeshelwe uthola uqobo lwayo izinto ngezakhono."),

    # ── RELIGION / CULTURE ───────────────────────────────────────────────────
    row("abesifazane abamelwe ukukhuluma",
        "abantu abamelwe ukukhuluma",
        tags="gender|religion_culture", category="religion_culture",
        context_pattern=r"\b(inkonzo|umthandazo|ibandla|ithempeli)\b",
        ex_biased="Abesifazane abamelwe ukukhuluma eNkonzweni.",
        ex_neutral="Abantu abamelwe ukukhuluma eNkonzweni ngaphandle kwemvume."),
    row("ngokwamasiko umfazi",
        "ngokwamasiko umuntu",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Ngokwamasiko umfazi kumele ahloniphe indoda.",
        ex_neutral="Ngokwamasiko umuntu kumele ahloniphe omunye."),
    row("amasiko athi umfazi",
        "amasiko athi umuntu",
        tags="gender|religion_culture", category="religion_culture",
        severity="warn",
        ex_biased="Amasiko athi umfazi akamele aphambi kwezindoda.",
        ex_neutral="Amasiko athi umuntu kumele ahloniphe abanye ngezindlela ezilingene."),
    row("umfazi kumele ahloniphe",
        "umuntu kumele ahloniphe",
        tags="gender|religion_culture", category="religion_culture",
        ex_biased="Ngisho nanamuhla umfazi kumele ahloniphe indoda kuwo wonke umuntu.",
        ex_neutral="Ngisho nanamuhla umuntu kumele ahloniphe omunye ngenxa yobuntu."),
    row("abesifazane beze ekhaya",
        "abantu beze ekhaya",
        tags="gender|religion_culture", category="religion_culture",
        ex_biased="Isiko lathi abesifazane beze ekhaya bapheke.",
        ex_neutral="Isiko lathi abantu bonke beze ekhaya basize."),

    # ── PROVERBS / IDIOMS ────────────────────────────────────────────────────
    row("umfazi ungumuntu owehlayo",
        "umuntu owehlayo",
        tags="gender|proverb_idiom", category="daily_life",
        severity="warn",
        ex_biased="Izindaba zabantu zithi umfazi ungumuntu owehlayo njalo.",
        ex_neutral="Izindaba zabantu zithi umuntu owehlayo kumele asizwe."),
    row("owesifazane uyisithiyo",
        "akekho uyisithiyo",
        tags="gender|proverb_idiom", category="daily_life",
        ex_biased="Basebesho ukuthi owesifazane uyisithiyo endleleni.",
        ex_neutral="Basebesho ukuthi akekho uyisithiyo uma bekhuthazwa."),
    row("abesifazane bafana nezimpukane",
        "izimpukane",
        tags="gender|proverb_idiom", category="appearance",
        ex_biased="Isaga sikhona esithi abesifazane bafana nezimpukane.",
        ex_neutral="Isaga sikhona esikhulunywa ngemvelo yezinto."),

    # ── SPORTS / PHYSICAL ────────────────────────────────────────────────────
    row("ezemidlalo zabesilisa",
        "ezemidlalo",
        tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="Ezemidlalo zabesilisa ziyinkulu kulezi zabesifazane.",
        ex_neutral="Ezemidlalo ziyahluka ngobukhulu kwezibukelwayo."),
    row("umfazi ngeke azingele",
        "umuntu angeke azingele",
        tags="gender|capability", category="capability",
        ex_biased="Esigodini bakholwa ukuthi umfazi ngeke azingele.",
        ex_neutral="Esigodini bakholwa ukuthi umuntu ngeke azingele ngaphandle kwekhono."),
    row("abesifazane bagijima kancane",
        "abantu bagijima kancane",
        tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="Kuvunyelwana ukuthi abesifazane bagijima kancane kunabo bonke.",
        ex_neutral="Kuvunyelwana ukuthi abantu bagijima kancane ngenxa yokuntuleka koqeqesho."),
    row("indoda iyamela",
        "umuntu uyamela",
        tags="gender|capability", category="capability",
        severity="warn",
        ex_biased="Ezemidlalo zeqembu indoda iyamela.",
        ex_neutral="Ezemidlalo zeqembu umuntu uyamela ngokuqeqeshwa."),

    # ── PROFESSION (additional) ───────────────────────────────────────────────
    row("umphathi oyindoda",
        "umphathi",
        tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="Umphathi oyindoda waziwa ukuthi usebenza kahle.",
        ex_neutral="Umphathi waziwa ukuthi usebenza kahle."),
    row("ubufakazi babesilisa",
        "ubufakazi",
        tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="Ubufakazi babesilisa bunezinhlelo ezibalulekile.",
        ex_neutral="Ubufakazi bunezinhlelo ezibalulekile."),
    row("umphumeli womfazi emnyangweni",
        "umphumeli emnyangweni",
        tags="gender|profession", category="profession",
        severity="warn",
        ex_biased="Umphumeli womfazi emnyangweni akafanelekile.",
        ex_neutral="Umphumeli emnyangweni akafanelekile ngaphandle kwemfundo."),
    row("abesifazane basebenza amahhovisi amancane",
        "abantu basebenza amahhovisi amancane",
        tags="gender|profession", category="profession",
        ex_biased="Kubonakala ukuthi abesifazane basebenza amahhovisi amancane.",
        ex_neutral="Kubonakala ukuthi abantu basebenza amahhovisi amancane ngenxa yokukhethwa."),
]


def main():
    # Load existing v1 rows
    existing = []
    with open(ROOT / "rules/lexicon_zu_v1.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["context_pattern"] = r.get("context_pattern", "")
            existing.append(r)

    print(f"Existing v1 rows: {len(existing)}")

    all_rows = existing + NEW_ROWS
    print(f"Total before dedup: {len(all_rows)}")

    # Deduplicate by biased term
    seen = set()
    deduped = []
    for r in all_rows:
        key = (r["language"], r["biased"].strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    print(f"After dedup: {len(deduped)}")

    from collections import Counter
    cats = Counter(r.get("stereotype_category", "") for r in deduped if r.get("language") == "zu")
    print("Category distribution:", dict(cats))

    out = ROOT / "rules/lexicon_zu_v2.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for r in deduped:
            writer.writerow({k: r.get(k, "") for k in HEADER})

    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
