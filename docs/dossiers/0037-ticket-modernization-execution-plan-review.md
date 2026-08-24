# Independent Architect review — 0037 ticket-modernization execution plan

## Review identity and immutable baseline

- **Reviewer:** Architect `jadzia` (Team DeepSpace9), `privileged`, distinct
  from plan author Benjamin and amendment author/reviewer Data
- **Assignment:** Project Lead `jean-luc`, item
  `review-0037-ticket-modernization-plan-jadzia-20260824`
- **Candidate:** substantive plan
  `fc80d5f082dc90f3c722bbb99939284a0f097249`, carried by final tip
  `457bb38760cdf2932565e8b2bd6a1d4b9b5495d8`
- **Candidate artifact:**
  `docs/dossiers/0037-ticket-modernization-execution-plan.md`
- **Author check:** Benjamin, `faithful`
- **Controlling Runner amendment:**
  `5d5996d07d8e8be71a99722a12e3afcb1d57919a`, actual branch tip
  `b38c3202d0d40812733204d4386388ff73234599`
- **Current backlog inspected:** `TODO.md` as carried by candidate tip
- **Review branch:**
  `review-0037-ticket-modernization-plan-jadzia-20260824`

This is an independent read-only architecture review of the candidate. It is
not Task Acceptance, an integration review, an operative backlog rewrite, a
checkpoint crossing, authority to start a job, or Feature closure.

## Verdict

**Verdict: `rejected`.** The candidate correctly retires the sandboxed-grunt,
queue, singleton, typed-action and host-transport architecture while retaining
Runner as a normally unprivileged operational role. That terminology correction
is necessary but insufficient. The proposed graph still names retired
`0037-47` as a live blocker, omits the amendment's shared accepted `0037-21`
role/job-control interface and consumer edges, and does not carry the Runner
contract through quiescence, authority preparation/switch or terminal proof.
Its three preparation packages are outlines rather than bounded executable
contracts. The plan therefore cannot safely drive backlog allocation or cutover.

## Passing architecture observations

1. The candidate states that `TODO.md` remains authoritative and `issues/` is a
   disposable shadow database until an authorized cutover.
2. It retains collision control, governance protection, claim CAS, recovery,
   immutable evidence, stale-client fencing, audit trails and independent
   checkpoint review independently of transport.
3. It explicitly retires `sandboxed-grunt`, runner queue, singleton,
   typed-action and host-transport semantics.
4. It retains Runner, separates it from the retired transport, makes Dispatcher
   selection explicit and maps it normally to unprivileged execution.

These passes do not establish a complete dependency graph, executable package
contracts, valid checkpoint placement or cutover readiness.

## Findings

### F-TICKET-PLAN-001 — Critical — the critical path retains a retired transport Task

The candidate says `0037-08` is blocked by `0037-39 → 0037-47 → 0037-46` and
labels the replacement merely “Align to unprivileged execution”. The controlling
amendment explicitly preserves removal of `0037-46` and `0037-47`; `0037-47`
exists solely to qualify Feature 0037 for sandboxed/grunt execution through the
queue. Current `TODO.md` confirms the stale edge: `0037-39` still has prerequisite
`0037-47`, and `0037-47` still requires sandboxed-grunt action mappings. A future
plan must describe their governed removal and the exact replacement edge, not
present the obsolete chain as the current blocker without a rewiring contract.

**Required correction:** include the complete remove/defer/retain/rewrite graph
delta from the reviewed decision, explicitly remove `0037-47` and its dependency
from retained nodes, retain `0037-39` with direct deterministic foreground and
Runner-compatible background invocation, and prove all remaining endpoints,
reachability, cycles and semantic start gates against the then-current graph.

### F-TICKET-PLAN-002 — Critical — the shared Runner contract, consumers and checkpoint are absent

The plan's single Runner sentence does not implement the controlling amendment.
It omits `0037-21` as owner of the shared operational-role/background-job
contract; the required `0037-51` and `0037-42` predecessors; the mandatory
intermediate checkpoint; and current-Acceptance-before-start edges from
`0037-25.01`, `0037-30`, `0037-34.01`, `0039-02` and `0044-05`. It also omits
the job record's Task/job/owner/base/epoch/command/scope/resource/external fields,
monotonic lifecycle, heartbeat/status/log/result evidence, cancellation,
timeout, restart, retry/idempotence, cleanup, handoff, recovery and authority
negative controls.

