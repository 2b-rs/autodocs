---
schema_version: "1.0"
id: "0037-15"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-15.01"
  - "0037-15.02"
  - "0037-15.03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2340"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-15:0037-15.01, 0037-15:0037-15.02, 0037-15:0037-15.03 Complete moving-source, moving-schema, and authorized-event reconciliation.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The combined candidate equals a clean latest-source import targeting the latest schema plus exactly-once replay of compatible authorized events
- **AC-002** no manual shadow state can win

## Definition of Done

All three Subtasks pass one scenario with intervening legacy commits and one target-schema upgrade, with no lost/duplicated item/event.
