---
schema_version: "1.0"
id: "0037-15.02"
level: "subtask"
parent: "0037-15"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-06.02"
  - "0037-14"
  - "0037-17.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2348"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-15.02:0037-06.02, 0037-15.02:0037-14, 0037-15.02:0037-17.01 Implement versioned shadow schema transforms and clean-import equivalence checks.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Each transform declares from/to schema and tool digest, reads immutable input, writes a fresh root, records an artifact set, and is deterministic/idempotent. Compare transformed candidate semantically with a clean importer run targeting the new schema
- **AC-002** mismatch is a stable blocking finding, never an accepted representation drift

## Definition of Done

Upgrade/downgrade-rejection, crash, unknown-version, lossy-transform, and equivalence fixtures pass for the approved versioned `issue-item@v1-draft`→`issue-item@v1` migration fixture; no artificial production schema bump is created merely to satisfy the test.
