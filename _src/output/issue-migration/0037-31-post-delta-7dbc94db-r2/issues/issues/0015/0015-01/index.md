---
schema_version: "1.0"
id: "0015-01"
level: "task"
parent: "0015"
state: "closed"
visibility: "internal"
prerequisites:
  - "0011-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2904"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-01:0011-05 Complete the controlled work-product/configuration-item catalogue for requirements, plans, records, source, generated artifacts, schemas, tests, reports, decisions, problems/changes, dependencies, releases, and assessment evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
