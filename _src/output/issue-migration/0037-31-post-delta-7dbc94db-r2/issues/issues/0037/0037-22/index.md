---
schema_version: "1.0"
id: "0037-22"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-12"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2383"
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
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0037-22:0037-12 Implement `tools/todo-dependency-graph.html` as the internal maintainer consumer of `issues/_views/dependency-graph.json`. **Claim:** `TODO-benjamin-chain-0037-22-20260828.md` (`owner_token: agent:deepspace9:chain-0037-22:20260828T223500Z`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve filtering, counts, zoom/scroll, all state/archive/edge legends, done handling, and actionable errors
- **AC-002** add internal item links, source/schema/tool/config digests and content-generation ID, with volatile execution-run linkage only in the external run manifest
- **AC-003** eliminate `../TODO.md` fetching
- **AC-004** work over documented local HTTP with only tracked assets
- **AC-005** expose stale/missing/malformed data instead of silently disappearing

## Definition of Done

Browser/DOM tests cover every state/edge class, redacted/missing endpoints, malformed/stale data, missing Graphviz assets, item navigation, keyboard/accessibility behavior, and exact catalog count/edge parity.
