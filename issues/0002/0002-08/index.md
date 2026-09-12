---
schema_version: "1.0"
id: "0002-08"
level: "task"
parent: "0002"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:99"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

include a section explaining failure handling: how to interpret rejects, fallback counts, stale diagrams, and validate errors without silently patching outputs -- DONE 2026-08-14: covered in sections 7 & 9 of `_src/sources/pages/process.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
