# Feature-breakdown instruction

**Status:** normative process instruction for architecture-led Feature
decomposition. It is applied with the current target-branch policy and the
capability-class authority in [`SANDBOX.md`](../../SANDBOX.md). The worked
application is retained in
[`docs/campaign-evidence/0044-04/feature-0043-breakdown.md`](../campaign-evidence/0044-04/feature-0043-breakdown.md).

## 1. Responsibility and source boundary

The management-instantiated Architect owns the breakdown. A Requirements
Engineer may prepare the requirement trace, but does not choose the work graph;
the Implementer does not fill in omitted constraints; and the Integrator does
not silently repair a defective decomposition at a checkpoint. The Architect
records the sources and the reasoning that produced each task contract.

Every Feature breakdown begins with these inputs, with stable identifiers or
file/commit references:

| Input | What the Architect derives from it |
| --- | --- |
| Customer source and requirement baseline | Feature goal, requirement IDs, acceptance obligations, open questions |
| Applicable decision records | Binding policy, authority, waivers, triggers, affected gates, and decisions that must not be re-decided locally |
| Existing architecture and interface contracts | Components, boundaries, invariants, risks, integration points, and the tests needed to exercise them |
| Repository evidence | Current files, branch topology, predecessor work, claims, generated artifacts, known findings, and duplicate/overlap checks |
| Current capability and process authority | Role, capability class, rights, data/tool handles, execution route, and independence restrictions |

The record names an input as `source`, gives its revision or commit where one
exists, and states whether the input is authoritative, evidentiary, or an
assumption. Missing or contradictory input is recorded as a finding; it is not
smoothed into an apparently complete plan. A decision whose reach crosses the
unit's boundary is recorded as a `TK-2` decision before the affected contract
is changed.

## 2. Required task record

For each Task or Subtask, the Architect records the following fields. Markdown,
JSON, or another structured repository format may carry them, but the field
names and controlled values below remain stable so a validator can check
presence and shape.

```yaml
task_id: "0043-06"
feature_id: "0043"
role: architect-elaboration | implementer | qa | integrator | other
architecture_decisions:
  - decision: "..."
    derives_from:
      requirements: ["RQ-..."]
      decision_records: ["DEC-..."]
      existing_architecture: ["path or interface"]
      repository_evidence: ["path@commit or finding"]
    authority_or_assumption: authority | evidence | assumption
prerequisites:
  - task_id: "0043-02"
    derives_from: "consumer contract in docs/pipeline/build-ledger.md"
planned_order:
  position: 3
  order: ["0043-01", "0043-02", "0043-03"]
  order_matters_because: "..."
test_scope:
  derives_from: ["interface contract", "architecture risk", "acceptance criterion"]
  kind: unit | integration | end_to_end | manual_inspection | none-with-reason
  evidence: "command, fixture, report, or explicit gap"
capability_profile:
  capability_class: sandboxed-grunt | unprivileged | privileged
  rights: ["read repository", "write declared paths"]
  data: ["git history", "non-git fixture", "PGP key handle", "none"]
  tools: ["stdlib Python", "Git", "browser", "runner"]
  execution_needs: direct | runner | none
  cognitive_demand: low | medium | high | critical
  independence: "..."
branch:
  parent: "0043"
  name: "0043-06"
  create: "pre-provision from parent; do not create from a stale checkout"
```

The capability profile describes the Task, not the preference of a receiving
session. Rights, data, tools, execution needs, and cognitive demand are
separate dimensions. A profile may require `unprivileged` or `privileged`
direct execution even when the role normally maps to `sandboxed-grunt`; it may
never grant authority forbidden by `SANDBOX.md`, `AGENTS.md`, or the role
catalog. The deterministic matcher introduced by a later Task consumes this
profile; an Architect must not select an agent by intuition in its place.

## 3. Deriving prerequisites and planned order

The prerequisite graph is derived from actual producer/consumer contracts,
shared baselines, required decisions, and integration boundaries. For every
edge, record the artifact or contract that makes the predecessor necessary and
whether the edge is a hard start gate or only an order preference. Check the
whole transitive closure for cycles, duplicate ownership, stale claims, and
unavailable branches.

If order matters, record the intended sequence before work starts. The sequence
must include the Feature's exactly-one integrating Task and its declared review
floor. A later deviation is not silently folded into the plan: compare the
actual event with the recorded sequence and apply Gate A2 below when the
canonical cross-item predicate is met.

