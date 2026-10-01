# `0044-07` Architect role-catalog decision packet

**Status:** read-only architecture candidate; not a decision, adoption, scope
review, acceptance record, integration verdict, or activation authority.

**Architect:** `data` (`agent:data:0044-07:20260827T115800Z-e2f77b46`)

**Candidate baseline:** branch `0044-07` after reconciliation commit `f272425`,
which incorporated exact `main@0523b9eaff34d26cd98507dedb71838b4f36b028`.

## 1. Executive result and missing authority

The current Task cannot safely satisfy its Definition of Done as one work unit.
Its no-checkpoint rationale says it produces proposals, while the DoD requires a
live update to normative `docs/pipeline/process-roles.md`. The contemplated
global A-prime direction would remove a selectable capability class, retire a
runner transport, replace ambiguous-capability fallback behavior, change
accepted `0044-04`/`0044-05` interfaces, and alter the execution assumptions of
Feature `0037`. Those effects meet `cross-item-blast-radius`,
`material-architecture-or-repository-behavior`, and authority/security
separation triggers.

The exact-source inquiry `agent-inbox:1787832040101-d063731d` received the
fail-closed answer `agent-inbox:1787832069123-cbb6c8d5`: the Team Enterprise
Project Lead found no current-user or registered-authority message delegating
the global choice to the cited Jean-Luc/Seven/Geordi consensus and cannot name
a stable deciding identity. The consensus and the preparation package are
therefore advisory evidence, not Management authority. No `DEC-` identifier is
allocated here and no policy, backlog, gate, accepted interface, or runtime is
changed.

### Decision needed

**Question:** Does the current user or a registered Management authority adopt
global A-prime, reject it in favor of B, or direct a narrower alternative?

**Paused action:** allocation of a conforming global `decision-record@v1`,
independent supporting Architect scope review, backlog repair, implementation,
invalidation/re-review, activation, and cutover.

**Recommendation:** choose **B now**: retain the global three-class and typed
runner model, make capability matching authoritative only as capability
evidence, and restrict Feature `0037` consumer policy to explicitly qualified
direct-execution agents where desired. A-prime may remain a staged candidate
until the repository can prove, in shadow operation, that every runner safety
invariant and active-work migration is rehomed. B has the smallest immediate
blast radius and preserves the technically enforced fallback while the
descriptor population is almost empty.

### Alternatives

| Option | Operative result | Principal benefit | Principal cost/risk |
|---|---|---|---|
| **A-prime** | Future selectable classes become `unprivileged` and `privileged`; Runner is a normally unprivileged direct process role; old runner service/queue/typed transport retires after migration. | Removes runner-slot serialization and aligns roles with direct runtime operation. | Repository-wide migration; weaker enforcement unless every invariant is rehomed; accepted contracts and active work require transition. |
| **B (recommended)** | Retain current three-class/runner architecture globally; reject `sandboxed-grunt` only in a bounded consumer policy when direct qualification is required. | Smallest reach; current fail-closed enforcement and recovery remain intact. | Keeps queue/transport cost and a class that some future runtimes may not supply. |
| **C** | Preserve both architectures indefinitely with dual selectable execution models. | Maximizes compatibility. | Permanent ambiguity, duplicated controls, matcher complexity, and inconsistent fallback; not recommended. |

## 2. Pinned evidence and observed inventory

The following SHA-256 values bind the principal repository evidence at the
candidate baseline:

