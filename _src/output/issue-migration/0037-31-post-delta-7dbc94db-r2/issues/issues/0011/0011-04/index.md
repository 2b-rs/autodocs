---
schema_version: "1.0"
id: "0011-04"
level: "task"
parent: "0011"
state: "closed"
visibility: "internal"
prerequisites:
  - "0011-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2842"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0011-04:0011-01 Define and assign the process-owner, performer, reviewer, approver, curator, release-authority, QA, assessor, and escalation roles, including authorities, independence requirements, deputies, and required competencies.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
