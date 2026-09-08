---
schema_version: "1.0"
id: "0002-09"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
prerequisites:
  - "0001"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:100"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0002-09:0001 — add links from the published process page to the relevant repo documentation (`_src/WARTUNG.md`, `docs/pipeline/*.md`) and to representative generated report pages once Feature 1 exists -- DONE 2026-08-14: covered in section 10 of `_src/sources/pages/process.json`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
