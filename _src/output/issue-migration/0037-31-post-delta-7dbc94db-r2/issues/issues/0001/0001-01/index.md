---
schema_version: "1.0"
id: "0001-01"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:75"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

define one canonical build-report schema for i18n + HTML publication runs, covering inputs, commands, timestamps, durations, exit codes, changed artifacts, fallback counts, reject counts, and validation findings -- DONE 2026-08-13: schema documented in `docs/pipeline/build-report-schema.md` (envelope + per-producer `counts` fields for i18n_merge, i18n_diagrams, html_generate, validate, combined). REF: d47435fb

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
