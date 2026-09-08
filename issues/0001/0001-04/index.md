---
schema_version: "1.0"
id: "0001-04"
level: "task"
parent: "0001"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:78"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

extend `i18n_diagrams.py` so each run emits a report of diagram sources considered, translated outputs written, unchanged outputs skipped, and stale translated SVGs deleted -- DONE 2026-08-13: `main()` now writes a schema-conformant `i18n_diagrams` report to `output/build-reports/`. REF: d85e0d86

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
