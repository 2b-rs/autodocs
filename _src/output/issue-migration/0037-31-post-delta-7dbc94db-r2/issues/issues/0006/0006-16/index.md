---
schema_version: "1.0"
id: "0006-16"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-15"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:207"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-16:0006-15 — add an immutable requirement-version store, separate from the current mutable record store — REF: 6e581ab5 — implemented as `_src/tools/version_store.py` (append-only JSONL per requirement under `_src/spec/versions/`, idempotent, never-delete); documented in `docs/pipeline/version-store.md`. Not yet wired into `spec_scrape.py`'s write path (0006-17 scope).

## Scope

- Current gap: records are overwritten in place per module/ID (`_src/spec/records/<MODULE>/<ID>.json`); there is no append-only history of prior content per requirement.
  - Design an append-only version table/store keyed by the requirement-version ID from **0006-15**, with the existing record store becoming a "current pointer" into it; define retention (never delete) and how old versions are exposed/rendered on request.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
