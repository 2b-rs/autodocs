---
schema_version: "1.0"
id: "0001-10"
level: "task"
parent: "0001"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:84"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

add tests/fixtures for report generation and schema stability, including failure cases (rejects, stale diagrams, fallback translations, validate findings) -- DONE 2026-08-14: unit tests added in `_src/tools/test_build_report.py`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
