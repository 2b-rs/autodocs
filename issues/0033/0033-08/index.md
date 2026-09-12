---
schema_version: "1.0"
id: "0033-08"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-05"
  - "0033-06"
  - "0033-07"
  - "0033-07.01"
  - "0033-07.02"
  - "0033-07.04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:864"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0033-08:0033-05, 0033-08:0033-06, 0033-08:0033-07, 0033-08:0033-07.01, 0033-08:0033-07.02, 0033-08:0033-07.04 Establish the ingestion security and side-effect regression gate using real stores and exhaustive negative paths.

## Scope

Claim: `DONE-worf-0033-08-20260901.md`; owner_token:
  `agent:worf:0033-08:1788264218303-f115c87f`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788264521130-5ea7256b` (Offer `1788264521130-5ea7256b` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T12:11:00Z`
  - **Baseline findings:** `RRB-SCHEMA-001`, `RRB-SCHEMA-002`, `RRB-INGEST-001`, `RRB-TRUST-001`, `RRB-QUEUE-001`, `RRB-QUEUE-002`, `RRB-AUTH-001`, `RRB-VALID-001`.
  - **Previous implementation flaws:** The old suite omitted unknown targets, internal lookup, apply-without-current-state, schema conformance, correct lifecycle/origin/canonical linkage, reserved trust fields, full mapping, warning persistence, claimed/concurrent duplicates, writer failures, and record/history immutability.
  - **Completion evidence (2026-09-01):** Established ingestion security and side-effect regression gate across real temporary stores and negative paths. Tests: 94 passed across `test_review_request_ingest.py`, `test_review_request_package.py`, `test_review_request_baseline_audit.py`, `test_review_request_retention.py`, and `test_review_request_package_v2_contract.py`.

### Campaign C — Production Metadata, Browser Behavior, and Accessibility

## Acceptance criteria

- **AC-001** The matrix covers valid GitHub, self-declared JSON, normalized no-JS Issue, unsupported category/evidence, insufficient attribution, malformed types, extra/reserved/sensitive fields, unknown/ineligible target, stale version/hash combinations, each selected trust profile's invalid-credential/signature/refetch path, wrong-repository/edited-body/replayed or spoofed envelope, same-ID identical/different client-payload digest retry and multiple transport attempts, open/claimed duplicate, concurrent race, target-change-before-commit, role/authorization failure, legacy migration/quarantine, retention/redaction/disposal, repeated same/different-target burst, quota/queue exhaustion, quarantine/moderation/escalation, queue writer failure, and normalization/transition failures. Include unsafe `javascript:`/`data:`/credentialed/private URLs, HTML/script, Markdown fence, control-character, oversized, and report/Issue/dialog output-injection payloads. For every rejected/failing case, snapshot comparisons prove no record, version, queue, history, report model, or unrelated file changed and no temp artifact remains. Tests use at least one real-schema production-record fixture with a valid canonical/version identity rather than an invented nonexistent record

## Definition of Done

The focused gate runs hermetically in temporary roots, passes repeatedly and in parallel, emits machine-readable case results, and is invoked by the project validator/CI path; mutation/leak detection fails the suite if a test writes into real stores.
