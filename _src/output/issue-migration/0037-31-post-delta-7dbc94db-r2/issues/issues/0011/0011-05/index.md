---
schema_version: "1.0"
id: "0011-05"
level: "task"
parent: "0011"
state: "closed"
visibility: "internal"
prerequisites:
  - "0011-01"
  - "0011-04"
  - "0020-08"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2843"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0011-05:0011-01, 0011-05:0011-04, 0011-05:0020-08 Extend the single ECU process/work-product/evidence catalogue with PA 2.1/PA 2.2 requirements, quality/control criteria, repositories, owners, review/approval rules, and retained attribute evidence; do not create a separate CL2 catalogue.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
