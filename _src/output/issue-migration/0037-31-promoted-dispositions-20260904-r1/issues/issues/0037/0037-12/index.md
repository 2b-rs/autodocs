---
schema_version: "1.0"
id: "0037-12"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0037-08"
  - "0037-09"
  - "0037-11.02"
  - "0037-39"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2327"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-12:0037-05, 0037-12:0037-08, 0037-12:0037-09, 0037-12:0037-11.02, 0037-12:0037-39 Replace free-form parsing in `tools/todo-graph-core.js`, `tools/todo-graph-embed.js`, and `tools/todo-dependency-graph.html` with the normalized graph adapter. **REF:** `e2eda5a7418df5c07b6c66f90df47c26824a7b88`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The shared core consumes validated graph JSON, emits deterministic DOT, and represents Feature/Task/Subtask nodes, `[w]`, every lifecycle/archive state, start-gate and Feature-closure edges, redacted/missing endpoints, counts, filters, and stable links. It never parses YAML, Markdown, `TODO.md`, or `DONE.md`
- **AC-002** malformed/stale catalogs fail visibly rather than dropping edges. Freeze current defects—missing `[w]`, ignored Feature prerequisites, duplicate/malformed IDs, cycles, and silently dropped endpoints—as negative/regression fixtures

## Definition of Done

Node/DOT tests compare every node/edge/count with Python output and prove standalone/embed consumers use the same core; no duplicate semantic classifier remains in browser code.
