---
schema_version: "1.0"
id: "0016-07"
level: "task"
parent: "0016"
state: "open"
visibility: "internal"
prerequisites:
  - "0014-13"
  - "0015-06"
  - "0016-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2927"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-07:0014-13, 0016-07:0015-06, 0016-07:0016-06 Make publication verify one complete atomic evidence bundle and approved baseline before delivery, package every configured artifact/language/report, and retain approval, delivery verification, and rollback evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
