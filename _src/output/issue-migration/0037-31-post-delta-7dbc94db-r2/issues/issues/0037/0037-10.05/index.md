---
schema_version: "1.0"
id: "0037-10.05"
level: "subtask"
parent: "0037-10"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-03.01"
  - "0037-08"
  - "0037-09"
  - "0037-10.03"
  - "0037-17.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2298"
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

PREREQ: 0037-10.05:0037-03.01, 0037-10.05:0037-08, 0037-10.05:0037-09, 0037-10.05:0037-10.03, 0037-10.05:0037-17.01 Implement criterion checking, closure, wontfix, supersession, duplicate/cancel, archive, and Feature-closure operations.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Require reachable criterion evidence and terminal `closure.json`
- **AC-002** enforce legal transitions, decision authority, real/reachable commit refs, the two-commit rule, and closure of every child before Feature closure
- **AC-003** retain withdrawn/superseded/non-accepted history without presenting it as success

## Definition of Done

Tests cover every terminal disposition, missing/invalid evidence, same-commit REF rejection, Feature `0021` archive semantics, partial Feature closure, injected write failure, and immutable history.
