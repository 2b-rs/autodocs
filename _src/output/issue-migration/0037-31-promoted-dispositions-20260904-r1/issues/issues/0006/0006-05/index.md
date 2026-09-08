---
schema_version: "1.0"
id: "0006-05"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:150"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-05:0006-03 — add first-class support for AI-proposed NEW elements in the DB and queue model

## Scope

- Current gap: `hypothesized/unconfirmed` exists in docs as a status, but no implemented CLI or queue path creates such elements.
  - Define where hypotheses live before acceptance (separate hypothesis store vs. lightweight record stubs), how they get canonical IDs, how evidence is attached, and how acceptance promotes them into the main DB without losing history. -- DONE 2026-08-13: added `_src/tools/hypothesis_store.py` giving AI-proposed NEW elements a concrete `hypothesis:<uuid7>` id (extends version_id.py's 0006-15 id family) and a SEPARATE store under `_src/spec/hypotheses/` (never a record stub, so unconfirmed guesses can't be mistaken for real curated records). `promote_hypothesis()` mints a real canonical id and writes into `_src/spec/records/` with an explicit `source_hypothesis` link in the new record's first history entry (bidirectional traceability); `reject_hypothesis()` marks status in place without ever deleting the file. Documented in `docs/pipeline/hypothesis-store.md`; unit tests in `_src/tests/test_hypothesis_store.py`. Does NOT wire any existing tool to actually start creating hypotheses automatically -- no such caller exists yet; this provides the store/promotion primitives for future callers, consistent with how 0006-15/16/17 were scoped. REF: 1d818be4

### Workflow / pipeline convergence

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
