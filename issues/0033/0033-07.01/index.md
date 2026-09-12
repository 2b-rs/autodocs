---
schema_version: "1.0"
id: "0033-07.01"
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
  source: "legacy:DONE.md:831"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0033-07.01:0033-02, 0033-07.01:0033-04.01, 0033-07.01:0033-07 Implement authenticated, role-enforced claim/propose/accept/reject/apply/close transitions instead of relying on caller convention or bare actor strings.

## Scope

Claim: `DONE-worf-0033-07.01-20260901.md`; owner_token:
  `agent:worf:0033-07.01:1788287929701-aa675c32`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788288839320-81d411b4` (Offer `1788288839320-81d411b4` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T18:55:00Z`
  - **Baseline finding:** `RRB-AUTH-001`.
  - **Previous implementation flaw:** Existing queue APIs and docstrings described human-only decisions but did not establish an authenticated authorization boundary, so an in-process caller could supply an actor/role string and invoke a privileged transition.

## Acceptance criteria

- **AC-001** Bind every privileged transition to an approved authenticated operator/session or verified service identity, check the role/authority and item/version/state at transition time, retain actor and authorization evidence, enforce separation of proposal from human decision, allow application only after acceptance, make rejection terminal without factual application, and prevent browser/AI/ingestion/report code from invoking human-only operations. Re-authenticate or re-authorize sensitive apply/close operations as policy requires
- **AC-002** reject stale-version, wrong-role, anonymous, replayed, and out-of-order transitions

## Definition of Done

Positive and negative transition tests cover each role/state, forged/bare identities, replay, concurrent decisions, stale items, accepted application, rejected no-application, and audit history; no public API accepts an unverified role/actor string as sufficient authority.
