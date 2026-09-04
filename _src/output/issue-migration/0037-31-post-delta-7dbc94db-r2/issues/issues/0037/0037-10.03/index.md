---
schema_version: "1.0"
id: "0037-10.03"
level: "subtask"
parent: "0037-10"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-03.01"
  - "0037-08"
  - "0037-09"
  - "0037-17.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2289"
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
---

## Goal

PREREQ: 0037-10.03:0037-03.01, 0037-10.03:0037-08, 0037-10.03:0037-09, 0037-10.03:0037-17.01 Implement stable finding and signed decision operations. **Claim:** `TODO-worf-0037-10-chain-20260828.md` (`owner_token: agent:worf:chain-0037-10-20260828T223000Z`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Mint/update findings without changing stable identity
- **AC-002** link exact evidence/issue/criterion/run
- **AC-003** create decision records on the approved signed-ref topology
- **AC-004** enforce role, separation, package/policy revision, validity/revocation, conditions, and immutable history
- **AC-005** never treat actor strings, tests, or requester identity as approval

## Definition of Done

Tests cover finding reruns/dispositions, authorized/revoked/wrong-policy/wrong-role/self approvals, digest mismatch, duplicate/replay, injected write failure, and bootstrap plus normal verification.
