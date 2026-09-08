---
schema_version: "1.0"
id: "0002-05"
level: "task"
parent: "0002"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:96"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

describe the end-to-end i18n → diagrams → HTML → validate pipeline in the published page, including which artifacts are sources, which are generated, and which are only caches/work products -- DONE 2026-08-14: covered in sections 1-6 of `_src/sources/pages/process.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
