---
schema_version: "1.0"
id: "0033-11"
level: "task"
parent: "0033"
state: "closed"
visibility: "internal"
prerequisites:
  - "0033-04"
  - "0033-04.01"
  - "0033-06"
  - "0033-07"
  - "0033-07.01"
  - "0033-07.02"
  - "0033-10"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:906"
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
---

## Goal

PREREQ: 0033-11:0033-04, 0033-11:0033-04.01, 0033-11:0033-06, 0033-11:0033-07, 0033-11:0033-07.01, 0033-11:0033-07.02, 0033-11:0033-10 Implement truthful transport, stale/duplicate, receipt, cancellation, and failure-state behavior with accessible user feedback.

## Scope

Claim: `agent-inbox:DONE-worf-0033-11-20260901.md`; owner_token:
  `agent:worf:0033-11:1788267032303-e089a2a0`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788267676473-2eaaf5cc` (Offer `1788267676473-2eaaf5cc` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:15:00Z`
  - **Baseline findings:** `RRB-IDENT-001`, `RRB-UX-001`, `RRB-BROWSER-001`, `RRB-TRACE-001`.
  - **Previous implementation flaws:** GitHub's receipt URL was discarded; errors were written into a hidden unfocusable form; confirmation and actual transport packages could differ; no authoritative stale result channel existed; no ingested/queued state was implemented; identity cancellation could reject an uncaught promise; and retry regenerated identity.

## Acceptance criteria

- **AC-001** A locally collected request says local-only/not submitted/not queued
- **AC-002** JSON completion says exported/not submitted
- **AC-003** GitHub success renders a durable issue receipt link and says submitted/awaiting ingestion
- **AC-004** only queue/report data may say ingested/queued. The confirmation step exposes only transport-valid actions: a self-declared/JSON selection cannot present a silent GitHub-only Submit action, and every missing-token, permission, validation, API/network, rate-limit, and transport mismatch produces visible actionable feedback in the active dialog. Authoritative post-submit stale, duplicate, attribution, or schema rejection is associated with the Issue/transport receipt or a separate ingestion-result channel without creating a queue/history item
- **AC-005** once queued, governed accepted/rejected audit outcomes remain visible while no rejected factual change is applied or published
- **AC-006** the browser does not claim that page age proves staleness. Pre-known active requests suppress duplicate intake with a valid public link, while race-time duplicates receive actionable non-blaming feedback. Transport and identity failures stay visible in the active dialog, use alert/live semantics, preserve entered data and exact retry package, and restore focus appropriately
- **AC-007** cancel at every stage is handled without unhandled rejection or submission. No error path creates a local success state

## Definition of Done

Automated scenarios cover export success/failure, GitHub success with receipt, signed-out and API/network/rate-limit failure, identity verification/cancel, stale-at-ingest, duplicate-before/race, retry after ambiguous failure, accepted/rejected follow-up, and absence of false queue/history state.
