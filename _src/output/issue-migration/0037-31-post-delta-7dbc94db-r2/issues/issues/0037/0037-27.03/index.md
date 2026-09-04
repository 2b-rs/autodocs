---
schema_version: "1.0"
id: "0037-27.03"
level: "subtask"
parent: "0037-27"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
  - "0037-27.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2472"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-27.03:0037-17, 0037-27.03:0037-19, 0037-27.03:0037-27.01 Extend user-guide/process-page authoring and page composition with typed claims and common provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Link guide/page fragment to exact records/evidence/claims/instructions/policy/config, authoring issue/criterion/run, composition input/output hashes, review decision, and invalidation cause
- **AC-002** generated HTML remains derived from `_src/` sources

## Definition of Done

A guide/page fixture traces every published claim to approved source/decision and input change creates bounded linked regeneration work.
