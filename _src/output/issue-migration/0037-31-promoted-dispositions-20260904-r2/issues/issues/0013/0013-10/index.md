---
schema_version: "1.0"
id: "0013-10"
level: "task"
parent: "0013"
state: "open"
visibility: "internal"
prerequisites:
  - "0013-07"
  - "0013-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2879"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0013-10:0013-07, 0013-10:0013-08 Migrate approved requirement candidates into the controlled hierarchy in reviewable batches while retaining source links and supersession history.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
