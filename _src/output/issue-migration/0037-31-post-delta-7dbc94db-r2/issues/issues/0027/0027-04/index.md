---
schema_version: "1.0"
id: "0027-04"
level: "task"
parent: "0027"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-08"
  - "0027-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2687"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0027-04:0020-08, 0027-04:0027-01 Establish and operate ECU `MAN.6` measurement from approved information needs through metric definition, validated collection, analysis, trend/limitation communication, and documented decisions. Retain each value's unit, source, timestamp, process-instance/baseline context, data-quality result, analysis, limitations, communication, and linked management decision; keep missing, invalid, or incomparable data visibly distinct from successful results.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
