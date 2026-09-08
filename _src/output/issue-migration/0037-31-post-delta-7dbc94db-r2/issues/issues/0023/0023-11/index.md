---
schema_version: "1.0"
id: "0023-11"
level: "task"
parent: "0023"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0027-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2783"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0023-11:0020-09, 0023-11:0027-05 Accept and baseline the allocated software-development inputs required by the approved profile: when `SYS.2`/`SYS.3` are internal, use the controlled outputs of `0029-02`/`0030-02`; when they are shared/external, validate the responsible party, allocated requirements, architecture/interface constraints, assumptions, acceptance criteria, configuration identity, change/problem/risk feedback, and bidirectional interface evidence without claiming internal `SYS` performance. The selected-profile register must materialize the actual internal predecessor or external/shared acceptance-gate edges.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
