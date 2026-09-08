---
schema_version: "1.0"
id: "0015-03"
level: "task"
parent: "0015"
state: "closed"
visibility: "internal"
prerequisites:
  - "0015-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2906"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-03:0015-02 Implement configuration identification, controlled change, baseline creation, configuration-status accounting, completeness/consistency audits, and uniquely reproducible release/campaign baseline IDs.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
