---
schema_version: "1.0"
id: "0003-08"
level: "task"
parent: "0003"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:54"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

translate and merge `_src/i18n/work/nl/batch_08.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 210/210 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
