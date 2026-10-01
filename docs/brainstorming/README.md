# Brainstorming Hub

This folder pulls together the **design notes, roadmap thinking, open process
ideas, and policy-level planning content** that is otherwise scattered across
the repository. It is intentionally separate from the operational pipeline
docs in `docs/pipeline/`.

## Scope

Included here:
- Roadmap / future-work thinking
- Design principles and architectural intent
- Traceability / evidence / inference ideas
- Process proposals and campaign concepts
- AI-content curation policy and regeneration workflow
- i18n translation policy and maintenance guidance where they contain
  non-trivial design rationale

Explicitly **not** moved here:
- Root TODO-style lists remain in the project root, per request (`TODO.md`,
  and practically also `BACKLOG.md` as a live checklist rather than a design
  note)

## Files in this folder

- `source-map.md` — where brainstorming content lives in the repo, and what
  kind of thinking each source contains.
- `quality-roadmap.md` — consolidated notes from `SPEC_QUALITY_ROADMAP.md`.
- `traceability-and-evidence.md` — consolidated ideas from
  `_src/SPEC_TRACEABILITY.md`, `_src/SPEC_BUILD_PROCESS.md`, and
  `upstream_evidence.py`.
- `content-and-i18n.md` — design-level notes from `_src/ai/RICHTLINIEN.md`,
  `_src/i18n/ANWEISUNG.md`, `_src/WARTUNG.md`, and `_src/KONVENTIONEN.md`.

## Primary sources gathered here

| Source | Why it belongs here |
|---|---|
| `SPEC_QUALITY_ROADMAP.md` | Pure roadmap / later-work brainstorming |
| `_src/SPEC_TRACEABILITY.md` | Design intent for provenance, evidence, inference |
| `_src/SPEC_BUILD_PROCESS.md` | Process design, still partly aspirational |
| `_src/ai/RICHTLINIEN.md` | Policy and regeneration rationale for AI-authored content |
| `_src/i18n/ANWEISUNG.md` | Translation policy / invariants |
| `_src/WARTUNG.md` | Maintenance philosophy and pipeline layering |
| `_src/KONVENTIONEN.md` | Editorial and evidentiary design rules |
| `_src/tools/upstream_evidence.py` | Important rationale note: preserve raw evidence at every stage |

## Relationship to `docs/pipeline/`

- `docs/pipeline/` answers: **what exists, who does what, which tool runs
  where**.
- `docs/brainstorming/` answers: **what ideas, design intentions, and future
  directions motivated the system**.
