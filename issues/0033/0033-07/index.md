---
schema_version: "1.0"
id: "0033-07"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-03"
  - "0033-05"
  - "0033-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:824"
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
---

## Goal

PREREQ: 0033-07:0033-03, 0033-07:0033-05, 0033-07:0033-06 Implement one atomic, policy-compliant, conformant review-request queue write and race-safe idempotency/duplicate handling across active states.

## Scope

- **Baseline findings:** `RRB-QUEUE-001`, `RRB-QUEUE-002`, `RRB-TRACE-001`.
  - **Previous implementation flaws:** The writer used the request ID as the normalized target, omitted top-level canonical linkage, emitted `outcome=requested` that became `proposed`, defaulted origin to `curator`, dropped/conflated package fields, kept the self-declared warning only in a transient report, patched `item_kind` in a second non-atomic rewrite, scanned only `open`, and allowed same-record different-version or concurrent duplicates.
  - **Completion evidence (2026-09-01):** Candidate commit `2012f8f106` on branch `chain-0033-07` (`worf`). Implemented atomic policy-compliant review-request queue write and race-safe idempotency/duplicate handling across active states. Tests: 75 passed across `test_review_request_ingest.py`, `test_review_request_package.py`, and `test_review_request_package_v2_contract.py`.

## Acceptance criteria

- **AC-001** One atomic writer emits an item accepted by the authoritative curation schema with top-level `canonical_id` equal to the target record, a separate request/item identity, `item_kind=review-request`, `origin=browser` or the approved intake origin, and initial `status=open` mapping to lifecycle `queued`
- **AC-002** it never fabricates `decided_by`/`decided_at` before a decision. Preserve every policy-permitted validated client/envelope field through a lossless mapping and provide the field classification/projection hooks consumed by `0033-07.02`, including `received_at`, warnings, receipt, target snapshot, evidence, and privacy classification
- **AC-003** `0033-07.02` exclusively owns redaction, expiry, and disposal behavior. Same-ID retries return the existing item/result idempotently only when the immutable canonical client-payload digest and approved stable trust bindings are identical
- **AC-004** transport attempts/envelopes remain separately linked, exact webhook redelivery is acknowledged idempotently, and contradictory actor/repository/body bindings or same-ID/different-payload collisions are rejected as tampering or conflict
- **AC-005** same-ID/different-payload collisions are rejected as tampering or conflict
- **AC-006** the approved same-record policy scans `open` and `claimed`
- **AC-007** atomic reservation/write prevents concurrent duplicates and performs the final target version/hash recheck under that reservation
- **AC-008** failures leave no partial, untagged, temp, or malformed item. Existing legacy/malformed queue items are inventoried and structurally migrated or quarantined according to the approved compatibility rule
- **AC-009** privacy redaction/disposal during that migration belongs to `0033-07.02`. Claim/release/complete retain canonical linkage and terminal rejected history

## Definition of Done

Normalization and workflow validators accept every emitted state; tests cover open/claimed/retried/concurrent/terminal cases, same-ID same/different client-payload digest, multiple transport attempts, exact webhook redelivery, contradictory trust bindings, target-change-before-commit, structural legacy disposition, injected write failures, process interruption between stages, and exact policy-permitted round-trip/classification-hook coverage; no adapter performs a post-write JSON patch.
