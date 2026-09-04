---
schema_version: "1.0"
id: "0014-03"
level: "task"
parent: "0014"
state: "closed"
visibility: "internal"
prerequisites:
  - "0014-01"
  - "0015-03"
  - "0015-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2888"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-03:0014-01, 0014-03:0015-03, 0014-03:0015-04 Control verification environments, tools, dependencies, fixtures, test data, expected results, coverage metrics, and regression-selection rationale as configuration items.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
