# 0037 Ticket Modernization Execution Plan (Final Revision - Runner Aligned)

**Author:** Benjamin (Project Lead)
**Target:** `docs/dossiers/0037-ticket-modernization-execution-plan.md`

## 1. Exact Current Implementation Inventory

- **Store Foundation:** `/issues/` directory structure exists.
- **Schemas (`issues/_schema/`):** 16 completed JSON schemas.
- **Policies (`issues/_policy/`):** 7 completed policy files.
- **Data State:** `TODO.md` is strictly authoritative. `issues/` is the disposable shadow database until authorized cutover.

## 2. Retained Transport-Independent Safety Invariants

- Collision detection.
- Governance write protection.
- Claim CAS and concurrency control.
- Recovery mechanisms.
- Evidence immutability (`task-evidence-pack@v1`).
- Stale-client fencing.
- Cutover audit trails.
- Checkpoint-driven independent Integrator review.

## 3. Authority Sequence and Task-Graph Rewire Contract

Task `0037-51` is preparation only. It supplies the reviewed decision and
Architect scope evidence; it does not own the operative transition, mutate a
gate, grant Acceptance, or authorize integration. The execution sequence is:

1. integrate the reviewed decision and amendment through the authorized
   governance path;
2. assign an implementation owner distinct from the amendment Architect to
   apply the exact backlog and instruction delta;
3. rewrite and obtain current Acceptance for the shared `0037-21` Runner
   role/job-control contract at its mandatory intermediate checkpoint;
4. start its consumers only after their explicit Acceptance-before-start edge
   is satisfied;
5. implement retained parser, projection, migration, and cutover packages;
6. pass the `0037-34.02` authority-switch checkpoint; and
7. pass `0037-40`, the single terminal integrating Task and Feature review
   floor.

No statement in this plan or author-review verdict substitutes for any step.

- **Sandboxed-Grunt and transport retirement:** `sandboxed-grunt`, runner
  queue, singleton, typed runner action, and host transport are retired from
  the future execution architecture. Completed artifacts and schemas remain
  append-only historical evidence but are not future mutation interfaces.
- **Retained Runner role:** Runner is not retired. A Dispatcher explicitly
  selects Programmer, Tester, or Runner for an assigned Task. Runner is
  normally `unprivileged` and owns Task-ID-bound long-running background-job
  lifecycle and agent interfaces through direct execution. Role selection
  grants no architecture, Acceptance, integration, specialist, credential,
  release, or risk authority.

| Work unit | Reviewed graph treatment | Start or completion gate |
|---|---|---|
| `0037-46`, `0037-46.01`, `0037-46.02`, `0037-47` | Remove from the future critical path through governed additive dispositions; preserve branches, claims, findings, rejected reviews, and completed evidence. | No retained node consumes them as a future start gate. |
| `0037-39` | Rewrite for deterministic direct foreground invocation and Dispatcher-selected Runner background invocation; replace `0037-39:0037-47` with `0037-39:0037-37` and `0037-39:0037-51`. | Reviewed decision/amendment integrated; exact toolchain validation passes. |
| `0037-08` | Retain parser scope and `0037-08:0037-39`; it no longer traverses `0037-47` or `0037-46`. | Rewritten `0037-39` complete. |
| `0037-11`, `0037-12`, `0037-13..16`, `0037-22`, `0037-23`, `0037-29`, `0037-31` | Retain domain behavior and existing non-transport prerequisites. | Their actual retained prerequisites are terminal; no blanket “native execution” shortcut. |
| `0037-21` | Rewrite as the shared Runner role/job-control contract; replace `0037-21:0038-16` with `0037-21:0038-16.01`, and add `0037-21:0037-51` plus retained domain inputs and rewritten `0037-42`. | Current Acceptance at a mandatory intermediate integration checkpoint. |
| `0037-25.01`, `0037-30`, `0037-34.01`, `0039-02`, `0044-05` | Add explicit Acceptance-before-start consumption of current accepted `0037-21`. | Each rejects missing, stale, or invalidated `0037-21` Acceptance. |
| `0037-30/31 → 0037-34.01/32/33 → 0037-34.02 → 0037-35/36` | Retain cutover order, adding the accepted Runner contract and active-job state described below. | `0037-34.02` remains the mandatory authority-switch checkpoint. |
| `0037-40` | Retain as final activation and single terminal integrating Task. | Signed predecessor evidence plus the synthetic Runner proof below. |

Before operative mutation, a graph candidate must enumerate every
remove/historical/retain/rewrite disposition from the controlling amendment,
validate all prerequisite endpoints, prove acyclicity and reachability, and
check semantic start gates and current Acceptance edges against then-current
`TODO.md`. This plan does not apply that backlog delta itself.

