---
schema_version: "1.0"
id: "0037-46"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2125"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Complete implementation, runner-side activation, and retirement-safe handoff from the qualified legacy singleton to the versioned queue. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded; the future system has no sandboxed-grunt transport cutover. Existing artifacts and review findings remain immutable history.

## Acceptance criteria

- **AC-001** Source implementation and runner-service activation are separate, recoverable Subtasks
- **AC-002** failure before protocol-epoch switch leaves the qualified singleton usable, and failure after switch automatically rolls back service configuration/epoch before accepting another request

## Definition of Done

Both Subtasks pass and the live runner consumes only the qualified queue protocol; legacy `run.sh` requests fail with one actionable queue-bootstrap message.
