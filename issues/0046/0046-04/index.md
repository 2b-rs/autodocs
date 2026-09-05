---
schema_version: "1.0"
id: "0046-04"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:970"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

(P0; Integration review: mandatory) Generate, validate and promote private runtime profiles; make Supervisor activate the exact published revision with restart-safe health receipt and rollback.

## Scope

- **Prerequisites:** `0046-03`.
  - **Planned order:** position `9`; may run in parallel with `0046-05` after source candidate.
  - **Test scope:** `end_to_end`; schema/size/determinism, partial regeneration, provider promotion, wrong revision, restart between request/receipt, health failure and rollback.
  - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot accept checkpoint or authorize activation policy"`.
  - **Branch/worktree:** `parent: "agent-inbox:0046"; name: "0046-04"; worktree: "/Users/tobias.anton/devel/agent-inbox/.worktrees/0046-04"`.
  - **Exhaustive write scope (agent-inbox):** `generate_profiles.py`, `test_generate_profiles.py`, `supervisor.py`, `test_supervisor.py`, `agent-profile-private-manifest-schema.json`, `agent-profile-activation-receipt-schema.json`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "REQ-0046-08/11/13/16/17 and Supervisor exact-revision/restart boundaries", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **Review rationale:** runtime authority, provider configuration, restart and every-future-Task behavior boundary.

## Acceptance criteria

- **AC-001** mixed output cannot promote
- **AC-002** Supervisor loads exact promoted private revision, proves health, reconciles restart idempotently and can restore named last-known-good

## Definition of Done

generator/Supervisor/tests/schemas and retained receipts committed; no public output exported.