### Complete Runner-amendment node/disposition manifest

This manifest is the plan's mechanical parity set for Data's Runner amendment.
Ranges name every individual node in the range. Operative work compares the
expanded sorted set and each disposition with the amendment; missing, extra, or
changed entries fail before mutation.

| Work unit/interface | Disposition | Dependency and contract effect |
|---|---|---|
| `0037-21` | rewrite | Own the shared role/job-control contract; replace `0038-16` with `0038-16.01`; add `0037-51` and `0037-42`; require current Acceptance at its intermediate checkpoint. |
| `0037-39` | rewrite | Replace `0037-47` with `0037-37` and `0037-51`; expose deterministic foreground and Runner-controlled background invocation. |
| `0037-42` | rewrite/retain direct bootstrap | Keep doctor, epoch, freeze and stale-client fencing; report operational role separately from capability class, reject `runner` as a capability class, and accept Runner only with a valid direct mapping. |
| `0037-25`, `0037-25.01` | rewrite | Retain the bounded regeneration DAG; background mode consumes current accepted `0037-21` and stable job/run identity without queue or action registry. |
| `0037-44` | rewrite/retain recovery | Retain direct freeze/export/restore/replay/forward-repair controls. Runner may execute an separately authorized long recovery job but cannot authorize freeze, restore, re-enable, risk, or release. |
| `0037-30` | rewrite | Add current accepted `0037-21`; quiescence consumes canonical active-job identity, process handle, lifecycle, cancellation/recovery, evidence and handoff state. |
| `0037-32`, `0037-35.01`, `0037-36` | rewrite | Runner may execute an already authorized long audit/rebuild; distinct Tester and registered signer evaluate evidence and own no execution-derived Acceptance authority. |
| `0037-34.01` | rewrite | Add current accepted `0037-21`; prepare exact accepted role/capability/job bundle, active-job disposition, inverse patch and stale-client proof. |
| `0037-34.02` | retain/checkpoint | Keep the mandatory atomic authority switch; reject stale Runner-as-transport or Runner-as-authority clients. |
| `0037-40` | retain/terminal checkpoint | Keep the single terminal integrating Task; consume synthetic long-job completion, cancel/recovery, stale-role and authority-negative proof. |
| `0038-07`, `0038-09` | retain | Bind context/resume capsule and environment identity to Task ID, job ID, owner, exact command/profile, state, results and recovery; never reinterpret them as queue requests. |
| `0038-16.01` | historical/retain inventory | Preserve the completed transport primitive inventory; reuse a primitive only behind an explicit direct interface. |
| `0043-01` | retain run identity | Bind `RUN_ARCHIVE_REF` and manual-cohort provenance to long build jobs through the direct job record; transport remains irrelevant. |
| `0039-02` | rewrite | Retain `0037-51`, add current accepted `0037-21`; classify tools as bounded foreground, Runner-controlled background, or both, with permissions/evidence/recovery and no typed allowlist. |
| `0044-04` | retain | Preserve capability-requirement profiling while keeping operational role, direct capability and authority separate. |
| `0044-05` | rewrite | Retain `0044-04` and `0037-51`, add current accepted `0037-21`; map Runner normally to `unprivileged` without inference from duration, model, or persona. |
| `0044-07` | rewrite | Remove sandbox/text-only and runner-obligation proposals while retaining role-gap analysis and Runner as a selectable operational role. |
| `0037-46`, `0037-46.01`, `0037-46.02`, `0037-47` | remove from future path | Preserve append-only branches, claims, implementation/rejection evidence; no future dependency consumes singleton/queue/qualification work. |
| `0037-50.02`, `0037-50.03`, `0037-50.04`, `0037-50.05` | remove from future path | Reconcile active claims, preserve evidence, and close additively; Runner retention creates no consumer for failover-remediation work. |
| `0038-16.02` | remove from future path | Preserve history and close additively; the retained `0038-16.01` inventory does not activate post-runner rollout. |

The expanded parity set is therefore:
`0037-21`, `0037-25`, `0037-25.01`, `0037-30`, `0037-32`,
`0037-34.01`, `0037-34.02`, `0037-35.01`, `0037-36`, `0037-39`,
`0037-40`, `0037-42`, `0037-44`, `0037-46`, `0037-46.01`,
`0037-46.02`, `0037-47`, `0037-50.02`, `0037-50.03`, `0037-50.04`,
`0037-50.05`, `0038-07`, `0038-09`, `0038-16.01`, `0038-16.02`,
`0039-02`, `0043-01`, `0044-04`, `0044-05`, `0044-07`.

