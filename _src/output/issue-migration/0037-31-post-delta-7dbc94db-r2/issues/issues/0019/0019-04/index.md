---
schema_version: "1.0"
id: "0019-04"
level: "task"
parent: "0019"
state: "closed"
visibility: "internal"
prerequisites:
  - "0019-02"
  - "0019-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3001"
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

PREREQ: 0019-04:0019-02, 0019-04:0019-03 Implement the v0.6.0 manifest-driven S-Core extraction adapter.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The adapter accepts only a manifest-pinned source set, extracts the profile’s supported artifacts, and emits deterministic raw extraction output
- **AC-002** it does not fall back to moving refs such as `main`
- **AC-003** failures identify repo/ref/path/locator and leave no partial canonical corpus presented as complete

## Definition of Done

Unit and integration tests cover successful extraction, missing source, invalid ref/hash, malformed Sphinx-needs item, duplicate identity, and unsupported artifact; repeated extraction from the same snapshot produces identical normalized raw output.
