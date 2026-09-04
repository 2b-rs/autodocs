---
schema_version: "1.0"
id: "0002-03"
level: "task"
parent: "0002"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:94"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

design the page structure for the published process documentation: source of truth, i18n extraction/translation/merge, diagram translation, HTML generation, validation, reports, and traceability links — DONE 2026-08-14: 10-section structure documented in `docs/pipeline/published-process-page.md`, incorporating the 0002-01 (agent-instructions-as-artifact-class) and 0002-02 (i18n'ed page family) decisions, fixing page-model placement (`_src/sources/pages/process.json` → `process.html`) and per-section hand-off to tasks 0002-04–0002-09.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
