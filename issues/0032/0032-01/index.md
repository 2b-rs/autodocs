---
schema_version: "1.0"
id: "0032-01"
level: "task"
parent: "0032"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0022-01"
  - "0027-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2773"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0032-01:0020-09, 0032-01:0022-01, 0032-01:0027-01 Accept the controlled system-requirement and integrated-system inputs for internal `SYS.5`: use `0029-02` and `0031-03` when those processes are internal, or validate each external/shared owner, baseline, exact ECU element/configuration/environment identity, status, acceptance, open findings, and feedback path without claiming external process performance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
