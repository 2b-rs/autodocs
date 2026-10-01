# Architect scope review — `0044-06` cognitive-demand calibration

**Position:** `supports-with-conditions`
**Review kind:** pre-mutation cross-item gate-scope review
**Reviewer:** `agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f`, management-instantiated Architect
**Decision:** [`DEC-0044-026`](dec-0044-026-cognitive-demand-scope.md)
**Baseline:** `main@433b41b04cd4b353f9681947a9e3c7897a751855`
**Implementation status:** prohibited until this decision and review are reachable from `main`

This review covers architecture and scope only. It does not claim Task
implementation, Acceptance, checkpoint review, integration, or Feature closure.
Data must not implement or later review, accept, or integrate this product.

## Existing contract and cross-item reach

Accepted `0044-04` already defines the normative field and closed values:

```yaml
cognitive_demand: low | medium | high | critical
```

Task `0044-06` therefore calibrates the meaning and estimation of those exact
values; it does not own their spelling, cardinality, or schema compatibility.
`0044-05` consumes the value as a scheduling/capability-matching input, and
`0044-08` consumes the completed method in the Feature-wide proof. A declared
estimator that changes eligibility, dispatch, validation, or acceptance can
block other work units, so `cross-item-blast-radius` applies even though the
Task's current checkpoint is not mandatory. The no-checkpoint justification is
preserved: `0044-08` is the integration review floor. This review does not move
or add a checkpoint.

`RQ-CB-06` is explicitly an interpretation awaiting customer confirmation at
`0044-08`. The implementation may test a reversible two-channel protocol, but
must not present that interpretation as customer-confirmed or activate an
irreversible scheduling rule.

## Smallest authorized calibration reach

The future Implementer may produce only:

1. a repository study defining the evidence population and at least ten
   historical calibration cases;
2. a normative rubric for the five Task-owned dimensions: scope breadth,
   reasoning depth, context volume, ambiguity, and verification hardness;
3. a deterministic mapping from the five dimension ratings to the existing
   four-value result, with boundary examples and missing-data behavior;
4. append-only prediction and later-outcome record formats;
5. a self-flag protocol for unexpected demand; and
6. an independent orchestrator-side result-quality check that operates whether
   or not the implementer self-flags.

The initial operational mode is `shadow`: record the computed class and any
disagreement with the currently declared class, but do not overwrite it or use
the estimate alone to accept/reject an assignment, mutate a claim, stop a Task,
or choose an agent. Existing authority and capability checks remain controlling.

## Required estimator properties

Each dimension uses the same four ordered levels as an internal ordinal input.
The implementation must define observable anchors, not personality or model
labels. The aggregation must be deterministic from the recorded vector and
explicit modifiers. At minimum it must specify:

- how the dominant/highest dimension affects the result;
- whether multiple adjacent high dimensions escalate the result;
- how unknown or unavailable evidence is represented without scoring it `low`;
- how decomposable breadth differs from irreducible reasoning depth;
- how verification hardness accounts for missing independent oracles;
- how ambiguity is reduced when a binding decision already exists; and
- how the same Task contract produces the same prediction independent of the
  identity of the intended agent.

Agent/runtime capability affects the later outcome comparison, not the package's
intrinsic demand label. The study may analyze conditional performance, but must
not redefine demand as "which model succeeded."

## Calibration and falsification matrix

The selection protocol must be frozen before inspecting case outcomes. The
sample must span at least two Features, all four predicted values where evidence
permits, and both clean completion and rework/failure/blocked outcomes. Each case
binds the exact historical Task contract and evidence REF. Exclusions and missing
telemetry are reported.

Required falsification includes:

