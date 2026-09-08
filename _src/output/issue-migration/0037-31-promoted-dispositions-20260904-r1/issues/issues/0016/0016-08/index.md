---
schema_version: "1.0"
id: "0016-08"
level: "task"
parent: "0016"
state: "open"
visibility: "internal"
prerequisites:
  - "0016-04"
  - "0016-05"
  - "0016-07"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2928"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-08:0016-04, 0016-08:0016-05, 0016-08:0016-07 Process one accepted change through authorization, implementation, verification, release, communication, and closure with full trace.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
