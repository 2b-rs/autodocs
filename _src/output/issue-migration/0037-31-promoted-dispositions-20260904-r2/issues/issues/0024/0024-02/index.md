---
schema_version: "1.0"
id: "0024-02"
level: "task"
parent: "0024"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-09"
  - "0024-01"
  - "0027-02"
  - "0027-03"
  - "0027-04"
  - "0027-06"
  - "0027-07"
  - "0027-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2802"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0024-02:0020-09, 0024-02:0024-01, 0024-02:0027-02, 0024-02:0027-03, 0024-02:0027-04, 0024-02:0027-06, 0024-02:0027-07, 0024-02:0027-08 Verify every release prerequisite activated by the selected-profile register—including internal validation execution or the approved external/shared acceptance gate—and verify the disposition/closure or authorized carry-over of every actual applicable problem/change; then assemble, audit, approve, deliver, and verify receipt or deployment of one complete controlled ECU release package. Retain baseline identity, release authority, quality/risk/validation status, accepted deviations, notes, support/rollback information, delivery result, and links to included problems and changes. The release gate fails when any selected-profile edge is absent, stale, inconsistent, or unsatisfied, but does not require inventing a problem or rejected change solely for release.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
