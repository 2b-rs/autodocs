---
schema_version: "1.0"
id: "0015-08"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-03"
  - "0015-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2911"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-08:0015-03, 0015-08:0015-06 Perform and retain configuration audits plus backup/restore tests for a representative source, campaign, evidence bundle, and published release baseline; record the mechanism's limits. Documentation source/campaign evidence qualifies only that mechanism and cannot satisfy ECU PA 2.2 or ECU `SUP.8` without application to the approved ECU product/process instance and baseline.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
