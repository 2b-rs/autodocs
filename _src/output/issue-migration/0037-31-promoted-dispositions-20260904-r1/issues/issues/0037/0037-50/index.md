---
schema_version: "1.0"
id: "0037-50"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2171"
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
---

## Goal

Correct the rejected `0037-46.02` failover candidate under `DEC-0037-001` and present a fresh immutable checkpoint candidate. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded as a package. `.01` remains governance history; `.02`--`.05` close without implementation and retain all prepared evidence.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** Architect `data`, proposal `164890ec3c`: Subtask `.05` is the sole integrating and live-deployment boundary and carries the mandatory checkpoint; duplicating it at this package aggregator would review the same exact candidate twice without adding a distinct risk boundary.

## Acceptance criteria

- **AC-001** Complete Subtasks `0037-50.01`--`.05` in order
- **AC-002** preserve the rejected `0d2088a6778820b83329fafe248f21b97d904654` history and Geordi findings
- **AC-003** implement Datas admission-coupled drain-before-reopen design without widening its paths, external scope, waiver, or role boundaries
- **AC-004** and bind the new candidate to hermetic plus operator-assisted evidence

## Definition of Done

All five Subtasks are terminal with real REFs and exact prerequisite tips; the parent `0037-46.02` points to the fresh candidate and remains unaccepted until its mandatory independent integration review passes; no request is grandfathered, both mutation protocols are never open together, and rollback failure remains fail-closed and recoverable.
