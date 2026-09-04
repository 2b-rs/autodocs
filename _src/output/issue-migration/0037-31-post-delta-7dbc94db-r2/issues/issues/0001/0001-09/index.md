---
schema_version: "1.0"
id: "0001-09"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:83"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

ensure the published report page links back to the corresponding `run.sh` archive (`run-<timestamp>-n<seq>.sh` + `.log`) so every generated artifact can be traced to its exact execution log -- DONE 2026-08-14: `build_report.py` extracts `run_archive_ref` and embeds clickable archive links in `build-reports.html`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
