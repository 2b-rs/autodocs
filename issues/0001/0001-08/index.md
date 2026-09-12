---
schema_version: "1.0"
id: "0001-08"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
prerequisites:
  - "0001-07"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:82"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0001-08:0001-07 — publish the combined build report into the generated HTML tree as a browsable report page with links to archived logs and referenced artifacts -- DONE 2026-08-14: `_src/tools/build_report.py publish` generates `_src/sources/pages/build-reports.json`, rendered to `build-reports.html`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
