---
schema_version: "1.0"
id: "0024-01"
level: "task"
parent: "0024"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-08"
  - "0023-10"
  - "0027-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2801"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0024-01:0020-08, 0024-01:0027-05, 0024-01:0023-10 Define `SPL.2` ECU release content, identity, eligibility/approval criteria, compatible hardware/vehicle and variant scope, firmware/executable, calibration/configuration and flashing/delivery artifacts as applicable, release notes, known limitations, licenses/notices, support and update/rollback information, recipients/delivery controls, and release-record requirements.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
