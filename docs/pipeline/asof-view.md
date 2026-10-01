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

## Exposure (CLI, Server API & HTML Presentation)

As completed under Feature **0006-23** / **0006-14**:
1. **CLI Query Interface:** `_src/tools/asof_view.py <id> [--release R] [--date D] [--json]` allows direct point-in-time state inspection from the terminal. Companion tool `_src/tools/delta_view.py [--release R] [--date D] [--json]` reports differences since any release.
2. **Server API Routes:** `_src/serve.py` exposes `/api/asof?id=...&release=...` and `/api/versions?id=...`, returning structured JSON for client-side point-in-time exploration.
3. **HTML Presentation & Version Navigation:** `_src/lib_docmodel.py` renders `.rec-version-nav` inside each record's `<details class="rec-history-panel">`, featuring active version badges, an interactive release switcher (`<select data-asof-select>`), a multi-version timeline, and an inline point-in-time snapshot container (`.rec-asof-display`). Client-side interactivity is handled via `review_request.js`.

