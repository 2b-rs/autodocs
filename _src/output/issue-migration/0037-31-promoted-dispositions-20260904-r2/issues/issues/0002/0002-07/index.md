---
schema_version: "1.0"
id: "0002-07"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:98"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0002-07:0006-09 — include a section explaining report artifacts (`fehler.json`, `i18n_translate.py status`, QA scans, validate findings, combined build reports) and where maintainers can inspect them -- DONE 2026-08-14: covered in section 8 of `_src/sources/pages/process.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