| Source | SHA-256 |
|---|---|
| `SANDBOX.md` | `4871c705af9f77bfedf6389c128df19d84d1a6eba948a498938f4c1bc5cb7604` |
| `AGENTS.md` | `4cca9f28316563f0c4b476ee6cdb68ae75b225f8a80f8364d1d0c694c2902935` |
| `docs/pipeline/agent-roster.md` | `63a063bfbc2640eae045fa00e7e022d20276eb870871e98e4d7f9d49ccece3c9` |
| `docs/pipeline/process-roles.md` | `a142e8885751c1c8a97faabfae7b6c579f1599333d3fd3e11ed869831191fc43` |
| `docs/pipeline/capability-matching.md` | `94cb5f097fe21c55113d9b6f02db4ba7165d128ca8df6dfdbb8a57e8d51415d1` |
| `docs/pipeline/feature-breakdown.md` | `b673f2740127b8d3055b32d3ea5c2b33032b5fb878ef8cd225ea794c45952ded` |
| `docs/pipeline/decision-record.md` | `dea2c93ad046d67a129d6b30b7715609a49afde26f47e5039cc2c2159cdb66c0` |
| A-prime preparation package | `8692a1fa0f1e5895739437e1c416259946cc7a722e08d64eeab5540cb07dbd44` |
| task-profile v1 schema | `97e7fb38d539f03523725968b339b54739fe3d8e1ecdbfb469ea8b191661c8c1` |
| descriptor v1 schema | `0902aa16148d5a1624992fc74e6dc65e8652f7a50b23ad4d5085c0a9808a2feb` |
| result v1 schema | `5dfada1ae6d8e67ad3ce26076b98fca8553ffc7e197e182834a663b82eaea551` |

Observed facts:

- The roster contains 40 identities in four teams: 4 Project Leads, 4
  Requirements Engineers, 8 Dispatchers, 4 Architects, 4 Integrators, 4
  Security Engineers, 4 QA-Managers, 4 Testers, and 4 Runners.
- Roster classes are 12 `privileged`, 24 `unprivileged`, and 4 literal
  `runner`. `runner` is not a valid capability class in either current v1
  schema; the four Runner rows therefore cannot be transcribed into valid v1
  descriptors without an architectural decision.
- Eleven SOPs exist: Architect, Dispatcher, Integrator, Process Optimizer,
  Programmer, Project Lead, QA-Manager, Requirements Engineer, Runner,
  Security Engineer, and Tester.
- The normative process-role document models only Architect, Implementer, and
  Integrator as roles, with Requirements Engineer and QA Manager as functions.
  It does not canonically map Project Lead, Dispatcher, Security Engineer,
  Tester, Runner, or Process Optimizer. `Programmer` versus `Implementer` and
  `QA-Manager` versus `QA Manager` create exact-string drift.
- No roster identity has primary role `Implementer`/`Programmer` or Process
  Optimizer.
- The accepted matcher inputs use free-string `process_role` and
  `process_roles`; they do not bind a versioned role catalog or aliases.
- The repository contains exactly one genuine
  `task-requirement-profile@v1`, one genuine
  `agent-capability-descriptor@v1`, and two genuine v1 results under
  `docs/campaign-evidence/0044-05/self-application/`. The positive self-check
  makes Belanna eligible; the negative result rejects the legacy schema.
- A deterministic TODO inventory reports 469 Task nodes, but almost all lack a
  machine-readable task profile. Five textual capability-profile labels and a
  handful of role annotations are not equivalent to closed-schema instances.

Consequently, the acceptance phrase “each existing role/persona is expressed
as a capability descriptor” cannot honestly mean “fabricate 40 valid v1
snapshots from the roster.” The roster lacks authoritative rights, data
handles, tools, budget ceilings, cognitive classes, assurances, fresh capacity,
and runtime execution routes. Model tier and persona prose are not substitutes.

## 3. Canonical role catalog candidate

Role is a stable responsibility vocabulary. Capability is a current execution
and assurance snapshot. Persona is communication style. Assignment, claim,
authority, ownership, independence, Acceptance, risk acceptance, and release
permission remain separate records. No field below grants any of them.

### 3.1 Stable IDs and disposition

