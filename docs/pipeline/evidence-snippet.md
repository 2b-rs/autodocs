# Evidence Snippets (`evidence:<uuid7>`, Feature 0006-17)

Status: defined 2026-08-13 for **0006-17**. Implemented in
`_src/tools/evidence_snippet.py`.

## Why

The unified curation-item schema's `evidence` field (**0006-03**) is a
descriptive list of strings. `evidence:<uuid7>` was named as an id family
in **0006-15** and given a node kind in **0006-18**'s dependency graph, but
until now nothing constructed one as a concrete object. Without a mandatory
pin to an exact requirement version, drift detection can only say "this
record changed since some undated point," never "this evidence snippet is
now stale relative to version X." This module closes that gap.

## Shape

```json
{
  "id": "evidence:<uuid7>",
  "canonical_id": "AUTOSAR/AP/record/SWS_UCM_00348",
  "source_version": "<canonical-id>@rel:<release>#<hash8>",
  "text": "...",
  "reason": "missing_space_suspects",
  "meta": {},
  "created": "2026-08-13T21:00:00+00:00"
}
```

`source_version` is **mandatory** and validated to be a well-formed
requirement-version id (`version_id.parse_version_id()`); this differs
deliberately from `curation-item@v1`'s `decided_on_version`, which is
nullable because many existing/legacy decisions predate version minting.
A fresh evidence snippet has no such excuse -- it can always be pinned at
extraction time.

## Storage

Append-only JSONL, one file per canonical requirement:
`_src/spec/evidence/<project>/<kind>/<id>.jsonl` -- mirrors
`version_store.py`'s layout and write-via-tmp-then-atomic-replace pattern.

## API

- `record_evidence_snippet(source_version, text, reason, meta=None) -> dict`
- `list_evidence_snippets(canonical_id) -> list[dict]`
- `is_stale(snippet) -> bool` -- compares `source_version` against
  `version_store.latest_version()` for the same requirement.

## Non-goals of this task

Does not wire `spec_scrape.py`/`review_flags.py`/`curation_flags.py` to
actually call `record_evidence_snippet()` or populate `decided_on_version`
at write time -- that remains future work, consistent with how 0006-15
and 0006-16 were scoped (design + storage primitives, not writer
migration).
