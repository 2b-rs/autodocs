---
schema_version: "1.0"
id: "0006-02.01"
level: "subtask"
parent: "0006-02"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:136"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-02.01:0006-02 — add a small `projects.json` registry listing every known `project` value, its display name, and its `kind` enum — REF: 9daffda4

## Scope

- One place to register `AUTOSAR/AP`, `AUTOSAR/CP`, `AUTOSAR/FOUNDATION`, `ECLIPSE/S-CORE` (and future projects) instead of leaving valid `project`/`kind` combinations implicit in scraper/validator code.
  - `validate.py` (or its 0006-13 extension) should check every canonical ID's `project`/`kind` against this registry.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
