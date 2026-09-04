---
schema_version: "1.0"
id: "0006-13"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-03"
  - "0006-06"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:185"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-13:0006-03, 0006-13:0006-06 — add validation and tests for the unified workflow model

## Scope

- Extend `validate.py` (or add a dedicated validator) to check canonical IDs, queue payload schema/version, allowed state transitions, referential integrity to records/pages, and history completeness.
  - Add fixtures covering at least: a scrape ambiguity, a DB correction request, an AI-generated amendment to an existing record, and a new hypothesized requirement. -- DONE 2026-08-13: added `_src/tools/curation_item_lifecycle_check.py` mapping curation_item.VALID_STATUSES (0006-03) onto workflow_lifecycle.STATES (0006-06) with a `validate_vocabularies()` drift check and an `item_lifecycle_state()` per-item lookup; wired into `validate.py` as `check_workflow_lifecycle()` (also walks any real review-queue/curation-queue payloads on disk, currently none in this sandbox); added `_src/tests/test_curation_item_lifecycle.py` covering the vocabulary mapping, from_review_flag/from_curation_flag status derivation, and failure cases (unknown status, wrong schema version, missing required field). Full validate.py run confirmed still exits 0. Documented in docs/pipeline/workflow-validation.md. REF: 65b9adc0

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
