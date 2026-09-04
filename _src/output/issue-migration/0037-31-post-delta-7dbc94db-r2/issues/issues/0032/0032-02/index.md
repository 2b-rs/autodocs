---
schema_version: "1.0"
id: "0032-02"
level: "task"
parent: "0032"
state: "closed"
visibility: "internal"
prerequisites:
  - "0022-02"
  - "0032-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2774"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0032-02:0032-01, 0032-02:0022-02 Define and approve `SYS.5` integrated-system verification against ECU system requirements, including selection/coverage and regression rationale, target or representative environments, data, versioned expected results, entry/exit, pass/fail, retention, and system-requirement-to-measure trace tied to the controlled requirement and environment/configuration baseline.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
