---
schema_version: "1.0"
id: "0013-07"
level: "task"
parent: "0013"
state: "open"
visibility: "internal"
prerequisites:
  - "0013-02"
  - "0013-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2876"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0013-07:0013-02, 0013-07:0013-03 Inventory and classify requirement candidates scattered across TODOs, conventions, maintenance/process documents, schemas, and tests; identify duplicates, conflicts, design statements, process rules, and imported domain content without migrating them yet.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
