---
schema_version: "1.0"
id: "0016-15"
level: "task"
parent: "0016"
state: "closed"
visibility: "internal"
prerequisites:
  - "0016-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2935"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0016-15:0016-03 Integrate validation findings, extraction residuals, review/curation queues, and AI proposals with canonical problem/change links without replacing their domain-specific records.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
