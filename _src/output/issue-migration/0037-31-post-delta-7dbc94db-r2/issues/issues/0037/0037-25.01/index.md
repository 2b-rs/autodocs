---
schema_version: "1.0"
id: "0037-25.01"
level: "subtask"
parent: "0037-25"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-11"
  - "0037-19"
  - "0037-23"
  - "0037-24"
  - "0037-38"
  - "0037-39"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2420"
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

PREREQ: 0037-25.01:0037-11, 0037-25.01:0037-19, 0037-25.01:0037-23, 0037-25.01:0037-24, 0037-25.01:0037-38, 0037-25.01:0037-39 Implement the `issuectl regenerate --all` DAG orchestrator and its typed sandboxed-runner action.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Topologically execute catalog/legacy views, internal/public graph data, title/UI completeness, DOT/SVG, page models, every language HTML tree, indexes, and validators under one run ID
- **AC-002** require exact input artifact sets and complete stage reports
- **AC-003** reject cycles, absent required stages, stale inputs, unrelated “latest by mtime” reports, and undeclared output changes

## Definition of Done

Orchestrator tests verify stage order, shared run identity, fail-fast/cleanup, exact issue/page/language/artifact counts, and no fixture/production-root crossover.
