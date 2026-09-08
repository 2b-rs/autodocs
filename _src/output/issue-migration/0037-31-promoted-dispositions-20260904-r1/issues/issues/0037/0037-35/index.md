---
schema_version: "1.0"
id: "0037-35"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-35.01"
  - "0037-35.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2532"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-35:0037-35.01, 0037-35:0037-35.02 Complete clean-cutover regeneration verification and rollback rehearsal.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Verification and rollback use isolated clean/detached worktrees and retained run/artifact evidence
- **AC-002** neither rewrites production history

## Definition of Done

Both Subtasks have signed passing transaction-ledger evidence against the actual cutover commit and identify exact environment, commands, inputs, outputs, and hashes; their issue closures are deferred to `0037-40`.
