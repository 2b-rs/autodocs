---
schema_version: "1.0"
id: "0015-10"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-07"
  - "0018-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2913"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0015-10:0015-07, 0015-10:0018-03 Verify that PA 2.2 work-product review and adjustment was operated throughout all scoped ECU pilot process instances: retain and check the exact version reviewed, applicable content/quality/review criteria, reviewer authority, findings, decisions, resulting revisions, consistency checks, and issue closure; explicitly justify any work-product type requiring no review or approval.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Every selected process's produced work-product types are covered
- **AC-002** missing criteria, unreviewed required products, unresolved material findings, wrong-product evidence, or an unexplained no-review classification fail the gate

## Definition of Done

The controlled ECU evidence set contains linked review/adjustment records and an independently checked coverage report for the approved process instances and baseline.
