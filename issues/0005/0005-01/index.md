---
schema_version: "1.0"
id: "0005-01"
level: "task"
parent: "0005"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:117"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0005-01:0006 — Requirement texts in the AUTOSAR AP documentation should be reviewable and approvable in a traceable way — directly in the published HTML documentation, without a separate tool and without a server component. -- DONE 2026-08-14: Implemented client-side review workflow in published HTML (`review.js`, `.rec-history-panel`, curation report linkage) with zero server-side requirement; verified across all 11 language trees.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
