---
schema_version: "1.0"
id: "0037-11"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-11.01"
  - "0037-11.02"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2302"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-11:0037-11.01, 0037-11:0037-11.02 Complete deterministic legacy and machine-readable issue views. **Claim:** `TODO-worf-0037-11-20260828.md` (`owner_token: agent:deepspace9:0037-11:20260828T223500Z`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Both renderers consume one normalized catalog and neither view becomes input authority. SQLite is explicitly out of scope for v1 and may be proposed only by a later performance measurement Feature

## Definition of Done

Both Subtasks reconcile source/view IDs, states, criteria, and edges exactly.
