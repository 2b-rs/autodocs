---
schema_version: "1.0"
id: "0003-17"
level: "task"
parent: "0003"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:63"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

translate and merge `_src/i18n/work/nl/batch_17.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 1218/1218 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced (179 German-bearing labels translated; 1039 code/identifier-only labels passed through unchanged). HTML tree regeneration still pending.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