## 4. Shared `0037-21` Runner Job-Control Contract

The rewritten `0037-21` product is one shared contract, not a transport service
and not a parallel protocol per consumer. Its versioned job record contains:

- Task ID, job ID, Dispatcher selector, Runner owner, branch/worktree, exact
  base and authority epoch;
- bounded command/profile digest, entry point, arguments, read/write scopes, input/output and
  evidence paths, resource/time limits, external hosts/data/credentials, and
  privacy classification;
- monotonic lifecycle (`requested`, `starting`, `running`, `cancelling`, `cancelled`,
  `succeeded`, `failed`, `timed-out`, `recovery-required`, `recovered`), with
  heartbeat/status, progress, logs, artifacts, result digests, and timestamps;
- cancellation and termination semantics, timeout handling, restart/recovery,
  retry and idempotence rules, cleanup, lease/ownership handoff, and abandoned
  job reconciliation;
- fail-closed checks for Task/claim/scope/base/epoch drift and explicit
  rejection of queue, singleton, typed-action, or host-transport restoration;
  and
- negative authority fields proving Runner execution does not make the Runner
  the Tester, signer, Architect, Integrator, specialist, or accepting authority.

The mandatory `0037-21` checkpoint tests schema and lifecycle monotonicity,
concurrent ownership, stale base/epoch, cancellation races, timeout, crash and
restart, idempotent retry, cleanup, evidence integrity, handoff, privacy and
external-resource boundaries, and all role/authority negatives. Programmer,
Tester, Runner, capability class, Architect/Implementer/Integrator role, and
specialist authority remain separately represented and validated dimensions.

## 5. Quiescence, Cutover, and Terminal Runner Proof

- **`0037-30` quiescence:** inventory every active Task-ID-bound job and its
  owner/base/epoch/scope/process-or-service handle; fence new starts; drain safe jobs; explicitly cancel
  or preserve non-drainable jobs; reconcile claims, leases, results, logs and
  recovery state; and fail closed on an unowned, stale, indeterminate, or
  externally active job. Evidence records the before/after job set and proves
  no future runner request is required.
- **`0037-34.01` preparation:** bind the current accepted `0037-21` contract,
  valid role-to-capability mappings, quiescence manifest, exact patch/digests,
  authority epoch, rollback bundle, stale-client fixtures, and active-job
  disposition into the prepared authority tree.
- **`0037-34.02` switch:** reject clients or jobs that interpret Runner as a
  transport, capability class, or authority; atomically advance the authority
  epoch while the write freeze remains; preserve job/evidence identities; and
  leave any mismatch frozen for rollback or forward repair.
- **`0037-35/36` verification:** rebuild and audit through direct execution,
  exercising the accepted Runner job contract without restoring a queue,
  singleton, typed action, or host service. A Runner may execute an already
  authorized long rebuild or audit; a distinct Tester/signer/Integrator
  evaluates its evidence.
- **`0037-40` terminal proof:** run a synthetic Task-ID-bound long job, observe
  heartbeats and bounded logs, cancel it during work, recover or restart it
  idempotently, verify cleanup and immutable results, reject stale role/epoch
  clients, and prove Runner cannot sign, accept, integrate, or grant itself
  specialist authority. Only the signed terminal review may lift the freeze.

Recovery before cutover restores the current legacy direct-execution state;
post-cutover recovery is forward issue-store recovery. Neither path restores
retired transport as a mandatory interface.

## 6. Preparation and Implementation Packages

These packages are allocation-neutral: the plan does not claim them or make
them immediately executable. Package A and Package B are explicitly
non-executable design-preparation proposals until their stop conditions are
resolved. Package C is a bounded implementation contract after its authority
and branch-sequencing gates are met.

### Package A — UI/projection design preparation (`0037-23`, not executable)

- **Inputs:** retained `0037-12` graph adapter; exact accepted UI F-J baseline
  if one has been allocated (otherwise stop); current schema fixtures and
  classified-projection policy. A Runner-controlled background generation mode
  additionally requires current accepted `0037-21`; foreground work does not
  gain a new start edge from this plan.
- **Stop condition:** no immutable accepted UI F-J baseline is pinned in this
  plan, and exact projection/site/test/fixture/evidence paths plus a finite
  predecessor-owned CPU/RAM/wall/output profile are absent. Therefore Package A
  authorizes no branch, write, generation job, or implementation.
