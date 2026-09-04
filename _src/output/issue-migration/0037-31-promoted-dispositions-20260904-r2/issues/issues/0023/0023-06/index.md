---
schema_version: "1.0"
id: "0023-06"
level: "task"
parent: "0023"
state: "open"
visibility: "internal"
prerequisites:
  - "0023-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2789"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0023-06:0023-05 Execute `SWE.4` on the controlled ECU unit baseline; retain pass/fail data and coverage, trace detailed design/units to measures/results, resolve or disposition findings, communicate the summary, and retain exact unit/source or model, build/toolchain, configuration, data, and environment identity.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
