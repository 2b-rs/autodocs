---
schema_version: "1.0"
id: "0001-05"
level: "task"
parent: "0001"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:79"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

extend the HTML build/publication path so each `generate.py` run emits a machine-readable report with generated page counts per language, fallback-to-German counts, changed target files, and wall-clock duration -- DONE 2026-08-13: `main()` now writes a schema-conformant `html_generate` report to `output/build-reports/`; `changed_targets` list is currently a stub (always empty) since `generate_lang`/main don't yet track per-file diffs -- follow-up noted for 0001-07. REF: d85e0d86

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
