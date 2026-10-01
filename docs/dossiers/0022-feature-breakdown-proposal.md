# Feature `0022` architecture and breakdown proposal

**Status:** non-operative pre-mutation proposal for independent Architect scope
review. It does not change a prerequisite, checkpoint, consumer contract, live
validator, assessment disposition, or evidence gate.

**Prepared by:** `agent:data:0022-01:20260828T095108Z-3e883c05`,
management-instantiated Architect, distinct from the future Implementer and
Integrator.

**Pinned preparation baseline:** `0022-01@4394a9960e2bb258b442f906bb153ee3046c4c83`
after merging `0020-09@032fcb6ccc72af6670b1aaffc67ed8041af1508b`.

## 1. Sources and authority

| Source | Pin | Classification | Derivation |
| --- | --- | --- | --- |
| `TODO.md` Feature `0022` and Tasks `0022-01`/`0022-02` | `main@542d9fa31fd6916571e2a7602c8179eeda9e0d6d` | authoritative backlog | Feature goal, existing Task obligations, current prerequisites |
| `docs/dossiers/dec-0020-01-ecu-scope.md` | blob `784f6e3ff827e6892a0b11114457bf7452777898` | Management decision | software-only supplied-product boundary; kernel and complete ECU lifecycle excluded |
| `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md` | blob `da4242a865aede7fa567c0a37ffc740b4ce24d7f` | authoritative `decision-record@v1` | refuse wrong-origin evidence at named use/freeze points; no broad start gate |
| `docs/dossiers/0020-02-gate-scope-review.md` | blob `1717e89262c557fda6fd5a86094d59f33a8a7351` | authoritative supporting review for `DEC-0020-002` | Feature `0022` receives no inherited new start gate; consumer-side refusal remains bounded |
| `docs/dossiers/req-0020-03-responsibility-authority-matrix.md` | blob `e010446318c1a70b9053942864d0f031fdf2d044` | authoritative predecessor work product | no complete-system owner; external parties and authorities remain unnamed |
| `docs/dossiers/req-0020-04-applicability-matrix.md` | blob `20aae90000bece895fa00a69562b28f697a9b22f` | authoritative predecessor work product | `SYS.1`–`SYS.5` are `out of scope/not rated`, execution `external`; zero shared rows |
| `docs/dossiers/req-0020-09-execution-register.md` | blob `74e19d1e5f2936dd26087cab7b524ebbdb0238b1` | authoritative direct prerequisite | selected-profile consumer edges and open external-party decisions |
| `docs/ASPICE/04-gap-roadmap.md` | blob `1345f120b4d7c479678a02d1f1141e3050130617` | informative architecture evidence | intended Feature `0022` boundary and conditional consumer sequence |
| `docs/pipeline/feature-breakdown.md` | blob `d15ee3ceb98ddfa611edffcbece01a54434498bc` | normative process | required source, dependency, test, profile, A1/A2, and integrating-Task fields |

Assumption A-01 is that the merged predecessor records remain current until an
append-only Management decision changes the supplied-product boundary or SYS
responsibility. A changed disposition invalidates this proposal; it is not
silently absorbed.

## 2. Normalized Feature requirements

These identifiers project the existing Feature/Task sentences into stable
architecture handles. They add no customer requirement.

- **`RQ-0022-01` — Per-process interface plan.** For each `SYS.1`–`SYS.5`,
  record assessment disposition separately from execution responsibility,
  assessed-unit outcome/activity boundary, performer and authority, typed
  inputs/outputs, configuration identity, acceptance, feedback, and the exact
  completion/evidence gate.
- **`RQ-0022-02` — Shared lifecycle trace contract.** Define versioned nodes and
  edges from stakeholder source through requirement, architecture/allocation,
  implementation, measure, result, finding, change, release, and validation,
  preserving responsibility origin, baseline, variant, status, and rationale.
- **`RQ-0022-03` — Fail-closed validation without false process credit.** Detect
  wrong verification basis, stale baseline, cross-variant edge, orphan,
  inconsistent responsibility origin, and substituted non-ECU evidence; do not
  claim that any SYS process was performed.