| Stable ID | Current sources and aliases | Kind | Candidate minimum class/route | Work product | Non-negotiable prohibitions |
|---|---|---|---|---|---|
| `project-lead` | roster/SOP `Project Lead` | coordination | `privileged`, direct or none | portfolio state, bounded assignments, human decision route | no Management inference; no architecture invention; no hygiene verdict or `main` merge |
| `requirements-engineer` | roster/SOP; process function | assurance/design input | `unprivileged`, direct or none | sourced atomic requirements and open questions | no architecture, production implementation, acceptance, or checkpoint sign-off |
| `dispatcher` | roster/SOP | coordination | `unprivileged`, direct or none | disjoint capability-complete briefing and tracking | no implementation, code review, product decision, or privileged boundary crossing |
| `architect` | roster/SOP/process role | architecture | `privileged`, direct or none | interfaces, prerequisite graph, Task contracts, decision inputs, checkpoint rationale | no Feature-branch advance; no own decisive implementation where separation applies; no self-acceptance |
| `implementer` | process role; SOP alias `Programmer` | delivery | task-dependent; normally `unprivileged`, direct; legacy runner route remains valid under B | smallest complete Task product and focused tests | no scope widening, self-acceptance, checkpoint crossing, or `main` integration |
| `integrator` | roster/SOP/process role | independent integration | `privileged`, direct | pinned review, hygiene verdict, authorized merge, post-merge proof | standby until assignment; no repair while reviewing; no unauthorized/self integration |
| `security-engineer` | roster/SOP | independent assurance | `unprivileged`, direct or none | threat model, negative tests, risk findings | no patching the assessed object; no residual-risk acceptance; no gate bypass |
| `qa-manager` | roster/SOP `QA-Manager`; process alias `QA Manager` | independent process assurance | `unprivileged`, direct or none | conformance audit, deviation evidence, quality trends | no product-code modification, own-change audit, or informal waiver |
| `tester` | roster/SOP | independent product assurance | `unprivileged`, direct or none | requirement-derived reproducible test verdict | no production repair, unexecuted sign-off, or single-command completeness claim |
| `runner` | roster/SOP | execution mechanism | **B:** `sandboxed-grunt` via runner; **A-prime:** normally `unprivileged`, direct after cutover | exact bounded execution evidence | no intent interpretation, authority decision, Acceptance, integration, uncontrolled network/credential use |
| `process-optimizer` | SOP only | advisory process analysis | `unprivileged`, direct or none | evidence-based improvement proposal with metric/rollback | no policy activation, product implementation, acceptance, integration, or history rewrite |

The catalog adopts `implementer` as the stable ID and retains `Programmer` only
as a display/SOP alias. It adopts `qa-manager` as the stable ID and treats both
punctuation variants as aliases. Aliases must resolve before matching and must
never be emitted as canonical IDs.

### 3.2 Complete current persona-to-template census

Each listed persona maps to one role template, but does **not** thereby acquire
a valid capability descriptor:

| Role ID | Current identities | Count | Snapshot status |
|---|---|---:|---|
| `project-lead` | `kathryn`, `jean-luc`, `benjamin`, `michael` | 4 | dynamic fields unverified |
| `requirements-engineer` | `doctor`, `beverly`, `julian`, `hugh` | 4 | dynamic fields unverified |
| `dispatcher` | `chakotay`, `tom`, `william`, `lore`, `kira`, `worf`, `gabriel`, `philippa` | 8 | dynamic fields unverified |
| `architect` | `seven`, `data`, `jadzia`, `saru` | 4 | dynamic fields unverified |
| `integrator` | `belanna`, `geordi`, `obrien`, `paul` | 4 | only Belanna has a genuine v1 pilot snapshot; freshness must be re-evaluated |
| `security-engineer` | `tuvok`, `tasha`, `odo`, `ellen` | 4 | dynamic fields unverified |
| `qa-manager` | `harry`, `troy`, `jake`, `sylvia` | 4 | dynamic fields unverified |
| `tester` | `neelix`, `wesley`, `nog`, `gen` | 4 | dynamic fields unverified |
| `runner` | `kes`, `guinan`, `quark`, `ash` | 4 | roster class incompatible with v1; do not infer replacement class |
| `implementer` | none | 0 | capacity gap |
| `process-optimizer` | none | 0 | capacity gap |

Mailbox broadcasts about future identities or Supervisor restarts are
coordination evidence only. The exact repository roster is the census baseline;
runtime changes require a new authoritative snapshot and cannot be credited
retroactively.

## 4. Proposal dispositions

1. **Adopt, after authority:** a versioned machine role catalog with the eleven
   stable IDs above and exact alias normalization.
