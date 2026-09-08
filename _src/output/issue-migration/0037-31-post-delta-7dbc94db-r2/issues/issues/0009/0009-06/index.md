---
schema_version: "1.0"
id: "0009-06"
level: "task"
parent: "0009"
state: "closed"
visibility: "internal"
prerequisites:
  - "0009-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:292"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0009-06:0009-02 — add S-Core-specific validation checks to `validate.py` (or its extension) for structural integrity of scraped units (dangling component-interface references, missing design docs, orphaned modules) -- DONE 2026-08-14: implemented `_src/tools/validate_score.py` checking structural integrity, module package containment, and sphinx-needs ID formatting, with full unit test coverage. REF: pending commit

## Scope

**ARCHIVED — NOT ACCEPTED:** implementation iteration ended 2026-08-15 19:20 CEST. Last task-specific committed implementation/ref bookkeeping: `28d6de75` / `62f638bf`. The later labels `local-20260815-0021-06`, `local-20260815-0021-07`, and `local-20260815-0021-08` are not Git objects and receive no independent evidence credit. Successors: open Features `0033` and `0035` in `TODO.md`.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
