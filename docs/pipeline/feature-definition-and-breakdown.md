# Feature Definition and Breakdown Process

**Status:** Candidate normative process for the repository engineering process. It becomes an approved baseline only through an independently assigned review and recorded authority decision. It neither approves a product architecture nor accepts security, privacy, safety, release, or residual risk.

**Authority epoch:** Until the authorized Feature `0037` cutover, `TODO.md`, `DONE.md`, and `TODO-*.md` claims are authoritative. The post-cutover mapping uses the issue-store contracts; do not hand-maintain both stores.

## 1. Purpose and boundary

This process turns an intake into a bounded Feature contract and executable Task/Subtask packages. It governs planning evidence, not product approval or reusable-tool lifecycle management (`0039-02`). A Feature contract records proposed scope and gates; it never grants a missing decision.

## 2. Required lifecycle

| Stage | Accountable role | Required result | Gate |
|---|---|---|---|
| Intake | Requirements Engineer | Immutable source locator, need, constraints, data classification, duplicate check | Enough evidence to investigate |
| Contract | Architect | Versioned Feature contract with outcomes, exclusions, requirements/architecture impacts, risks, scopes, and authority interfaces | All material unknowns are decisions or bounded investigations |
| Breakdown | Architect | Task/Subtask graph, stable criteria, scopes, verification and closure package | Structural and semantic checks pass |
| Readiness | Implementer | Capability, action, resource, credential, recovery, and evidence audit | Each Task is executable or explicitly waiting only for a human decision |
| Baseline | Assigned reviewer/authority | Reviewed exact contract, findings, change class, and baseline reference | Process baseline decision only; never product approval |
| Execution and closure | Implementer then integrator | Criterion evidence, parent integration, residual finding disposition, learning record | Existing Task acceptance and Feature-closure rules apply |

## 3. Feature contract rules

A contract MUST use stable `FD-<feature>-AC-<NNN>` acceptance IDs. Each active criterion has one observable outcome, verification method, evidence class, failure meaning, and one or more implementing Tasks. Changed intent receives a new ID and an explicit `supersedes`; withdrawn criteria remain tombstones.

The contract MUST distinguish: stakeholder outcome; product requirements; architecture alternatives/decisions; direct, derived, external, and integration scope; Task start gates; Feature closure gates; and approval authority. A proposed solution is an option, not an approved architecture. Every external effect, credential, security, privacy, safety, release, or irreversible migration interface has a named authority record or a preparatory Task that stops before that effect.

## 4. Breakdown rules

Each Task or Subtask MUST have one primary observable result, bounded inputs/outputs, direct and derived scopes, feasible validation (including negative or recovery evidence where applicable), an execution capability, and an evidence relation. Split a package when preparation and approval need different authority, an architecture decision selects among material alternatives, scopes cannot safely transact together, an irreversible activation needs separate recovery, or the result cannot complete in one bounded attempt after its gates are met.

Dependencies point from consumer to prerequisite. They represent a consumed producer result, decision, readiness condition, integration, or closure condition—not narrative order. A parent owns package closure: terminal children are inputs, never automatic parent completion. Every Feature has exactly one integration Task marked `Integration review: mandatory`; each other Task records either a checkpoint rationale or a no-checkpoint justification.

## 5. Semantic-deadlock and executability audit

In addition to a directed-acyclic graph check, reviewers MUST ask for every item: (1) are all start inputs available; (2) does its completion require a later artifact; (3) does an approval precede the package it reviews; (4) does a parent require a downstream aggregate; and (5) is its required executor capability produced by a successor? Repair an evident defect by correcting the edge, splitting preparation from activation, introducing a local intermediate deliverable, or moving aggregate evidence to parent closure. Do not weaken acceptance to pass a check.

An executable Task names its expected baseline, allowed action/environment, resource and external limits, idempotence/retry/recovery behavior, evidence output, and cleanup. Missing authority, credential, or external configuration blocks only the exact decision/effect; preparatory work remains separately actionable.

## 6. Change, tailoring, metrics, and improvement

Changes are classified as editorial, intent-preserving repair, criterion supersession, scope/architecture change, risk-control change, or emergency containment. Material changes trigger impact analysis for criteria, scopes, dependencies, evidence, and baseline. Tailoring names context, omitted or substituted control, owner, rationale, expiry, compensating control, and approving authority; it cannot silently remove authority, privacy, safety, external-effect, or closure controls.

Measure intake-to-baseline time, criteria with complete implementation-and-verification coverage, pre-execution graph/scope defects, blocked time by cause, Task reopenings, parent-closure lag, and process findings. Report counts and denominator; do not infer capability or performance claims from automation volume.

## 7. Review and migration

Use [`feature-definition-templates.md`](feature-definition-templates.md) for records, [`feature-definition-structural-rules.md`](feature-definition-structural-rules.md) for deterministic checks, and [`feature-definition-migration.md`](feature-definition-migration.md) for legacy/cutover handling. The pilots in `evidence/0039-01/` demonstrate candidate-process assessment only; they do not re-open or alter their assessed Features.

## 8. Automotive SPICE relationship

This process is process support only. Its traceability, configuration, review, risk, and measurement practices may support later assessment preparation, but no document, pilot, check, or metric here asserts assessed capability or conformity for an ECU product.
