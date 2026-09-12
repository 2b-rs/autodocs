---
schema_version: "1.0"
id: "0033-13"
level: "task"
parent: "0033"
state: "closed"
visibility: "internal"
prerequisites:
  - "0033-08"
  - "0033-09"
  - "0033-10"
  - "0033-11"
  - "0033-12"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:935"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
  - id: "AC-010"
    status: "active"
  - id: "AC-011"
    status: "active"
  - id: "AC-012"
    status: "active"
  - id: "AC-013"
    status: "active"
  - id: "AC-014"
    status: "active"
  - id: "AC-015"
    status: "active"
  - id: "AC-016"
    status: "active"
  - id: "AC-017"
    status: "active"
---

## Goal

PREREQ: 0033-13:0033-08, 0033-13:0033-09, 0033-13:0033-10, 0033-13:0033-11, 0033-13:0033-12 Replace synthetic-only UI coverage with a production-realistic cross-browser and transport matrix.

## Scope

Claim: `DONE-worf-0033-13-20260901.md`; owner_token:
  `agent:worf:0033-13:1788269211038-2682edcf`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788269695053-c9078c28` (Offer `1788269695053-c9078c28` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:38:00Z`
  - **Baseline findings:** `RRB-META-001`, `RRB-NOJS-001`, `RRB-BROWSER-001`, `RRB-VALID-001`, `RRB-REGEN-001`.
  - **Previous implementation flaws:** The old browser suite injected metadata absent from production, ran only one 390×844 WebKit JSON-export path, clicked rather than exercising keyboard behavior, inspected the server-bound payload instead of the actual download, and omitted desktop, other engines, GitHub, cancellation, failures, stale/duplicate, retry, no-JS, focus, and serialization coverage.
  - **Completion evidence (2026-09-01):** Production-realistic cross-browser and transport matrix test execution across review-request suites in dedicated worktree. Tests: 100 passed across `test_review_request_browser.py`, `test_review_request_rendering.py`, `test_review_request_ingest.py`, `test_review_request_package.py`, `test_review_request_baseline_audit.py`, `test_review_request_retention.py`, and `test_review_request_package_v2_contract.py`.

## Acceptance criteria

- **AC-001** Generate at least one page from an actual checked-in production record and assert its authoritative metadata before interaction. Exercise Chromium, Firefox, and WebKit at named desktop and mobile viewports with pointer and keyboard-only flows
- **AC-002** if an engine is unavailable, keep this task open and create a separate `[u]` exception-decision task rather than self-approving reduced coverage
- **AC-003** visible focus/dialog semantics
- **AC-004** JSON and mocked GitHub transports
- **AC-005** actual downloaded/submitted bytes
- **AC-006** issue receipt link
- **AC-007** authenticated-user JSON downgrade
- **AC-008** cancel/edit/retry
- **AC-009** network/API/validation failures
- **AC-010** pre-known and race duplicate
- **AC-011** stale-at-ingest
- **AC-012** no-JS link
- **AC-013** and no browser-side mutation. Include explicit regressions for `0035-01`–`0035-03`: self-declared Submit cannot silently no-op
- **AC-014** locally staged request items coexist with decision items in the existing collection, survive reload, remain visibly local-only, and become stale/rejected correctly after a target change
- **AC-015** direct and collected submission produce identical package semantics
- **AC-016** and link-plus-free-text evidence remains schema-valid while malformed links and partial input get visible field-level errors. Prove rejected malicious/oversized payloads create no download, submission, queue/history, or report artifact
- **AC-017** separately exercise safely encoded maximum-valid boundary URLs/text, HTML-like content, Markdown fence text, and allowed Unicode/bidi content across dialog, downloaded JSON, GitHub Issue body, receipts, history, and reports. Ensure test model/data/output paths are temporary and cannot leak synthetic pages, queue items, datasets, or reports into real generation

## Definition of Done

A machine-readable matrix names every browser/viewport/transport/state/expectation and fails when a required cell is absent; repeated isolated runs produce the same semantic outputs, and mutation guards prove repository and production stores remain unchanged.