2. **Adopt, after authority:** role-qualified agent descriptors and Task
   profiles as additive v2 contracts; preserve all v1 bytes and evidence.
3. **Adopt under either A-prime or B:** Runner is a process role, never a
   capability class. Its class/route is selected by the authorized architecture
   version, not inferred from the word Runner.
4. **Reject:** a new “text-only sandboxed role.” `execution_needs: none` is a
   Task-profile dimension, not a role. Under B, any compatible class may satisfy
   a non-executing Task. Under A-prime, a runtime without independently known
   direct capability remains outside normal selectable profiles.
5. **Retain:** Process Optimizer as an advisory role even though the roster has
   no current holder. Its absence is a capacity finding, not a reason to delete
   the SOP.
6. **Reject:** deriving descriptor budgets/cognition from model marketing tier,
   deriving rights/tools from a role title, or deriving authority from either.
7. **Reject:** treating a missing, expired, ambiguous, or conflicting descriptor
   as normally eligible. Temporary handling must be an explicit bootstrap
   record outside ordinary matching.

## 5. Additive interface contracts

These are predecessor interfaces for a future distinct Implementer. Names are
candidates; an authorized decision may revise them before implementation.

### 5.1 `process-role-catalog@v1`

Closed, canonical JSON object:

- `schema`, `catalog_id`, `effective_policy_id`, `role_entries`,
  `alias_entries`, `source_bindings`, and `non_authority_notice`.
- Each role entry contains stable `role_id`, display name, kind, purpose, SOP
  reference/digest, allowed/minimum class and execution-route combinations,
  work products, required assurances, authority boundary, prohibited acts, and
  separation constraints.
- Every alias maps to exactly one role ID; cycles, duplicate normalized aliases,
  unknown role IDs, and an alias identical to a different canonical ID reject.
- The catalog records whether the active execution architecture is B or
  A-prime. It does not silently reinterpret historic evidence.

### 5.2 `task-requirement-profile@v2`

Additive successor to v1:

- replace free-string `process_role` with canonical `required_role_id`;
- add `role_catalog_id` and SHA-256 binding;
- retain class, execution, rights, data, tools, budgets, cognition, assurances,
  test scope, resource bounds, and source derivations;
- add explicit `profile_valid_until` or an explicit immutable-event scope;
- reject aliases and unknown role IDs at the schema/tool boundary.

### 5.3 `agent-capability-descriptor@v2`

Additive successor to v1:

- replace free-string `process_roles` with sorted `qualified_role_ids` plus
  qualification source/digest and optional expiry per qualification;
- add `role_catalog_id` and digest;
- bind runtime/class/routes, rights, data handles, tools, budgets, cognitive
  classes, assurances, capacity, and snapshot observation/expiry to exact
  authoritative sources;
- permit `unknown`/`unavailable` values only as non-eligible census evidence;
- contain no persona prose, model marketing names, secrets, credential paths,
  assignment, claim, independence, or authority assertions.

### 5.4 `capability-match-result@v2`

Additive successor to v1:

- bind profile, every descriptor, catalog, matcher version, and active
  execution-policy digest;
- preserve deterministic ordering and complete rejection reasons;
- add stable rejections for catalog mismatch, unknown role, expired profile,
  expired descriptor, expired role qualification, ambiguous source, and active
  policy mismatch;
- retain the non-authority notice: eligibility is evidence only and grants no
  assignment, ownership, independence, Acceptance, waiver, specialist
  approval, risk/release authority, or scope expansion.

### 5.5 `capability-resolution@v1` bootstrap record

This record handles missing/ambiguous capability **outside** normal eligibility:

- exact identity, item, observation time, conflicting/missing fields and
  sources, temporary ceiling, allowed preparation, prohibited operations,
  resolver route, deadline, and append-only outcome;
- default ceiling is `unprivileged` **authority**, not a claim of class or
  direct execution;
- read-only diagnosis and coordination are allowed;
- item-owned write preparation is allowed only when direct capability,
  assignment, item, claim, worktree, and exact scope are independently valid;
- Acceptance, checkpoints, integration, `main`, `DONE.md`, release, credentials,
  external/irreversible effects, governance, and cross-item gate mutation are
  prohibited;