| Case | Expected property |
|---|---|
| Narrow, explicit, locally verifiable edit | Must not rise solely because the repository is large. |
| Small diff with deep authority reasoning | Reasoning/ambiguity may dominate breadth. |
| Broad mechanical change with strong oracle | Breadth alone does not imply `critical`. |
| Missing independent verification oracle | Verification hardness cannot silently score `low`. |
| Binding decision removes ambiguity | Re-estimation reflects the reduced ambiguity with other dimensions unchanged. |
| Same package, different proposed agent | Intrinsic demand prediction remains identical. |
| Self-flag absent but output violates contract | Independent quality gate rejects or returns findings. |
| Self-flag present but output is conforming | Signal is recorded; disposition follows evidence, not the flag alone. |

Report at least the confusion matrix over the four ordered classes, exact-match
rate, within-one-class rate, false-high/false-low direction, and every
misprediction narrative. Ten examples are a minimum calibration exercise, not
evidence of statistical generality.

## Nondeterminism protocol boundary

The implementer-side signal records an unexpected context/complexity condition,
the affected dimension, work and validation already completed, safe next step,
and requested response. It does not automatically set `[u]`, release ownership,
authorize a new agent, or waive completion.

The orchestrator-side gate checks contract coverage, required artifacts,
validation outcomes, and evidence integrity. It is independent of self-report
and must fail closed on absent required evidence. Its outcome can trigger the
ordinary finding/correction/assignment process, but this Task does not invent a
new Acceptance or lifecycle state.

## Explicit exclusions

This scope does not authorize:

- changing `low | medium | high | critical`, their schema spelling, or adding a
  parallel numeric public field;
- mutating `AGENTS.md`, `TODO.md`, `feature-breakdown.md`, capability schemas,
  matcher tools, Task markers, Acceptance, checkpoints, or `DONE.md` in this
  governance phase;
- using tokens, wall time, completion, model identity, or self-confidence as a
  sole demand or quality oracle;
- retroactively rewriting historical task records or inventing missing usage
  measurements;
- automatic dispatch, rejection, reassignment, or work stoppage from a shadow
  estimate; or
- claiming the `RQ-CB-06` customer-confirmation point is resolved.

## Role separation, activation, and recovery

After this packet is integrated to `main`, a separately assigned Implementer may
author the bounded study and normative implementation. Data is excluded from
that implementation and from subsequent Acceptance and integration of the same
product. The Acceptance reviewer independently checks the frozen sample,
evidence bindings, rubric determinism, misprediction analysis, and unchanged
vocabulary. The separately assigned Integrator evaluates cross-contract
composition at `0044-08` and preserves the customer-confirmation gate.

Activation beyond shadow recording requires measured calibration evidence and a
new cross-item decision/scope review. Rollback stops new estimator use and
removes the later implementation as one bounded change while preserving this
decision, review, versioned prediction/outcome evidence, findings, and prior
authority history.

## Advisory delivery profile

- **Capability:** future Implementer `unprivileged` or `privileged`; local Git,
  documentation and deterministic test execution; no network or credentials.
- **Cognitive demand:** `high`; historical calibration and gate direction need
  careful evidence handling, but no irreversible operation is authorized.
- **Estimate:** 4-8 implementation/study/documentation paths, at least ten bound
  historical cases, 8-16 focused tests, under 20 CPU minutes and 1 GiB memory.
- **Risk:** false-low estimates under-resource difficult work; false-high
  estimates serialize or over-provision work. Neither direction may silently
  become authority in shadow mode.

## Current-main re-pin provenance

The governance-only re-pin requested under
`agent-inbox:1787698716694-07e845be` is re-derived from
`main@433b41b04cd4b353f9681947a9e3c7897a751855` and retains exact candidate
`5ff57c7717208283c1000530b93318b633d64918` as ancestry. The intervening main
changes are disjoint from all four packet paths and alter none of this review's
evidence, affected gates, shadow-only activation, recovery, or separation
conditions. The re-pin commit touches only the declared packet and carries
current `Base-Ref`, `Prior-Candidate`, and `Policy-Origin-Branch: main`.

## Architect verdict

**Supports with the conditions above.** Any vocabulary change, automatic
scheduling enforcement, new lifecycle state, or claim that `RQ-CB-06` is
customer-confirmed exceeds this review and requires fresh authority before
mutation.
