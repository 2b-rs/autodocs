---
schema_version: "1.0"
id: "0037-15.01"
level: "subtask"
parent: "0037-15"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-06.01"
  - "0037-14"
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2344"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-15.01:0037-06.01, 0037-15.01:0037-14, 0037-15.01:0037-17.01 Implement source-watermark tracking and fresh full re-import.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Record baseline/latest source, candidate schema, importer tool commit/digest, run, and source artifact set
- **AC-002** detect every committed delta including Feature `0037`, deleted/reused IDs, task moves, changed prerequisites, and dirty/staged final-source blockers
- **AC-003** build in a new temp root and atomically promote only after validation

## Definition of Done

Tests simulate multiple source commits, interrupted/stale runs, dirty final state, and deleted/reused IDs and prove latest-source equivalence.
