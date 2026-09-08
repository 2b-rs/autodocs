---
schema_version: "1.0"
id: "0025-06"
level: "task"
parent: "0025"
state: "closed"
visibility: "internal"
prerequisites:
  - "0025-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2815"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0025-06:0025-05 Triage every material outcome weakness/finding with root cause, impact, owner, due date, approved correction or accepted-residual decision, links to controlled problems/changes, affected lifecycle evidence, and required re-verification.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
