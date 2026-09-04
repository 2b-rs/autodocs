---
schema_version: "1.0"
id: "0037-30"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-03"
  - "0037-10"
  - "0037-14"
  - "0037-15"
  - "0037-20"
  - "0037-21"
  - "0037-28"
  - "0037-29"
  - "0037-43"
  - "0037-44"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2499"
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

PREREQ: 0037-30:0037-03, 0037-30:0037-10, 0037-30:0037-14, 0037-30:0037-15, 0037-30:0037-20, 0037-30:0037-21, 0037-30:0037-28, 0037-30:0037-29, 0037-30:0037-43, 0037-30:0037-44 Reconcile active legacy claims/work, staged or uncommitted backlog edits, new-store leases, and handoffs before the final source watermark.

## Scope

- **DEC-0037-002 execution model:** Reconcile direct processes and every Task-ID-bound background Runner job; the accepted `0037-21` job-control contract is a start prerequisite.

## Acceptance criteria

- **AC-001** Inventory each active agent session/task/owner identity/capability class/base commit/instruction-contract version/runner request or result/authority epoch/write scope/expiry and discrepancy
- **AC-002** merge or explicitly preserve uncommitted task text
- **AC-003** require every session to stop, every legacy/new-store claim to be signed-released or closed, and every runner request to be terminal with reconciled results before the freeze
- **AC-004** as the final pre-freeze operation, atomically bump `agent-workflow.json` to a new `legacy-frozen` epoch/capability set enforced by `0037-43`, record its bundle/source digests in the quiescence barrier, and prove no pre-cutover session may mutate or resume after the switch
- **AC-005** never activate a dormant candidate `claim.json` or `refs/autodocs/claims/*` before/at cutover
- **AC-006** never overwrite another agent
- **AC-007** and block reused IDs, dirty/staged backlog state, stale ambiguous ownership, overlapping scopes, or simultaneous ownership in both models. New claims may be created only after both `0037-40` activation/reference commits complete and lift the write freeze

## Definition of Done

Signed reconciliation/quiescence report is bound to the exact final `legacy-frozen` selector/instruction/source digests and clean committed legacy source watermark; no later ordinary Feature work or agent pickup is permitted—only the named transaction-bound operators for `0037-31`, `0037-34.01`, `0037-32`, `0037-33`, and `0037-34.02` may run, without claims or item writes; every known session, `TODO-<agent-id>.md`, and claim ref is stopped/released/dispositioned and no active work is orphaned, dual-owned, or carried stale across cutover.