Without that shared product, each long-running consumer can invent a parallel
protocol, infer Runner from duration or model name, or accidentally treat role
selection as authority. The terminal Feature checkpoint cannot substitute for
the amendment's specifically required intermediate shared-interface review.

**Required correction:** make rewritten `0037-21` a first-class package and
mandatory intermediate checkpoint; enumerate its full contract; add its exact
predecessors and current-Acceptance consumer edges; keep Runner normally
`unprivileged`; and prove role, capability class, Architect/Implementer/
Integrator authority and specialist authority remain separate dimensions.

### F-TICKET-PLAN-003 — Critical — cutover and quiescence do not consume Runner state

The cutover row compresses `0037-30/31 → 34.01/32/33 → 34.02 → 35/36` into
“Native execution”. It does not require `0037-30` to inventory, reject new,
drain/cancel or preserve every Task-ID-bound background job; does not require
`0037-34.01` to carry the current accepted role/job-control contract and valid
role-to-capability mappings; and does not require `0037-34.02` to reject stale
clients that interpret Runner as transport or authority. `0037-40` lacks the
required synthetic long job, cancellation/recovery proof and role/authority
negative controls. The plan also omits the distinction between a Runner
executing an already authorized long audit/rebuild and the independent Tester,
signer or Integrator evaluating its evidence.

**Required correction:** expand each cutover package with amendment-bound
inputs, outputs, gates, rollback and evidence. Preserve `0037-34.02` as the
authority-switch checkpoint and `0037-40` as the single terminal integrating
Task; add the accepted `0037-21` contract to the prepared bundle and quiescence;
and demonstrate no restoration of queue/singleton/host transport in recovery.

### F-TICKET-PLAN-004 — High — the preparation packages are not bounded or executable

Packages A–C have no exact write scope, branch/merge target, predecessor
products, validation command/profile, evidence path, recovery rehearsal,
resource/time bound, uncertainty estimate or completion predicate. Package A
depends on “reviewed UI F-J” without pinning a reviewable accepted baseline.
Package B says only “design preparation”. Package C orders Data to conduct the
scope review even though the pinned amendment already is that completed review,
and it conflates consuming the result with repeating the authority step. The
statement that these packages are “authorized immediately” is not supported by
Task IDs, claims, exact authority references or write-collision analysis.

**Required correction:** either map each preparation package to a real current
Task or keep it explicitly allocation-neutral; in either case define exact
inputs, output paths, disjoint writes, start gates, direct capability and role,
validation/evidence, negative/recovery tests, resource estimates and branch
target. Replace Package C with bounded implementation of the already reviewed
delta by an identity distinct from Data, after the decision/amendment is
integrated on `main`; do not recharacterize review completion as implementation.

### F-TICKET-PLAN-005 — High — `0037-51` is assigned operative transition authority it does not have

The plan says `0037-51` “will govern the transition”. Current `TODO.md` defines
`0037-51` as preparation only: decision candidate and independent Architect
scope review, with no gate, dependency, instruction, selector or production
mutation. The amendment likewise requires its decision/corrections and authority
reference to be integrated before a distinct assigned implementation applies
the delta. Treating `0037-51` as the transition owner blurs architecture review,
governance integration, implementation and cutover authority.

**Required correction:** state the sequence explicitly: integrate the reviewed
decision/amendment through the authorized governance path; assign a distinct
implementation owner for the exact backlog delta; establish and accept the
`0037-21` shared contract before consumers start; implement retained packages;
then pass `0037-34.02` and the single `0037-40` terminal review floor. No plan
status or author `faithful` check supplies Acceptance or integration authority.

## Task-graph and role disposition

- **Transport retirement:** supported in prose, contradicted by the live
  `0037-47` critical-path edge.
- **Runner role boundary:** correctly named, materially incomplete.
- **Shared interface:** missing.
- **Consumer Acceptance edges:** missing.
- **Intermediate checkpoint:** missing.
- **Quiescence/cutover:** missing active-job and stale-role semantics.
- **Terminal floor:** `0037-40` named but required Runner proof absent.
- **Preparation packages:** not executable contracts.
- **Architecture/implementation/integration separation:** blurred at `0037-51`.

## Validation performed

- Pinned and inspected candidate substantive REF `fc80d5f082d`, final tip
  `457bb38760c`, amendment `5d5996d07d` and its actual tip `b38c3202d0`.
- Inspected the complete 46-line candidate and its changed-path set.
- Compared every Runner role, interface, dependency, checkpoint, cutover,
  recovery and negative-test requirement against the amendment.
