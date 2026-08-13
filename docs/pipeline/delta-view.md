# Delta View: What Changed Since a Release or Date (Feature 0006-24)

Status: implemented 2026-08-13. Module: `_src/tools/delta_view.py`.

## Relationship to 0006-20

Per the task text, this is a QUERY over the stored cascade results 0006-18
(dependency graph), 0006-19 (confidence/invalidation), and 0006-20
(supersession trigger) already produce -- not a second cascade mechanism.
0006-20's `process_trigger()` reports the immediate blast radius of ONE
trigger; `delta_view()` aggregates across an arbitrary time/release window
for ad-hoc review.

## Baseline resolution

`resolve_baseline_timestamp(release=None, date=None)` (exactly one
required): a `date` is used unchanged (already ISO-sortable). A `release`
is resolved to the earliest `recorded_at` timestamp of any version tagged
with that release anywhere in the corpus -- documented, not hidden, because
invalidation (`invalidated_at`) and revisit (`enqueued_at`) timestamps are
wall-clock, not release-tagged, so a release baseline must become a
timestamp to be comparable against those two stores. An unknown release
returns `None` (an empty delta), not an error -- a caller querying a
release that was never recorded is a valid (if unusual) empty-result query.

## `delta_view(release=None, date=None)` return shape

| Field | Meaning |
|---|---|
| `baseline` | `{release, date, resolved_timestamp}` -- echoes what was asked and what it resolved to. |
| `changed_requirements` | Canonical IDs with a version recorded after the baseline. |
| `invalidated_nodes` | Full `confidence.INVALIDATED_FILE` entries (`node_id`, `reason`, `invalidated_at`) since the baseline. |
| `revisit_tasks_enqueued` | Count of `confidence.REVISITS_FILE` entries since the baseline. |
| `revisit_tasks` | The full entries backing that count. |

## Schema alignment with 0006-20

Field names deliberately echo `supersession_trigger.summarize_reports()`'s
output shape (`changed_requirements`, `revisit_tasks_enqueued`) per the
task's explicit instruction to align rather than invent a second,
incompatible "what changed" format.

## Non-goals of this task

Does not add any new cascade/invalidation logic -- purely a read-side
aggregation over 0006-18/19/20's existing stores. Does not build a CLI or
HTML render (same deferral rationale as 0006-23, pending 0006-14).
