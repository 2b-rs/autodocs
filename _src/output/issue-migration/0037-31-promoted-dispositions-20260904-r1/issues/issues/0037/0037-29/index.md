---
schema_version: "1.0"
id: "0037-29"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-14"
  - "0037-15"
  - "0037-16"
  - "0037-21"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:1022"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-29:0037-14, 0037-29:0037-15, 0037-29:0037-16, 0037-29:0037-21 Execute repeated non-authoritative shadow migrations from pinned committed legacy sources and resolve every importer/schema finding. **Acceptance: ✓** (2026-09-03, Project Lead `jadzia`, independent of implementer `data`). Canonical integration receipt `593f5a1c3937fa368d4c11f182a664cb66cfeadd` on main.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
