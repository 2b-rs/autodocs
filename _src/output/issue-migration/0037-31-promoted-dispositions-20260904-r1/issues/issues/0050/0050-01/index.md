---
schema_version: "1.0"
id: "0050-01"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:137"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

(P0) Implement the append-only team generation, pause inventory, fold, schema and canonical API foundation.

## Scope

- **Task record:** `task_id: "0050-01"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-05/06/16/18/19/20`, `DEC-0050-001`, and the record/API contract in `docs/pipeline/team-pause-phaseout.md`.
  - **Prerequisites:** `0050-00` is a hard acceptance-before-start gate because this code activates the reviewed cross-item state contract.
  - **Planned order:** `position: 2`; foundation for every later task.
  - **Test scope:** `kind: unit`; schema/fold/idempotence/generation regression/partial-event/privacy negative cases plus exhaustive finite-state fold properties.
  - **Capability profile:** `capability_class=privileged; rights=["read/write declared agent-inbox paths", "run tests", "commit candidate"]; data=["reviewed 0050 baseline", "assignment journal fixtures"]; tools=["Git", "Python", "pytest"]; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot review scope, accept checkpoint or activate/deploy"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high; reasoning_depth=critical; context_volume=high; ambiguity=low; verification_hardness=critical`; append-only concurrency determines `critical`.
  - **Branch/worktree:** `parent: agent-inbox/main; name: 0050-01; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-01`.
  - **Exhaustive write scope (agent-inbox):** `team-state-machine.json` (new), `agent_inbox_mcp.py`, `test_agent_inbox.py`, `test_team_pause_phaseout.py` (new).
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-05/06/16/18/19/20 and reviewed 0050-00 interface", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **No-checkpoint justification (architect):** non-operative record/fold foundation; composition and activation are reviewed at `0050-03` and `0050-08`.

## Acceptance criteria

- **AC-001** Monotonic generations, deterministic fold, stable errors, bounded fields, append-only events and idempotent APIs match the reviewed contract
- **AC-002** malformed or partial histories fail closed

## Definition of Done

Source/schema/tests and retained property evidence committed; no live team is paused.
