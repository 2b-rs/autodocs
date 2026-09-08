---
schema_version: "1.0"
id: "0027-05"
level: "task"
parent: "0027"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-08"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2688"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0027-05:0020-08 Establish and operate ECU `SUP.8` configuration management for requirements, architecture/design, source/generated code, binaries/firmware, toolchain/configuration, calibration/variant data, test assets/environments, supplier items, records/evidence, and releases; perform controlled change/versioning, baselines, status accounting, audits, backup/restore, access, retention, and availability controls.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
