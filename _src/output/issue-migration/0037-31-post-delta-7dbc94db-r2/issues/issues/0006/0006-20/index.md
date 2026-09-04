---
schema_version: "1.0"
id: "0006-20"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-15"
  - "0006-16"
  - "0006-18"
  - "0006-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:229"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-20:0006-15, 0006-20:0006-16, 0006-20:0006-18, 0006-20:0006-19 — generalize release-diff into a supersession-trigger job that detects changed inputs and cascades invalidation / revisit requests

## Scope

- Triggers to cover: new AUTOSAR release, new curation input, user comment, scraper update, extraction bugfix, newly available sources, and AI model/settings change.
  - On each trigger, compute which requirement versions / curated decisions / evidence snippets / synthesis inputs changed, write new immutable versions where applicable (**0006-16**), and walk the dependency graph (**0006-18**) to mark dependent knowledge `invalidated` and/or enqueue it for AI revisit (**0006-19**).
  - Current gap: no existing tool (`review_flags.py`, `curation_flags.py`, `review_ingest.py`, `curation_ingest.py`, `spec_scrape.py`) performs version-to-version diffing plus graph-based revisit scheduling across releases and non-release triggers; this is new pipeline logic.
  - Emit a report of: changed requirements, superseded decisions/evidence/artifacts, revisit tasks enqueued, and any cases that could not be resolved automatically (candidates for **0001**'s build-report work). -- DONE 2026-08-13: added `_src/tools/supersession_trigger.py` with `process_trigger(trigger_kind, canonical_id, release, content, reason)` covering all 6 named trigger kinds. It diffs against `version_store.latest_version()` by recomputing the candidate version_id via `version_id.requirement_version_id()` and comparing to the stored version_id (mirroring record_version()'s own idempotency check), records a new version on genuine change, and invokes the ALREADY-EXISTING `confidence.cascade_invalidate()` (0006-19, which already walks `dependency_graph.find_dependents()` from 0006-18 and enqueues revisits) -- this task did not need to reimplement graph-walking or invalidation, only the trigger-level orchestration and diffing around them. `summarize_reports()` aggregates a batch into changed/superseded/revisits-enqueued/unresolved. `write_report()` persists JSON under `_src/spec/supersession-reports/`, pending Feature 0001's build-report pipeline (not yet built). Added `_src/tests/test_supersession_trigger.py` (9 tests, all 6 trigger kinds exercised, module state isolated to tmpdirs). Documented in `docs/pipeline/supersession-trigger.md`. Does not wire any existing tool to call `process_trigger()` automatically -- no such caller exists yet, same scoping pattern as 0006-05 through 0006-19. REF: a21e5905

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
