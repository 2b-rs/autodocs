---
schema_version: "1.0"
id: "0014-13"
level: "task"
parent: "0014"
state: "open"
visibility: "internal"
prerequisites:
  - "0014-04"
  - "0014-08"
  - "0014-09"
  - "0014-10"
  - "0014-11"
  - "0014-12"
  - "0015-06"
  - "0015-07"
  - "0016-01"
  - "0016-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2898"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-13:0014-04, 0014-13:0014-08, 0014-13:0014-09, 0014-13:0014-10, 0014-13:0014-11, 0014-13:0014-12, 0014-13:0015-06, 0014-13:0015-07, 0014-13:0016-01, 0014-13:0016-02 Retain release-specific verification, validation, and QA summaries with exact baseline/tool/environment identity, findings, waivers, approvals, issue links, communication, and closure evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
