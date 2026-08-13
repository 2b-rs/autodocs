# Campaign Manifest Schema (campaign-manifest@v1, Feature 0006-08)

Status: implemented 2026-08-13. Path: `_src/spec/campaigns/<campaign-id>.json`.
Writers: `_src/tools/campaign_manifest.py`.

## Fields

| Field | Type | Notes |
|---|---|---|
| `schema` | string | Always `"campaign-manifest@v1"`. |
| `campaign` | string | The campaign id, matching the file stem. |
| `trigger` | string \| null | Why this campaign ran, e.g. "spec update after tool improvement". |
| `release` | string \| null | AUTOSAR release, if applicable. |
| `scope` | string \| null | Human-readable subset description, e.g. "SWS_LOG pilot module". |
| `created` | string (ISO 8601) | Set once, on first write. |
| `updated` | string (ISO 8601) | Refreshed on every `write_manifest(..., overwrite=True)` or append call. |
| `tool_git_commit` | string \| null | Git commit hash that last touched `_src/tools/spec_scrape.py`. |
| `backends` | list | Extraction backends in use for this campaign, if known. |
| `corpus_hash` | string \| null | hash8 of a sorted (relative path, mtime) listing of every file under `_src/spec/records/`. Detects "did the record set change", not a content archive. `null` if the records directory doesn't exist. |
| `queue_snapshot` | object | `{"review-queue": {"open": n, "claimed": n, "done": n}, "curation-queue": {...}}`, counted at write time. |
| `curator_decisions` | list | Append-only; grows via `append_decision(campaign_id, decision_ref)`. |
| `published_reports` | list | Append-only; grows via `append_report(campaign_id, report_ref)`. |

## Refresh semantics

`write_manifest(campaign_id, ...)` without `overwrite=True` is idempotent --
calling it again on an existing manifest is a no-op (returns the existing
path unchanged). With `overwrite=True`, `trigger`/`release`/`scope`/
`backends` are updated to any newly-passed values (or kept from the
existing manifest if omitted), while `tool_git_commit`/`corpus_hash`/
`queue_snapshot` are always recomputed to their current state --
`curator_decisions`/`published_reports` are always preserved, since those
only ever grow via the dedicated append functions, never via `write_manifest()`.

## Backfilled campaigns

Three campaign IDs found in real records were backfilled with manifests on
implementation day: `2026-08-sws-log-pilot-after-tool-improvement`,
`requirement-import`, `legacy-desc-import`. See `campaigns.md` for what each
represents.

## Non-goals of this task

Does not retroactively wire `spec_scrape.py`'s `--campaign` flag to
automatically call `write_manifest()` -- no such caller exists yet, matching
the scoping pattern of 0006-05/0006-06/0006-07 (primitives + docs + tests,
future callers wire themselves in as needed). Does not implement PDF-cache
hashing (`docs/pipeline/campaigns.md`'s original schema mentions it, but no
PDF cache exists in this sandbox to hash against).
