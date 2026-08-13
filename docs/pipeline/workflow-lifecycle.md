# Unified Curation/Review Lifecycle (Feature 0006-06)

Status: defined 2026-08-13 for **0006-06**. Implemented in
`_src/tools/workflow_lifecycle.py`.

## Why

Before this, the docs described two partially disconnected paths: queue-based
(`review-queue`/`curation-queue` -> AI agent -> curator) and browser-based
(`review.js` -> GitHub issue/JSON -> `*_ingest.py`). **0006-05** added a third
entry point (`hypothesis_store.py`) that touches neither queue. This gives
all three one shared vocabulary.

## States

`discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied
-> published -> superseded`

These extend **curation-item@v1**'s (0006-03) `status` enum with two states
that describe pipeline *position* rather than a curation-item's own
persisted field: `discovered` (before any queue/store entry exists) and
`published` (the change is visible in the generated HTML tree).

Two entry points intentionally skip intermediate states:

- `discovered -> applied` directly: the browser-ingest path
  (`review_ingest.ingest`) can write a decision straight into the record
  without ever touching a queue.
- `discovered -> proposed` directly: `hypothesis_store.record_hypothesis`
  (0006-05) has no queue of its own -- an AI proposing a brand-new spec
  element goes straight to "proposed, awaiting curator decision".
- `proposed -> applied` directly (not only via `accepted`):
  `review_flags.py` has no separate curator-accept step distinct from
  completion, so an AI-proposed decision on a review-queue item goes
  straight from `proposed` to `applied` when the flag is completed.
  `curation_flags.py`, by contrast, does have a distinct human accept step,
  hence `curation_flags.complete_flag` is also mapped as reachable from
  `"accepted"`.

## Tool-to-transition mapping

| Tool function | From | To | Notes |
|---|---|---|---|
| `review_flags.write_review_flag` | discovered | queued | Extraction can't auto-resolve an ambiguity. |
| `review_flags.claim_flag` | queued | claimed | Atomic `os.rename`; exactly one agent wins. |
| `review_flags.release_flag` | claimed | queued | Agent aborts. |
| `review_flags.complete_flag` | claimed, proposed | applied | Flag file deleted; decision already in the record. No separate accept step in this path. |
| `curation_flags.write_curation_flag` | discovered | queued | Written by `curation_ingest.py` after a browser package is accepted for queuing. |
| `curation_flags.claim_flag` | queued | claimed | AI agent claims to propose a concrete change. |
| `curation_flags.release_flag` | claimed | queued | Agent aborts. |
| `curation_flags.complete_flag` | claimed, proposed, accepted | applied | Only the human operating the extraction scripts calls this. |
| `review_ingest.ingest` | discovered, claimed | applied | Browser path; can skip queued/claimed entirely. |
| `curation_ingest.ingest` | discovered | queued | Writes a new curation-queue flag rather than applying directly. |
| `hypothesis_store.record_hypothesis` | discovered | proposed | No queue for hypotheses (0006-05); starts directly at proposed. |
| `hypothesis_store.promote_hypothesis` | proposed | applied | Mints a real canonical id, writes the record. |
| `hypothesis_store.reject_hypothesis` | proposed | rejected | Marked in place, never deleted. |
| `generate.py` (publish step) | applied | published | Regular HTML build; not a curation-queue tool. |
| next-release import (0006-15/0006-18 supersession) | published | superseded | Explicit edge, never inferred from timestamps. |

## Non-goals of this task

Does not change how any existing tool physically persists state -- queue
file existence (open/claimed/done directories) remains each queue tool's own
state representation; `workflow_lifecycle.py` is a shared reference
vocabulary and transition validator, not a rewrite of
`review_flags.py`/`curation_flags.py`/`review_ingest.py`/`curation_ingest.py`'s
underlying mechanics. That kind of physical unification, if ever desired, is
separate future work.
