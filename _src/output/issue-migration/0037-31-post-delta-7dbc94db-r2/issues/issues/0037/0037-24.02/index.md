---
schema_version: "1.0"
id: "0037-24.02"
level: "subtask"
parent: "0037-24"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-12"
  - "0037-23.02"
  - "0037-24.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2407"
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

PREREQ: 0037-24.02:0037-12, 0037-24.02:0037-23.02, 0037-24.02:0037-24.01 Move graph controls, legends, state/edge labels, summaries, errors, and public titles into the existing i18n/runtime pipeline and generate `_src/data/issue-graph-public.<lang>.json` payloads.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Store graph chrome in `_src/i18n/ui.json`
- **AC-002** remove hardcoded English/German text from `tools/todo-graph-core.js`, `tools/todo-graph-embed.js`, and standalone HTML
- **AC-003** join the locale-neutral projection with title/UI records into deterministic per-language payloads, render language-local deep links, and never persist translated titles in the internal or locale-neutral projection
- **AC-004** public generation fails on a missing required UI/title translation, while the maintainer view marks canonical-English fallback visibly with `lang="en"`
- **AC-005** preserve RTL direction and protected IDs/refs

## Definition of Done

Client/DOM tests cover all configured languages, Arabic RTL, fallback only in maintainer mode, stale/missing public translation failure, no German leakage, and no corrupted identity token.
