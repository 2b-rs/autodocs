---
schema_version: "1.0"
id: "0006-11"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:174"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

expose curator-visible history for each DB element in published pages -- DONE 2026-08-14: `_src/lib_docmodel.py` renders collapsible `.rec-history-panel` with status badges, full `history[]` transition timelines, and verified depth-aware relative links to `curation-report.html`. Documented in `docs/pipeline/rec-history.md`; tested in `_src/tests/test_rec_history.py`.

## Scope

- Current gap: record pages do not systematically surface `history[]`, status evolution, or open review/curation state to users.
  - Add a visible section/badge on record pages showing current review/curation status, latest accepted decision, and links to the relevant curation item/report entry.
  - This should work for both existing records and future AI-proposed elements, with clear labeling of "proposed", "accepted", "rejected", and "applied".

### Hardening / migration

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
