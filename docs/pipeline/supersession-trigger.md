# Supersession-Trigger Job (Feature 0006-20)

Status: implemented 2026-08-13. Module: `_src/tools/supersession_trigger.py`.

## What this generalizes

Before this task, nothing generalized "a release changed, walk dependents,
invalidate, enqueue revisit" beyond an ad-hoc release-diff notion. This
module is deliberately thin: it does NOT reimplement graph-walking or
invalidation, which already existed and were already tested as of 0006-18
(`dependency_graph.find_dependents()`) and 0006-19
(`confidence.cascade_invalidate()`, which already walks dependents AND
records a `cascade_invalidation` confidence event that enqueues a revisit).

## Trigger kinds (all 6 named in the task text)

`new_release`, `new_curation_input`, `user_comment`, `scraper_update`,
`extraction_bugfix`, `new_source_available`, `ai_model_change` --
`supersession_trigger.TRIGGER_KINDS`.

## `process_trigger(trigger_kind, canonical_id, release, content, reason=None)`

1. Rejects an unknown `trigger_kind` as `unresolved` (does not crash).
2. Diffs `content` against `version_store.latest_version(canonical_id)` by
   recomputing the candidate `version_id` via
   `version_id.requirement_version_id()` and comparing it against the
   stored version's `version_id` -- the SAME idempotency check
   `version_store.record_version()` performs internally, so a truly
   unchanged trigger never produces a spurious new version. An unchanged
   trigger is a documented no-op (`changed=False`).
3. On a genuine change: records the new immutable version
   (`version_store.record_version()`, 0006-16) and calls the existing
   `confidence.cascade_invalidate()` (0006-19) on `canonical_id`, which
   walks `dependency_graph.find_dependents()` (edges where `from` matches
   the changed node, transitively) and marks every reachable dependent
   invalidated.
4. Returns a report dict: `trigger_kind`, `canonical_id`, `release`,
   `changed`, `new_version_id`, `dependents_invalidated`,
   `revisit_enqueued`, `unresolved`.

## `summarize_reports(reports)`

Aggregates a batch into exactly the shape the task text asks for: changed
requirements, superseded decisions/evidence/artifacts (dependents
invalidated across the batch), revisit tasks enqueued, unresolved cases.

## Non-goals of this task

Does not wire this into a real caller (no scraper/ingest tool calls
`process_trigger()` automatically yet -- same primitives-first scoping as
0006-05 through 0006-19). Does not feed `summarize_reports()`'s output into
**0001**'s build-report pipeline, since Feature 0001 does not exist yet in
this repo -- `write_report()` persists each trigger's report as its own
JSON file under `_src/spec/supersession-reports/` in the meantime, ready to
be picked up once 0001 lands.
