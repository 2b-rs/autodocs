---
schema_version: "1.0"
id: "0006-10"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-09"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:173"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-10:0006-09 — design the future dynamic JS/API view around the same schema, not a second ad-hoc model -- DONE 2026-08-14: `_src/tools/curation_report.py` exports the canonical dataset to `_src/data/curation-items.json` (`curation-items-export@v1`) matching the exact schema for future client-side and API filtering.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
