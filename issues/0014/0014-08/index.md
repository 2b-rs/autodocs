---
schema_version: "1.0"
id: "0014-08"
level: "task"
parent: "0014"
state: "open"
visibility: "internal"
prerequisites:
  - "0014-02"
  - "0014-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2893"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-08:0014-02, 0014-08:0014-03 Execute selected SWE.4 unit-verification measures, record pass/fail data and coverage, trace results to measures/units, resolve findings, and communicate the summary.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
