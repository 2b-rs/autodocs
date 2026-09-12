---
schema_version: "1.0"
id: "0010-01"
level: "task"
parent: "0010"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:69"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

parallelize `validate.py` -- 2026-08-14: parallelized check_client_rendered_german() (per-language Node/WebKit calls) via ThreadPoolExecutor; check_build()/check_langs() were already parallelized via ProcessPoolExecutor. Pre-existing rc=1 (30 dead links under process.html in all languages) is unrelated and tracked separately. REF: 941b73a4

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