- **Required local deliverable before conversion:** an allocated `0037-23`
  contract must pin the immutable UI baseline or explicitly reject the
  dependency; enumerate exact authored/generated/test/fixture/evidence paths;
  name its branch/merge target and disjoint scope; provide deterministic
  no-JS/link/privacy/determinism/cancel/recovery profiles with finite workers,
  CPU, RAM, wall time and output bytes; and name success, partial-failure,
  cleanup and recovery artifacts. Only then may a direct Programmer start, with
  Runner background generation conditional on accepted `0037-21`.
- **Advisory estimate:** 12k–25k tokens and 1–3 hours for design preparation,
  35–50% uncertainty until baseline and corpus measurement. This is not an
  execution estimate or permission.

### Package B — parser design preparation (`0037-08`, not executable)

- **Inputs:** retained parser/schema contracts, rewritten `0037-39`, exact
  canonical fixtures and dependency locks; no `0037-47`/`0037-46` dependency.
- **Known future target:** Task branch/worktree `0037-08` and
  `_src/tools/issue_store.py`; no implementation starts from this plan.
- **Stop condition:** the exact test/fixture/evidence paths and deterministic
  predecessor-owned profile with finite seed count, workers, CPU, RAM, wall and
  output limits are not yet pinned. Package B therefore authorizes no parser
  mutation or fuzz/background job.
- **Required local deliverable before conversion:** the allocated `0037-08`
  contract enumerates exact parser/test/fixture/lock/evidence paths, immutable
  corpus and dependency digests, fixed seeds and finite resource limits, exact
  unit/property/fuzz/malformed/Unicode/determinism commands, success artifacts,
  failure/cleanup state and recovery proof. A Runner-owned long fuzz job is
  conditional on accepted `0037-21` and that checked profile.
- **Advisory estimate:** 18k–30k tokens and 2–5 hours for design preparation,
  25–40% uncertainty until the predecessor profile is pinned. This is not an
  execution estimate or permission.

### Package C — shared Runner contract implementation (`0037-21`)

- **Inputs:** the already completed Data amendment
  `5d5996d07d8e8be71a99722a12e3afcb1d57919a` at actual tip
  `b38c3202d0d40812733204d4386388ff73234599`, integrated through its authorized
  governance path; rewritten `0037-42`; retained `0038-16.01` inventory and
  `0037-21` domain inputs.
- **Governance slice:** `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`,
  `agent-workflow.json`, `docs/pipeline/agent-workflow.md`,
  `docs/pipeline/tools.md`, `docs/pipeline/reports.md`,
  `docs/pipeline/README.md`, `docs/pipeline/roles/programmer.md`,
  `docs/pipeline/roles/tester.md`, `docs/pipeline/roles/runner.md`,
  `docs/pipeline/agent-roster.md`, and `docs/pipeline/process-roles.md` are
  authored in a Package-C-owned isolated worktree on a branch cut from current
  `main`. Before authoring and immediately before integration, run the required
  root hard preflight and `check_integration_hygiene.py`; any non-zero result
  stops. A separately authorized governance integrator advances current `main`
  immediately through the repository's governance route. The ordinary Task
  branch never privately carries these shared changes while parallel agents
  consume old governance.
- **Ordinary slice:** the versioned background-job schema/direct interface and
  their task-owned fixtures, tests, evidence and claim paths remain on the exact
  `0037-21` item topology. If the integrated operative Task has not allocated
  these paths, the slice stops rather than inventing them locally.
- **Atomic compatibility boundary:** the governance slice first defines a
  versioned compatibility range that accepts the current ordinary product and
  rejects premature new semantics. After its immediate integration, the
  ordinary slice implements the new version. Activation occurs only in a
  separately reviewed compatibility commit/bundle that pins both digests;
  rollback restores the prior compatible pair. No agent observes a role/schema/
  instruction bundle that requires an unavailable interface.
- **Execution:** direct Programmer implements; Runner may execute only its
  Task-ID-bound long validation fixtures; an independent Integrator owns the
  mandatory intermediate checkpoint.
- **Validation/evidence:** every field, lifecycle transition, concurrent owner,
  stale epoch/base, timeout, cancel/restart, idempotent retry, cleanup, handoff,
  privacy/external boundary, transport non-restoration and authority-negative
  case from Sections 4–5.
- **Bounds/recovery/completion:** Task contract pins exact paths, fixtures,
  workers, wall/CPU/memory/log limits and rollback before start; partial
  activation is prohibited; completion requires current independent Acceptance
  before any named consumer starts. This consumes Data's completed review; it
  does not order Data to repeat it. Advisory estimate: 18k–35k tokens and 2–5
  hours for the role/contract product plus 25k–50k tokens and 3–8 hours for the
  direct background-job implementation/fixtures, with 20–40% uncertainty and
  independent review time additional.
