---
schema_version: "1.0"
id: "0050-02"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:152"
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

(P0; Integration review: mandatory) Atomically block team offer delivery/acceptance and freeze affected pre-award rounds without advancing ownership.

## Scope

- **Task record:** `task_id: "0050-02"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `REQ-0050-01/02/11/18`, `DEC-0050-001` admission and generation consequences.
  - **Prerequisites:** `0050-01` produces the generation/fold API.
  - **Planned order:** `position: 3`.
  - **Test scope:** `kind: integration`; pause-versus-accept race, mixed-team offer, tier freeze/resume, stale generation, duplicate request and restart fixtures.
  - **Capability profile:** `capability_class=privileged; rights=["edit declared offer paths", "run concurrency tests", "commit candidate"]; data=["0050-01 candidate", "offer fixtures"]; tools=["Git", "Python", "pytest"]; execution_needs=direct; cognitive_demand=critical; independence="cannot accept or integrate own admission gate"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=medium; reasoning_depth=critical; context_volume=high; ambiguity=low; verification_hardness=critical`; atomic race safety determines `critical`.
  - **Branch/worktree:** `parent: agent-inbox/0050; name: 0050-02; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-02`.
  - **Exhaustive write scope (agent-inbox):** `agent_inbox_mcp.py`, `test_agent_inbox.py`, `test_team_pause_phaseout.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: agent-inbox/main, basis: "REQ-0050-01/02/11/18 and canonical mailbox lock", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Review rationale:** admission is a repository-wide ownership gate; independently review with `0050-03` before activation.

## Acceptance criteria

- **AC-001** Pause and ACCEPT serialize
- **AC-002** no paused member receives or accepts new work
- **AC-003** unaffected paths are explicit
- **AC-004** frozen rounds neither expire nor advance until authorized resume/cancellation

## Definition of Done

Race/integration evidence committed; feature remains non-operative until checkpoint integration.