- **`RQ-0022-04` — Governed composition.** Integrate the interface plan and
  trace controls through exactly one terminal integrating Task with independent
  review, current source pins, recovery evidence, and consumer handoffs.

## 3. Current process/interface baseline

The present disposition is uniform and must remain explicit rather than being
collapsed into “not applicable”:

| Process | Assessment disposition | Execution responsibility | External performer/authority | Assessed-unit boundary now |
| --- | --- | --- | --- | --- |
| `SYS.1` | `out of scope/not rated` | `external` | `not-decided` | no SYS.1 outcome claimed; receive only an identified stakeholder baseline if a consumer needs it |
| `SYS.2` | `out of scope/not rated` | `external` | `not-decided` | validate an allocated system/software-requirement input for `0023-11`; do not claim internal SYS.2 |
| `SYS.3` | `out of scope/not rated` | `external` | `not-decided` | validate architecture, allocation, and interface constraints for `0023-11`; do not claim internal SYS.3 |
| `SYS.4` | `out of scope/not rated` | `external` | `not-decided` | no complete-ECU integration or SYS.4 measure/result credit |
| `SYS.5` | `out of scope/not rated` | `external` | `not-decided` | no integrated-ECU/system-requirement verification credit |

There are zero shared processes. A row cannot become `shared` merely because
the assessed unit receives an artifact: both parties, both activity boundaries,
and both evidence gates must first be named by an authorized decision.

### 3.1 Proposed typed interface rows

The eventual `0022-01` work product should use one row per process with these
required fields:

`process_id`, `assessment_disposition`, `execution_responsibility`,
`assessed_unit_outcomes`, `external_outcomes`, `performer`, `review_authority`,
`approval_authority`, `acceptance_authority`, `input_types`, `output_types`,
`product_id`, `project_id`, `process_instance_id`, `baseline_id`, `revision`,
`variant_id`, `responsibility_origin`, `status`, `validity`, `retention`,
`confidentiality`, `configuration_gate`, `acceptance_gate`,
`problem_feedback`, `change_feedback`, `risk_feedback`, and `evidence_gate`.

`not-decided` is valid only for a definition record and is never a passing
activation or evidence-gate value. A consumer must fail closed when it requires
an external party/authority that remains unnamed.

### 3.2 Process-specific input/output contract

| Process | Required input types | Required output types | Conditional consumer/use gate |
| --- | --- | --- | --- |
| `SYS.1` | stakeholder/source register, intended-use and operating-context sources, change/risk inputs | agreed stakeholder-requirement baseline plus communication/change history | input to selected `SYS.2` or approved external allocation; no current internal consumer credit |
| `SYS.2` | controlled stakeholder baseline | analyzed system-requirement baseline, verification criteria, allocation candidates, trace/consistency result | `0023-11` may accept only an exact external/shared baseline with named origin and authority; conditional Feature `0029` remains inactive now |
| `SYS.3` | controlled system requirements and constraints | evaluated system architecture, element allocations, interfaces, budgets, rationale, trace/consistency result | `0023-11` may accept exact allocated requirements and architecture/interface constraints; Features `0030`/`0031` remain conditional |
| `SYS.4` | accepted architecture and element baselines, integration sequence, environment, architecture/interface measures | integrated-system baseline, measure specifications and results, finding/disposition summary | conditional Feature `0031`; no substitution by `SWE.5` or pipeline integration evidence |
| `SYS.5` | accepted system requirements, integrated-system baseline, controlled environment, requirements-based measures | system-verification specifications/results and communicated summary | conditional Feature `0032` and external release/validation interface; no substitution by `SWE.6` or repository validation |

All five rows link feedback by stable reference to `SUP.9`, `SUP.10`, and
`MAN.5`, and configuration identity to `SUP.8`. Those links are interface
obligations, not newly proposed Task-start prerequisites. Current incomplete
execution of those processes remains visible and is not fabricated here.

## 4. Cross-item reach and decision proposal

