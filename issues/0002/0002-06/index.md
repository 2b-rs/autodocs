---
schema_version: "1.0"
id: "0002-06"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:97"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

describe how `run.sh` / `output/run-archive/` fit into traceability, including what can be reconstructed from archived script+log pairs and what cannot -- DONE 2026-08-14: covered in section 8 of `_src/sources/pages/process.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
