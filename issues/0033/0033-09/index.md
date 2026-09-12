---
schema_version: "1.0"
id: "0033-09"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-03"
  - "0033-07"
  - "0033-07.02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:880"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0033-09:0033-03, 0033-09:0033-07, 0033-09:0033-07.02 Wire authoritative review-request metadata into every eligible real generated record page and validate corpus-wide coverage.

## Scope

Claim: `DONE-quark-0033-09-20260901.md`; owner_token:
  `agent:quark:0033-09:1788264586172-d0d9fe1e`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788266456010-597d91d9` (Offer `1788266456010-597d91d9` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T12:42:00Z`
  - **Baseline findings:** `RRB-META-001`, `RRB-QUEUE-001`.
  - **Previous implementation flaws:** Tests injected a complete `review_request` object, but none of 3,882 production records contained it; real pages therefore emitted bare IDs, null version/hash, and empty source URLs, making every browser package invalid for ingestion. Open-request lookup also lacked a reliable target canonical key.

## Acceptance criteria

- **AC-001** Derive full canonical identity through the project/kind registry, authoritative latest version through the version store, content hash through the same algorithm used by ingestion, current status from the controlled record, and a stable deep page/source locator
- **AC-002** do not require synthetic per-record metadata that production writers never emit. Define and report every eligible/excluded record and page kind. Generation fails on bare IDs, missing registry entries, null/invalid hashes, version/hash/canonical mismatch, empty/non-deep source URLs, stale snapshots, duplicate panels, or an eligible record with no action. Queue lookup uses the target canonical ID and distinguishes open/claimed requests without exposing local filesystem details as public URLs

## Definition of Done

A machine-readable inventory reconciles record, eligible, excluded, rendered-action, and active-request counts; assertions inspect real generated examples from every supported page/record kind and language depth; at least one checked-in production record travels through the strict package validator and live ingestion fixture without synthetic metadata overrides.
