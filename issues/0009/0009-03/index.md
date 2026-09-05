---
schema_version: "1.0"
id: "0009-03"
level: "task"
parent: "0009"
state: "open"
visibility: "internal"
prerequisites:
  - "0009-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:289"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0009-03:0009-01 — register `ECLIPSE/S-CORE` `kind` values in `projects.json` (extending **0006-02.01**) so `validate.py`/`0006-13` can check S-Core canonical IDs against the registry like any other project -- DONE 2026-08-14: registered `module`, `component`, `design-doc`, `process-doc` under `ECLIPSE/S-CORE` in `_src/spec/projects.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
