---
schema_version: "1.0"
id: "0037-26.04"
level: "subtask"
parent: "0037-26"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2448"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-26.04:0037-17, 0037-26.04:0037-19 Extend database rebuild, migration, and version/snapshot writers with deterministic provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Record schema/migration/tool/config commits, ordered input artifact sets, changed/added/deleted records and versions, output snapshot/tree digest, trigger issue/finding/campaign/run, and rollback/rebuild relation
- **AC-002** identical inputs/config produce the same semantic identity

## Definition of Done

Rebuild/migration fixtures detect input/config/schema drift, trace each changed record to evidence and trigger, prove deterministic identity, and prevent partial snapshot promotion.
