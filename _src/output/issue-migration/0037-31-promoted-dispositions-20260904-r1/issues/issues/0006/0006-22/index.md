---
schema_version: "1.0"
id: "0006-22"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-15"
  - "0006-16"
  - "0006-18"
  - "0006-21"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:240"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-22:0006-15, 0006-22:0006-16, 0006-22:0006-18, 0006-22:0006-21 — document the resulting DB schema, graph semantics, and ID scheme in the pipeline data-model docs before implementation spreads — done so far: `docs/pipeline/data-model.md` has a draft "Versionierungs- und ID-Schema" section (2026-08-13); TODO: worked examples (a)-(c) not yet added, and `docs/pipeline/{roles,actions,processes,reports,tools}.md` / `_src/SPEC_BUILD_PROCESS.md` not yet cross-updated

## Scope

- Primary documentation home: `docs/pipeline/data-model.md`.
  - Update `docs/pipeline/{roles,actions,processes,reports,tools}.md` and `_src/SPEC_BUILD_PROCESS.md` where needed so the versioned requirement/evidence/synthesis graph and invalidation semantics are described consistently across the repo.
  - Include worked examples covering: (a) new AUTOSAR release superseding a curated requirement, (b) human comment triggering AI resynthesis, (c) curator dismissal pruning future propagation while preserving audit history. -- DONE 2026-08-13: updated `docs/pipeline/data-model.md` to turn the draft version/ID section into an integrated, implementation-backed data-model description with worked examples for (a) new AUTOSAR release superseding a curated requirement, (b) human comment triggering AI resynthesis, and (c) curator dismissal halting future propagation while preserving audit history. Cross-updated `docs/pipeline/{roles,actions,processes,reports,tools}.md` and `_src/SPEC_BUILD_PROCESS.md` so the repo consistently references the now-real modules and semantics (`version_store`, `dependency_graph`, `confidence`, `typed_claim`, `supersession_trigger`, `asof_view`, `delta_view`). No behavior change; docs spread only. REF: d3117a83

### Point-in-time and delta views

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
