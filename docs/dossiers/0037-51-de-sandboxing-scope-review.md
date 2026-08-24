# Architect scope review — Feature 0037 future direct execution

## Review identity and immutable baseline

- **Review item:** `0037-51`
- **Architect:** `agent:data:0037-51:20260824T083513Z`
- **Role/capability:** Management-instantiated Architect; `privileged`
- **Authority:** `TODO.md`, Task `0037-51`, authority commit `a57582e6cdf60a2d5ba37d1af3ff3be7de3afe77`
- **Baseline:** `main@a57582e6cdf60a2d5ba37d1af3ff3be7de3afe77`
- **Decision candidate:** `DEC-0037-002` in `docs/dossiers/dec-0037-future-direct-execution.md`
- **Branch:** `review-0037-51-scope-data-20260824T083513Z`
- **Worktree:** `.review-worktrees/0037-51-scope-data-20260824T083513Z`
- **Write scope:** this review and the decision candidate only

## Boundary and current status

This is preparation under the cross-item gate-scope exception. It does not edit
`TODO.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `agent-workflow.json`,
`docs/pipeline/**`, runner code, selectors, production paths, Acceptance records,
integration checkpoints, `main`, or `DONE.md`. The affected-item matrix,
dependency rewiring, activation, self-application, recovery, rollback,
non-grandfathering, validation, and risk analysis below are recommendations
checked against the pinned baseline; they become operative only through the
separate implementation and authority sequence stated in the verdict.

## Initial classification rule

An item is a removal candidate only when its required outcome has no future
consumer after all agents gain direct Shell and Git access. An item is retained
when it defines issue-store data, provenance, authority, validation, privacy,
collision protection, deterministic generation, evidence, migration, cutover,
or recovery independent of the runner transport. A mixed item is rewritten so
the invariant remains and the runner envelope, action registry, host deployment,
or sandbox-only fixture is removed. Completed artifacts are never erased; their
future normative role is dispositioned explicitly.

## Verdict

**Verdict: `scope-supported-with-bounds`.** The future direct-execution model is
architecturally coherent and implements the recorded Management direction. It
may become operative only after `DEC-0037-002` and this review are integrated on
`main`, a distinct implementer applies the exact backlog/instruction changes,
and the checkpoint moves below are recorded before any affected node receives
Acceptance. This is not Task acceptance, an integration verdict, a waiver, or
permission to cross `main` or an external boundary.

## Exhaustive Feature 0037 disposition matrix

The matrix covers every Task/Subtask currently declared inside Feature `0037`.
`historical` preserves completed work and its dependency history without making
it a future transport dependency. `remove` means an additive `[w]` disposition
under the integrated decision, never deletion. `rewrite` preserves the named
outcome but removes sandbox/runner transport. `retain` needs no contract change
from this decision.

| Disposition | Work units | Required operative treatment |
|---|---|---|
| `historical` | `0037-48` | Preserve singleton qualification and retained logs as evidence of the former bootstrap; no future start gate consumes it. |
| `historical` | `0037-01`, `0037-02`, `0037-02.01`, `0037-02.02`, `0037-02.03`, `0037-03`, `0037-03.01`, `0037-03.02`, `0037-04`, `0037-04.01`, `0037-04.02`, `0037-05`, `0037-06`, `0037-06.01`, `0037-06.02`, `0037-06.03` | Preserve accepted architecture/data/lifecycle/provenance/migration contracts. Capability-specific examples are historical inputs; shared data and safety semantics remain authoritative where later approved. |
| `historical` | `0037-45`, `0037-41` | Preserve the former capability and bootstrap contracts append-only. Open consumers use `DEC-0037-002` and the rewritten direct bootstrap, not the two-class runner transport. |
| `historical` | `0037-37`, `0037-49`, `0037-07` | Preserve the approved architecture package, external-readiness record, and approval. Their runner-specific evidence remains provenance but does not prove future runner need. |
| `remove` | `0037-46`, `0037-46.01`, `0037-46.02` | Close as superseded/non-implementation after preserving branch tips, the unintegrated implementation, rejected candidate, review verdict, and claims. Do not integrate the queue/activation candidates into the future Feature branch. |
| `remove` | `0037-50`, `0037-50.02`, `0037-50.03`, `0037-50.04`, `0037-50.05` | Close the runner-failover correction package and open descendants as superseded. Reconcile existing `.02`/`.03` claims with their owners; do not appropriate or delete them. |
| `historical` | `0037-50.01` | Keep `DEC-0037-001` and its completed decision Task as the valid historical decision for the rejected queue-failover path; record that `DEC-0037-002` supersedes only its unimplemented future planning effect. |
| `retain` | `0037-51` | Complete this decision/scope-review preparation only. It becomes the prerequisite and authority anchor for operative rewrites after integration on `main`. |
| `remove` | `0037-47` | Eliminate sandboxed-grunt first-attempt runner qualification; no replacement execution-profile Task is required. Direct-tool validation moves into the owning Tasks and bootstrap/cutover checks. |
| `retain` | `0037-08`, `0037-09`, `0037-09.01`, `0037-09.02`, `0037-09.03`, `0037-09.04`, `0037-17`, `0037-17.01`, `0037-17.02`, `0037-17.03` | Keep issue-store parsing, validation, sole-writer, lifecycle, provenance, graph, and query contracts unchanged. |
| `rewrite` | `0037-39` | Keep reproducible toolchain locks and drift checks; replace sandboxed runner provisioning with a directly executable, clean-worktree/offline verification command. |
| `retain` | `0037-10`, `0037-10.01`, `0037-10.02`, `0037-10.03`, `0037-10.05` | Keep controlled issue edits, claims, decisions, and criteria operations unchanged. |
| `rewrite` | `0037-10.04` | Keep CLI/query semantics; remove typed runner-action registration as a required interface. Test direct CLI invocation and stable exit/JSON contracts. |
| `retain` | `0037-11`, `0037-11.01`, `0037-11.02`, `0037-12`, `0037-13`, `0037-14`, `0037-15`, `0037-15.01`, `0037-15.02`, `0037-15.03`, `0037-16` | Keep deterministic views, legacy import/reconciliation, migration reporting, and provenance writers. References to historical runner request/result data remain import coverage, not execution requirements. |
| `rewrite` | `0037-42` | Keep bootstrap doctor, epoch, freeze phases, stale-client fencing, protected-integration checks, and direct command availability checks. Remove runner-only bootstrap and typed transaction-operator transport. |
| `rewrite` | `0037-43` | Keep the non-bypassable hosted policy gate and authenticated branch-rule evidence. Configuration is a separately authorized direct repository-owner operation, not a generic runner action and not implied by privilege. |
| `retain` | `0037-18`, `0037-19`, `0037-20` | Keep canonical lifecycle/regeneration/migration documentation; its generated direct-execution interfaces follow the rewritten bootstrap and tools. |
| `rewrite` | `0037-21` | Publish one direct-execution capability model and direct doctor/tool/recovery sequence. Remove runner request/action instructions, sandboxed classes, and legacy-frozen runner-operator exception while retaining authority, claims, privacy, recovery, and stale-client behavior. |
| `retain` | `0037-22`, `0037-23`, `0037-23.01`, `0037-23.02`, `0037-24`, `0037-24.01`, `0037-24.02`, `0037-38` | Keep graph, projection, website, i18n, and translation review work unchanged. |
| `rewrite` | `0037-25`, `0037-25.01` | Keep the bounded regeneration DAG and direct `issuectl regenerate --all` command; remove the runner action/envelope and sandbox-only fixture. |
| `retain` | `0037-25.02`, `0037-25.03`, `0037-26`, `0037-26.01`, `0037-26.02`, `0037-26.03`, `0037-26.04`, `0037-26.05`, `0037-26.06`, `0037-27`, `0037-27.01`, `0037-27.02`, `0037-27.03`, `0037-27.04`, `0037-27.05`, `0037-28`, `0037-29`, `0037-31` | Keep staging/promotion/determinism, producer provenance, graph demonstration, shadow migration, and frozen candidate work unchanged. Domain review/curation queues are not runner queues. |
| `rewrite` | `0037-44` | Keep emergency freeze, export, restore, replay, forward repair, authority epoch, and signed re-enable. Expose exact direct privileged/unprivileged commands instead of authenticated emergency runner actions. |
| `rewrite` | `0037-30` | Keep quiescence, claim/lease reconciliation, epoch bump, collision checks, and transaction-bound operators. Reconcile historical runner requests but require only active direct sessions/claims to stop; no future runner request is required. |
| `rewrite` | `0037-32` | Keep independent signed pre-cutover audit and fixed profile; an assigned direct audit agent executes exact commands and retains results without a runner submission. |
| `retain` | `0037-34` | Keep aggregate prepared/authorized cutover contract. |
| `rewrite` | `0037-34.01` | Keep detached preparation, exact patch, digests, epochs, rollback, and stale-client tests; replace the qualified grunt-runner/action-registry bundle with the direct-execution bootstrap/tool contract. |
| `rewrite` | `0037-33` | Keep signed process/security/release review and unchanged-candidate authorization; replace zero-privileged/grunt-runner proof with evidence that mechanical commands grant no review authority and require no runner service. |
| `retain` | `0037-34.02` | Keep the atomic authority switch, frozen state, follow-up reference, one-authority invariant, and exact-patch check. It consumes the rewritten prepared tree. |
| `retain` | `0037-35`, `0037-35.02` | Keep clean verification aggregation and isolated rollback/event-replay rehearsal. |
| `rewrite` | `0037-35.01` | Keep clean rebuild and double-run determinism; replace the fresh sandboxed-agent/runner request with a fresh directly executing agent and exact command manifest. |
| `rewrite` | `0037-36` | Keep independent signed post-cutover audit; replace grunt-runner profile submission with direct execution of the exact fixed audit profile. |
| `retain` | `0037-40` | Keep signed activation, follow-up reference, freeze lifting, generated closure, fresh-agent doctor, and point-of-no-return rules. Make this the terminal integrating Task and Feature review floor. |

## Cross-Feature disposition matrix

| Work units/artifacts | Disposition and boundary |
|---|---|
| `0038-17`, `0038-24`, `0038-28`, `0038-30` | Completed runner/sandbox enforcement, host package, disposition, and activation-gate work remains historical. It is not deleted or treated as the future capability model. |
| `0038-02`, `0038-04`, `0038-06`, `0038-07`, `0038-09`, `0038-10` | Retain transaction recovery, diagnostics, collision planning, context capsules, environment fingerprinting, and immutable result/evidence semantics. Adapt reusable code to direct invocation rather than discarding it with the envelope. |
| `0038-19`, `0038-20` | Keep completed typed branch/merge semantics as historical design input. Future implementation uses direct commands/libraries with the same scope, stale-tip, journal, rollback, and checkpoint rejections; the typed runner action is not a required boundary. |
| `0038-22` | Retain and prefer the self-service item worktree provisioner for direct Git agents. It replaces host-only provisioning as the normal future path. |
| `0038-23` | Retain checkpoint authority and doctor/editor enforcement; later terminology changes remove sandbox-author restrictions without weakening Architect separation. |
| `0038-16.01` | Preserve the completed handoff manifest as an exhaustive historical primitive inventory. A later direct-execution rewrite dispositions each still-useful primitive once; it does not activate its queue mappings. |
| `0038-16.02`, `0038-16` | Close the post-activation runner rollout Subtask and its runner-specific aggregate as superseded/non-implementation. Preserve `0038-16.01` and its evidence independently. |
| `0039-02` | Rewrite the future tool-process contract from typed runner allowlisting to reviewed direct executable interfaces, exact side-effect classes, permissions, recovery, and catalog ownership. |
| `0039-05` | Replace the wait for `0037-50` with the integrated direct capability/bootstrap path; retain machine acceptance, authority, signature, audit, and rejection semantics. |
| `0041-01` | Preserve completed host clone provisioning as historical/optional isolation. It is no longer the mandatory normal path once direct agents can create isolated item worktrees or clones themselves. |
| `0041-02`, `0041-03` | Retain atomic self-describing check-in and Acceptance-owned REF work; neither outcome depends on sandboxing. |
| `0041-04`, `0041-06`, `0041-05` | Rewrite host-runner push and transaction integration into direct item-scoped push/transaction checks, retaining branch guard, CAS, journal, rollback, provenance, and the mandatory end-to-end checkpoint. |
| `0044-04` | Retain the capability requirement profile but use the direct-execution model as its current architecture input. |
| `0044-05` | Rewrite the capability schema/matcher so execution capability is direct for every future agent while authority, data, tools, cognition, and specialist eligibility remain independently matched. |
| `0044-07` | Remove the proposed sandbox/text-only role and runner-obligation choice; retain the role-gap and cost analysis for direct agents. |

## Implemented-artifact disposition

| Baseline/artifact | Disposition |
|---|---|
| `runner-host/**`, `issues/_policy/runner-service.json` on `main` | Preserve while the current legacy workflow still references them. After direct authority activation, mark them non-normative and retire live service configuration only through a separately validated cleanup; never infer external service shutdown from a Git edit. |
| `_src/tools/runner_transaction.py`, `_src/tools/test_runner_transaction.py`, `docs/pipeline/runner-transaction.md` | Reuse journal, CAS, exact-scope, detached candidate, rollback, and evidence logic through a direct transaction interface. Remove the runner envelope as the required caller, not the safety library. |
| `agent-workflow.json`, `issues/_schema/agent-workflow-bootstrap-v1.schema.json`, bootstrap fixtures | Rewrite the capability/transport selector while retaining authority epoch, freeze state, bundle digests, stale-client rejection, partial-switch detection, and recovery. |
| `issues/_schema/runner-request-v1.schema.json`, `issues/_schema/runner-result-v1.schema.json`, runner-protocol fixtures | Preserve as historical schemas/evidence; do not expose them as future issue-store mutation APIs. |
| `docs/pipeline/legacy-handoff-manifest{,-v1.json}`, its checker/tests | Preserve as the immutable pre-activation inventory and use it once to prove that every primitive is retained, replaced, or retired. Do not require its queue liveness gate after the direct rewrite. |
| `0037-46.01@95dd730ddc` (substantive `2afb4d2ca5`) | Preserve branch and claim. Do not merge `_src/runner/**`, `_src/tools/runner_dispatch.py`, dispatcher tests, or runner-dispatch documentation into the future Feature branch solely because implementation completed off-main. |
| Rejected `0037-46.02@0d2088a677`, review `b57fa240859`, and retained campaign evidence | Preserve append-only as rejected evidence. No finding is cleared or reclassified; the selected future architecture removes the subject before deployment. |
| `0037-50.02@56562ff08c`, `0037-50.03@7ef4a317ae` | These tips contain active claim preparation but no corrective implementation beyond the rejected baseline. Owners must release/close them additively before `[w]`; this review does not appropriate them. |
| `logs/runner-qualification-0037-48/**` and other completed runner evidence | Preserve under existing retention rules as historical proof. It grants no future authority and is not regenerated as a direct-execution requirement. |

## Dependency rewiring

| Current edge/gate | Reviewed replacement |
|---|---|
| `0037-46.01 → 0037-46.02 → 0037-46 → 0037-47` | Remove the complete future runner activation/qualification chain after additive `[w]` dispositions. Preserve tips and review history. |
| `0037-50.01 → {0037-50.02,0037-50.03} → 0037-50.04 → 0037-50.05 → 0037-50` | Keep `.01` historical; remove the open corrective chain and aggregate after claim reconciliation. |
| `0037-39:0037-47` | Replace with `0037-39:0037-37` and `0037-39:0037-51`. The architecture package supplies the toolchain selection; the integrated decision supplies the capability model. |
| `0037-08:0037-39` and downstream issue/provenance edges | Keep unchanged; direct toolchain qualification continues to gate parser and generator work. |
| `0037-42:0037-09,0037-10,0037-11` | Add `0037-42:0037-51`; keep existing inputs. This makes the new bootstrap wait for the integrated direct capability decision. |
| `0037-21:0038-16` | Replace with `0037-21:0038-16.01` and add `0037-21:0037-51`; the manifest is inventory, while the removed rollout aggregate is not a prerequisite. |
| `0038-16.02:0038-16.01,0037-46` | Remove the Subtask through `[w]`. Recast `0038-16` as a bounded supersession closure over completed `0038-16.01` plus `0037-51`, or close the aggregate `[w]` if no independent package work remains. |
| `0039-05` textual resume gate on `0037-50` | Replace with current `0037-51` plus the rewritten `0037-42` bootstrap/transaction boundary before issue-store acceptance enforcement begins. |
| `0039-02` with no capability-decision prerequisite | Add `0039-02:0037-51` before adopting the direct tool-execution process. |
| `0041-04`, `0041-06` old host/runner execution contracts | Add `0037-51` to each rewritten Task. `0041-05` consumes them transitively and retains its mandatory integration review. |
| `0044-05:0044-04` | Add `0044-05:0037-51`; `0044-07` consumes the updated matcher transitively. |

No other Feature `0037` prerequisite is removed merely because a Task mentions a
queue: review queues, curation queues, claim stores, and transaction refs are
domain data, not the runner transport.

## Interfaces retained as explicit predecessor products

The operative rewrite must baseline these shared interfaces before consumers
start; later Task text may narrow paths but must not invent parallel semantics:

1. **Direct bootstrap interface (`0037-42`):** `agent doctor --json`, authority
   epoch, capability/freeze phase, bundle digests, stale-client errors, and
   immediately-before-write epoch recheck.
2. **Direct transaction interface (`0037-10`/`0038-02` semantics):** exact item,
   branch/base, read/write scopes, validation set, evidence outputs, journal,
   CAS publication, rollback/recovery, and structured failure result.
3. **Collision/governance interface (`0037-09`, `0038-06` semantics):** derived
   scopes, overlap rejection, protected governance paths, no implicit authority,
   and deterministic diagnostics.
4. **Regeneration interface (`0037-25`):** one direct bounded DAG command with
   exact inputs/outputs, run identity, staging, atomic promotion, and no partial
   success.
5. **Recovery interface (`0037-44`):** signed/authorized freeze and re-enable,
   exact export/restore/replay, epoch invalidation, forward repair, and retained
   RTO/data-loss limitations.

## Checkpoints and governance activation

- The existing mandatory review and rejected verdict at `0037-46.02`, and the
  planned `0037-50.05` checkpoint, remain append-only history. Their flags are
  not silently moved; operative backlog repair closes those nodes `[w]` under
  `DEC-0037-002` and records the replacement checkpoint rationale.
- Add an intermediate mandatory integration review to `0037-34.02`, because it
  applies the atomic authority switch and point-of-no-return preparation.
- Mark `0037-40` as the **single terminal integrating Task** and mandatory Feature
  review floor. It is the only Task that validates post-cutover audit/rollback,
  lifts the freeze, generates closure, and moves the Feature to `DONE.md`.
- No extra checkpoint is required for rewritten direct CLI wrappers whose safety
  invariants are verified at `0037-34.02` and `0037-40`; security/privacy or
  external repository configuration still receives its specialist/authority
  review at the owning gate.
- Activation order is: integrate decision and review on `main`; independently
  implement/review backlog rewiring; reconcile active runner claims; rewrite
  predecessor interfaces; execute ordinary implementation; review `0037-34.02`;
  execute frozen verification/recovery; review `0037-40`; then close Feature.
- This review self-applies the direct-execution assumption only to preparation:
  Data used Shell/Git in an isolated item worktree and produced no runner request.
  That observation is not qualification evidence for downstream tools or agents.

## No implicit grandfathering and recovery

- No open claim, queue request, rejected verdict, off-main implementation, or
  completed evidence gains a new state from this record alone. Owners or an
  explicitly assigned reconciler close active claims and record exact preserved
  tips before any `[w]` transition.
- No already accepted/historical record is rewritten. Future contracts refer to
  `DEC-0037-002`; `DEC-0037-001` and runner decisions remain readable in their
  original scope.
- Before `DEC-0037-002` integration, abandoning this branch has no operative
  effect. After integration but before implementation, a new append-only decision
  is required to reverse direction; no gate has yet moved.
- Before issue-store cutover, recovery remains the current legacy direct Git
  workflow with the current authoritative lists and exact source commit. During
  cutover, `0037-34.01`/`.02` retain the inverse patch and frozen transaction
  evidence. After the point of no return, `0037-44` forward recovery governs;
  restoring a retired runner is not promised.
- Live runner-host retirement or external service shutdown is never inferred
  from repository deletion. It requires explicit external authority, observed
  service identity/state, retained stop evidence, and an independently tested
  direct recovery path.

## Validation and test design for the operative rewrite

1. A backlog-graph fixture applies the reviewed changes and proves all IDs and
   prerequisite endpoints exist, no cycle or semantic deadlock is introduced,
   removed nodes have no open successors, and every retained Task is reachable.
2. A capability scan proves no future normative Task requires
   `sandboxed-grunt`, `run.sh`, runner queue, typed runner action, host service,
   or zero-direct-execution fixtures; historical blocks are explicitly exempted
   by stable path/section, not broad text suppression.
3. Direct transaction negative tests cover wrong item/branch/base, overlapping
   scope, governance path, stale epoch, failed validation, partial mutation,
   CAS loss, interrupted recovery, and authority escalation.
4. Clean direct-agent fixtures execute bootstrap, issue mutation, regeneration,
   audit, cutover preparation, rollback rehearsal, and stale-client recovery
   without a runner service and with exact command/result manifests.
5. Checkpoint validation proves exactly one terminal integrating Task (`0037-40`),
   the intermediate authority-switch checkpoint (`0037-34.02`), independent
   reviewers, current Acceptance closure, and no Feature close on stale evidence.

## Advisory execution estimates

Assumptions: current repository size, stdlib-first tools, existing fixtures are
reused, no external service mutation, and each package is handled by a fresh
qualified session with exact context.

| Package | Tokens / cognitive demand | Runtime / CPU | Uncertainty | Material risk |
|---|---|---|---|---|
| Backlog and authority-instruction rewrite | 18k–35k; high | 1–3 h; low CPU | 20–35% due concurrent backlog drift | high, repository-wide gate reach |
| Direct bootstrap/transaction adaptation | 25k–50k; high | 2–6 h; medium CPU, focused tests 10–30 min | 25–40% due legacy coupling | high, mutation and recovery boundary |
| Regeneration/recovery direct interfaces | 20k–45k; high | 2–5 h; medium/high CPU, full DAG 20–90 min | 20–35% | high, provenance and data recovery |
| Cutover preparation/audits/closure | 30k–60k; very high | 4–10 h plus reviews; high CPU 30–120 min | 30–45% until candidate exists | very high, authority switch and point of no return |

These are planning ranges, not acceptance evidence or budget authority. Split a
package if its exact write set exceeds the declared interface owner or if one
session cannot retain the required candidate, baseline, and validation context.

## Start and completion evidence

`DEC-0037-002` was confirmed free against the pinned `main` baseline before this
branch was created. Start commit `849fc917f` added exactly the two declared
files. The final handoff must report the final tip, file digests, identifier and
coverage checks, graph-rewrite validation, document validation, and clean status.