The operative plan would change contracts used by `0023-11`, conditional
Features `0028`–`0032`, release/validation consumers, and Feature `0022`
closure. It therefore triggers both `cross-item-blast-radius` and
`material-architecture-or-repository-behavior`.

Existing `DEC-0020-002` governs evidence-origin refusal and prohibits broad
start/validation gates. It does not choose the exact SYS interface-row schema,
activation conditions, consumer acceptance semantics, or the Feature `0022`
task/checkpoint graph. A new conforming record is required. This proposal does
not allocate a `DEC-0022-*` identifier; allocation must occur against current
`main` in the separately authorized governance path.

### `PD-0022-01-GATE-01` — proposed decision subject

Select a versioned, per-process conditional interface contract in which the
current five SYS rows remain external and not rated; `not-decided` authorities
permit definition but never gate satisfaction; future activation requires an
append-only Management disposition change plus named performer/acceptance
authority and exact baseline; `0023-11` may accept external SYS.2/SYS.3 inputs
only at use and without adding SYS Tasks as unconditional predecessors; and
wrong-origin evidence is refused under `DEC-0020-002` without registering a
repository-wide validator.

Considered alternatives for the future record:

- **ALT-01 (selected in this proposal):** conditional typed interfaces with
  fail-closed use/activation gates and no broad start edge.
- **ALT-02 (reject):** activate `0028`–`0032` or the 20-process profile now;
  contradicts the selected profile and absent complete-system ownership.
- **ALT-03 (reject):** allow unnamed external parties to satisfy a consumer;
  invents performer and authority.
- **ALT-04 (reject):** add `0029`/`0030` as unconditional predecessors of
  `0023-11`; repeats the start-gate widening rejected by `DEC-0020-002`.
- **ALT-05 (reject):** treat interface documentation, pipeline tests, or
  controlled scenarios as SYS execution evidence; violates the evidence
  boundary and Feature goal.

Affected work units: `task:0022-01`, `task:0022-02`, proposed `task:0022-03`,
`task:0023-11`, `feature:0028`, `feature:0029`, `feature:0030`,
`feature:0031`, `feature:0032`, `task:0024-02`, and `feature:0022`.

Affected gates: `task-start`/activation of `0028-01`, `0029-01`, `0030-01`,
`0031-01`, and `0032-01`; use-time acceptance at `0023-11`; validation of the
shared trace contract; integration/closure of Feature `0022`; and the external
system-verification/validation input to `0024-02`. The independent review must
confirm whether `0024-02` is a direct affected gate or only a downstream
consumer before the decision record is allocated.

## 5. Proposed Task graph

No line below is operative until the decision record and supporting independent
Architect scope review are reachable on the implementation baseline.

```text
0020-09 [x]
    |
0022-01  per-process interface plan  [mandatory checkpoint]
    |
0022-02.01  versioned lifecycle node/edge contracts
    |
0022-02.02  validator and adversarial fixtures
    |
0022-02  parent consistency/aggregation
    |
0022-03  terminal Feature integration package [mandatory checkpoint]
```

### `0022-01` — baseline the conditional system-interface plan

- **Role:** `implementer` (Requirements Engineer or other exact assigned role),
  distinct from Architect Data and the Integrator.
- **Architecture decisions:** implement only the independently reviewed
  `PD-0022-01-GATE-01` decision; preserve all current external/not-rated rows;
  treat `not-decided` as non-passing for activation/use.
- **Prerequisite:** `0020-09`; derives from the selected-profile register.
- **Planned order:** first; it establishes the consumer contract for every
  later Task.
- **Write scope:** `docs/dossiers/req-0022-01-system-interface-plan.md`, own
  claim, and item-local `TODO.md` bookkeeping only.
- **Acceptance criteria:** all five rows and every required field are present;
  assessed/external boundaries are explicit; inputs/outputs and feedback links
  are process-correct; no SYS execution/rating is claimed; no unnamed authority
  passes; consumer and recovery behavior are explicit.
- **Definition of Done:** committed definition with source pins, a complete
  five-row matrix, deterministic completeness check or bounded manual table
  audit, finding disposition, and real REF. No live validator or downstream
  activation.
