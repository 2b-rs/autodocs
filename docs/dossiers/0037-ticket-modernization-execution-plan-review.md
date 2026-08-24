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
