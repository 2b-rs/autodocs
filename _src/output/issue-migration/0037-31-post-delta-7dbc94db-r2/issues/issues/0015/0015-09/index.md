---
schema_version: "1.0"
id: "0015-09"
level: "task"
parent: "0015"
state: "closed"
visibility: "internal"
prerequisites:
  - "0015-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2912"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-09:0015-05 Wire evidence snippets, dependency edges, supersession triggers, invalidation/revisit results, and their reports into real writers and controlled stores.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
