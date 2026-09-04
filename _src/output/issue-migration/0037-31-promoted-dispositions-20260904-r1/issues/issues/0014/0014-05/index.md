---
schema_version: "1.0"
id: "0014-05"
level: "task"
parent: "0014"
state: "open"
visibility: "internal"
prerequisites:
  - "0007-04"
  - "0014-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2890"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-05:0007-04, 0014-05:0014-03 Qualify the independently approved and frozen 200-record extraction benchmark for the verification strategy: define its applicability, shape/document coverage and limits, regression-selection use, controlled environment, and retained benchmark-version/hash evidence without treating it as ECU verification evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
