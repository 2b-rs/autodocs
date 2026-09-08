---
schema_version: "1.0"
id: "0045-04"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:590"
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
---

## Goal

(D/P1) Implement the awarded AI proposal recipe, causal live

## Scope

conversation, and structured GitHub handoff.
  - **Task record:**
    `task_id: "0045-04"; feature_id: "0045"; role: implementer`
  - **Architecture decisions and sources:** Implement `REQ-0045-06`,
    `REQ-0045-08`, and proposal/chat portions of `REQ-0045-12`. The committed
    queue item and Project Lead scheduling decision are authoritative inputs;
    streamed conversation remains non-authoritative until structured handoff.
  - **Prerequisites:** `0045-03` is a hard producer edge for the committed queue
    item, exact baseline binding, and scheduling event.
  - **Planned order:** `position: 7; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`.
    Proposal generation cannot start before an atomic award on the ingested
    item and must finish before Curator review.
  - **Test scope:** `kind: integration`, derived from causal chat, pinned
    baseline, evidence, Git commit/push handoff, restart, and authority risks.
    Evidence: `pytest -q test_ai_proposal_recipe.py test_supervisor.py` with
    fixtures for awarded/not-awarded, stale baseline, causal turn replay,
    same-key conflict, incomplete handoff, push failure, retry ancestry, and
    proof that no decision/apply transition is exposed.
  - **Capability profile:** `capability_class=unprivileged; rights=["read awarded queue item and pinned baseline", "write declared recipe/supervisor tests", "run local tests", "commit candidate; external push only through separately authorized fixture/runner"]; data=["queue item", "baseline record version", "evidence fixtures", "conversation and handoff records"]; tools=["Git", "Python", "pytest", "typed recipe harness"]; execution_needs=direct; cognitive_demand=high; independence="proposal author cannot accept, apply, integrate, publish, or act as sole validation producer"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=medium ("proposal, chat, handoff, supervisor continuation"); reasoning_depth=high ("causality and authority separation"); context_volume=high ("evidence and conversation context"); ambiguity=high ("research result may require explicit gaps"); verification_hardness=high ("push/restart/replay and forbidden transition proof")`. Peak `high` determines the class.
  - **Branch:** `parent: "agent-inbox:0045-03.01 exact candidate ref"; name: "0045-04"; create: "create in the agent-inbox repository from the pinned 0045-03.01 candidate (and therefore 0045-02 ancestry); consume the autodocs 0045-03 queue-item/aggregation artifacts only by immutable ref/digest"`.
  - **Exhaustive write scope (agent-inbox repository):**
    `recipes/ai_proposal.py` (new), `test_ai_proposal_recipe.py` (new),
    `supervisor.py`, and `test_supervisor.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main@071c1cb1365ec90a9c4f70748275e615b9df475d", basis: "REQ-0045-06/08/12, the exact ancestral 0045-03.01 agent-inbox candidate, and the immutable autodocs 0045-03 queue-item/aggregation contract", checked_at: "2026-08-31T20:52:11Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** independent provenance/authority review prevents live
    discussion or AI output from being mistaken for an accepted change.
    covers restart, replay, conflict, push failure, and structured handoff; the
    committed candidate performs no production push without separate authority.

## Acceptance criteria

- **AC-001** The exact proposal and chat keys govern replay
- **AC-002** only an awarded item produces an evidence-bearing proposal bound to a pinned baseline
- **AC-003** the GitHub handoff is durable and causal
- **AC-004** every terminal result names Curator notification or typed failure
- **AC-005** AI cannot decide or apply the proposal

## Definition of Done

Recipe and integration tests pass; retained evidence
