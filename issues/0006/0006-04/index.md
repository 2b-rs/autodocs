---
schema_version: "1.0"
id: "0006-04"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:145"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-04:0006-03 — extend the record schema to carry stable provenance for curator-visible changes across all modules, not just pilot records

## Scope

- Current gap: `history[]`, `status`, and field-level states exist mostly in pilot-style records (`SWS_LOG` etc.), while many production records still only carry additive fields like `upstream` without matching lifecycle/history entries.
  - Make `status`, `history[]`, and (where applicable) field-level `fields.<name>.state/reason/trace` mandatory or mechanically backfillable for any write path (`spec_scrape.py`, `review_ingest.py`, `curation_ingest.py`, migrations, future AI-amendment tools).
  - Add explicit provenance for AI-originated proposals vs. curator-accepted DB changes so that "proposal" and "applied truth" remain distinguishable in static and dynamic views. -- DONE 2026-08-13: added `_src/tools/migriere_status_backfill.py`, a one-shot idempotent migration that adds `status`/`history` to every record lacking them (3459 of 3882) with an HONEST `state="valid/unmigrated"` (never claiming a real review that didn't happen, unlike SWS_LOG's campaign-derived `"valid/auto-approved"`). Added `validate.py`'s `check_record_status()` to prevent future write paths from regressing. Field-level `fields.<name>` backfill (no real per-field vote data exists outside the pilot set) is explicitly deferred as a documented limitation, not silently dropped. REF: 991603be

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