- Inspected current `TODO.md` entries for `0037-08`, `0037-21`, `0037-25.01`,
  `0037-30`, `0037-34.01`, `0037-34.02`, `0037-39`, `0037-40`, `0037-42`,
  `0037-46`, `0037-47` and `0037-51`.
- Confirmed `0037-39 → 0037-47 → 0037-46` remains current legacy text and that
  the candidate provides no executable replacement graph.
- Confirmed the candidate contains no `0037-21`, `0037-25.01`, `0037-42`,
  `0039-02`, `0044-05`, `Acceptance`, `heartbeat`, `idempotence`, `quiescence`,
  `cancel`, `timeout`, `stale client` or intermediate-checkpoint contract.
- `git diff --check` is required before this review is handed off.

## Re-review entry criteria

A fresh immutable plan is reviewable when it:

1. represents the complete reviewed graph delta and removes every future
   sandbox/queue/singleton/typed-action/host-transport dependency;
2. makes `0037-21` the accepted shared Runner contract with its required
   predecessors, intermediate checkpoint and complete consumer edge set;
3. carries active-job state, evidence, cancellation/recovery and role/authority
   negatives through quiescence, authority preparation/switch and `0037-40`;
4. turns all preparation packages into bounded executable contracts; and
5. preserves exact separation of architecture review, implementation,
   Acceptance, integration and Feature closure.

The reviewer did not correct the candidate and grants no implementation,
Acceptance, checkpoint or integration credit.

## Re-review attempt — corrected candidate `702021c6c70cf467a36877e996e4e99545a75196`

### Immutable re-review baseline

- **Corrected substantive plan:**
  `fb6580eb3922bc2694f3117d395bec05d69c9d05`
- **Corrected final tip:**
  `702021c6c70cf467a36877e996e4e99545a75196`
- **Prior review:** `c456d66c394306a1667d20cf9d2fe4f62012da12`
- **Controlling Runner amendment:**
  `5d5996d07d8e8be71a99722a12e3afcb1d57919a`

The re-review is append-only and uses the same identity, independence, scope and
authority boundary as the initial review.

### Re-review verdict

**Verdict: `rejected`.** The correction fully closes the prior Runner shared-
contract, cutover and `0037-51` authority-separation findings. It also removes
the stale `0037-47` edge from the graph rows it covers. It does not, however,
provide the complete affected-node delta it says must precede mutation, and two
of its three proposed packages remain non-executable because exact write and
resource bounds are deferred. Package C additionally routes governance outputs
through a normal Task branch without reconciling the mandatory governance-on-
`main` integration path. These are allocation and execution blockers, not
editorial omissions.

### F-TICKET-PLAN-R2-001 — Critical — the advertised complete graph delta omits controlling amendment nodes

Section 3 correctly removes `0037-46`, `.01`, `.02` and `0037-47`, rewires
`0037-39`, establishes `0037-21`, and names its five direct accepted consumers.
But the controlling amendment also gives explicit dispositions for retained
`0037-42`, `0037-44`, `0037-32`, `0037-35.01`, `0037-36`, `0038-07`, `0038-09`,
`0043-01`, `0044-04`, `0044-07`, and explicit removals of `0037-50.02`–`.05`
and `0038-16.02`. None of those rows appears in the candidate's graph contract
(except bare mentions of “rewritten `0037-42`” and the cutover chain). Their
role/capability, historical-transport, recovery, signer-separation and run-ID
contracts therefore remain unbound.

The generic instruction that a later graph candidate must enumerate every
disposition does not make this plan itself complete or independently
reviewable. In particular, the plan cannot prove that no future consumer of the
removed singleton/queue/failover packages survives when the relevant removals
are absent from its own matrix.

**Required correction:** add every affected-node delta from the amendment with
its retain/rewrite/remove/historical disposition and exact dependency impact;
state the separate role/capability doctor behavior for `0037-42`, recovery
authority boundary for `0037-44`, background capsule/run-identity bindings,
signer separation, `0044-04/.07` role treatment, and all remaining removal
rows. Then mechanically validate complete set equality against the amendment,
not only endpoint validity for the listed subset.

### F-TICKET-PLAN-R2-002 — High — Packages A and B still defer executable bounds

