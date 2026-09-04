---
schema_version: "1.0"
id: "0021-06"
level: "task"
parent: "0021"
state: "closed"
visibility: "internal"
prerequisites:
  - "0021-05"
labels:
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:342"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0021-06:0021-05 Render review-request state and traceability in record history and curation/report views. HISTORICAL CLAIM ONLY: `local-20260815-0021-06` is not a Git object; no independent completion evidence credited.

## Scope

- **Closure evidence (2026-08-15)**: `lib_docmodel.py` derives open review-request state from `spec/curation-queue/{open,claimed}` and renders request identity/target-version/status snapshot/queue-file link on record pages; `curation_item.py` fixed so `outcome="requested"` maps to `open`/`claimed` rather than `proposed`; `curation_report.py` extended to show requester trust/transport/target-version for `review-request` items and to stop dropping terminal statuses (`accepted`/`rejected`/`proposed`/`superseded`) from report views. 51 tests passing (new coverage: duplicate suppression, lifecycle mapping, report rendering).

### Campaign C — Assurance and Release

## Acceptance criteria

- **AC-001** An ingested/queued request is discoverable from the target record’s history/details and from curation reports
- **AC-002** views show request identity, lifecycle state, status snapshot, target version, actor/trust presentation consistent with privacy rules, and a durable link to the queue item and available transport receipt
- **AC-003** exported packages and submitted-but-not-ingested GitHub issues are not represented as queue/history state, and the record remains visibly valid until a later governed decision changes it

## Definition of Done

Generated-page and report assertions cover a valid curator-decided record with an open re-review request plus accepted and rejected lifecycle outcomes; browser/ingestion tests separately prove that stale or otherwise rejected pre-ingest submissions create no queue/history entry; link and DOM validation pass.
