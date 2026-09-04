---
schema_version: "1.0"
id: "0050-04"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:182"
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

(P0; Integration review: mandatory) Make Supervisor schedule typed drain/deadline escalation, verify coordinator response and converge restart/retry behavior without choosing the outcome.

## Scope

- **Task record:** `task_id: "0050-04"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-07/08/10/13/17/18`, current deadline and claim nudges, and Supervisor evidence at agent-inbox `b94b609e2`.
  - **Prerequisites:** `0050-03` provides typed outcomes and lifecycle fold.
  - **Planned order:** `position: 5`.
  - **Test scope:** `kind: integration`; boundary timestamps, delivery retry, ignored/misread escalation, repeated escalation, coordinator transfer, restart during drain and stale evidence.
  - **Capability profile:** `capability_class=privileged; rights=["edit Supervisor paths", "run restart/time tests", "commit candidate"]; data=["0050-03 API", "synthetic time/quota/claim fixtures"]; tools=["Git", "Python", "pytest"]; execution_needs=direct; cognitive_demand=critical; independence="Supervisor routes; it cannot make coordinator product decisions or accept checkpoint"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high; reasoning_depth=critical; context_volume=high; ambiguity=low; verification_hardness=critical`.
  - **Branch/worktree:** `parent: agent-inbox/0050; name: 0050-04; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-04`.
  - **Exhaustive write scope (agent-inbox):** `supervisor.py`, `test_supervisor.py`, `test_team_pause_phaseout.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-07/08/10/13/17/18 and existing Supervisor escalation/fold interfaces", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Review rationale:** missed or duplicated escalation can strand or wrongly reclaim assignments fleet-wide.

## Acceptance criteria

- **AC-001** One idempotent escalation per boundary
- **AC-002** delivery/retry and coordinator accountability are durable
- **AC-003** missing action re-escalates
- **AC-004** Supervisor never selects an outcome

## Definition of Done

Source/tests and restart/time evidence committed; mandatory independent review passes.
