---
schema_version: "1.0"
id: "0023-10"
level: "task"
parent: "0023"
state: "open"
visibility: "internal"
prerequisites:
  - "0023-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2793"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0023-10:0023-09 Execute `SWE.6` on the controlled integrated ECU software baseline; retain pass/fail and coverage results, trace results to software requirements, resolve or disposition findings, communicate the summary, and preserve exact source/executable/configuration/toolchain/target/environment identity.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
