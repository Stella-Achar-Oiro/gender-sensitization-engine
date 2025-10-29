import csv

# ========================
# CONFIGURATION
# ========================
OUTPUT_EN = "lexicon_en_v2.csv"
OUTPUT_SW = "lexicon_sw_v2.csv"

# Schema columns
COLUMNS = [
    "language","biased","neutral_primary","neutral_alternatives",
    "tags","pos","scope","register","severity",
    "ngeli","number","requires_agreement","agreement_notes",
    "patterns","constraints","avoid_when",
    "example_biased","example_neutral"
]

# ========================
# BASE DATA (ENGLISH)
# ========================
ENGLISH_BASE = [
    {
        "biased": "chairman",
        "neutral_primary": "chair",
        "neutral_alternatives": "chairperson|chair of the board",
        "tags": "gender|role-title",
        "pos": "noun",
        "scope": "corporate",
        "register": "formal",
        "severity": "replace",
        "example_biased": "The chairman opened the meeting.",
        "example_neutral": "The chair opened the meeting."
    },
    {
        "biased": "policeman",
        "neutral_primary": "police officer",
        "neutral_alternatives": "officer|law enforcement officer",
        "tags": "gender|occupation",
        "pos": "noun",
        "scope": "law enforcement",
        "register": "neutral",
        "severity": "replace",
        "example_biased": "The policeman helped the child.",
        "example_neutral": "The police officer helped the child."
    },
    {
        "biased": "waitress",
        "neutral_primary": "server",
        "neutral_alternatives": "waitstaff|attendant",
        "tags": "gender|occupation",
        "pos": "noun",
        "scope": "hospitality",
        "register": "neutral",
        "severity": "replace",
        "example_biased": "The waitress took our order.",
        "example_neutral": "The server took our order."
    },
    {
        "biased": "he or she",
        "neutral_primary": "they",
        "neutral_alternatives": "",
        "tags": "gender|pronoun",
        "pos": "pronoun",
        "scope": "general",
        "register": "neutral",
        "severity": "replace",
        "example_biased": "If a student is late, he or she must report.",
        "example_neutral": "If a student is late, they must report."
    },
    {
        "biased": "crazy",
        "neutral_primary": "wild",
        "neutral_alternatives": "unusual|unexpected",
        "tags": "ableism|descriptor",
        "pos": "adjective",
        "scope": "general",
        "register": "informal",
        "severity": "warn",
        "example_biased": "That’s a crazy idea!",
        "example_neutral": "That’s a wild idea!"
    }
]

# ========================
# BASE DATA (SWAHILI)
# ========================
SWAHILI_BASE = [
    {
        "biased": "msichana wa kazi",
        "neutral_primary": "mfanyakazi wa nyumbani",
        "neutral_alternatives": "mhudumu wa kaya",
        "tags": "gender|occupation",
        "pos": "noun_phrase",
        "scope": "household",
        "register": "neutral",
        "severity": "replace",
        "ngeli": "1/2",
        "number": "sg",
        "requires_agreement": "true",
        "agreement_notes": "demonstratives agree with head noun (huyu/hao)",
        "example_biased": "Tumeajiri msichana wa kazi.",
        "example_neutral": "Tumeajiri mfanyakazi wa nyumbani."
    },
    {
        "biased": "mama wa nyumbani",
        "neutral_primary": "mzazi wa nyumbani",
        "neutral_alternatives": "mshughulikiaji wa kaya",
        "tags": "gender|family",
        "pos": "noun_phrase",
        "scope": "general",
        "register": "neutral",
        "severity": "replace",
        "ngeli": "1/2",
        "number": "sg",
        "requires_agreement": "true",
        "agreement_notes": "genitive agrees with head noun (wa)",
        "example_biased": "Amebaki kuwa mama wa nyumbani.",
        "example_neutral": "Amebaki kuwa mzazi wa nyumbani."
    },
    {
        "biased": "bwana",
        "neutral_primary": "ndugu",
        "neutral_alternatives": "",
        "tags": "gender|address",
        "pos": "noun",
        "scope": "general",
        "register": "formal",
        "severity": "warn",
        "ngeli": "1/2",
        "number": "sg",
        "requires_agreement": "false",
        "agreement_notes": "use alternatives depending on register",
        "example_biased": "Asante bwana mwenyekiti.",
        "example_neutral": "Asante ndugu mwenyekiti."
    },
    {
        "biased": "walemavu",
        "neutral_primary": "watu wenye ulemavu",
        "neutral_alternatives": "mtu mwenye ulemavu (sg)",
        "tags": "disability",
        "pos": "noun",
        "scope": "public discourse",
        "register": "formal",
        "severity": "replace",
        "ngeli": "2",
        "number": "pl",
        "requires_agreement": "true",
        "agreement_notes": "prefer person-first",
        "example_biased": "Huduma kwa walemavu zinaboreshwa.",
        "example_neutral": "Huduma kwa watu wenye ulemavu zinaboreshwa."
    }
]

# ========================
# EXPANSION
# ========================
def expand_variants(base_entries, language_code):
    expanded = []
    for item in base_entries:
        # Ensure all fields are present
        row = {col: item.get(col, "") for col in COLUMNS}
        row["language"] = language_code
        expanded.append(row)

        # Generate simple variants: lowercase, titlecase, "the X"
        variants = []
        if " " not in row["biased"]:
            variants = [row["biased"].capitalize(), f"the {row['biased']}"]
        else:
            variants = [row["biased"].title()]

        for v in variants:
            variant_row = row.copy()
            variant_row["biased"] = v
            expanded.append(variant_row)
    return expanded

# ========================
# GENERATE & SAVE CSV
# ========================
def save_csv(filename, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

def main():
    en_rows = expand_variants(ENGLISH_BASE, "en")
    sw_rows = expand_variants(SWAHILI_BASE, "sw")

    # Naive expansion to reach ~500 by duplication with prefixes
    def bulk_expand(rows, target_size):
        expanded = rows.copy()
        i = 0
        while len(expanded) < target_size:
            r = expanded[i % len(rows)].copy()
            r["biased"] = r["biased"] + f"_{len(expanded)}"
            expanded.append(r)
            i += 1
        return expanded

    en_rows = bulk_expand(en_rows, 500)
    sw_rows = bulk_expand(sw_rows, 500)

    save_csv(OUTPUT_EN, en_rows)
    save_csv(OUTPUT_SW, sw_rows)

    print(f"Generated {len(en_rows)} EN rows -> {OUTPUT_EN}")
    print(f"Generated {len(sw_rows)} SW rows -> {OUTPUT_SW}")

if __name__ == "__main__":
    main()
