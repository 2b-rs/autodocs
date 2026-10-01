# Content, AI, and i18n Notes

This file consolidates design-level thinking from `_src/ai/RICHTLINIEN.md`,
`_src/i18n/ANWEISUNG.md`, `_src/WARTUNG.md`, and `_src/KONVENTIONEN.md`.

## Maintenance philosophy

The repository is built around a strict layering rule:

`Spec-DB → KI-Kuratierung → Komposition → i18n → HTML`

The generated HTML tree is a build artifact, not an editing surface. Changes
belong in `_src/`, then the tree is regenerated.

This is more than an operational instruction; it is one of the central design
constraints of the project.

## AI-content policy

From `ai/RICHTLINIEN.md` and `ai_workflow.py`:

- AI-generated explanations and diagrams are part of a curated workflow,
  never free-floating text.
- Policy is versioned in `ai/policy.json`; if policy changes, affected
  fragments become stale and can be invalidated/regenerated.
- AI content is generated canonically in German only; translation is a later,
  separate pipeline.
- API identifiers, code, enum values, and `[SWS_…]` / `[RS_…]` markers remain
  unchanged across languages.

This creates a strong conceptual boundary: AI generation and human/automated
translation are different concerns with different invariants.

## Translation policy

From `_src/i18n/ANWEISUNG.md`:

- Translation input/output is rigid JSONL with stable IDs.
- Placeholder tokens like `⟦0⟧` must be preserved exactly.
- Protected technical content is never translated indirectly by damaging the
  placeholders.
- Translation is treated as a machine-checkable transformation, not a freeform
  editorial exercise.

The broader implication is that i18n is designed as a **controlled data
pipeline**, not a loose content workflow.

## Editorial and evidentiary conventions

From `_src/KONVENTIONEN.md`:

- Official AUTOSAR PDFs are the truth source.
- The site is not itself an official AUTOSAR publication.
- Main UI language is German, but original spec descriptions remain English
  across language trees.
- Every substantive statement in AI text must be backed by an `[SWS_…]`,
  `[RS_…]`, or precise PDF chapter reference.

That means even the narrative/explanatory layer is intended to be evidence-led,
not merely reader-friendly prose.

## Practical design consequences

| Theme | Consequence |
|---|---|
| Generated artifacts are disposable | Editing happens in sources, never in built HTML |
| AI text is policy-bound | Regeneration must track policy version and provenance |
| Translation is constrained | IDs, placeholders, and technical markers are protected invariants |
| Evidence matters even in prose | Explanation quality is judged by traceability, not style alone |

## Why this belongs in brainstorming

These files are partly operational, but they also capture the project's
strongest design convictions: layered generation, traceable explanation,
post-generation translation, and strict protection of technical tokens.
Those ideas shape future decisions well beyond the current code.
