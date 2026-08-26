# Cognitive Demand Estimation Study (0044-06)

**Status:** completed elaboration study; **estimator:** `cognitive-demand-rubric@v1`; **mode:** shadow only.

This study calibrates the existing `low | medium | high | critical` vocabulary.
It changes no capability, assignment, ownership, Acceptance, integration,
execution authority, Task marker, matcher eligibility, or existing profile.

## Five-dimension method

Rate the package, independently of the intended agent, and bind every rating to
the exact Task contract and evidence.

| Level | Scope breadth | Reasoning depth | Context volume | Ambiguity | Verification hardness |
| --- | --- | --- | --- | --- | --- |
| `low` | One isolated path/checklist | Direct transformation | 1-2 short sources | One binding reading | Local deterministic oracle |
| `medium` | Localized multi-path unit | Defined interacting logic | Several bounded sources | Minor resolved choices | Focused tests/exact inspection |
| `high` | Cross-component/process reach | Architecture or competing invariants | Large transitive contract set | Material interpretation | Independent failure/recovery checks |
| `critical` | Repository-wide coupled state | Security, authority, migration, or state-machine reasoning | Repository-scale dependent state | Choices change authority/irreversible behavior | No simple oracle; adversarial recovery evidence |

Record `scope/reasoning/context/ambiguity/verification`. Missing evidence is
`unknown`, never `low`, and makes the result `incomplete`. Otherwise the result
is the highest rating. A binding decision may lower ambiguity on re-estimation;
other dimensions require new evidence. Decomposition lowers breadth/context
only for a complete independently verifiable child contract, never irreducible
reasoning. Boundary canaries are `L/L/L/L/L -> low`, `M/L/M/L/M -> medium`,
`L/H/M/H/H -> high`, and `M/C/H/H/C -> critical`.

## Frozen historical calibration

Before outcomes were inspected, the supplied packet fixed these ten Tasks.
Inclusion required reachable IDs/REFs; conflicts with repository evidence are
reported. The observed class is a disclosed outcome proxy, not ground truth:
clean bounded completion supports its band; material correction can raise it;
repeated correction/checkpoint rejection indicates at least `high`; and an
authority-sensitive repository transaction state machine supports `critical`.
Missing resource telemetry remains missing.

| Task | Recorded vector | Prediction | Repository-bound outcome | Proxy | Error |
| --- | --- | --- | --- | --- | --- |
| `0044-01` | H/H/H/H/H | high | `decfce912`, then material corrections `711095a5b`, `36d048ce2`, `fc466afb2` | high | exact |
| `0044-02` | H/H/H/H/H | high | Management-resolved semantics; implementation `c9f0968e9` | high | exact |
| `0044-03` | H/H/H/M/H | high | `431cb97908`, integrated by `5e1ee62df` | high | exact |
| `0044-04` | H/H/H/H/H | high | corrective `7ed7d2ab5` and `e1127ac2f` after earlier substantive work | high | exact |
| `0044-05.01` | H/H/H/H/H | high | architecture baseline `9854d2f18` | high | exact |
| `0044-05.02` | M/M/M/M/M | medium | findings `F-0044-05-GEORDI-001/-002`; correction `e637660978` | high | false-low 1 |
| `0044-05.03` | L/L/L/L/L | low | adoption `6bfd0fc74`; actual self-application profile declares `high` | high | false-low 2 |
| `0038-01` | C/C/C/H/C | critical | fail-closed transaction coordinator `b55913571f`, 23/23 tests recorded | critical | exact |
| `0044-14` | M/M/M/M/M | medium | tool `11d3498e8` plus governance `649db737b` | high | false-low 1 |
| `0044-15` | M/M/M/L/M | medium | focused blind-spot correction `0d2497caf` | medium | exact |

Confusion matrix, rows predicted and columns observed (`low/medium/high/critical`):
`low=0/0/1/0`, `medium=0/1/2/0`, `high=0/0/5/0`,
`critical=0/0/0/1`. Exact match is 7/10; within one class 9/10;
false-low 3/10; false-high 0/10. This imbalanced minimum sample is not evidence
of statistical generality. Errors show that small-looking implementation and
adoption hid schema, authority, and composition constraints.

## Prediction, outcome, and nondeterminism protocol

Each append-only prediction records estimator version, Task/contract REF and
digest, five ratings, result, rationale/evidence, predictor/time, current
declared value and disagreement. Later append outcome REF/disposition,
agent/runtime context, validation/rework evidence, and error direction.

An implementer encountering state explosion, lost constraints, guessing, or a
failure loop emits `COGNITIVE_OVER_DEMAND`, recording the affected dimension,
completed work/validation, safe state, and requested response. It leaves `[p]`;
it is not `[u]`, abandonment, reassignment, Acceptance, or waiver authority.

Independently, the Orchestrator checks required artifacts/scope, reproducible
validation evidence, unsupported compliance claims, and repeated findings
without progress. Missing evidence fails the quality check without a self-flag;
a self-flag does not fail conforming work. Findings use ordinary correction and
assignment processes. This protocol does not automatically reassign, stop work,
initiate a waiver, or change matching eligibility.

Falsification canaries include a narrow edit unaffected by repository size, a
small diff dominated by authority reasoning, broad mechanical work with a
strong oracle not automatically critical, missing oracle recorded `unknown`,
ambiguity reduced by a binding decision, and an identical prediction for the
same package with a different proposed agent. Rollback stops new predictions
and removes normative estimator text while retaining decisions, reviews,
prediction/outcome evidence, discrepancies, and lifecycle history.
