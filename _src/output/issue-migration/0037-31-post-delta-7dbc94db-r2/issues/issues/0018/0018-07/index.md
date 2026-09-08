---
schema_version: "1.0"
id: "0018-07"
level: "task"
parent: "0018"
state: "closed"
visibility: "internal"
prerequisites:
  - "0018-06"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2959"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0018-07:0018-06 Execute versioned correction/re-verification/effectiveness cycles, publish a new evidence-baseline revision and reassessment after each cycle, and exit only when no CL2-blocking finding remains or the sponsor records that CL2 cannot be claimed and opens a next-cycle plan. A finding is CL2-blocking whenever it prevents `PA 1.1 = F`, `PA 2.1 = L/F`, or `PA 2.2 = L/F` for any declared target process.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
