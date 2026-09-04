---
schema_version: "1.0"
id: "0045-00"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:308"
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

(P0; single start) Prepare the Management gate decision,

## Scope

obtain the distinct Architect scope review, and bind one approved shared
  Feature/interface baseline.
  - **Task record:**
    `task_id: "0045-00"; feature_id: "0045"; role: architect-elaboration`
  - **Architecture decisions and sources:** Prepare, but do not decide, the
    cross-item Supervisor→priority-gated-Project-Lead policy in
    `REQ-0045-04`/`REQ-0045-05` and the typed-recipe/authoritative-selector
    compatibility decision in `REQ-0045-16`. Authoritative sources:
    `AGENTS.md` cross-item gate-scope exception,
    `docs/pipeline/decision-record.md`, and
    `docs/pipeline/score-feedback-loop.md`. Repository evidence: no
    `docs/decisions/` directory exists and no `DEC-*` identifier may be
    allocated on this branch. The approved baseline is a consumer contract,
    not an authority grant.
  - **Prerequisites:** none; this is the single start node.
  - **Planned order:** `position: 1; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`.
    Order matters because both fan-out branches must consume the same resolved
    policy and reviewed interface digest before any operative gate mutation.
  - **Test scope:** `kind: manual_inspection`, derived from the decision-record
    and cross-item blast-radius authority contracts. Evidence: retained
    decision-request status, Management resolution, named distinct Architect
    review, schema-valid `score-feedback-loop-approved-baseline.json`, and
    digest comparison against the proposed contract, current
    `agent-workflow.json` selector, and agent-inbox assignment Runner. The
    inspection must prove no preallocated decision ID/path, no assumed absent
    registry, and no self-decision/self-review.
  - **Capability profile:** `capability_class=privileged; rights=["read both repositories and durable decision state", "write declared autodocs governance-preparation paths", "invoke the assigned decision-request route", "record resolved references without deciding them"]; data=["requirements dossier", "pipeline contract", "agent-workflow.json selector", "agent-inbox assignment Runner contract", "Management resolution", "Architect review", "Git history"]; tools=["Git", "agent-inbox decision_request/status", "stdlib JSON validator"]; execution_needs=direct; cognitive_demand=critical; independence="preparer, Management decider, and management-instantiated Architect reviewer are three distinct authorities; implementer may not create the decision or review"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("shared scheduling policy and two repositories"); reasoning_depth=critical ("cross-item authority/gate semantics"); context_volume=high ("requirements, governance, overlap, and interfaces"); ambiguity=high ("Management must select policy"); verification_hardness=critical ("identity, resolution, review, and digest must all be independently proven")`. Peak `critical` determines the class.
  - **Branch:** `parent: "0045"; name: "0045-00"; create: "pre-provision from parent; do not create from a stale checkout"`.
  - **Exhaustive write scope (autodocs repository):**
    `docs/dossiers/score-feedback-loop-gate-decision-preparation.md` (new),
    `docs/dossiers/score-feedback-loop-architect-scope-review.md` (new), and
    `docs/pipeline/score-feedback-loop-approved-baseline.json` (new). No
    `DEC-*` path is in scope.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-04/05 plus AGENTS.md cross-item gate-scope exception; preparation is non-operative until Management resolution and distinct Architect review", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** mandatory authority and cross-item scope review before
    either fan-out task can implement the approved contract.
    committed; durable resolution and distinct-review evidence is reachable;
    digest verification passes; no operative gate mutation or private
    `DEC-*` allocation occurred.

## Acceptance criteria

- **AC-001** The durable decision request cites permanent evidence, deciding role, options/consequences, affected work products and processes, and paused action
- **AC-002** Management resolves it
- **AC-003** a distinct management-instantiated Architect supports the resulting scope
- **AC-004** and one approved JSON baseline binds exact resolution/review/interface references and digests for `0045-01` and `0045-02`
- **AC-005** it also chooses and justifies the typed-recipe binding compatible with the authoritative selector, without treating the absent registry files or superseded `0037-46.01`/`.02` as current producers

## Definition of Done

The three scoped preparation/baseline artifacts are
