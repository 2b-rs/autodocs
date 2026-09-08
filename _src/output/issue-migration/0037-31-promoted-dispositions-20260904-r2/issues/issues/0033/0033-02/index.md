---
schema_version: "1.0"
id: "0033-02"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:778"
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
---

## Goal

PREREQ: 0033-02:0033-01 Prepare a review-ready reconciliation of the authoritative website review-request process, including eligibility, exclusions, abuse handling, role authority, closure, privacy, and retention.

## Scope

- **Baseline findings:** `RRB-PROC-001`, `RRB-AUTH-001`, `RRB-PRIV-001`.
  - **Previous implementation flaws:** `website-review-flag.md` omitted the required abuse policy and exhaustive eligibility/exclusion rule; rejected closure conflicted with the terminal lifecycle; request routing was described as identical to a decision-bearing `curation_request`; and documented actor deletion contradicted retention in `curation-queue/done/`.
  - **Completion evidence (2026-08-30):** Class R candidate `docs/dossiers/0033-02-process-reconciliation.md`, REF `99fdc4a2b` on branch `chain-0033-chakotay`, claim `TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`. Per architect scope review (`docs/dossiers/0033-02-04-architect-scope-review.md`) and `DEC-0033-002`, this Task's deliverable is Class R only — it does not and cannot land `docs/pipeline/website-review-flag.md` etc.; that transition is exclusively `0033-04.01`'s. Requirement-to-section matrix in the candidate §8. No `docs/pipeline/**` path touched by this Task.
  - **Acceptance: ✓** (2026-08-30, Integrator `obrien`, award `1788098846986-89dd4738`, review REF `54d3cf1a4` `docs/campaign-evidence/0033-recovery/chain-0033-acceptance-review-obrien-20260830.md`).

## Acceptance criteria

- **AC-001** The contract explicitly states which published record/page kinds are eligible and why every exclusion exists
- **AC-002** defines behavior for missing immutable target metadata and already-open/claimed requests
- **AC-003** separates a request from a curator decision
- **AC-004** assigns submit/ingest/claim/propose/accept/reject/apply/close/publish authorities
- **AC-005** defines `rejected` as retained terminal closure whose audit/result state remains visible but for which no factual-record change is applied or published
- **AC-006** defines repeated, abusive, sensitive, malicious-link, and attribution-policy cases plus moderation/escalation/audit behavior
- **AC-007** states what actor claim, trusted envelope, rationale/evidence, diagnostics, receipts, and queue/history data are retained/redacted/disposed and for how long
- **AC-008** and preserves the rule that browser/AI/ingestion cannot mutate facts or perform human-only decisions

## Definition of Done

A review-ready change set for `website-review-flag.md`, `workflow-lifecycle.md`, `roles.md`, `actions.md`, `status-model.md`, `curation-item-schema.md`, reports/tools guidance, and privacy/retention wording—including public GitHub Issue bodies, comments, and attachments, controller boundaries, deletion limitations, and consent—has no known terminology or transition conflict; open policy decisions and proposed authorities are explicit for the approval gate in `0033-04.01`.
