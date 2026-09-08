---
schema_version: "1.0"
id: "0002-10"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:101"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

ensure the published process page itself is covered by generate/validate and documented in repo-level maintenance docs -- DONE 2026-08-14: generated across all 10 language trees via `_src/generate.py` and verified by `_src/validate.py`. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
