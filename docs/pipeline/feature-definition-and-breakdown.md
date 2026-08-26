# Feature Definition and Breakdown Process

**Status:** Candidate normative process for the repository engineering process. It becomes an approved baseline only through an independently assigned review and recorded authority decision. It neither approves a product architecture nor accepts security, privacy, safety, release, or residual risk.

**Measured against baseline:** `docs/pipeline/feature-breakdown.md` at `main` commit
`9ccd99b25ccadffa951b0f184e174dd4fa2b8621` (Task `0044-04`, `[x]`, **Task Acceptance `✓`**),
including its §8 added by Task `0044-06` (`[x]`, integration-reviewed, **no Task Acceptance**).
The three states — implementation-complete, integration-reviewed, accepted — are recorded
separately and never collapsed; §8's reference may still move.

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

**The breakdown mechanics are owned by [`feature-breakdown.md`](feature-breakdown.md) and
are cited here, never restated.** Two normative texts on one contract diverge silently, and
the divergence is invisible until they disagree in a live case. That document governs the
source boundary, the required task record, prerequisite and order derivation, test scope and
kind, branch creation, gates A1/A2, and — per its §8 — cognitive-demand estimation, for which
a task record carries **all five dimension ratings, the evidence, and the estimator version**,
with missing evidence recorded as `unknown` and never scored `low`.

This section adds only what is specific to *Feature definition* and is not covered there:

Split a package when preparation and approval need different authority, an architecture
decision selects among material alternatives, scopes cannot safely transact together, an
irreversible activation needs separate recovery, or the result cannot complete in one bounded
attempt after its gates are met.

Dependencies point from consumer to prerequisite and represent a consumed producer result,
decision, readiness condition, integration, or closure condition — not narrative order. A
parent owns package closure: terminal children are inputs, never automatic parent completion.
Every Feature has exactly one integration Task marked `Integration review: mandatory`; each
other Task records either a checkpoint rationale or a no-checkpoint justification.

## 5. Semantic-deadlock and executability audit

In addition to a directed-acyclic graph check, reviewers MUST ask for every item: (1) are all start inputs available; (2) does its completion require a later artifact; (3) does an approval precede the package it reviews; (4) does a parent require a downstream aggregate; and (5) is its required executor capability produced by a successor? Repair an evident defect by correcting the edge, splitting preparation from activation, introducing a local intermediate deliverable, or moving aggregate evidence to parent closure. Do not weaken acceptance to pass a check.

An executable Task names its expected baseline, allowed action/environment, resource and external limits, idempotence/retry/recovery behavior, evidence output, and cleanup. Missing authority, credential, or external configuration blocks only the exact decision/effect; preparatory work remains separately actionable.

## 6. Change, tailoring, metrics, and improvement

Changes are classified as editorial, intent-preserving repair, criterion supersession, scope/architecture change, risk-control change, or emergency containment. Material changes trigger impact analysis for criteria, scopes, dependencies, evidence, and baseline. Tailoring names context, omitted or substituted control, owner, rationale, expiry, compensating control, and approving authority; it cannot silently remove authority, privacy, safety, external-effect, or closure controls.

Measure intake-to-baseline time, criteria with complete implementation-and-verification coverage, pre-execution graph/scope defects, blocked time by cause, Task reopenings, parent-closure lag, and process findings. Report counts and denominator; do not infer capability or performance claims from automation volume.

## 7. Review and migration

Use [`feature-definition-templates.md`](feature-definition-templates.md) for records, [`feature-definition-structural-rules.md`](feature-definition-structural-rules.md) for deterministic checks, and [`feature-definition-migration.md`](feature-definition-migration.md) for legacy/cutover handling. The pilots in `evidence/0039-01/` demonstrate candidate-process assessment only; they do not re-open or alter their assessed Features.

## 7a. Claim discipline for planning statements

Every rule in this section was derived from a recorded defect in this repository, several of
them made by this document's own author while producing it. They are stated as requirements
because a planning process that cannot make its own claims checkable cannot make anyone
else's checkable either.

**7a.1 Every check declares direction, reach, and effect.** A check's declared semantics and
its actual semantics diverge on three axes, and each has produced a real incident:

| Axis | The question it answers | Failure when unstated |
|---|---|---|
| **Direction** | What can this check structurally *not* find? | A marker-transition reader reports "no escalation" for a Task escalated twice, because a `[u]` integration verdict lives beneath the node while its marker stays `[x]` |
| **Reach** | What may *not* be inferred from a passing result? | Agreement with one known incident is evidence against false positives only; it says nothing about completeness |
| **Effect** | Does it observe, or does it mutate? | A deliberately held-open verification transaction is indistinguishable, in one sample, from an abandoned staged tree |

A check whose direction is unstated will be read as exhaustive. State it.

**7a.2 A deliverable pins the baseline it was measured against, and that baseline's
acceptance state.** Record the exact commit **and** whether it carried current Task Acceptance
at measurement time, keeping *implementation-complete*, *integration-reviewed*, and *accepted*
as three distinct states. A commit hash alone pins provisional state as though it were
foundation. The failure this prevents is silent, not frequent: one occurrence justifies it.

**7a.3 An overlap, duplication, or conflict claim quotes the text of both sides.** A
structural resemblance between two headings is not evidence that two documents normatively
duplicate each other; measured, they may address different objects behind similar titles, and
each may already exclude the other. Cite both texts or do not make the claim.

**7a.4 A lexical measure may not be reported as a structural one.** Keyword presence cannot
distinguish a state from a requirement about that state, from the topic of the document, or
from a sentence *forbidding* the thing being counted. Where the object being counted has no
defined shape, say so and adjudicate case by case with quoted evidence, rather than reporting
whichever proxy reads better.

**7a.5 Escalation needs a record shape, and does not yet have one.** The `[u]` marker and the
`[u]` integration verdict are lifecycle states, not escalation records, and they miss
escalations recorded in prose or resolved without a surviving marker transition. Until a
conforming shape exists, an escalation count is an adjudication with quoted evidence per case,
never a parser result. **This is an open requirement on this process, recorded rather than
silently satisfied.**

**7a.6 A frequency claim names its population before it is counted.** Aggregating unlike
events into a rate inflates it; the correct response to two similar-looking incidents is to
ask whether they are the same kind of event, not to report a cadence.

## 8. Automotive SPICE relationship

This process is process support only. Its traceability, configuration, review, risk, and measurement practices may support later assessment preparation, but no document, pilot, check, or metric here asserts assessed capability or conformity for an ECU product.
