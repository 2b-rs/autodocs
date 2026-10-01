# Workflow-Model Validation and Tests (Feature 0006-13)

Status: implemented 2026-08-13. PREREQs 0006-03 (curation-item@v1) and
0006-06 (unified lifecycle) both done.

## What this adds

- `_src/tools/curation_item_lifecycle_check.py`: maps every
  `curation_item.VALID_STATUSES` value onto the corresponding
  `workflow_lifecycle.STATES` member, and exposes `validate_vocabularies()`
  (detects drift between the two independently-maintained vocabularies) and
  `item_lifecycle_state(item)` (per-item lookup).
- `validate.py::check_workflow_lifecycle()`: runs `validate_vocabularies()`
  as part of the normal `validate.py` run, and additionally walks any
  persisted `review-queue/`/`curation-queue/` payloads on disk (there are
  none in this sandbox at the time of writing -- the check degrades
  gracefully to a no-op over real data in that case, but still always
  exercises the vocabulary-consistency check) asserting each normalizes
  into a conformant curation-item@v1 with a resolvable lifecycle state.
- `_src/tests/test_curation_item_lifecycle.py`: unit tests for the mapping
  itself, for `from_review_flag`/`from_curation_flag`'s produced statuses
  under representative payloads (open/claimed/applied and
  accepted/rejected/proposed), and failure cases (unknown status, wrong
  schema version, missing required field) per this task's phrasing
  ("including failure cases").

## Why "open" maps to "queued"

curation-item@v1 (0006-03) predates the unified lifecycle vocabulary
(0006-06) and calls the not-yet-claimed state `"open"`. Both describe
"written to a queue, not yet claimed" -- this is a deliberate, documented
synonym, not a bug; `curation_item.py`'s own field name is left unchanged
since changing it would touch every existing reader/writer of
review-flag/curation-flag payloads, which is out of scope for a validation-
and-tests-only task.

## Non-goals

Does not change `review_flags.py`/`curation_flags.py`/`review_ingest.py`/
`curation_ingest.py`'s writing logic, and does not change
`curation_item.py`'s or `workflow_lifecycle.py`'s existing public API --
only adds a new cross-check module, a new `validate.py` check function, and
tests, per this task's own wording ("add validation and tests").
