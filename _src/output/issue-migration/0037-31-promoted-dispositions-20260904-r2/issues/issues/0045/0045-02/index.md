---
schema_version: "1.0"
id: "0045-02"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:414"
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

(B/P0; fan-out B) Implement the typed GitHub event,

## Scope

Supervisor detection, priority-gated Project Lead offer, and durable
  scheduling-decision contract.
  - **Task record:**
    `task_id: "0045-02"; feature_id: "0045"; role: implementer`
  - **Architecture decisions and sources:** Implement `REQ-0045-04`,
    `REQ-0045-05`, `REQ-0045-08`, `REQ-0045-16`, and the event continuation
    contract from the `0045-00` approved baseline. Current
    `agent-workflow.json` declares `runner-request@v1`; the absent
    `_src/tools/runner_dispatch.py` and `_src/runner/actions-v1.json` and
    superseded `0037-46.01`/`.02` are negative repository evidence. Existing `supervisor.py` and
    `assignment-state-machine.json` are evidentiary interfaces, not authority
    to choose a policy absent `0045-00`.
  - **Prerequisites:** `0045-00` is a hard start gate and supplies the exact
    approved scheduling/gate interface consumed here.
  - **Planned order:** `position: 3; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`.
    It may execute in parallel with `0045-01`; it must finish before a durable
    arrival envelope can emit an operative offer.
  - **Test scope:** `kind: integration`, derived from external-event
    authentication, offer lifecycle, Project Lead choice, duplicate/similar
    item, selector compatibility, restart, and durable continuation risks.
    Evidence: `pytest -q test_supervisor.py test_github_event_adapter.py` with
    a pinned authoritative-selector fixture and fixtures
    for all three Project Lead branches, expired/declined offers, duplicate
    delivery, retry, and no runner execution before an award.
  - **Capability profile:** `capability_class=privileged; rights=["read agent-inbox repository and approved baseline", "write declared scheduler/state-machine paths", "run local integration tests", "commit candidate without deploying"]; data=["approved policy/interface digest", "authoritative selector and agent-inbox Runner contract", "typed GitHub event fixtures", "assignment lifecycle fixtures"]; tools=["Git", "Python", "pytest", "agent-inbox state-machine validator"]; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot supply the Management decision, Architect review, assignment acceptance, integration verdict, or release approval"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("event adapter, supervisor, state machine"); reasoning_depth=critical ("cross-item scheduling gates and restart semantics"); context_volume=high ("offer and assignment lifecycles"); ambiguity=medium ("policy fixed by approved baseline"); verification_hardness=critical ("false offer/execution can misassign work across items")`. Peak `critical` determines the class.
  - **Branch:** `parent: "agent-inbox:refs/heads/main"; name: "0045-02"; create: "create in the agent-inbox repository from its current main after pinning the immutable autodocs 0045-00 baseline ref/digest; never use or merge an autodocs branch as the parent"`.
  - **Exhaustive write scope (agent-inbox repository):**
    `supervisor.py`, `test_supervisor.py`,
    `assignment-state-machine.json`, `github_event_adapter.py` (new), and
    `test_github_event_adapter.py` (new).
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main@071c1cb1365ec90a9c4f70748275e615b9df475d", basis: "REQ-0045-04/05/08, the resolved reviewed 0045-00 baseline consumed by immutable autodocs ref/digest, and observed absence of an agent-inbox 0045 parent branch", checked_at: "2026-08-31T20:52:11Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** mandatory independent scheduler/security review because
    false positives, implicit decisions, or replay defects can start or route
    foreign work.
    schema/adapter and durable decision results are committed; compatibility
    and recovery evidence is retained; nothing is deployed.

## Acceptance criteria

- **AC-001** Each durable curation/review arrival envelope that passes only the minimum safe-routing validation creates one priority-gated Project Lead offer before trusted ingestion or decision-recipe execution
- **AC-002** the awarded Project Lead durably selects similar-item handoff, dependent typed-runner assignment, or trivial same-item runner handoff
- **AC-003** the selected recipe performs full trust/authority/binding/staleness/duplicate checks before any mutation and emits its durable continuation
- **AC-004** all outcomes name the next handler
- **AC-005** no Supervisor/runner product decision, pre-award recipe execution, or pre-recipe mutation is possible
- **AC-006** restart/replay is idempotent
- **AC-007** the concrete recipe binding matches the authoritative selector and does not depend on an absent or retired registry

## Definition of Done

State-machine and integration tests pass; new event