- everything else fails closed; unresolved cases route through the Project Lead
  no later than the next coordination cycle or 120 minutes;
- the record never produces a normal eligible match.

## 6. Global reach and unchanged invariants

### 6.1 Affected work units and gates if A-prime is selected

| Scope | Contract/gate effect |
|---|---|
| Feature `0044`, accepted Tasks `0044-04` and `0044-05` | capability vocabulary, feature-breakdown fields, v1 matcher assumptions, dispatch pilot, acceptance impact/invalidation and independent re-review |
| Task `0044-07` | proposal-only contract must be separated from live adoption; current DoD/checkpoint rationale contradiction repaired |
| terminal Task `0044-08` | remains the Feature's exactly one terminal integrating Task; must verify the selected policy and all induced predecessor acceptance |
| Feature `0037` and active claims using `sandboxed-grunt`/runner queue | explicit legacy/import and active-work transition; no silent class upgrade or credit |
| `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, bootstrap, role/catalog and branch workflow | capability discovery, dispatch, execution, fallback, authority boundary, integration behavior |
| v1 schemas, matcher, producers/consumers and evidence | additive supersession, catalog binding, legacy preservation, no-grandfathering |
| runner service, queue, request/result schemas, dispatch and recovery | every safety invariant must be rehomed and verified before transport retirement |
| roster and runtime snapshots | `runner` class rows corrected only after selected policy and current authoritative runtime evidence |

### 6.2 Invariants that do not change

- Role, class, model, persona, matcher output, mailbox coordination, or record
  presence never creates assignment, ownership, claim, independence, authority,
  Acceptance, waiver, risk acceptance, release permission, or write scope.
- Root checkout remains read-only except the separately assigned Integrator's
  final authorized merge; hygiene and root preflight remain mandatory.
- Exact claims, branches/worktrees, prerequisites, four-eyes separation,
  checkpoint authority, and append-only evidence remain binding.
- Unknown, expired, invalid, or contradictory state fails closed.
- Historic v1 schemas, profiles, descriptors, results, claims, decisions, and
  runner records retain their original meaning and bytes; no grandfathering.
- Runner mechanisms grant no interpretive or acceptance authority.

## 7. Bounded prerequisite graph for later implementation

Task IDs are deliberately not allocated here. The current-main allocator and
an authorized backlog Implementer assign collision-free IDs after the decision
and supporting independent Architect review are main-visible.

```text
authorized global decision + independent supporting scope review
    -> P1 policy/interface baseline and accepted-contract impact records
        -> P2 catalog/v2 schemas/matcher/legacy adapter
        -> P3 capability-resolution bootstrap fallback
        -> P4 direct Runner invocation + rehomed execution invariants
    -> P5 descriptor/profile census, active-work migration, shadow/dual proof
        -> P6 atomic cutover or B activation (mandatory intermediate checkpoint)
            -> existing 0044-08 terminal integration (mandatory; unchanged)
