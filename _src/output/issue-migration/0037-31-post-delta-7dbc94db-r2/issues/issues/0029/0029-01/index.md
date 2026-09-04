---
schema_version: "1.0"
id: "0029-01"
level: "task"
parent: "0029"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0022-01"
  - "0027-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2751"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0029-01:0020-09, 0029-01:0022-01, 0029-01:0027-01 Accept and baseline the stakeholder-requirement input for internal `SYS.2`: use Feature `0028` output when `SYS.1` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.1` performance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
