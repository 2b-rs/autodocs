---
schema_version: "1.0"
id: "0027-08"
level: "task"
parent: "0027"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-08"
  - "0027-01"
  - "0027-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2691"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0027-08:0020-08, 0027-08:0027-01, 0027-08:0027-05 Establish and approve one ECU `SUP.10` change-request lifecycle covering intake/status, affected-baseline and dependency/resource/schedule/risk impact, priority, approve/reject/withdraw authority, implementation trace for approved changes, proof of non-implementation for rejected/withdrawn requests, verification/consistency, communication, closure, trends, and links to problems; validate every decision branch with positive/negative fixtures.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
