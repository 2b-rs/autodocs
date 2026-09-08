---
schema_version: "1.0"
id: "0008-09"
level: "task"
parent: "0008"
state: "closed"
visibility: "internal"
prerequisites:
  - "0008-08"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:278"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0008-09:0008-08 — extend `validate.py`'s `check_no_hardcoded_german()` (or add a companion check) to catch hardcoded German strings that are only introduced client-side via JS DOM mutation (e.g. `review.js`), not just in generated static HTML -- DONE 2026-08-14: `_src/tools/check_client_rendered_german.cjs` and `validate.py::check_client_rendered_german()` execute headless WebKit rendering of representative pages across all language trees to scan post-mutation DOM text for leaked German chrome strings. Documented in `docs/pipeline/client-rendered-validation.md`; tested in `_src/tests/test_client_rendered_german.py`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
