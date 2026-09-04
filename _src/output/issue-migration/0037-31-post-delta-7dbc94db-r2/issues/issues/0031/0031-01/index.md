---
schema_version: "1.0"
id: "0031-01"
level: "task"
parent: "0031"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0022-01"
  - "0027-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2765"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0031-01:0020-09, 0031-01:0022-01, 0031-01:0027-01 Accept and baseline the system architecture and all system-element inputs for internal `SYS.4`: use `0030-02` and applicable internal element outputs when those processes are internal, or validate each external/shared owner, baseline, interface, configuration, acceptance, open finding, and feedback path without claiming its process performance. The selected-profile register must materialize the applicable internal predecessor tasks and external/shared acceptance gates; no hard-coded software-only predecessor may stand in for that selected system-element set.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
