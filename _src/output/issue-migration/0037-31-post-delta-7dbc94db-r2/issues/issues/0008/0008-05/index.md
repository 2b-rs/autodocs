---
schema_version: "1.0"
id: "0008-05"
level: "task"
parent: "0008"
state: "closed"
visibility: "internal"
prerequisites:
  - "0008-01"
  - "0008-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:272"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0008-05:0008-01, 0008-05:0008-02 — after fixing, rebuild and `--check` all 10 language trees (not just nl) since both bugs are structural to `render_page`/`_review_page_enhancements` and are not nl-specific -- DONE 2026-08-13: `generate.py --check` (canonical German) and `generate.py --lang=<x> --check` for all 10 non-German trees all pass with zero stale/mismatched pages after the 0008-01/0008-02 fixes. REF: 82b25ae6

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
