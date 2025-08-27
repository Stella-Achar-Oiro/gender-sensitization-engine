# Lexicon v2 Schema

Each CSV row defines a *biased surface form* and one or more *neutral* options
with metadata to guide policy, ranking, and display.

## Columns (CSV)
- `language` (str): e.g., `en`, `sw`
- `biased` (str): surface form to match (word boundaries; variants are allowed)
- `neutral_primary` (str): preferred replacement
- `neutral_alternatives` (str): other options, pipe-separated (e.g., `chairperson|chair of the board`)
- `tags` (str): pipe or comma separated labels, e.g., `gender|role-title`
- `pos` (str): noun, pronoun, adjective, noun_phrase…
- `scope` (str): domain (corporate, household, general…)
- `register` (str): neutral, formal, informal
- `severity` (enum): `replace` | `warn`
- `ngeli` (str): Swahili noun class info (e.g., `1/2`, `2`, …)
- `number` (str): `sg` | `pl` | empty
- `requires_agreement` (bool-as-str): `"true"` | `"false"`
- `agreement_notes` (str): guidance to handle concord
- `patterns` (str): optional regex or keyphrase hints
- `constraints` (str): conditions to apply the rule
- `avoid_when` (str): contexts where you must *not* replace
- `example_biased` (str): example sentence
- `example_neutral` (str): neutral rewrite example

## Matching
- Defaults to **word-boundary** exact match, case-insensitive.
- Provide **variants** as additional rows (e.g., `Chairman`, `the chairman`).

## Policy
- `severity=replace` → replace term
- `severity=warn` → **do not** replace, add inline suggestion (Week 1 behavior)

## Notes
- Keep alternatives realistic; register should match expected tone.
- Use person-first language (e.g., `watu wenye ulemavu`).
- Swahili: set `ngeli`, `requires_agreement`, and add notes if replacement affects concord.