- **Test scope:** `manual_inspection` plus a small deterministic table-shape
  check if the selected format is machine-readable; derive cases from missing
  field, unnamed-authority, wrong disposition, and accidental shared-row risks.
- **Capability profile:** `unprivileged`; read/write declared docs, Git and
  stdlib checker; direct execution; cognitive `high`; independence from this
  Architect and the Integrator.
- **Demand/risk estimate:** 18k–30k model tokens; 35–70 minutes; <1 CPU-minute;
  context `high`; ambiguity `medium`; verification hardness `medium`; uncertainty
  ±35%; material risk `high` because consumers can accept the wrong system input.
- **Integration review:** `mandatory`.
- **Checkpoint rationale:** this is the shared, cross-Feature interface baseline
  consumed by at least six later work units; a false pass can create internal SYS
  credit or admit an unowned external baseline.

### `0022-02.01` — define versioned lifecycle node and edge contracts

- **Role:** `implementer`.
- **Architecture decisions:** separate artifact nodes from verification measure
  and result nodes; require responsibility origin, product/project/process
  identity, baseline/revision/variant, status/rationale, and typed source/target
  roles; preserve distinct `SWE.4`/`SWE.5`/`SWE.6`/`SYS.4`/`SYS.5`/`VAL.1`
  bases.
- **Prerequisite:** `0022-01`; derives from its exact interface fields and
  consumer boundary.
- **Planned order:** second, before validator code.
- **Write scope:** proposed
  `provenance/_schema/ecu-lifecycle-node-v1.schema.json`,
  `provenance/_schema/ecu-lifecycle-edge-v1.schema.json`,
  `docs/dossiers/0022-lifecycle-trace-contract.md`, fixtures owned by this
  Subtask, claim, and bookkeeping.
- **Acceptance criteria:** canonical serialization and identity rules; closed
  node/edge vocabularies; correct responsibility/baseline/variant semantics;
  immutable source identity; explicit extension/version compatibility; no
  collision with documentation provenance schemas.
- **Definition of Done:** schemas, contract, positive/negative fixtures, and
  schema-validation evidence committed with REF.
- **Test scope:** `unit` with schema fixtures plus exhaustive finite enumeration
  of node-kind/edge-kind compatibility. AE-1/AE-5 applies to identity,
  serialization, and set/sequence invariants.
- **Capability profile:** `unprivileged`; stdlib JSON/schema tooling and Git;
  direct; cognitive `high`; implementer distinct from Architect/Integrator.
- **Demand/risk estimate:** 20k–34k tokens; 50–100 minutes; 1 CPU core and
  <3 CPU-minutes; context `high`; ambiguity `medium`; verification hardness
  `high`; uncertainty ±40%; risk `high` because a schema false positive can
  erase lifecycle distinctions.
- **Integration review:** not mandatory.
- **No-checkpoint justification:** the mandatory `0022-01` contract checkpoint
  precedes it and the terminal `0022-03` checkpoint reviews schema plus validator
  composition; this Subtask has no external effect or irreversible migration.

### `0022-02.02` — implement the lifecycle-trace validator

- **Role:** `implementer`.
- **Architecture decisions:** validate only explicit candidate roots; never
  register a default repository-wide gate; report stable findings for wrong
  basis, orphan, stale baseline, cross-variant, responsibility mismatch,
  illegal status, and non-ECU evidence substitution; do not rewrite evidence.
- **Prerequisite:** `0022-02.01`; derives from the schema contract.
- **Planned order:** third.
- **Write scope:** proposed `_src/tools/check_ecu_lifecycle_trace.py`, focused
  tests under `_src/tests/`, Subtask fixtures, claim, and bookkeeping; no
  `_src/validate.py`, policy allowlist, or unrelated producer.
- **Acceptance criteria:** deterministic JSON/human output and exit codes;
  bounded input; exact candidate-root selection; fail-closed malformed input;
  all named findings with positive/negative tests; no ECU-process credit from
  tool execution.
- **Definition of Done:** committed tool/tests, registration in a non-governance
  local tool note or separately governed documentation path, automation-safety
  pass, py_compile, focused suite, red-baseline/green-candidate evidence, and
  complete material-finding disposition.
