---
schema_version: "1.0"
id: "0019-08"
level: "task"
parent: "0019"
state: "closed"
visibility: "internal"
prerequisites:
  - "0019-06"
  - "0019-07"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3019"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0019-08:0019-06, 0019-08:0019-07 Perform the Phase-6 validation and curator release-readiness review before generated-tree publication.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The persisted validation report passes
- **AC-002** record/status and exception/queue counts reconcile
- **AC-003** unresolved items, exclusions, low-confidence decisions, and hypotheses are quantified and linked
- **AC-004** the curator reviews every required class and records accept, reject, or explicitly bounded conditional acceptance for the exact corpus/report versions. A rejection or blocking condition leaves this task open and creates linked remediation/re-run work

## Definition of Done

An authenticated accepting decision (or defined non-blocking conditional acceptance) identifies the exact source snapshot, record corpus, validation report, queue snapshot, permitted publication scope, limitations, and required post-generation checks; no generated tree is published before this gate.
