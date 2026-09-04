---
schema_version: "1.0"
id: "0037-10.02"
level: "subtask"
parent: "0037-10"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-03.02"
  - "0037-08"
  - "0037-09"
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2285"
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

PREREQ: 0037-10.02:0037-03.02, 0037-10.02:0037-08, 0037-10.02:0037-09, 0037-10.02:0037-17.01 Implement claim, renew, release, handoff, and authorized recovery operations. **Claim:** `TODO-worf-0037-10-chain-20260828.md` (`owner_token: agent:worf:chain-0037-10-20260828T223000Z`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Acquire same-clone Git refs by compare-and-swap, write/validate item-local state, fetch/recheck the integration branch, reject stale/overlapping claims, and preserve claim/release/recovery events. Expiry blocks rather than transfers
- **AC-002** takeover requires a verified approval role
- **AC-003** failure rolls back the ref/file pair or reports a recoverable split state

## Definition of Done

Multi-worktree and simulated multi-clone tests cover races, lease renewal/expiry, remote unavailable, integration rejection, handoff, takeover, crash points, and exact recovery instructions.
