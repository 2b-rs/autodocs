---
schema_version: "1.0"
id: "0001-11"
level: "task"
parent: "0001"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:85"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

update `_src/WARTUNG.md`, `docs/pipeline/actions.md`, `docs/pipeline/reports.md`, and `docs/pipeline/tools.md` so the build-report process is documented as a required part of i18n/HTML publication -- DONE 2026-08-14: documented across all 4 pipeline specification files.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
