---
schema_version: "1.0"
id: "0046-01"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:894"
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

(P0 parent package) Deliver the bounded submission and append-only feedback-record boundary.

## Scope

- **Prerequisites:** `0046-00`.
  - **Planned order:** positions `2–4`; `.01` and `.02` may execute in parallel after `0046-00`, then this parent aggregates them.
  - **Test scope:** `integration`; schema/idempotence/identity/privacy and UX-to-store contract including malformed, oversized, duplicate, replay and anonymous-policy fixtures.
  - **Capability profile:** `capability_class=unprivileged; execution_needs=direct; cognitive_demand=high; independence="implementers cannot approve, promote, accept or publish"`.
  - **Branch/worktree:** `parent: "0046"; name: "0046-01"; worktree: "/Users/tobias.anton/devel/autodocs/.worktrees/0046-01"`.
  - **Exhaustive write scope:** `docs/campaign-evidence/0046-01-feedback-ingress-aggregation.json`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0046-01/02/03 and the approved non-operative ingress/store boundary", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **No-checkpoint rationale:** package aggregates non-operative ingress/store candidates; `0046-00` already gates scope and `0046-06` gates integration.
    - **Prerequisites:** `0046-00`.
    - **Test scope:** `unit+integration`; accessibility, target resolution, consent/visibility, bounds, injection-safe rendering and error cases.
    - **Capability profile:** `capability_class=unprivileged; execution_needs=direct; cognitive_demand=high`.
    - **Branch/worktree:** `parent: "0046-01"; name: "0046-01.01"; worktree: "/Users/tobias.anton/devel/autodocs/.worktrees/0046-01.01"`.
    - **Exhaustive write scope (autodocs):** `_src/templates/agent_feedback.html`, `_src/static/agent-feedback.js`, `_src/tools/agent_feedback_form.py`, `_src/tests/test_agent_feedback_form.py`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0046-01/02 and existing static-site/tool boundaries", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
    - **No-checkpoint rationale:** no external or authoritative mutation; downstream package and terminal integration review the boundary.
    - **Prerequisites:** `0046-00`.
    - **Test scope:** `property+integration`; duplicate/replay/concurrency/restart, attribution, visibility and retention transitions.
    - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical; independence="store implementer cannot decide policy or approve profile changes"`.
    - **Branch/worktree:** `parent: "agent-inbox:0046-01"; name: "0046-01.02"; worktree: "/Users/tobias.anton/devel/agent-inbox/.worktrees/0046-01.02"`.
    - **Exhaustive write scope (agent-inbox):** `agent_profile_feedback.py`, `test_agent_profile_feedback.py`, `agent-profile-feedback-schema.json`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "REQ-0046-02/03/14/15/16 and append-only assignment-store conventions", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
    - **Review rationale:** privacy/security boundary for attributed and potentially anonymous user data.

## Acceptance criteria

- **AC-001** journal is append-only, idempotent and restart-safe
- **AC-002** correction/redaction/expiry never erase audit identity
- **AC-003** anonymous input has no approval authority

## Definition of Done

schema/store/tests committed; no analyzer or profile mutation runs.