```

### P1 — policy/interface baseline and impact

- **Exact scope:** decision product, independent scope-review evidence,
  candidate role catalog, accepted `0044-04`/`0044-05` impact/invalidation
  records, repaired `0044-07` proposal-only contract, and prerequisite graph.
- **Acceptance:** authority source and stable deciding identity; all affected
  units/gates named; option and fallback exact; no hidden grandfathering;
  separation and recovery explicit.
- **DoD:** main-visible governance baseline before any P2–P6 qualifying
  mutation.
- **Capability:** privileged governance Implementer distinct from Data; 15k–30k
  tokens, low CPU, high cognition/uncertainty/risk.
- **Recovery:** append-only rejection/supersession; do not delete prior records.

### P2 — catalog, v2 schemas, matcher, legacy adapter

- **Exact scope:** new schemas/catalog, deterministic matcher/tool/docs/tests;
  no dispatch activation or runner retirement.
- **Acceptance:** closed schemas; stable aliases; catalog/profile/descriptor/
  policy digest binding; all rejection reasons; v1 byte identity; v1 inputs
  either remain on v1 or pass an explicit adapter with provenance.
- **DoD:** hermetic tests and fixtures committed; v2 stays non-authoritative
  capability evidence until P6.
- **Capability:** unprivileged direct Implementer; 25k–45k tokens, CPU under 10
  minutes, high cognition, medium risk.
- **Recovery:** remove v2 consumers while retaining schemas/results as evidence;
  v1 path remains functional.

### P3 — explicit unresolved-capability path

- **Exact scope:** bootstrap record/schema, resolver procedure, bounded timeout,
  negative authority tests; no normal-match eligibility.
- **Acceptance:** every prohibited operation rejects; direct execution cannot be
  inferred; deadline/escalation visible; append-only resolution.
- **DoD:** deterministic fixtures cover missing, expired, conflicting, and stale
  capability sources.
- **Capability:** unprivileged direct Implementer plus independent security
  design/test; 15k–30k tokens, CPU under 10 minutes, high cognition/risk.
- **Recovery:** disable bootstrap writes and revert to read-only coordination;
  retain resolution evidence.

### P4 — Runner invocation and safety-invariant rehoming

- **Exact scope:** direct Runner invocation interface and implementation; scope
  validation, request identity/idempotence, collision rejection, CAS, lease/
  timeout, bounded output, journal/provenance, recovery, credential/network
  boundary, and acceptance/integration prohibition.
- **Acceptance:** one-to-one invariant ledger from current runner/queue contracts
  to replacement controls; no invariant merely deleted with transport code;
  adversarial and crash/recovery fixtures.
- **DoD:** candidate mechanism complete but old transport remains available;
  no production cutover.
- **Capability:** unprivileged direct Implementer, independent Security Engineer
  and Tester; 30k–60k tokens, CPU 10–30 minutes, critical cognition/risk.
- **Recovery:** old transport remains source of service; discard candidate
  runtime without losing request/result history.

### P5 — population census, active-work migration, shadow proof

- **Exact scope:** all 40 baseline identities plus later authorized roster delta;
  all open/active Task profiles and claims affected by class/route semantics;
  shadow/dual execution evidence.
- **Acceptance:** every identity has a fresh valid descriptor or explicit
  unknown/unavailable non-eligible record; every relevant Task has a v2 profile
  or explicit legacy disposition; no capability is invented; result differences
  classified; active claims preserve owner/scope and require explicit transition.
- **DoD:** bounded observation window and success thresholds met; rollback drill
  succeeds; historic evidence unchanged.
- **Capability:** unprivileged producers coordinated by Dispatcher, independent
  QA/Test; 30k–60k aggregate tokens, CPU 10–30 minutes, high context/risk.
- **Recovery:** stop shadow path, retain evidence, continue old architecture.

### P6 — selected-policy activation and atomic cutover

- **Exact scope:** one reviewed transaction activating B or, if authorized and
  proven, A-prime; under A-prime only, retire old selectable class/service/
  queue/transport after P2–P5 pass.
- **Acceptance:** exact candidate/target; current decision and scope review;
  all impacted acceptance current; zero unresolved invariant gaps; active-work
  transition complete; rollback rehearsal; pre/post hygiene and validation.
- **DoD:** activated policy version and evidence manifest committed; obsolete
  mechanism disabled but recoverable; no historic rewrite.
- **Checkpoint:** **Integration review mandatory** as an intermediate checkpoint.
  It changes repository-wide execution and fallback, accepted interfaces, and
  active work, and may remove the only technical enforcement path. This does
  not replace `0044-08`, which remains exactly one terminal integrating Task.
- **Capability:** privileged Integrator distinct from Data and all decisive
  Implementers; 20k–40k review tokens, CPU 15–45 minutes, critical cognition,
  uncertainty, and risk.
- **Recovery:** atomically restore previous policy version, schemas/matcher
  routing, roster interpretation, fallback, runner service/queue/transport, and
  active-work transition state; invalidate affected new acceptance additively.

## 8. Verification design

The later candidate is not activatable unless all of these are reproducible:

1. **Catalog exhaustiveness:** all 11 SOP roles dispositioned; all 40 baseline
   identities unique and mapped; aliases resolve exactly; unknown role rejects.
2. **Baseline-red/candidate-green:** current Runner `runner` class mismatch,
   `Programmer`/`Implementer`, and QA punctuation drift reproduce as failures
   before the candidate and pass only through explicit catalog/policy mapping.
3. **No fabrication:** missing rights, tools, routes, assurances, budgets,
   cognition, source, or freshness yields unknown/unavailable and non-eligible.
4. **Matrix/property coverage:** every role ID × class × route × authority
   constraint combination; privilege does not substitute for runner route or
   role qualification.
5. **Freshness:** missing/expired/ambiguous profile, descriptor, qualification,
   catalog, or policy binding rejects deterministically.
6. **Non-authority:** no result or bootstrap record can grant claim, assignment,
   ownership, independence, Acceptance, checkpoint, integration, feature close,
   risk/release permission, or wider paths.
7. **Fallback negative suite:** every closed prohibition is tested; the 120-minute
   route is bounded and observable; timeout never upgrades capability.
8. **Legacy identity:** v1 schemas and accepted evidence remain byte-identical;
   imports record origin and do not retroactively credit historic dispatches.
9. **Runner invariant ledger:** scope, collision, CAS, idempotence, lease,
   journal, bounded output, recovery, network/credential boundary, and
   acceptance prohibition each have positive, negative, crash, and rollback
   evidence before old transport retirement.
10. **Active-work transition:** every affected `[p]` claim retains immutable
    owner token, scope, baseline, and an explicit policy disposition; no silent
    appropriation or class upgrade.
11. **Repository gates:** targeted unit tests, schema fixtures, matcher self-check,
    process-document validation, integration hygiene with exact candidate, root
    preflight immediately before/after authorized merge, and terminal `0044-08`
    prerequisite-closed review.

## 9. Activation, observation, and recovery

Activation is explicit, versioned, non-retroactive, and performed only after P1
through P5 are main-visible and accepted as required. A-prime must use a bounded
shadow/dual observation window with stated workload and thresholds: zero lost or
unattributed executions, zero scope/CAS/authority escapes, complete request and
result provenance, bounded timeout/cleanup, and successful rollback rehearsal.
Any unresolved safety-invariant mapping, descriptor ambiguity, active-claim
transition gap, acceptance invalidation, or hygiene finding blocks cutover.

Recovery is a single reviewed transaction, not selective edits. It restores the
previous capability vocabulary, role/catalog/policy binding, fallback, schemas
and matcher routing, Runner service/queue/transport, roster interpretation, and
active-work transition state. Append-only decisions, findings, historic v1
artifacts, journals, and acceptance/invalidation records are retained.

## 10. Self-application and separation

- This Task applied its own critical cognitive-demand profile and A1 check. A1
  is `does-not-fit`; reports are `agent-inbox:1787831951985-70580d34` and
  `agent-inbox:1787831952141-3fcfb074`.
- Data is the decisive Architect and a recorded dissenter recommending B. Data
  must not become the decisive Implementer, Integrator, or Acceptance reviewer
  for P1–P6 absent a separately authorized bounded waiver; the substantive
  cross-item/material triggers normally prohibit Architect/Implementer
  combination.
- A future supporting scope review must be performed by a Management-instantiated
  Architect distinct from the Implementer. This packet is the architecture
  source to inspect; it is not that later review and does not accept itself.
- `0044-08` remains the Feature's exactly one terminal integrating Task.
- Governance activates only from `main`, after the required decision/review and
  authorized Integrator transaction. There is no implicit grandfathering.

## 11. Current validation and limits

Read-only inspection at the pinned candidate verified source digests, 40 roster
identities, role/class counts, 11 SOP files, the v1 schema contracts, the single
profile/descriptor population, and the accepted matcher self-application. The
repository's TODO doctor reports 469 Task nodes. These are architecture inputs,
not proof that a future candidate passes its implementation or integration
tests.

This packet intentionally performs no network call, external effect, runtime
restart, schema/tool/policy edit, backlog repair, decision allocation,
acceptance, merge to `main`, or Feature closure.
