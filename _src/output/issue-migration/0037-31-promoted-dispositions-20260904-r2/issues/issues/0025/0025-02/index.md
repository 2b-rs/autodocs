---
schema_version: "1.0"
id: "0025-02"
level: "task"
parent: "0025"
state: "open"
visibility: "internal"
prerequisites:
  - "0024-02"
  - "0025-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2811"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0025-02:0025-01, 0025-02:0024-02 Execute the machine-enforced selected-profile readiness gate: verify that every included process's registered Feature/task and conditional predecessor edge is complete with valid ECU execution evidence; every shared in-scope process has ECU execution evidence for the assessed unit's portion plus approved external interface/acceptance evidence; every relevant fully external process has approved interface/acceptance evidence and no internal rating; every out-of-scope process has approved exclusion rationale, no internal rating, and interface evidence only where an actual lifecycle interface exists; every exclusion remains justified; and no activated conditional lifecycle is missing. Block evidence freeze on any absent, stale, inconsistent, wrong-origin, or unsatisfied gate.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
