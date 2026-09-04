---
schema_version: "1.0"
id: "0004-01"
level: "task"
parent: "0004"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:108"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0004-01:0006 — investigate 3811 spec records without an explicit namespace (e.g. `SWS_AIDSM_10706`, `SWS_AIDSM_10301`, `SWS_AIDSM_10602`, `SWS_AIDSM_10205`, `SWS_AIDSM_10710`), flagged by `validate.py` (2026-08-12, run.sh #252). Currently causes `validate.py` to exit 1. TODO: whether namespace should be inferred/backfilled during scrape/rebuild, or whether these records are legitimately namespace-less and validate.py's check needs an allowlist/exception similar to the existing PRS_E2E carve-out, is an explicit either/or choice in the task text itself; needs a manager/domain decision before implementation can start (flagged 2026-08-13 review). — DECIDED 2026-08-14: user ruled this shall be **the curator's decision** (case-by-case, not a blanket infer/backfill vs. allowlist policy choice made by the agent), with each case surfaced as a normal review request in the pipeline, attached to the affected record ID in published HTML, and linked from the traceability report. RESOLVED-BY-OBSOLESCENCE 2026-08-14 (verified via `run.sh` #109-#112): re-running `check_namespaces()` standalone today finds **0** namespace problems across all 3,882 spec records (349 PRS_E2E-exempt + 3,533 with a usable `namespace_meta.namespace` string; 0 missing/`None`). Git history confirms two intervening commits already closed this gap independent of this decision: `991603be` ("mechanically backfill status/history onto all records missing them", 0006-04) and `4fcb351e` ("actually backfill service-interface namespace for the 34 SWS_UCM/SWS_CM/SWS_SM records", 0008-07). `validate.py` currently exits 0 cleanly. The curator-decision review-request mechanism (per-ID flag in published HTML + traceability-report link) remains the correct design for *any future* recurrence of this class of finding, but there is currently no live case to route through it — building that plumbing now would have no record to attach it to. If `check_namespaces()` ever reports a new namespace-less record again, route it through `review_flags.py`/`curation_flags.py` (record-level, since these are class/type records without a `requirement_text` block, so the existing per-block review-panel in `lib_docmodel.py` does not apply) with a link from `traceability_report.py`'s namespace-deviation section, per this decision.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
