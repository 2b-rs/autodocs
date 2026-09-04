---
schema_version: "1.0"
id: "0037-34"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-34.01"
  - "0037-34.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2513"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-34:0037-34.01, 0037-34:0037-34.02 Complete prepared and authorized atomic authority cutover.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preparation and execution remain separate
- **AC-002** the executed patch is byte-identical to the authorized patch except fields that must record the resulting cutover commit through the required follow-up reference commit

## Definition of Done

Both Subtasks complete with one authority at every committed state and retained rollback/event-replay material.
