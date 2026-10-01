# Immutable Requirement-Version Store (0006-16)

Status: implemented 2026-08-13 in `_src/tools/version_store.py`. Keyed by
the requirement-version ID from **0006-15**
(`<canonical-id>@rel:<release>#<hash8>`).

## Relationship to the existing record store

`_src/spec/records/<MODULE>/<ID>.json` (written by `spec_scrape.py`) remains
the **current-pointer** view: one file per requirement, overwritten in
place on every scrape. This new store is the **full history**: every
distinct `(release, content)` snapshot ever recorded for a requirement,
never overwritten, never deleted.

## Layout

```
_src/spec/versions/<project>/<kind>/<id>.jsonl
```

One append-only JSON-Lines file per requirement (e.g.
`_src/spec/versions/AUTOSAR/AP/record/SWS_UCM_00348.jsonl`), one JSON
object per line: `version_id`, `canonical_id`, `release`, `content`,
`meta`, `recorded_at`.

## Guarantees

- **Append-only**: `record_version()` only ever adds a line; it never
  rewrites or truncates existing lines.
- **Idempotent**: recording the same `(release, content)` twice yields the
  same `hash8` and thus the same `version_id`; a duplicate append is
  skipped, so re-running a scrape over unchanged input never bloats the
  file.
- **Retention**: nothing is ever deleted. `list_versions()`/`get_version()`
  can retrieve any prior snapshot indefinitely.

## Non-goals of this task

This task adds the store and its API only. It does **not** yet wire
`record_version()` calls into `spec_scrape.py`'s write path (so no
versions are recorded automatically yet), and does not implement pinning
decisions/evidence to specific versions -- both remain **0006-17** scope.
