---
schema_version: "1.0"
id: "0006-23"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-15"
  - "0006-16"
  - "0006-17"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:247"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-23:0006-15, 0006-23:0006-16, 0006-23:0006-17 — support retrieving a coherent "as of release R" (or "as of date D") view of requirements, curated decisions, and AI artifacts

## Scope

- Motivating scenario (2026-08-13): after R32-11 ships, a user must still be able to review R25-11's requirement text, the curator's decisions, and the AI comments/syntheses that applied to it — even though newer versions now exist and older ones are marked superseded/invalidated.
  - Define a query contract that, given a release tag (or a date, resolved to the latest version/decision/artifact at or before that date), returns: the requirement-version active at that point, the curation decision(s) whose `decided_on_version` matches or precedes it, and the evidence/artifact graph nodes valid as of that point — all without filtering out `superseded`/`invalidated` items, since "superseded now" must not mean "absent from a past view."
  - Because nothing in **0006-16** through **0006-19** is ever deleted, this is a read-side query problem ("reconstruct the graph state as of R/D"), not a storage problem; document it as such to avoid accidental future work on redundant snapshot storage.
  - Decide how this view is exposed: CLI query, static per-release HTML render, or both; note dependency on **0006-14**'s presentation-layer work. -- DONE 2026-08-13: added `_src/tools/asof_view.py` with `as_of_release(canonical_id, release)`/`as_of_date(canonical_id, date)`, a pure query module with ZERO new storage (matches the task's own instruction that this is a read-side problem, since 0006-16 through 0006-19 never delete). Returns the active requirement-version, matching curation decision(s), and the artifact-dependency graph -- the latter NEVER filtered by invalidated/dismissed state, per the explicit requirement that a past view must not hide superseded items (each dependent is annotated with its current invalidated/dismissed flags instead). Release-tag ordering documented as a plain-string-sort assumption (fixed-width AUTOSAR convention). Exposure decision: ship the query function only for now, deferring CLI/HTML-render to 0006-14's presentation work since no real caller exists yet. Added `_src/tests/test_asof_view.py` (8 tests). Documented in `docs/pipeline/asof-view.md`. REF: 71790b27

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
