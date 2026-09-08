---
schema_version: "1.0"
id: "0018-06"
level: "task"
parent: "0018"
state: "open"
visibility: "internal"
prerequisites:
  - "0018-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2958"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0018-06:0018-05 Triage every assessment finding, record root cause/impact/owner/due date and an approved correction or accepted-residual disposition, and create bounded child remediation tasks linked to controlled changes and required re-verification.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
