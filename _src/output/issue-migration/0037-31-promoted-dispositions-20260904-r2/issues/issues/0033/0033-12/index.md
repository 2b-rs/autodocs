---
schema_version: "1.0"
id: "0033-12"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-04"
  - "0033-04.01"
  - "0033-06"
  - "0033-10"
  - "0033-11"
  - "1788"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:919"
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
---

## Goal

PREREQ: 0033-12:0033-04, 0033-12:0033-04.01, 0033-12:0033-06, 0033-12:0033-10, 0033-12:0033-11 Implement and verify keyboard, focus, dialog, responsive/mobile, live-announcement, and no-JavaScript behavior.

## Scope

Claim: `DONE-worf-0033-12-20260901.md`; owner_token:
  `agent:worf:0033-12:1788268588967-8f39ee85`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788269009832-a7b7807e` (Offer `1788269009832-a7b7807e` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:25:00Z`
  - **Baseline findings:** `RRB-UX-001`, `RRB-NOJS-001`, `RRB-BROWSER-001`.
  - **Previous implementation flaws:** There was no focus trap, dialog title IDs were reused, context lacked an accessible description relationship, dynamic states lacked live semantics, hidden errors could not receive focus, cancellation focus was incomplete, mobile behavior did not implement the specified sheet, and the visible action was inert without JavaScript.
  - **Completion evidence (2026-09-01):** Verified keyboard, focus, dialog, responsive/mobile, live-announcement, and no-JavaScript behavior in review request frontend. Tests: 100 passed across `test_review_request_browser.py`, `test_review_request_rendering.py`, `test_review_request_ingest.py`, `test_review_request_package.py`, `test_review_request_baseline_audit.py`, `test_review_request_retention.py`, and `test_review_request_package_v2_contract.py`.

### Campaign D — Realistic End-to-End Assurance and Closure

## Acceptance criteria

- **AC-001** Every action is natively keyboard-operable
- **AC-002** each dialog has unique labelled/described IDs, `aria-modal`, background inertness or equivalent, contained Tab/Shift-Tab order, visible focus, initial/failure/confirmation focus, Escape/cancel behavior, and restoration to the invoking control
- **AC-003** dynamic success/failure states use appropriate live/alert semantics. At named viewport breakpoints the layout is usable without clipped controls or lost target context. With JavaScript disabled, an accessible link opens a prefilled GitHub intake containing target context explicitly treated as an untrusted claim unless protected by an approved tamper-evident token and clear not-yet-submitted wording
- **AC-004** the trusted Issue adapter derives UUID/timestamps/actor/receipt after submission, performs authoritative target lookup plus source-page/origin consistency checks, and signed-out/login, disabled-Issue, edited-prefill, missing/unverified-actor, and failure expectations are documented. No-JS markup must not be an inert button or pretend to create a schema-valid browser package before GitHub assigns envelope data

## Definition of Done

DOM/accessibility assertions plus keyboard-only browser tests cover multiple panels/dialogs, unique IDs, focus loop/restoration, labels/descriptions/errors/live regions, zoom/narrow viewport, reduced motion where applicable, and the no-JS link/intake normalization path; screenshots supplement but do not replace assertions.
