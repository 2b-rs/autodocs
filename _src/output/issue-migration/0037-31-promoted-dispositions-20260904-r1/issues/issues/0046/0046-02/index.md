---
schema_version: "1.0"
id: "0046-02"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:926"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

(P0) Implement isolated classification and baseline-bound AI proposal generation with diff preview and rationale.

## Scope

- **Prerequisites:** `0046-01`.
  - **Planned order:** position `5`.
  - **Test scope:** `integration+adversarial`; all six classes, untrusted prompt injection, evidence/rationale/diff bindings, conflict and stale baseline.
  - **Capability profile:** `capability_class=unprivileged; execution_needs=direct; cognitive_demand=critical; independence="AI/proposal producer has no approval or mutation authority"`.
  - **Branch/worktree:** `parent: "agent-inbox:0046"; name: "0046-02"; worktree: "/Users/tobias.anton/devel/agent-inbox/.worktrees/0046-02"`.
  - **Exhaustive write scope (agent-inbox):** `agent_profile_analysis.py`, `test_agent_profile_analysis.py`, `agent-profile-proposal-schema.json`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "REQ-0046-04/05 and the non-mutating proposal separation", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **No-checkpoint rationale:** produces non-operative proposals only; approval/source promotion is the mandatory `0046-03` checkpoint.

## Acceptance criteria

- **AC-001** deterministic record bindings, controlled classification, diff/rationale/evidence/conflict/validation/rollback preview
- **AC-002** no write path to authoritative sources

## Definition of Done

analyzer/schema/tests committed and adversarial suite passes.
