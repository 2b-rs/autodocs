---
schema_version: "1.0"
id: "0037-25"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-25.01"
  - "0037-25.02"
  - "0037-25.03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2416"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-25:0037-25.01, 0037-25:0037-25.02, 0037-25:0037-25.03 Complete issue-derived orchestration, atomic promotion, and deterministic validation.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** One bounded runner action executes the approved DAG against committed source/translations for a sandboxed agent, never performs external translation, never mutates authoritative issue/provenance input, and cannot publish a partial stage set

## Definition of Done

All three Subtasks pass clean-checkout, crash, stale-input, and no-op rerun scenarios.
