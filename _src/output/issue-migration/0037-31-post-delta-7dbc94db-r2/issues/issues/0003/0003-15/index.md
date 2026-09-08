---
schema_version: "1.0"
id: "0003-15"
level: "task"
parent: "0003"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:61"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

translate and merge `_src/i18n/work/nl/batch_15.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 199/199 entries completed and merged (2026-08-13, corrected after prior mislabeling — see 2026-08-13 note above), 0 rejects, no `fehler.json` produced. `python3 _src/i18n_translate.py merge nl` reported: übernommen 4655, abgelehnt 0, offen 0 (all languages fully translated per `i18n_translate.py status`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
