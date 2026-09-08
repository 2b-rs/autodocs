---
schema_version: "1.0"
id: "0033-07.02"
level: "subtask"
parent: "0033-07"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-02"
  - "0033-04.01"
  - "0033-07"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:844"
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

PREREQ: 0033-07.02:0033-02, 0033-07.02:0033-04.01, 0033-07.02:0033-07 Implement the approved privacy, retention, redaction, expiry, and disposal policy across active/done queues, receipts/envelopes, history, reports, logs, exports, and external GitHub Issues/comments/attachments where controllable, with explicit consent and limitation handling where external deletion cannot be guaranteed.

## Scope

- **Integration review: mandatory.** **Rationale (architect):** recorded by Architect `seven`, 2026-08-30, in `docs/dossiers/0033-02-04-architect-scope-review.md` §4.2 under award `1788084568192-5900e508`. This is the only node in Feature `0033` with an irreversible external effect: it governs privacy, retention, redaction, expiry and disposal across queues, receipts, history, reports, logs, exports and **public GitHub projections**, and data published to a public Issue cannot be recalled. The candidate suite itself records controller deletion limits as accepted residual risk (`PROC-0033-02-13`, `-14`, `-16`). Irreversibility is checkpoint-triggering independently of size.
  - **Baseline finding:** `RRB-PRIV-001`.
  - **Previous implementation flaw:** Documentation claimed actor deletion while completed payloads retained it indefinitely; the implementation had no policy enforcement for actor claims, trusted envelope metadata, rationale/evidence, diagnostics, receipts, logs, rejected items, or report projections.
  - **Completion evidence (2026-09-01):** Candidate commit `f427a280c4` on branch `chain-0033-07.02` (`worf`). Implemented privacy, retention, redaction, expiry, and disposal policy across queues, receipts, history, reports, and public projections per authority decisions `PROC-0033-02-08/12/13/14/15/16`. Tests: 69 passed in `test_review_request_retention.py`, `test_review_request_ingest.py`, `test_review_request_package.py`.
  - **Acceptance: ✓** (2026-09-01, Integrator `obrien`, award `1788229641611-ec3716a9`, review REF `docs/campaign-evidence/0033-recovery/integration-review-0033-07.02-obrien-20260901.md`).

## Acceptance criteria

- **AC-001** Classify every field and storage/projection location
- **AC-002** enforce access, retention period, redaction/pseudonymization, expiry/disposal, legal/audit holds, and public-report minimization
- **AC-003** preserve auditable markers and required non-sensitive trace after disposal without retaining forbidden raw data. Report/render/export paths consume approved projections rather than raw envelopes, and logs/errors do not leak tokens, private evidence, or deleted actor data. Migration covers existing active/done and malformed legacy items

## Definition of Done

Time-controlled lifecycle tests prove retention before/after expiry, accepted/rejected/duplicate/abuse cases, holds, redacted reports/history, disposal idempotency, backup/export behavior, public GitHub retention/deletion limitations, and absence of sensitive values from logs/public output; a review-ready implementation evidence package is prepared for `0033-07.03`.
