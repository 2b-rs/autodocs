---
schema_version: "1.0"
id: "0050-06"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:212"
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

(P0; Integration review: mandatory) Reconcile emergency blackout, claim/WIP preservation, migration, zero proof, resume and additive rollback with the same ownership receipts.

## Scope

- **Task record:** `task_id: "0050-06"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-06/10/12/14/15/18/20`, blackout behavior at agent-inbox `b94b609e2` and `DEC-0050-001` no-destruction consequence.
  - **Prerequisites:** `0050-04`, `0050-05`.
  - **Planned order:** `position: 7`.
  - **Test scope:** `kind: end_to_end`; mixed-provider blackout, WIP failure, stale claims, restart in every team state, zero-proof indeterminacy, resume generation and rollback/supersession.
  - **Capability profile:** `capability_class=privileged; rights=["edit declared recovery paths", "run end-to-end fixtures", "commit candidate"]; data=["all prior 0050 candidates", "Git/worktree/claim fixtures"]; tools=["Git", "Python", "pytest"]; execution_needs=direct; cognitive_demand=critical; independence="cannot accept preservation loss, waive authority or integrate own recovery gate"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high; reasoning_depth=critical; context_volume=critical; ambiguity=medium; verification_hardness=critical`.
  - **Branch/worktree:** `parent: agent-inbox/0050; name: 0050-06; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-06`.
  - **Exhaustive write scope (agent-inbox):** `supervisor.py`, `agent_inbox_mcp.py`, `assignment-state-machine.json`, `team-state-machine.json`, `test_supervisor.py`, `test_agent_inbox.py`, `test_team_pause_phaseout.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-06/10/12/14/15/18/20 and unified receipt model", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Review rationale:** emergency and rollback paths can bypass ordinary ownership and destroy the only useful work copy.

## Acceptance criteria

- **AC-001** Blackout uses identical receipts
- **AC-002** preservation failure is visible and nondestructive
- **AC-003** migration has no grandfathering
- **AC-004** stale roster/status projections are not ownership
- **AC-005** unknown pre-migration identifiers remain visible and receive typed reconciliation receipts
- **AC-006** quiescence is iff zero proof
- **AC-007** resume/rollback never resurrect ownership

## Definition of Done

Recovery/migration/property evidence committed; mandatory independent review passes.
