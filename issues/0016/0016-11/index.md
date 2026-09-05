---
schema_version: "1.0"
id: "0016-11"
level: "task"
parent: "0016"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-09"
  - "0016-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2931"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-11:0015-09, 0016-11:0016-05 Demonstrate one supersession/invalidation path with preserved audit history, affected-party communication, revisit work, verification, and closure.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
