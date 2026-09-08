---
schema_version: "1.0"
id: "0006-06"
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
  source: "legacy:DONE.md:156"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-06:0006-03 — converge browser review, queue review, AI proposals, and curator decisions into one end-to-end state machine

## Scope

- Current gap: the docs show two partially disconnected paths — queue-based (`review-queue` / `curation-queue` -> AI agent -> curator) and browser-based (`review.js` -> GitHub issue / JSON -> `*_ingest.py`).
  - Model one shared lifecycle with explicit states and transitions, including: discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied -> published -> superseded.
  - Map every existing tool to that lifecycle (`review_flags.py`, `curation_flags.py`, `review_ingest.py`, `curation_ingest.py`, `spec_scrape.py`, future AI-amendment tools) and document which transitions each tool may perform. -- DONE 2026-08-13: added `_src/tools/workflow_lifecycle.py` defining the shared discovered->queued->claimed->proposed->accepted/rejected->applied->published-> superseded lifecycle, with a `TOOL_TRANSITIONS` table mapping every function in `review_flags.py`/`curation_flags.py`/`review_ingest.py`/`curation_ingest.py`/ `hypothesis_store.py` (0006-05) to the exact from/to states it performs, plus a `validate_transition()` helper. Documented in `docs/pipeline/workflow-lifecycle.md`; unit tests (`_src/tests/test_workflow_lifecycle.py`) assert every mapped transition is internally consistent, including the two documented shortcuts (review_flags.py's proposed->applied with no separate accept step, and hypothesis_store's discovered->proposed with no queue at all). Does NOT change how any tool physically persists state (queue-file existence remains each tool's own representation) -- this is the shared reference vocabulary/validator the task's wording asked for, not a queue-mechanics rewrite. REF: a71765e0

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