- **Test scope:** `unit` plus `integration`; falsification case red on `.01`
  baseline and green on candidate, two adjacent cases per changed behavior, and
  exhaustive/property evidence for graph membership, basis compatibility,
  reachability, multiplicity, and ordering invariants.
- **Capability profile:** `unprivileged`; direct Python/Git; cognitive `high`;
  implementer distinct from Architect/Integrator.
- **Demand/risk estimate:** 30k–48k tokens; 80–150 minutes; 1–2 CPU cores and
  5–15 CPU-minutes; context `high`; ambiguity `medium`; verification hardness
  `high`; uncertainty ±45%; risk `high` in both false-pass and false-block
  directions.
- **Integration review:** not mandatory.
- **No-checkpoint justification:** it is candidate-root-only and not a default
  shared gate; terminal `0022-03` reviews the composed behavior before Feature
  integration. Any proposal to register it broadly is a new TK-2 decision.

### `0022-02` — parent consistency and aggregation

- **Role:** `qa` or package implementer distinct from both child principal
  implementers where practical.
- **Prerequisites:** `0022-02.01`, `0022-02.02`.
- **Planned order:** fourth.
- **Write scope:** package evidence under `docs/campaign-evidence/0022-02/`,
  claim, and bookkeeping; child product edits only through a returned finding.
- **Acceptance criteria:** schema/tool/docs vocabulary is identical; every
  interface field maps to a node/edge or is explicitly non-graph; legacy
  provenance bytes and semantics are unchanged; complete findings disposition.
- **Definition of Done:** aggregation manifest, digest list, focused test
  results, and consumer mapping committed with REF.
- **Test scope:** `integration`; recompute fixture/schema/validator matrix and
  compare declared coverage bidirectionally.
- **Capability profile:** `unprivileged`; direct; cognitive `high`.
- **Demand/risk estimate:** 12k–22k tokens; 35–70 minutes; 1 CPU core and
  <8 CPU-minutes; uncertainty ±30%; risk `medium-high`.
- **Integration review:** not mandatory; terminal review consumes it directly.

### `0022-03` — terminal Feature integration and consumer-readiness package

- **Role:** `implementer`; package preparation is performed by a separately
  assigned privileged Implementer, and the terminal Integrator who reviews and
  crosses the checkpoint must remain distinct from Architect Data and every
  decisive implementer.
- **Prerequisites:** `0022-01`, `0022-02`.
- **Planned order:** fifth and terminal.
- **Write scope:** `docs/campaign-evidence/0022-03/`, Feature bookkeeping and
  integration-only claim paths; no consumer implementation.
- **Acceptance criteria:** exact digest-bound aggregate manifest; all source and
  decision pins current; both Task packages terminal; complete five-process
  matrix and trace coverage; independent negative-path rerun; `0023-11` and
  conditional `0028`–`0032` handoffs are explicit; no SYS execution/rating,
  unnamed-authority pass, broad gate, or Feature closure gap.
- **Definition of Done:** passing mandatory integration review on the exact
  candidate, prerequisite-closed Acceptance batch, hygiene/root preflights,
  recovery plan, and only then authorized Feature integration/closure.
- **Test scope:** `end_to_end` over a hermetic external-SYS.2/SYS.3 input into
  the trace contract plus negative wrong-origin, stale/cross-variant, wrong-basis,
  and unnamed-authority cases.
- **Capability profile:** `privileged`; direct Git/Python and exact-branch
  access; cognitive `critical`; strict independence and no network/credentials.
- **Demand/risk estimate:** 35k–60k tokens; 120–240 minutes; 1–2 CPU cores and
  10–30 CPU-minutes; context `very-high`; ambiguity `medium`; verification
  hardness `critical`; uncertainty ±50%; risk `critical` because this is the
  Feature review floor and consumer-readiness boundary.
- **Integration review:** `mandatory`.
- **Checkpoint rationale:** exactly-one terminal integrating Task; composition
  crosses evidence, configuration, responsibility, and multiple consumer gates.

