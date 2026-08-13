# AI-Proposed New Elements (`hypothesis:<uuid7>`, Feature 0006-05)

Status: defined 2026-08-13 for **0006-05**. Implemented in
`_src/tools/hypothesis_store.py`.

## Why

`hypothesized/unconfirmed` existed only as prose in the process docs --
no CLI or queue path ever created such an element. This closes that gap by
giving AI-proposed new spec elements a concrete, queryable object with a
defined promotion path into the main DB.

## Where hypotheses live before acceptance

A **separate store**, not a lightweight record stub in
`_src/spec/records/`: an unconfirmed AI guess must never be
indistinguishable -- even transiently -- from a real curated record.
Hypotheses live under `_src/spec/hypotheses/<project-slug>/<hypothesis-id-slug>.json`
until a human curator promotes or rejects them.

## Identity before promotion

`hypothesis:<uuid7>` (`version_id.hypothesis_id()`, extends the
`curation:`/`evidence:`/`artifact:` id family from **0006-15** with a 4th
prefix). The hypothesis's *proposed* `(project, kind, proposed_id)` is
deliberately **not** a `canonical_id` yet -- `canonical_id.is_valid()` only
validates that `(project, kind)` is a registered pair, not that `id` is
unique against not-yet-existing records, so `proposed_id` stays plain text
until promotion actually mints the real canonical id.

## Lifecycle

`open` -> `rejected` (marked in place, file never deleted -- same
never-delete precedent as the **0006-16** version store) or `open` ->
`applied` (via `promote_hypothesis()`, which mints a real canonical id via
`canonical_id.canonical_id()` and writes a new record into
`_src/spec/records/`). `status`/`item_kind='ai-hypothesis'`/`origin='ai'`
follow the **curation-item@v1** enum from **0006-03**, so hypotheses remain
expressible in that unified schema.

## Promotion without losing history

`promote_hypothesis()` writes the new record's first `history[]` entry with
an explicit `source_hypothesis` field pointing back at the originating
`hypothesis:<uuid7>` id, and marks the hypothesis itself `applied` with
`promoted_to` set to the new canonical id -- so the link is traceable in
both directions. Promotion refuses to overwrite an existing record at the
target path (one-shot per `proposed_id`).

## API

- `record_hypothesis(project, kind, proposed_id, subject, proposed_state, evidence=None, decision_basis=None) -> dict`
- `get_hypothesis(hyp_id) -> dict | None`
- `list_hypotheses(project=None, status=None) -> list[dict]`
- `reject_hypothesis(hyp_id, reason, decided_by) -> dict`
- `promote_hypothesis(hyp_id, decided_by, reason=...) -> dict`

## Non-goals of this task

Does not wire any existing tool (`spec_scrape.py`, a future AI-amendment
tool, etc.) to actually start CREATING hypotheses automatically -- there is
no existing "AI proposes a new element" caller yet to integrate; this task
provides the store and promotion primitives for that future caller to use,
consistent with how 0006-15/0006-16/0006-17 were scoped.
