---
schema_version: "1.0"
id: "0017-05"
level: "task"
parent: "0017"
state: "closed"
visibility: "internal"
prerequisites:
  - "0017-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2945"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0017-05:0017-04 Specify each metric’s definition, unit, source, owner, collection/validation method, baseline, target/threshold, cadence, analysis, presentation, retention, and decision use; version the measurement specification.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