## 6. Planned order, branch graph, and dispatch boundary

The planned order is exactly:

`0022-01 → 0022-02.01 → 0022-02.02 → 0022-02 → 0022-03`.

Task branches start from Feature branch `0022`; Subtask branches start from
Task branch `0022-02`; each merges its done-but-unintegrated prerequisite first
and records the tip. An A2 record is required if actual order can change a
consumer contract or block another work unit. Ordinary scheduling delay alone
is not A2.

The Project Lead should route implementation first to the same-team
Requirements Engineer (`beverly`) if available and suitable, then use ordinary
priority-offer policy. This proposal is not an assignment. Every briefing must
state capability class, exact item/branch/worktree, exact paths, and explicit
prohibitions on Acceptance/checkpoint/DONE actions.

## 7. Governance activation and rollback

- **Activation condition:** a newly allocated conforming `DEC-0022-*` record is
  reachable from `main`, and a supporting scope review by a management-
  instantiated Architect distinct from the future Implementer approves the
  exact affected-unit/gate set and proposed Task graph. Only then may operative
  Task text, prerequisites, checkpoint attributes, schemas, or validators be
  changed.
- **Affected gates:** the gates in §4; no additional gate is implied by a path
  being shared or by a checker existing.
- **Self-application:** this proposal records sources, derivations, profiles,
  A1 evidence, exact terminal integration, and the no-implementation boundary.
  It does not retroactively certify an earlier Feature branch; none existed at
  branch creation.
- **No implicit grandfathering:** after activation, any consumer using SYS
  interface or trace evidence must meet the current contract. Existing prose,
  pipeline traces, tests, or unbound external artifacts receive no automatic
  credit. Current SYS exclusions remain effective until append-only Management
  change.
- **Rollback before activation:** leave `0022-01` `[p]`, preserve this proposal
  and claim, and make no operative contract change.
- **Rollback after activation:** stop new use, record append-only invalidation or
  superseding decision, reopen affected Tasks, retain prior records and fixtures,
  remove only the activated consumer/checker wiring in its owned branch, and
  revalidate every named consumer. No silent deletion or rewritten history.

## 8. Findings requiring independent review

1. **F-0022-ARCH-01:** Feature `0022` currently lacks the mandatory exactly-one
   terminal integrating Task. Proposed correction: add `0022-03` only after the
   governance/scope gate.
2. **F-0022-ARCH-02:** `0022-02` combines persistent schemas, validator logic,
   adversarial testing, and package aggregation. Proposed bounded split:
   `.01`/`.02` plus parent completion.
3. **F-0022-ARCH-03:** `0024-02` may be a direct external SYS.5/VAL consumer or
   only downstream of another acceptance interface. The independent reviewer
   must classify it before the decision record's affected-gate list is fixed.
4. **F-0022-ARCH-04:** performer and acceptance authority are not named. This is
   conforming in a definition but must fail closed at activation/use; no agent
   may convert it into an assumed OEM, customer, supplier, or assessed-unit role.

## Appendix A — required structured Task records

The prose contracts above remain normative. This appendix supplies the exact
stable field names and controlled values required by
`docs/pipeline/feature-breakdown.md`.

