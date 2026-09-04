---
schema_version: "1.0"
id: "0032-03"
level: "task"
parent: "0032"
state: "open"
visibility: "internal"
prerequisites:
  - "0032-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2775"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0032-03:0032-02 Execute `SYS.5` on the controlled integrated ECU baseline; retain pass/fail and coverage results, trace results to system requirements, resolve or disposition findings, communicate the summary, and preserve exact ECU hardware/software/calibration/configuration/tool/environment identity.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
