---
schema_version: "1.0"
id: "0006-09"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0001-08"
  - "0006-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:172"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-09:0006-03, 0006-09:0001-08 — build a static HTML "curation report" that renders all open and recent curation items from the queue(s) -- DONE 2026-08-14: `_src/tools/curation_report.py` normalizes all items from `curation-queue` and `review-queue` into `curation-item@v1` and generates `curation-report.html`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
