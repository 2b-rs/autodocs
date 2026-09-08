---
schema_version: "1.0"
id: "0033-06"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-02"
  - "0033-03"
  - "0033-04.01"
  - "0033-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:818"
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

PREREQ: 0033-06:0033-02, 0033-06:0033-03, 0033-06:0033-04.01, 0033-06:0033-05 Implement authoritative live-target resolution and approved trusted-transport verification that cannot be bypassed by optional caller arguments.

## Scope

- **Baseline findings:** `RRB-INGEST-001`, `RRB-TRUST-001`.
  - **Previous implementation flaws:** `apply=True` accepted a package when current hash/version arguments were omitted; tests echoed package values as authoritative state; no live record existed for the happy-path fixture; a bare caller-provided actor string stood in for a verified GitHub envelope; JSON/client metadata could influence trust; and unknown-record coverage was absent.

## Acceptance criteria

- **AC-001** Applying ingestion resolves the canonical target internally through the approved record and version stores, rejects unknown/unpublished/ineligible records, and obtains authoritative current version/hash/status/source without accepting caller-supplied substitutes. Dry-run behavior cannot be confused with apply behavior. GitHub ingestion accepts a structured envelope whose trust is established by the profile(s) selected in `0033-04.01`—verified webhook signatures, authenticated GitHub API refetch, or both—with repository/installation allowlisting, issue/body-package digest binding, and delivery/issue replay protection, never caller-authored `verified` fields
- **AC-002** selected profiles provide repository/issue identity, verified author, receipt URL/number, event identity, and timestamps validated by an adapter
- **AC-003** JSON/local import is always self-declared unless a later trusted envelope is explicitly and losslessly attached. No-JavaScript GitHub intake is normalized by this same envelope adapter. Actor claims remain distinct from authoritative actors
- **AC-004** mismatches/spoofed reserved fields are rejected or downgraded exactly as the approved policy specifies. Every stale/unknown/invalid/duplicate/trust failure occurs before any queue/history/record write, and accepted ingestion imports no factual-record mutation path. Return an authoritative expected target version/hash token for the queue writer
- **AC-005** `0033-07` owns the final reserved compare-and-set/recheck so a target change between lookup and commit is rejected. Negotiate incoming package versions and route delayed legacy exports through the approved normalization, quarantine, or actionable rejection path rather than silently accepting or dropping them
- **AC-006** persisted historical queue-item disposition belongs to `0033-07`/`0033-07.02`

## Definition of Done

Integration tests use real temporary record/version stores and prove unknown record, wrong canonical prefix, obsolete/mismatched version/hash, unversioned hash mismatch, ineligible status, every selected trust profile's missing/invalid credential or signature, wrong repository/installation, edited Issue body/package digest, replayed delivery, envelope/package mismatch, spoofed trust, self-declared JSON, signed-in no-JavaScript Issue, signed-out/no-envelope rejection, legacy delayed export, expected target token generation, and happy paths; `apply=True` with omitted or forged live values cannot succeed.
