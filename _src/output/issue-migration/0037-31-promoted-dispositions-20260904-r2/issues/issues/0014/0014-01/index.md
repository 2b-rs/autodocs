---
schema_version: "1.0"
id: "0014-01"
level: "task"
parent: "0014"
state: "open"
visibility: "internal"
prerequisites:
  - "0013-03"
  - "0013-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2886"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-01:0013-03, 0014-01:0013-05 Define reviewed strategies for SWE.4 unit verification, SWE.5 component/integration verification, and SWE.6 integrated-software verification, including methods, selection, coverage, regression, environments, entry/exit, pass/fail, and result-retention criteria.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
