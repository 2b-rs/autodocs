---
schema_version: "1.0"
id: "0016-03"
level: "task"
parent: "0016"
state: "closed"
visibility: "internal"
prerequisites:
  - "0016-01"
  - "0016-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2923"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-03:0016-01, 0016-03:0016-02 Define classification/linking rules that keep MAN.3 work packages and improvement work in the managed plan, create SUP.9 records only for problems, create SUP.10 records only for requested changes, and link related records without conflating their lifecycles.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
