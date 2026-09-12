---
schema_version: "1.0"
id: "0006-12"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:181"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-12:0006-03 — inventory and migrate existing queue items and special-case review surfaces into the unified model

## Scope

- Inputs to cover: `review-queue`, `curation-queue`, extraction-report `RESIDUAL` items, ad-hoc TODO-driven investigations like the 34 service-method namespace conflict, and any pilot record-level `requirement_meta.review_*` states.
  - Define which of these become first-class curation items, which remain reports only, and which are historical artifacts to archive. -- DONE 2026-08-13: added `_src/tools/curation_inventory.py`, a read-only scanner classifying all 4 named input categories into first_class/report_only/historical_archive with a documented rule each. Real counts: 349 open review-queue items and 34 open curation-queue items (confirmed to be exactly the '34 service-method namespace conflict' via their shared campaign field) classified first_class (already losslessly normalized read-only by 0006-03's adapters, so no physical file migration needed); 3 extraction_report.RESIDUAL entries classified report_only (finished code-level decisions, not pending items); 47 SWS_LOG pilot records' requirement_meta.review_* fields classified historical_archive (predates the model, pilot campaign already completed). Added `_src/tests/test_curation_inventory.py`. Documented with full rationale and current counts in `docs/pipeline/curation-inventory.md`. Does not build the 0006-09 report itself (still blocked on 0001-08) or alter any scanned file. REF: 50761057

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
