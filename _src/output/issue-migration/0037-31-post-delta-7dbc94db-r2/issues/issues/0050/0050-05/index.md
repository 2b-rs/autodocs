---
schema_version: "1.0"
id: "0050-05"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:197"
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

(P1) Add GUI team/assignment drain visibility and canonical pause, decision and resume controls without conflating runtime stop with quiescence.

## Scope

- **Task record:** `task_id: "0050-05"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-16/17/19`, canonical APIs and current Supervisor GUI assignment controls.
  - **Prerequisites:** `0050-04` supplies authoritative projection fields and escalation state.
  - **Planned order:** `position: 6`.
  - **Test scope:** `kind: integration`; API/GUI parity, all states/counts, stable errors, keyboard/focus/accessibility, stale command and no-JavaScript/operator fallback.
  - **Capability profile:** `capability_class=unprivileged; rights=["edit declared GUI/test paths", "run local UI tests", "commit candidate"]; data=["0050-04 snapshot fixtures"]; tools=["Git", "Python", "browser test harness"]; execution_needs=direct; cognitive_demand=high; independence="GUI implementer cannot authorize pause/revocation or certify integration"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high; reasoning_depth=medium; context_volume=high; ambiguity=low; verification_hardness=high`.
  - **Branch/worktree:** `parent: agent-inbox/0050; name: 0050-05; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-05`.
  - **Exhaustive write scope (agent-inbox):** `supervisor-gui.py`, `test_supervisor.py`, `test_team_pause_phaseout.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-16/17/19 and existing GUI command projection", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** projection-only UI; canonical API enforcement is reviewed at `0050-03/04` and end-to-end parity at `0050-08`.

## Acceptance criteria

- **AC-001** Required fields/counts/coordinator are visible
- **AC-002** controls invoke canonical APIs
- **AC-003** runtime stop is distinctly labeled
- **AC-004** stale/unauthorized operations show fail-closed errors

## Definition of Done

GUI/tests committed; no live pause or external effect.
