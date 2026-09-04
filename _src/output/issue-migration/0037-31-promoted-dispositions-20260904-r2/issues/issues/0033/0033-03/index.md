---
schema_version: "1.0"
id: "0033-03"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-01"
  - "0033-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:786"
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
---

## Goal

PREREQ: 0033-03:0033-01, 0033-03:0033-02 Prepare a review-ready redesign of `review-request-package@v1` or a deliberately versioned successor with unambiguous identity, canonical serialization, transport, staleness, duplicate, compatibility, and retention semantics.

## Scope

- **Baseline findings:** `RRB-SCHEMA-001`, `RRB-IDENT-001`, `RRB-TRUST-001`, `RRB-PRIV-001`.
  - **Previous implementation flaws:** The task called request identity deterministic while `request_id` was random; no pinned identity vector existed; three incompatible duplicate rules coexisted; canonical serialization was disconnected from identity/deduplication; null-version records could never become hard-stale; client transport and authoritative trust were conflated; and retry, transfer, and retention semantics contradicted implementation.
  - **Completion evidence (2026-08-30):** Class R candidate `docs/dossiers/0033-03-schema-reconciliation.md` plus `_src/tests/fixtures/review_request_v2/**` and `_src/tests/test_review_request_package_v2_contract.py`, REF `f6af48701` on branch `chain-0033-chakotay`, claim `TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`. Candidate JSON Schema lives at `_src/tests/fixtures/review_request_v2/review-request-package-v2.schema.candidate.json` (not `docs/pipeline/`, per architect scope review Sec2/Sec6 — that placement is exclusively `0033-04.01`'s). `python3 -m pytest _src/tests/test_review_request_package_v2_contract.py -q` -> 13 passed. Requirement-to-artifact matrix in the candidate §9. No `docs/pipeline/**` path touched.
  - **Acceptance: ✓** (2026-08-30, Integrator `obrien`, award `1788098846986-89dd4738`, review REF `54d3cf1a4` `docs/campaign-evidence/0033-recovery/chain-0033-acceptance-review-obrien-20260830.md`).

## Acceptance criteria

- **AC-001** Define a proper RFC 9562 UUIDv7 event/request ID and separately define a deterministic idempotency or concern key from pinned canonical bytes
- **AC-002** specify whether edits mint a new request and require transport retries to reuse the same event ID
- **AC-003** publish exact canonical byte/string and digest vectors. Define one duplicate policy covering same-ID retry only when the immutable canonical client-payload digest and approved stable trust bindings are identical, same-ID/different-payload collision or tampering, separately linked transport attempts/envelopes whose delivery IDs, issue numbers, or timestamps may legitimately differ, idempotent exact webhook redelivery, distinct requests for the same canonical record across `open` and `claimed`, terminal/closed/superseded requests, versioned and legacy/unversioned records, and concurrent submissions. Bind `target_version_id` to `target_canonical_id` and content hash
- **AC-004** define authoritative current-version lookup and hash-only staleness for unversioned records
- **AC-005** eliminate age-based claims that cannot detect live changes. Separate client package claims from trusted GitHub Issue/webhook or local-import envelopes, including the JSON-export/later-transfer case. Define supported GitHub trust profiles—verified webhook signatures, authenticated API refetch, or both—and require `0033-04.01` to select them
- **AC-006** each selected profile includes repository/installation allowlists, body/package-digest binding, and delivery/issue replay protection rather than accepting a caller-authored `verified` field. Define allowed fields, additional-property behavior, sensitive/server-owned fields, UTC timestamps, semver, URL scheme/credential/private-target rules, category/evidence vocabularies, control-character/HTML/Markdown-fence handling, size limits, and retention/redaction. Define version negotiation plus migration, quarantine, or actionable rejection for delayed historical `review-request-package@v1` exports and already persisted legacy/malformed queue items

## Definition of Done

A review-ready schema document, formal JSON Schema or equally strict executable-contract design, valid GitHub/JSON/no-JS-normalized examples, invalid/adversarial examples, pinned canonicalization/UUID/idempotency vectors, compatibility/disposition rules, and a requirement-to-test matrix are prepared; no requirement relies on an unspecified caller promise, and all policy choices are explicit for `0033-04.01` approval.
