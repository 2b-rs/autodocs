---
schema_version: "1.0"
id: "0016-13"
level: "task"
parent: "0016"
state: "closed"
visibility: "internal"
prerequisites:
  - "0012-02"
  - "0016-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2933"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-13:0012-02, 0016-13:0016-03 Classify TODO/BACKLOG entries, retain planning work as managed work packages, migrate only true problems/changes, preserve aliases/history, and retire competing active backlog semantics.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