```yaml
- task_id: "0022-01"
  feature_id: "0022"
  role: implementer
  architecture_decisions:
    - decision: "Baseline five external/not-rated SYS interface rows; not-decided authority never satisfies activation or use."
      derives_from:
        requirements: ["RQ-0022-01", "RQ-0022-03"]
        decision_records: ["DEC-0020-001", "DEC-0020-002", "PD-0022-01-GATE-01 pending governance allocation"]
        existing_architecture: ["docs/ASPICE/04-gap-roadmap.md#feature-0022--ecu-system-process-interface-and-trace-foundation"]
        repository_evidence: ["docs/dossiers/req-0020-09-execution-register.md@74e19d1e5f2936dd26087cab7b524ebbdb0238b1"]
      authority_or_assumption: authority
  prerequisites:
    - task_id: "0020-09"
      derives_from: "selected-profile disposition and consumer edges"
  planned_order:
    position: 1
    order: ["0022-01", "0022-02.01", "0022-02.02", "0022-02", "0022-03"]
    order_matters_because: "Every schema, validator, and consumer handoff needs the same reviewed interface fields and gate semantics."
  test_scope:
    derives_from: ["five-row completeness", "unnamed-authority fail-closed rule", "no false SYS credit"]
    kind: manual_inspection
    evidence: "five-row audit plus optional deterministic table-shape check and retained finding dispositions"
  capability_profile:
    capability_class: unprivileged
    rights: ["read repository", "write declared Task paths"]
    data: ["git history", "merged 0020-09 predecessor records"]
    tools: ["Git", "stdlib Python"]
    execution_needs: direct
    cognitive_demand: high
    independence: "Implementer distinct from Architect data and terminal Integrator"
  branch:
    parent: "0022"
    name: "0022-01"
    create: "pre-provision from parent; merge 0020-09 first; do not create from a stale checkout"

- task_id: "0022-02.01"
  feature_id: "0022"
  role: implementer
  architecture_decisions:
    - decision: "Define versioned ECU lifecycle node/edge contracts with separate measure and result nodes and distinct verification bases."
      derives_from:
        requirements: ["RQ-0022-02", "RQ-0022-03"]
        decision_records: ["DEC-0020-001", "DEC-0020-002", "PD-0022-01-GATE-01 pending governance allocation"]
        existing_architecture: ["provenance/_schema/provenance-graph-v1.schema.json", "provenance/_schema/typed-reference-v1.schema.json"]
        repository_evidence: ["docs/ASPICE/02-level-1-requirements.md#51-system-engineering-and-validation"]
      authority_or_assumption: authority
  prerequisites:
    - task_id: "0022-01"
      derives_from: "reviewed process interface field and responsibility contract"
  planned_order:
    position: 2
    order: ["0022-01", "0022-02.01", "0022-02.02", "0022-02", "0022-03"]
    order_matters_because: "Validator behavior must derive from a frozen schema rather than inventing graph semantics in code."
  test_scope:
    derives_from: ["canonical identity", "serialization", "node/edge compatibility", "basis separation"]
    kind: unit
    evidence: "positive/negative schema fixtures and exhaustive finite node-kind/edge-kind compatibility cases"
  capability_profile:
    capability_class: unprivileged
    rights: ["read repository", "write declared Subtask paths"]
    data: ["git history", "0022-01 interface plan"]
    tools: ["Git", "stdlib Python", "JSON Schema fixtures"]
    execution_needs: direct
    cognitive_demand: high
    independence: "Implementer distinct from Architect data and terminal Integrator"
  branch:
    parent: "0022-02"
    name: "0022-02.01"
    create: "pre-provision from parent; merge 0022-01 first; do not create from a stale checkout"

- task_id: "0022-02.02"
  feature_id: "0022"
  role: implementer
  architecture_decisions:
    - decision: "Implement a candidate-root-only read-only validator with stable findings; do not register a default shared gate."
      derives_from:
        requirements: ["RQ-0022-02", "RQ-0022-03"]
        decision_records: ["DEC-0020-002", "PD-0022-01-GATE-01 pending governance allocation"]
        existing_architecture: ["0022-02.01 schema contract"]
        repository_evidence: ["docs/dossiers/0020-02-gate-scope-review.md@1717e89262c557fda6fd5a86094d59f33a8a7351"]
      authority_or_assumption: authority
  prerequisites:
    - task_id: "0022-02.01"
      derives_from: "versioned node, edge, identity, and compatibility contract"
  planned_order:
    position: 3
    order: ["0022-01", "0022-02.01", "0022-02.02", "0022-02", "0022-03"]
    order_matters_because: "Writing validator logic before schema completion would duplicate or drift the interface model."
  test_scope:
    derives_from: ["wrong basis", "orphan", "stale baseline", "cross variant", "responsibility mismatch", "origin substitution"]
    kind: integration
    evidence: "red-baseline/green-candidate falsification, adjacent cases, and exhaustive/property graph invariants"
  capability_profile:
    capability_class: unprivileged
    rights: ["read repository", "write declared Subtask paths"]
    data: ["git history", "0022-02.01 fixtures"]
    tools: ["Git", "stdlib Python"]
    execution_needs: direct
    cognitive_demand: high
    independence: "Implementer distinct from Architect data and terminal Integrator"
  branch:
    parent: "0022-02"
    name: "0022-02.02"
    create: "pre-provision from parent; merge 0022-02.01 first; do not create from a stale checkout"

- task_id: "0022-02"
  feature_id: "0022"
  role: qa
  architecture_decisions:
    - decision: "Aggregate the schema and validator without changing either child contract; return defects to their owner."
      derives_from:
        requirements: ["RQ-0022-02", "RQ-0022-03"]
        decision_records: ["PD-0022-01-GATE-01 pending governance allocation"]
        existing_architecture: ["0022-02.01 schema contract", "0022-02.02 validator contract"]
        repository_evidence: ["child candidate REFs and validation manifests"]
      authority_or_assumption: evidence
  prerequisites:
    - task_id: "0022-02.01"
      derives_from: "schema work product"
    - task_id: "0022-02.02"
      derives_from: "validator work product"
  planned_order:
    position: 4
    order: ["0022-01", "0022-02.01", "0022-02.02", "0022-02", "0022-03"]
    order_matters_because: "Package consistency can be evaluated only after both child products are terminal."
  test_scope:
    derives_from: ["schema/tool/docs vocabulary", "bidirectional interface coverage", "legacy non-regression"]
    kind: integration
    evidence: "digest-bound aggregation manifest and recomputed fixture/schema/validator matrix"
  capability_profile:
    capability_class: unprivileged
    rights: ["read repository", "write package evidence paths"]
    data: ["git history", "child branches and validation evidence"]
    tools: ["Git", "stdlib Python"]
    execution_needs: direct
    cognitive_demand: high
    independence: "Package author does not self-accept and preferably differs from both principal child implementers"
  branch:
    parent: "0022"
    name: "0022-02"
    create: "pre-provision from parent; merge both terminal child branches; do not create from a stale checkout"

- task_id: "0022-03"
  feature_id: "0022"
  role: implementer
  architecture_decisions:
    - decision: "Prepare the single terminal consumer-readiness and Feature integration package for independent checkpoint review."
      derives_from:
        requirements: ["RQ-0022-01", "RQ-0022-02", "RQ-0022-03", "RQ-0022-04"]
        decision_records: ["DEC-0020-001", "DEC-0020-002", "PD-0022-01-GATE-01 pending governance allocation"]
        existing_architecture: ["0022-01 interface plan", "0022-02 trace package"]
        repository_evidence: ["exact predecessor branches, claims, manifests, and validation outputs"]
      authority_or_assumption: authority
  prerequisites:
    - task_id: "0022-01"
      derives_from: "per-process consumer interface baseline"
    - task_id: "0022-02"
      derives_from: "complete trace schema/validator package"
  planned_order:
    position: 5
    order: ["0022-01", "0022-02.01", "0022-02.02", "0022-02", "0022-03"]
    order_matters_because: "This is the terminal integrating Task and cannot prepare a complete manifest before both packages are terminal."
  test_scope:
    derives_from: ["Feature composition", "consumer handoffs", "wrong-origin and wrong-basis risks", "recovery"]
    kind: end_to_end
    evidence: "hermetic external SYS.2/SYS.3 input flow plus negative authority, origin, basis, baseline, and variant cases"
  capability_profile:
    capability_class: privileged
    rights: ["read repository", "write terminal package paths", "prepare exact integration candidate"]
    data: ["git history", "exact predecessor branches", "validation manifests"]
    tools: ["Git", "stdlib Python"]
    execution_needs: direct
    cognitive_demand: critical
    independence: "Package Implementer distinct from Architect data and separately assigned terminal Integrator"
  branch:
    parent: "0022"
    name: "0022-03"
    create: "pre-provision from parent; merge 0022-01 and 0022-02 first; do not create from a stale checkout"
```
