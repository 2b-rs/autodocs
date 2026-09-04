---
schema_version: "1.0"
id: "0017-06"
level: "task"
parent: "0017"
state: "closed"
visibility: "internal"
prerequisites:
  - "0015-06"
  - "0017-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2946"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0017-06:0015-06, 0017-06:0017-05 Implement trustworthy correlated collection and trend reporting, including completeness/data-quality flags so missing stages or incomparable process instances cannot appear as successful measurements.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
