---
schema_version: "1.0"
id: "0021-07"
level: "task"
parent: "0021"
state: "closed"
visibility: "internal"
prerequisites:
  - "0021-03"
  - "0021-05"
  - "0021-06"
labels:
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:349"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0021-07:0021-03, 0021-07:0021-05, 0021-07:0021-06 Verify end-to-end lifecycle, authorization, and anti-bypass behavior. HISTORICAL CLAIM ONLY: `local-20260815-0021-07` is not a Git object; no independent completion evidence credited.

## Scope

- **Closure evidence (2026-08-15)**: Full pipeline run: `curation_report.py build` + `open_reviews_report.py build`, focused pytest (review-request rendering/browser/package/ingest, curation-item lifecycle/versioning, curation-report — all passing), `generate.py --lang=alle` (canonical + 10 translated trees), `validate.py` → "alle internen Links und Anker gültig, keine Waisen". Found and fixed a real hygiene bug in `test_curation_report.py` that was leaking a synthetic `records/rec1.html` link into the real build via unsandboxed `PAGE_MODEL`/`DATASET_JSON` writes; also cleared a stray `_review_request_probe/` fixture directory from earlier manual debugging.

## Acceptance criteria

- **AC-001** An end-to-end fixture demonstrates published record → browser request → validated ingestion → queued item → claim/proposal → human accept/reject → governed application/closure
- **AC-002** negative tests cover altered target identity/hash, spoofed actor/trust metadata, stale/duplicate requests, and prove that UI, AI, and ingestion cannot silently approve, reject, close, or edit a record outside their permitted roles

## Definition of Done

Automated test suite and validation reports pass; findings are recorded and resolved or explicitly queued; traceability from rendered control through submission and queue item to the record is reproducible.
