---
schema_version: "1.0"
id: "0001-07"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
prerequisites:
  - "0001-01"
  - "0001-03"
  - "0001-04"
  - "0001-05"
  - "0001-06"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:81"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0001-07:0001-01, 0001-07:0001-03, 0001-07:0001-04, 0001-07:0001-05, 0001-07:0001-06 — add a runner-side orchestration step (via `run.sh` archive flow) that combines merge/diagram/build/validate subreports into one end-to-end publication report for a release/build run -- DONE 2026-08-14: `_src/tools/build_report.py combine` aggregates all producer subreports into `output/build-reports/combined-<timestamp>.json`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