Package A declares only “outputs only its declared public-projection and
generated-site paths” and says the allocator later pins exact output paths,
wall/CPU/memory limits and corpus. Package B similarly defers exact seed count,
workers, wall/CPU/memory and corpus limits to the Task claim. These are precisely
the write-collision, resource and validation boundaries the initial finding
required the plan to define before calling the packages bounded. Package A also
conditions its input on an accepted UI F-J baseline “if one has been allocated”,
without pinning an immutable candidate or defining the local deliverable when it
has not.

The new advisory ranges are useful planning evidence, but 35–50% uncertainty
and later allocator-selected output sets do not constitute exact executable
contracts. By contrast, Package C enumerates its paths and stop condition much
more concretely.

**Required correction:** enumerate Package A's exact public projection/site,
test, fixture and evidence paths and a pinned/explicitly absent UI baseline;
enumerate Package B's exact test/fixture/evidence paths; assign finite seed,
worker, CPU, memory, wall and output bounds or a deterministic checked profile
owned by a named predecessor; and state exact success/recovery artifacts. If
these cannot yet be known, label the entries design-preparation proposals rather
than bounded implementation packages and do not claim executability.

### F-TICKET-PLAN-R2-003 — High — Package C's branch route conflicts with governance-on-main

Package C correctly lists `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`,
`agent-workflow.json` and `docs/pipeline/**` outputs. Those are governance
artifacts. It nevertheless assigns all work to “Task branch/worktree `0037-21`”
without stating that the governance change is authored in an isolated worktree
on a branch cut from current `main` and integrated immediately through the
authorized governance route before agents consume it. An ordinary Task branch
cannot hold private shared governance state while parallel work proceeds.

The correction's authority sequence says the decision/amendment is integrated
through governance, but that does not resolve the later Package C implementation
route for the listed governance files.

**Required correction:** split or explicitly sequence the Package C governance
slice and ordinary work products. Bind governance authoring to an item-owned
worktree/branch based on current `main`, run required hygiene/preflight, and use
the separately authorized governance integration route; keep non-governance
Task products on the exact `0037-21` topology. Record the atomic compatibility
boundary so no agent observes a half-updated role/schema/instruction bundle.

### Disposition of prior findings F-TICKET-PLAN-001..005

1. **F-TICKET-PLAN-001 — partially resolved, still blocking.** The stale
   `0037-47` critical edge is removed, but the complete amendment node/removal
   matrix is not represented; R2-001 remains.
2. **F-TICKET-PLAN-002 — resolved.** `0037-21`, its complete job-control
   lifecycle, mandatory intermediate checkpoint, current-Acceptance edges and
   role/authority separation are now explicit.
3. **F-TICKET-PLAN-003 — resolved.** Quiescence, prepared authority bundle,
   stale-client switch behavior, independent evidence evaluation and synthetic
   `0037-40` cancellation/recovery proof are present without transport revival.
4. **F-TICKET-PLAN-004 — partially resolved, still blocking.** Package C is
   materially bounded, but A/B defer exact paths/resources and C's governance
   route is invalid; R2-002 and R2-003 remain.
5. **F-TICKET-PLAN-005 — resolved.** The plan now states `0037-51` is
   preparation only and separates governance integration, distinct
   implementation, Acceptance, checkpoints and terminal integration.

### Regression check

- `TODO.md` remains authoritative until cutover; `issues/` remains disposable.
- Transport-independent safety invariants remain retained.
- Sandboxed-grunt/queue/singleton/typed-action/host transport remain retired.
- Runner remains normally `unprivileged`, Task-ID-bound and authority-negative.
- `0037-21`, `0037-34.02` and the single `0037-40` terminal floor remain distinct.
- No candidate, backlog, governance, Acceptance, integration or `main` state was
  mutated by this review.

### Re-review validation

- Pinned candidate `fb6580eb3922` and final tip `702021c6c70c`; inspected the
  complete corrected plan and changed-path set.
- Compared the candidate row-by-row with all five original findings and the
  controlling amendment's affected-node, dependency, checkpoint, recovery and
  validation sections.
- Positive token checks confirmed the full shared job record/lifecycle,
  Acceptance consumer edges, quiescence, authority switch, synthetic terminal
  proof and `0037-51` preparation-only sequence.
- Whole-document affected-node comparison found the omitted nodes/removals named
  in R2-001; direct searches confirmed only a bare `0037-42` reference among
  that omitted set.
- Package-field review confirmed A/B defer exact paths/resources and Package C
  combines governance outputs with a normal Task branch route.
- `git diff --check` is required before the append-only review commit.

The corrected candidate remains rejected. This review grants no Acceptance,
integration, checkpoint-crossing or Feature-closure credit.
