---
schema_version: "1.0"
id: "0021-08"
level: "task"
parent: "0021"
state: "closed"
visibility: "internal"
prerequisites:
  - "0021-07"
labels:
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:354"
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

PREREQ: 0021-08:0021-07 Publish the feature, update operating guidance, and close the implementation campaign. HISTORICAL CLAIM ONLY: `local-20260815-0021-08` is not a Git object; the former `ship as-is` statement is revoked and no release evidence is credited.

## Scope

- **Closure evidence (2026-08-15)**: Operator guidance added as `docs/pipeline/website-review-flag.md` §"Operator guidance: submit, triage, decide, follow", with an explicit authority/confidence framing subsection and a "Known limitations (for release notes)" subsection covering identity-strength, self-declared-identity, triage-latency, and export-not-submitted limitations. Tool catalog (`docs/pipeline/tools.md`) and report catalog (`docs/pipeline/reports.md`) updated to document `review_request_ingest.py`, `curation_item.py`, `curation_report.py`, `open_reviews_report.py`, and `check_review_request_ui.cjs`, replacing the stale "future curation report" placeholder. Release decision: ship as-is; no blocking residual items. Full pipeline verified green: report rebuild, focused pytest (review-request + curation-item suites), `generate.py --lang=alle` (de + 10 language trees), `validate.py` → "alle internen Links und Anker gültig, keine Waisen".

## Acceptance criteria

- **AC-001** Operator and user guidance explains how to submit, triage, decide, and follow a website-originated re-review request
- **AC-002** reports identify web-originated requests without overstating their authority
- **AC-003** release notes identify security/privacy and process limitations

## Definition of Done

Full generation, validation, and regression checks pass; the feature Definition of Done is evidenced by committed documentation, tests, and generated output; campaign closure records the release decision and any residual follow-up items.
