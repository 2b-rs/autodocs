---
schema_version: "1.0"
id: "0037-23.02"
level: "subtask"
parent: "0037-23"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-22"
  - "0037-23.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2395"
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

PREREQ: 0037-23.02:0037-22, 0037-23.02:0037-23.01 Integrate the public graph and summaries through `_src/sources/pages/index.json`, `_src/sources/pages/issues.json`, templates, and generation—not direct HTML edits.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Consume the sanitized payload
- **AC-002** generate language-tree-correct assets/links and stable `issues.html#<item-id>` anchors
- **AC-003** provide pre-rendered Graphviz SVG plus accessible list/count summary and no-JS fallback
- **AC-004** make missing/stale payload a visible validation/build failure on required deployments
- **AC-005** retain internal maintainer tooling outside published payloads

## Definition of Done

Page-model, generation, DOM/link/accessibility, no-JS, client-render, missing-data, and canonical/translated-tree tests pass and generated HTML contains no internal-catalog path or restricted fixture token.
