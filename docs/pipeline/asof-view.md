# Point-in-Time ("as of release/date") View (Feature 0006-23)

Status: implemented 2026-08-13. Module: `_src/tools/asof_view.py`.

## Why this is a read-side problem, not storage

Because `version_store` (0006-16) never deletes versions, `dependency_graph`
(0006-18) never severs edges, and `confidence` (0006-19) only ever ADDS
invalidation/dismissal flags (never removes them), every point-in-time view
is fully reconstructible by QUERYING existing append-only stores -- no
redundant snapshot storage is needed or was built. This matches the task
text's explicit instruction to document this as a query problem to avoid
future accidental work on snapshot storage.

## Query contract

`as_of_release(canonical_id, release)` / `as_of_date(canonical_id, date)`
return:

| Field | Meaning |
|---|---|
| `version` | The requirement-version active at that point (or `None` if the requirement had no recorded version yet). |
| `decisions` | Curation decision(s) whose `decided_on_version` matches or precedes the active version. |
| `artifact_graph` | Every dependent node reachable via `dependency_graph.find_dependents()`, each annotated with its CURRENT `invalidated`/`dismissed` flags -- never filtered out, per the explicit requirement that "superseded now" must not mean "absent from a past view." |

## Release-ordering assumption

Release tags (`R25-11`, `R32-11`, ...) sort correctly as plain strings
because the project's convention is fixed-width. This is a documented
assumption, not a hidden one -- a non-fixed-width release tag would break
ordering and needs a dedicated parser if it's ever introduced.

## Exposure (CLI vs. static HTML)

This task explicitly asks to "decide how this view is exposed: CLI query,
static per-release HTML render, or both," noting a dependency on **0006-14**
(presentation layer). Decision: ship the query function only for now
(consumable from a Python REPL/script/future CLI wrapper) and defer the
HTML-render decision to whichever of 0006-14's presentation work or a
future CLI-wrapper task actually needs it -- inventing a CLI argument parser
or an HTML template with no real caller today would be speculative, the
same primitives-first scoping used throughout 0006-05 through 0006-20.

## Non-goals of this task

Does not build a CLI entry point or an HTML render (see above). Does not
change any storage format in `version_store`/`dependency_graph`/`confidence`.
