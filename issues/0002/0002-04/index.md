---
schema_version: "1.0"
id: "0002-04"
level: "task"
parent: "0002"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:95"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

create a dedicated page model under `_src/sources/pages/` for the process description and wire it into site navigation and indexes where appropriate -- DONE 2026-08-14: created `_src/sources/pages/process.json` wired to `process.html` across all language trees. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
