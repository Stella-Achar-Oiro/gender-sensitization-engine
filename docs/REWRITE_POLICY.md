# Rewrite Policy (v0.1)

## Principles
1. **Preserve meaning**: never change factual content.
2. **Remove bias, not identity**: target biased roles/titles/stereotypes, not names.
3. **Use inclusive, idiomatic language** for each locale and register.
4. **Prefer person-first** where appropriate (e.g., `watu wenye ulemavu`).
5. **Escalate ambiguity**: if meaning could change, mark `needs_review` (or `warn`).
6. **Full traceability**: every change is logged with rationale and examples.

## Severity semantics
- `replace`: auto-apply deterministic substitution.
- `warn`: keep original but annotate suggestion (Week 1); escalate to review in later phases.

## Style notes
- Titles/roles: chair → chairperson/chair; policeman → police officer.
- Pronouns: “he or she” → “they” where singular they is idiomatic.
- Swahili: ensure agreement when possible; if non-trivial, prefer review.

## Human review is required when
- Multiple valid alternatives exist with different tone/register.
- The term is polysemous and context is unclear.
- Replacement affects morphology/grammar beyond simple substitution.

## Out-of-scope (v0.1)
- Complex discourse-level bias or sarcasm.
- Entity renaming (names, proper nouns).
- Non-text inputs.

## Documentation obligations
- Every lexicon entry should include an example (biased vs neutral).
- Keep a changelog of lexicon revisions with date, author, and rationale.
