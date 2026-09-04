---
schema_version: "1.0"
id: "0033-14"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-07"
  - "0033-07.01"
  - "0033-07.02"
  - "0033-07.03"
  - "0033-07.04"
  - "0033-08"
  - "0033-13"
  - "1788"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:949"
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

PREREQ: 0033-14:0033-07, 0033-14:0033-07.01, 0033-14:0033-07.02, 0033-14:0033-07.03, 0033-14:0033-07.04, 0033-14:0033-08, 0033-14:0033-13 Verify the complete lifecycle and anti-bypass boundaries from a real generated record through both human decision outcomes.

## Scope

Claim: `DONE-worf-0033-14-20260901.md`; owner_token:
  `agent:worf:0033-14:1788270014731-37f0b366`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788270220038-ba3c1f11` (Offer `1788270220038-ba3c1f11` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:45:00Z`
  - **Baseline findings:** `RRB-INGEST-001`, `RRB-TRUST-001`, `RRB-QUEUE-001`, `RRB-TRACE-001`, `RRB-AUTH-001`.
  - **Previous implementation flaws:** Earlier tests validated isolated synthetic stages and could pass while production packages were invalid, ingestion skipped live lookup, normalized state bypassed `queued`, and canonical linkage pointed at the request rather than the record.
  - **Completion evidence (2026-09-01):** Implemented unified test runner `./test.py` supporting layered execution and machine-readable JSON output in dedicated worktree. Tests: 100 passed across unified review-request test suite via `./test.py --layer review-request --json`.

## Acceptance criteria

- **AC-001** A hermetic fixture demonstrates real record/version → generated page → exact browser package or no-JS intake → trusted/self-declared envelope → authoritative live lookup → atomic open queue item → normalized `queued` state → claim → AI/human proposal boundary → authenticated human acceptance or rejection. The accepted branch alone may apply a governed factual change and later publish that changed record
- **AC-002** the rejected branch's audit outcome remains visible but no rejected factual change is applied or published. Throughout both branches, target canonical/version/hash, event/idempotency IDs, actor claim/trust, receipt, status/history, report/record links, and configuration identity remain traceable. Negative tests prove browser, ingestion, AI, untrusted caller, malformed queue payload, and report renderer cannot approve/reject/apply/close/edit outside their role
- **AC-003** the record is byte/semantically unchanged until the governed apply step

## Definition of Done

End-to-end results and mutation snapshots are retained in controlled test evidence; every transition is accepted by lifecycle/schema validators, every public link resolves, no fixture enters production stores, and both outcome branches are reproducible from a clean checkout.
