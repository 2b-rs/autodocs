---
schema_version: "1.0"
id: "0050-03"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:167"
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
---

## Goal

(P0; Integration review: mandatory) Implement draining, checkpoint, evidence-bound coordinator decisions, atomic delegation and cancellation/revocation ownership transitions.

## Scope

- **Task record:** `task_id: "0050-03"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-03/04/08..13/18..20` and one-owner/reclamation contract.
  - **Prerequisites:** `0050-02` supplies the admission/freeze boundary.
  - **Planned order:** `position: 4`.
  - **Test scope:** `kind: integration`; exact deadline, handoff then exhaustion, quota known/unknown/stale, recovery before/after revocation, duplicate outcome, extension abuse, delegation race and preservation-failure cases.
  - **Capability profile:** `capability_class=privileged; rights=["edit assignment lifecycle", "run race/recovery tests", "commit candidate"]; data=["reviewed contract", "assignment/claim/worktree fixtures"]; tools=["Git", "Python", "pytest"]; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot supply checkpoint verdict or waive preservation/ownership rules"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high; reasoning_depth=critical; context_volume=high; ambiguity=medium; verification_hardness=critical`.
  - **Branch/worktree:** `parent: agent-inbox/0050; name: 0050-03; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-03`.
  - **Exhaustive write scope (agent-inbox):** `assignment-state-machine.json`, `agent_inbox_mcp.py`, `test_agent_inbox.py`, `test_team_pause_phaseout.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-03/04/08..13/18..20 and existing offer_control/assignment_transition authority model", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Review rationale:** false reclamation can lose work or create double ownership across every team.

## Acceptance criteria

- **AC-001** Exactly one reasoned outcome per escalation
- **AC-002** current owner persists until successor ACCEPT or prior closure
- **AC-003** extension bounds, evidence freshness and preservation failures fail closed
- **AC-004** no automatic deletion

## Definition of Done

State-machine/API/tests and adversarial race/property evidence committed; mandatory independent review passes before upward integration.
