---
schema_version: "1.0"
id: "0030-01"
level: "task"
parent: "0030"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0022-01"
  - "0027-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2758"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0030-01:0020-09, 0030-01:0022-01, 0030-01:0027-01 Accept and baseline the system-requirement input for internal `SYS.3`: use `0029-02` when `SYS.2` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.2` performance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
