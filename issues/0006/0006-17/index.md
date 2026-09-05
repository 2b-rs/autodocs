---
schema_version: "1.0"
id: "0006-17"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-15"
  - "0006-16"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:211"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-17:0006-15, 0006-17:0006-16 — pin every curation decision and evidence snippet to the exact requirement version they judged or extracted from

## Scope

- Add a `decided_on_version` field (requirement-version ID) to the unified curation-item schema from **0006-03**, populated at decision time.
  - Add an equivalent `source_version` field to each `evidence:<uuid7>` snippet so first-pass extraction always points at one immutable requirement snapshot.
  - Without these pins, drift detection can only say "this record changed since some undated point," not "this decision/evidence snippet is now stale relative to version X." -- DONE 2026-08-13: added `decided_on_version` (nullable) to the curation-item@v1 schema in `curation_item.py` (both adapters), with a `resolve_decided_on_version()` helper for future writer wiring. Introduced `_src/tools/evidence_snippet.py`, the first-class `evidence:<uuid7>` object conceptually named in 0006-15/0006-18 but never previously constructed, with a MANDATORY `source_version` pin (unlike decided_on_version, which is nullable for legacy decisions) and an `is_stale()` drift check against the 0006-16 version store. Documented in `docs/pipeline/curation-item-schema.md` and new `docs/pipeline/evidence-snippet.md`; unit tests in `_src/tests/test_curation_item_versioning.py`. Does NOT wire existing writers (review_flags.py/curation_flags.py/spec_scrape.py) to populate these fields at write time -- that remains future work, consistent with 0006-15/0006-16's own scoping. REF: b576a180

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
