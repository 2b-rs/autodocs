---
schema_version: "1.0"
id: "0046-03"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:938"
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

(P0 parent; Integration review: mandatory) Join authorized human decision and compare-and-swap authoritative-source promotion.

## Scope

- **Prerequisites:** `0046-02`.
  - **Planned order:** positions `6–8`; `.01` precedes `.02`, then parent validates the authority boundary.
  - **Test scope:** `security+integration`; unauthorized approval, stale/replayed/revised decisions, concurrent conflicts, schema/policy failure and atomic source promotion.
  - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical; independence="implementers cannot supply policy decision, accept checkpoint or integrate"`.
  - **Branch/worktree:** `parent: "0046"; name: "0046-03"; worktree: "/Users/tobias.anton/devel/autodocs/.worktrees/0046-03"`.
  - **Exhaustive write scope:** `docs/campaign-evidence/0046-03-approval-promotion-aggregation.json`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0046-06/07/17 and the approved cross-item authority/source-promotion baseline", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **Review rationale:** decisive human-authority and cross-item source-promotion boundary.
    - **Prerequisites:** `0046-02`.
    - **Test scope:** `security+integration`; least privilege, proposal/diff digest binding, revise flow, replay and restart.
    - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical`.
    - **Branch/worktree:** `parent: "agent-inbox:0046-03"; name: "0046-03.01"; worktree: "/Users/tobias.anton/devel/agent-inbox/.worktrees/0046-03.01"`.
    - **Exhaustive write scope (agent-inbox):** `agent_profile_approval.py`, `test_agent_profile_approval.py`, `agent-profile-decision-schema.json`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "REQ-0046-05/06 and existing role/authority separation contracts", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
    - **Review rationale:** authorization and separation-of-duty boundary.
    - **Prerequisites:** `0046-03.01`.
    - **Test scope:** `property+integration`; compare-and-swap, schema/reference/policy validation, duplicate/conflict/replay and atomic failure.
    - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical`.
    - **Branch/worktree:** `parent: "agent-inbox:0046-03"; name: "0046-03.02"; worktree: "/Users/tobias.anton/devel/agent-inbox/.worktrees/0046-03.02"`.
    - **Exhaustive write scope (agent-inbox):** `agents.json`, `agent_profile_promotion.py`, `test_agent_profile_promotion.py`, `agent-profile-source-candidate-schema.json`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "REQ-0046-07/17, exact approved baseline, agents.json and role/capability policy validators", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
    - **Review rationale:** operative shared profile/role/capability mutation with cross-item reach; `0046-00` record/review is a hard start gate.

## Acceptance criteria

- **AC-001** only current approved decisions promote
- **AC-002** all structural/policy gates pass before atomic candidate
- **AC-003** exact ref/tree/digests retained

## Definition of Done

code/tests/candidate schema committed; no runtime activation or public deployment.
