---
schema_version: "1.0"
id: "0037-10"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-10.01"
  - "0037-10.02"
  - "0037-10.03"
  - "0037-10.04"
  - "0037-10.05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2277"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-10:0037-10.01, 0037-10:0037-10.02, 0037-10:0037-10.03, 0037-10:0037-10.04, 0037-10:0037-10.05 Complete `_src/tools/issuectl.py` lifecycle, rendering, validation, and query operations.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Every subcommand validates before atomic promotion, supports `--dry-run` and explicit candidate/staged roots where applicable, compares expected source digests to prevent lost updates, emits immutable events, and uses documented stable diagnostics/exit codes

## Definition of Done

All five Subtasks pass CLI/API and injected-failure tests; no command silently overwrites hand edits or bypasses role/claim checks.
