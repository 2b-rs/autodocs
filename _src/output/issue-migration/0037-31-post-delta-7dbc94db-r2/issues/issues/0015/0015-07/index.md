---
schema_version: "1.0"
id: "0015-07"
level: "task"
parent: "0015"
state: "closed"
visibility: "internal"
prerequisites:
  - "0015-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2910"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-07:0015-02 Define and enforce review/approval criteria and evidence schemas for each controlled work-product type, including authenticated actor, role/authority, version reviewed, criteria, findings, decision, timestamp, and issue closure.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