## 4. Deriving test scope and kind

Test obligations come from the architecture risks and interfaces that the Task
changes, the acceptance criteria, the producer/consumer contract, and any
external or irreversible effect. The record states why the selected kind is
proportionate:

- unit tests exercise local transformations and invariants;
- integration tests exercise the declared interface between integrated units;
- end-to-end tests exercise the real chain when composition is the failure
  mode;
- manual inspection is valid only when the contract identifies what is
  inspected and what evidence is retained; and
- `none-with-reason` names the unautomated gap and its compensating review or
  escalation path. It is never a silent omission.

The planned command, fixture or manual procedure, expected evidence, and
known baseline findings are recorded with the derivation. A green test result
does not prove that the decomposition's scope or authority is correct.

## 5. Branch creation and target-policy checks

The implementer receives a pre-provisioned branch named for the item. A Task
branch starts from its Feature branch; a Subtask branch starts from its Task
branch, as specified by
[`branch-workflow.md`](branch-workflow.md). Before authoring, merge every
done-but-unintegrated prerequisite branch required by the binding base-and-merge
rule, record each merged tip, and verify the checkout is the item-owned
worktree. The root checkout is read-only.

### Gate A1 — structured branch-time evidence

At branch creation, compare the proposed work against the policy of `main`,
which is the required primary target. If an intermediate target is also
checked, name it as an additional comparison and explain why. The breakdown or
branch record contains exactly one structured A1 field (a prose sentence may
also render it for humans):

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits | does-not-fit
  checked_target: main
  basis: "requirements/decision/architecture/repository references"
  checked_at: "ISO-8601 timestamp"
  recorded_by: "role and owner token"
```

`basis` is the recorder's attribution, not Management wording. The field's
presence and well-formedness are mechanically checkable; its truth is a known
residual risk. The field is a **net**, not the final gate: the Integrator's A1
/ A2 triage at the integration checkpoint remains the **gate**. A missing or
malformed field is a finding against the operation, never a neutral blank.

If the verdict is `does-not-fit`, report the finding to the relevant
Integrator, who escalates to the Project Lead when needed. Prefer the person
already handling the operation; if unavailable, use another reachable
representative of the same role. This is a role-based report, not a
person-dependent bypass. Under `DEC-0044-017`, work may continue while the
report is pending; that assumption is explicit and must be revisited if
Management changes it. The Architect does not self-authorize a policy change.

## 6. Gate A2 — order deviations and foreign impact

Gate A2 is an application of the canonical `cross-item-blast-radius` predicate
in [`decision-record.md`](decision-record.md#2-wann-ein-datensatz-verpflichtend-ist),
not a second test. Use the canonical modal scope: record a deviation when it
**can** block the start, validation, acceptance, integration, or closure of
another work unit, **or can change that unit's contract**. A deviation that
affects only the owner's internal order is not an A2 record.

The owner of the deviating unit records the event at the time it is recognized,
including planned order, actual order, affected unit, mechanism of impact,
decision/authority, timestamp, and resulting work or contract change. The
owner is responsible for the first record, but the Integrator owns the
checkpoint triage: it may demand a missing A2 record, and in case of doubt the
event is recorded. The record identifies whether it is a trigger under the
canonical predicate; it does not claim that an ordinary delay is a gate.

## 7. Pilot and applicability

The source/dependency/test/profile record shape is binding for breakdowns. The
new A1/A2 behavior is binding first for the named pilot Tasks, and general
effectiveness is claimed only after the pilot is evaluated, at the latest by
the mandatory `0044-08` review. Its explicit worked pilot is retained before
broad claims of successful operation. For the authorized Feature `0043` pilot,
A1 evidence is limited to Tasks
`0043-03`, `0043-06`, and `0043-07`; `0043-04` and `0043-05` are excluded by
their current `[u]`/foreign-claim state, and `0043-01`/`0043-02` are terminal.
The evidence records any pre-existing branch honestly rather than retroactively
certifying a branch-time check. Feature `0043` currently supplies no genuine
foreign-impact order deviation, so A2 is explicitly **not tested** there. A2
becomes tested only when the next newly broken-down Feature supplies such a
case; until then, the untested status is a carried, disclosed risk.

The pilot-first condition is explicit: general effectiveness of A1/A2 is not
claimed merely because this document is linked from an authority file. The
pilot evidence and later mandatory `0044-08` review determine whether the
instruction is complete in practice.
