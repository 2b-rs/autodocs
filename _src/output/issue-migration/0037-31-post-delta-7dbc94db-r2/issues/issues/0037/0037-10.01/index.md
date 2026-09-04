---
schema_version: "1.0"
id: "0037-10.01"
level: "subtask"
parent: "0037-10"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-08"
  - "0037-09"
  - "0037-17.01"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2281"
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
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0037-10.01:0037-08, 0037-10.01:0037-09, 0037-10.01:0037-17.01 Implement item creation and controlled structural edits. Claim: `TODO-gabriel-issuectl-0037-10.01-20260825T114200Z.md` (`owner_token: agent:gabriel-issuectl:0037-10.01:20260825T114200Z`). **REF:** `007234d85b53b4fc5e7d57e817b24095ff3e5259`. **Validation:** `/tmp/autodocs-0037-08-venv-julian/bin/python _src/tests/test_issuectl.py` — 18 tests OK; `py_compile` PASS. No Acceptance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Create Feature/Task/Subtask paths
- **AC-002** edit approved front-matter fields
- **AC-003** allocate/withdraw/supersede/move `AC-NNN`
- **AC-004** and add/remove prerequisites/relations using expected input digest and atomic temp-file replacement. Validate ID/path/parent, cycles, criterion invariants, claim/write scope, and no-op behavior before promotion
- **AC-005** preserve unrelated prose bytes

## Definition of Done

Tests cover each operation, concurrent edit rejection, invalid cycle/parent/move, criterion history, crash rollback, dry-run diff, and byte-stable no-op.
