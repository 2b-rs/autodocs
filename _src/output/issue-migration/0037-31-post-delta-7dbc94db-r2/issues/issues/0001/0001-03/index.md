---
schema_version: "1.0"
id: "0001-03"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:77"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

extend the i18n pipeline so each `i18n_translate.py merge <lang>` run emits a machine-readable report with batch files consumed, accepted/rejected counts, `fehler.json` summary, and resulting register changes -- DONE 2026-08-13: `merge()` now writes a schema-conformant `i18n_merge` report to `output/build-reports/`. REF: d85e0d86

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
