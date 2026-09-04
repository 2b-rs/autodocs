---
schema_version: "1.0"
id: "0006-08"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:166"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

resurrect and implement campaign manifests as the versioning backbone for curation work

## Scope

- Current gap: `docs/pipeline/data-model.md` documents `_src/spec/campaigns/<id>.json`, but explicitly notes no such manifest files were found in the repo.
  - Use campaign manifests to version review/curation waves across projects/releases (source corpus hash, tool versions, queue snapshot, curator decisions, published reports) so a curator can later answer "which exact state of the corpus and tools produced this request?" -- DONE 2026-08-13: added `_src/tools/campaign_manifest.py` implementing the campaign-manifest@v1 schema already documented in `campaigns.md` (trigger, release, scope, tool git commit, backends, a cheap listing-based `corpus_hash`, and a queue snapshot), plus append-only `curator_decisions`/`published_reports` lists via `append_decision()`/`append_report()`. Backfilled manifests for all 3 real campaign IDs found in records. Added `_src/tests/test_campaign_manifest.py`. Documented in `docs/pipeline/campaign-manifest-schema.md`; updated `campaigns.md`'s 'not materialized' caveat. Does not wire spec_scrape.py's --campaign flag to auto-write manifests (no such caller exists yet, same scoping pattern as 0006-05/06/07). REF: 53eb37ae

### Visibility / UX

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
