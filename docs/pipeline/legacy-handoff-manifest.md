# Pre-Activation Legacy Handoff Manifest

**Status:** Normative hand-over record produced by Task `0038-16.01` (Feature `0038`,
Campaign E). Machine-readable authority is
[`legacy-handoff-manifest-v1.json`](legacy-handoff-manifest-v1.json); this page is its
human-readable rendering and rationale. Where the two disagree, the JSON wins.

**Checker:** `python3 _src/tools/legacy_handoff_manifest.py --check [--json]` — read-only,
stdlib-only, exit 0 only at zero findings.

## What this document is, and what it is not

It is the single record that hands the surviving Feature `0038` legacy execution bridge over to
the versioned runner queue that Task `0037-46.01` implements and Task `0037-46.02` activates.

It **maps**; it does not migrate. Reading or validating this manifest:

- activates no queue (`activates_queue: false`),
- changes no authority (`changes_authority: false`),
- creates, changes or invalidates no `Acceptance: ✓` record,
- leaves the legacy singleton `run.sh` as the **only** mechanism that accepts mutating requests
  until `0037-46.02` bumps the runner protocol epoch.

The singleton's expected steady state on disk is *absent* — it is a consumable one-use envelope
(see [`../../SANDBOX.md`](../../SANDBOX.md)). Absence is not deactivation, and the checker
therefore asserts the *inverse*: that no `.runner/` runtime root and no `_src/runner/` registry
exists yet.

## The two dispositions

Every primitive carries exactly one disposition — never both, never neither:

| Disposition | Consumer | Meaning |
|---|---|---|
| `typed-action` | `0037-46.01` | The capability survives. The named typed action/contract IDs must be registered in the permanent registry, honouring the compatibility note and inheriting the named test fixtures. |
| `retirement-trigger` | `0037-46.02` | The capability does not survive. The named trigger states exactly what must be durably true before the legacy path stops accepting work, and `removal_condition` states when the artifact may actually be deleted. |

Two invariants make the mapping total and unambiguous, and the checker enforces both:

1. **Zero unmapped** — every primitive has a disposition, and every mechanism enumerated by the
   living `## Skript-Ausführungs-Infrastruktur` table of [`tools.md`](tools.md) is either a
   primitive source or an explicitly justified exclusion. The inventory is read from that living
   table rather than copied, so drift is detected instead of frozen.
2. **Zero multiply authoritative** — each `authority_key` and each typed action/contract ID has
   exactly one owning primitive. No two tools may claim to implement the same capability, in
   either direction across the cutover.

`superseded_by` links a retiring primitive to the typed action that replaces it, and must resolve
to an action some primitive in this manifest owns.

## Retirement discipline

A retirement trigger never fires before the queue's success for that capability is **durable**.
The legacy path is *removed*, not disabled in place, and only when its `removal_condition` is met.
Critically, `recovery.singleton-rollback` is itself a primitive: the tested automatic rollback
that restores the singleton and the prior epoch must stay executable for the whole activation
window, which is why no primitive may be deleted merely because the queue started working once.

## Bound `0037-37` review package

- producer Task `0037-37`, REF `927da0690a964249f7ca0b83719601b849be801f`
- package `docs/pipeline/issue-store-review-package.json`
  - `sha256` `bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f`
  - `base_commit` `e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f`
- architecture: [`issue-store-architecture.md`](issue-store-architecture.md) · findings: [`issue-store-findings.md`](issue-store-findings.md)
- 17 contract digests bound verbatim; the checker recomputes every one of them
  against the working tree and fails on any drift.

Recorded residual risks (carried, not resolved here):

- external approval/signing/hosting credential readiness is deferred to 0037-49
- implementation is forbidden until architecture approval

## Queue consumers

### `0037-46.01`

Register every `typed-action` disposition's action IDs in the permanent typed-action registry (`_src/runner/actions-v1.json`) with the compatibility note honoured and the named test fixtures inherited; implement no generic shell action; do not activate.

### `0037-46.02`

Fire every `retirement-trigger` disposition in the recorded order only after queue success is durable, keep the singleton rollback executable for the whole activation window, and remove a primitive only when its `removal_condition` is met.

## Primitives (72)

### Actions — `action` (14)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `action.bootstrap.instance`<br>`bootstrap_instance.sh` — agent instance bootstrap | `0038-23` | → `0037-46.01` | `env.bootstrap-instance@v1` |
| `action.bootstrap.ssh-known-hosts`<br>`bootstrap_ssh_known_hosts.sh` — fingerprint-verified host key installation | `0038-27` | → `0037-46.01` | `env.bootstrap-known-hosts@v1` |
| `action.branch-merge.base-branch`<br>Typed `base-branch` action: create the item branch off its declared parent | `0038-20` | → `0037-46.01` | `git.base-branch@v1` |
| `action.branch-merge.integrate-checkpoint`<br>Typed `integrate-checkpoint` action (Task→Feature, Feature→main) — contract only, structurally refused by the legacy bridge | `0038-19` | → `0037-46.01` | `git.integrate-checkpoint@v1` |
| `action.branch-merge.merge-prereqs`<br>Typed `merge-prereqs` action: sequential non-octopus two-parent merges with append-only claim union | `0038-20` | → `0037-46.01` | `git.merge-prereqs@v1` |
| `action.provision.tmp-worktree`<br>`provision_tmp_worktree.sh` — explicitly superseded shared-checkout worktree provisioner | `0038-22` | ⌫ `0037-46.02` | `0037-46.02` activation, by which time `env.provision-worker-clone@v1` is the sole provisioning authority. |
| `action.provision.worker-clone`<br>`provision_worker_clone.sh` — current privileged worker-clone provisioner | `0041-01` | → `0037-46.01` | `env.provision-worker-clone@v1` |
| `action.publish.public-site`<br>`publish_public_site.sh` — external publication to the deploy repository | `0038-14` | → `0037-46.01` | `publish.public-site@v1` |
| `action.retired.task-bookkeeping-closure`<br>`task_bookkeeping_closure.py` — already-decommissioned free-form TODO/claim direct write surface | `0038-05.02` | ⌫ `0037-46.02` | `0037-46.02` completes activation, at which point no caller can reach a pre-queue bookkeeping write path at all. |
| `action.runner-transaction.close-task-v1`<br>Legacy fail-closed close-task transaction (generate → validate → promote → substantive commit → REF bookkeeping → claim finalization) | `0038-05` | → `0037-46.01` | `repo.generate@v1`, `repo.validate@v1`, `git.commit-path-limited@v1`, `bookkeeping.two-commit-ref-closure@v1`, `claim.finalize@v1` |
| `action.runner-transaction.legacy-editor-candidate-v1`<br>Authoritative multi-file promotion of a pre-planned legacy_task_editor.py candidate | `0038-05.02` | → `0037-46.01` | `bookkeeping.promote-editor-candidate@v1` |
| `action.runner-transaction.verify-and-commit-v1`<br>Legacy verify-then-commit transaction without bookkeeping closure | `0038-05` | → `0037-46.01` | `git.commit-verified@v1` |
| `action.singleton.run-loop`<br>`runner-host/run-loop.sh` — legacy watch/one-shot runner host with sandbox and environment self-test | `0040-10` | ⌫ `0037-46.02` | `0037-46.02` registers the runner-side queue trigger/service and dedicated runtime root, replacing the singleton watch loop. |
| `action.singleton.run-sh`<br>Root `run.sh` — the consumable, parameterless singleton runner request envelope | `0037-46.02` | ⌫ `0037-46.02` | `0037-46.02` bumps the runner protocol epoch in the live bootstrap selector after queue health, round-trip, concurrency, restart and mutation-isolation tests pass durably. |

### Approval readiness — `approval-readiness` (4)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `approval.authorities-policy`<br>`issue-authorities@v1` and `credential-handles@v1` policy records | `0038-15` | → `0037-46.01` | `approval.ref-create-append-cas@v1`, `sign.create@v1` |
| `approval.bootstrap-verifier`<br>`verify_issue_approval_bootstrap.py` — approval-ref bootstrap verifier | `0038-15` | → `0037-46.01` | `approval.verify-bootstrap@v1`, `sign.verify@v1` |
| `approval.external-readiness-blocker`<br>`BLOCKING-EXTERNAL-001` — external approval/signing/hosting credential readiness deferred to `0037-49` | `0037-49` | → `0037-46.01` | `approval.check-readiness-external@v1` |
| `approval.readiness-manager`<br>`manage_approval_readiness.py` — machine-checkable readiness gate for the `0037-07` approval flow | `0038-15` | → `0037-46.01` | `approval.check-readiness@v1` |

### Context — `context` (3)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `context.backlog-diagnosis`<br>`legacy_task_doctor.py` — read-only backlog, claim, REF, prerequisite and bootstrap diagnosis | `0038-06` | → `0037-46.01` | `runner.discovery@v1` |
| `context.bookkeeping-planner`<br>`legacy_task_editor.py` — digest-bound structural planner for backlog bookkeeping | `0038-05.02` | → `0037-46.01` | `bookkeeping.plan@v1` |
| `context.resume-capsule`<br>`task_context_capsule.py` — bounded resume capsule after a context/tool-budget boundary | `0038-07` | → `0037-46.01` | `context.build-capsule@v1` |

### Evidence — `evidence` (4)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `evidence.pack-builder`<br>`task_evidence_pack.py` — deduplicated, content-addressed evidence pack builder | `0038-12` | → `0037-46.01` | `evidence.build-pack@v1`, `evidence.verify-pack@v1` |
| `evidence.request-log-root`<br>`output/logs/<task-id>/<request-id>/` — bounded, git-ignored per-request evidence root | `0038-11` | → `0037-46.01` | `evidence.request-log-root@v1` |
| `evidence.run-archive`<br>`output/run-archive/run-<timestamp>-n<seq>.sh` + `.log` — complete singleton invocation archive | `0037-46.02` | ⌫ `0037-46.02` | `0037-46.02` identifies the last accepted singleton request and rejects new submissions; from that point the archive is closed, not deleted. |
| `evidence.run-current-log`<br>`output/run-current.log` — live singleton invocation log | `0037-46.02` | ⌫ `0037-46.02` | `0037-46.02` epoch bump: the singleton stops accepting requests, so nothing writes this path again. |

### Recovery — `recovery` (4)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `recovery.artifact-quarantine-gc`<br>Claim-aware quarantine, retention tiering and dry-run-first GC | `0038-11` | → `0037-46.01` | `recovery.quarantine@v1`, `recovery.gc-plan@v1` |
| `recovery.rollback-and-ref-cleanup`<br>Rollback of partial mutations plus temporary ref/worktree cleanup | `0038-05` | → `0037-46.01` | `git.rollback-ref-cleanup@v1`, `git.worktree-detached@v1` |
| `recovery.singleton-rollback`<br>Tested automatic rollback restoring the singleton and prior protocol epoch | `0037-46.02` | ⌫ `0037-46.02` | `0037-46.02` post-switch verification passes durably and management no longer requires the rollback window. |
| `recovery.transaction-journal`<br>Transaction and promotion journals with crash-safe replay | `0038-10` | → `0037-46.01` | `recovery.journal-replay@v1` |

### Results — `result` (10)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `result.approval-readiness`<br>Approval-readiness verdict | `0038-15` | → `0037-46.01` | `result.approval-readiness@v1` |
| `result.artifact-gc-report`<br>Dry-run-first retention/GC report | `0038-11` | → `0037-46.01` | `result.artifact-gc@v1` |
| `result.candidate-budget-report`<br>Candidate budget PASS/FAIL/INCONCLUSIVE report | `0038-13` | → `0037-46.01` | `result.candidate-budget@v1` |
| `result.candidate-promotion`<br>Candidate promotion result | `0038-13` | → `0037-46.01` | `result.candidate-promotion@v1` |
| `result.legacy-runner-transaction`<br>Structured transaction result | `0038-05` | → `0037-46.01` | `result.transaction@v1` |
| `result.legacy-scope-planner`<br>PARALLEL/SERIALIZE/BLOCK/INCOMPLETE scope verdict | `0038-21` | → `0037-46.01` | `result.scope-verdict@v1` |
| `result.legacy-task-doctor-report`<br>Read-only backlog/claim/REF diagnosis | `0038-06` | → `0037-46.01` | `result.doctor-report@v1` |
| `result.legacy-task-editor`<br>Bookkeeping planning/promotion result | `0038-05.02` | → `0037-46.01` | `result.bookkeeping@v1` |
| `result.task-validation-report`<br>Validation evaluation report | `0038-08` | → `0037-46.01` | `result.validation-report@v1` |
| `result.task-validation-run`<br>Immutable validation run record | `0038-08` | → `0037-46.01` | `result.validation-run@v1` |

### Schemas — `schema` (22)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `schema.agent-workflow-bootstrap`<br>Agent bootstrap/protocol-epoch selector | `0037-37` | → `0037-46.01` | `contract.agent-workflow-bootstrap@v1` |
| `schema.artifact-quarantine`<br>Quarantine record for partial/failed attempts | `0038-11` | → `0037-46.01` | `contract.artifact-quarantine@v1` |
| `schema.candidate-budget`<br>Candidate output/diff/realism budget contract | `0038-13` | → `0037-46.01` | `contract.candidate-budget@v1` |
| `schema.candidate-manifest`<br>Per-attempt candidate manifest | `0038-13` | → `0037-46.01` | `contract.candidate-manifest@v1` |
| `schema.candidate-promotion-pointer`<br>Atomic candidate promotion pointer | `0038-13` | → `0037-46.01` | `contract.promotion-pointer@v1` |
| `schema.cutover-control-ledger`<br>Cutover control ledger | `0037-37` | → `0037-46.01` | `contract.cutover-ledger@v1` |
| `schema.environment-doctor-requirements`<br>Environment requirement/profile/observation inputs | `0038-23` | → `0037-46.01` | `contract.environment-requirements@v1` |
| `schema.issue-regeneration-dag`<br>Authoritative derived-artifact regeneration DAG | `0037-37` | → `0037-46.01` | `contract.regeneration-dag@v1` |
| `schema.legacy-runner-current-pointer`<br>Atomic `current.json` attempt pointer | `0038-10` | → `0037-46.01` | `contract.result-pointer@v1` |
| `schema.legacy-runner-lock`<br>Singleton slot lock record | `0038-05` | → `0037-46.01` | `contract.queue-claim@v1` |
| `schema.legacy-runner-transaction`<br>Legacy transaction request manifest | `0038-05` | → `0037-46.01` | `contract.runner-request@v1` |
| `schema.legacy-scope-planner-request`<br>Scope-collision planning request | `0038-21` | → `0037-46.01` | `contract.scope-request@v1` |
| `schema.legacy-task-editor-candidate`<br>Content-addressed bookkeeping candidate | `0038-05.02` | → `0037-46.01` | `contract.bookkeeping-candidate@v1` |
| `schema.legacy-task-editor-operation`<br>Declarative bookkeeping operation set | `0038-05.02` | → `0037-46.01` | `contract.bookkeeping-operation@v1` |
| `schema.prepared-environment`<br>Digest-bound prepared-environment record | `0038-23` | → `0037-46.01` | `contract.prepared-environment@v1` |
| `schema.prepared-environment-cache`<br>Verified prepared-environment cache | `0038-23` | → `0037-46.01` | `contract.prepared-environment-cache@v1` |
| `schema.runner-request-v1`<br>Frozen `runner-request@v1` request contract | `0037-37` | → `0037-46.01` | `contract.runner-request-schema@v1` |
| `schema.runner-result-v1`<br>Frozen `runner-result@v1` result contract | `0037-37` | → `0037-46.01` | `contract.runner-result-schema@v1` |
| `schema.task-context-capsule`<br>Bounded resume capsule | `0038-07` | → `0037-46.01` | `contract.context-capsule@v1` |
| `schema.task-evidence-pack`<br>Content-addressed task evidence pack | `0038-12` | → `0037-46.01` | `contract.evidence-pack@v1` |
| `schema.task-validation-profile`<br>Immutable validation-profile contract | `0038-08` | → `0037-46.01` | `contract.validation-profile@v1` |
| `schema.typed-claim`<br>Typed claim record | `0038-21` | → `0037-46.01` | `contract.typed-claim@v1` |

### Scopes — `scope` (5)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `scope.forbidden-branch-writes`<br>Structural refusal of `DONE.md` writes and checkpoint-crossing merges on the legacy bridge | `0038-20` | → `0037-46.01` | `scope.authority-boundary@v1` |
| `scope.planner.collision-preflight`<br>Read-only, fail-closed write-scope collision planner | `0038-21` | → `0037-46.01` | `scope.preflight@v1` |
| `scope.policy-provenance`<br>Integration-policy provenance classification for merge candidates | `0044-01` | → `0037-46.01` | `scope.policy-provenance@v1` |
| `scope.run-attempt-roots`<br>Per-attempt isolated roots (`.candidates/`, `.partial/`) under `output/logs/<task-id>/<request-id>/` | `0038-13` | → `0037-46.01` | `scope.isolated-attempt-root@v1` |
| `scope.write-scope-declaration`<br>Claim-declared intended write scope and runner scope | `0038-21` | → `0037-46.01` | `scope.claim-declaration@v1` |

### Validation — `validation` (6)

| Primitive | Owner | Disposition | Target / trigger |
|---|---|---|---|
| `validation.automation-safety`<br>`automation_safety.py` + policy — static safety gate over tracked automation | `0038-03` | → `0037-46.01` | `validate.automation-safety@v1` |
| `validation.chore-tool-inventory`<br>`chore_tool_inventory.py` — lifecycle-contract classification of tracked mutating chore tools | `0038-14` | → `0037-46.01` | `validate.chore-inventory@v1` |
| `validation.handoff-manifest`<br>`legacy_handoff_manifest.py` — checker proving this manifest's totality and single-authority properties | `0038-16.01` | → `0037-46.01` | `validate.handoff-manifest@v1` |
| `validation.task-validation`<br>`task_validation.py` — profile-driven evaluation of an immutable validation run | `0038-08` | → `0037-46.01` | `validate.run-profile@v1` |
| `validation.transaction-fixtures`<br>`test_runner_transaction.py` — hermetic Git and fault-injection fixture suite | `0038-05` | → `0037-46.01` | `validate.transaction-fixtures@v1` |
| `validation.workflow-validator`<br>`validate_workflow_validator.py` / `workflow_lifecycle.py` — lifecycle vocabulary consistency | `0038-14` | → `0037-46.01` | `validate.workflow-lifecycle@v1` |

## Carried open item

Primitive `validation.automation-safety` records an unresolved **TK-2 confirmation** inherited
from Task `0038-27` and reaffirmed by the `0038-22` integrator reconciliation: the
`automation_safety_policy.json` dispositions for `_src/tools/sync_to_devel.sh` and
`_src/tools/provision_tmp_worktree.sh` were re-pointed to `owner_task: 0038-16` as the durable
custodian, because the disposition schema requires a *live* owner Task. This manifest records the
open confirmation; it does not resolve it, and resolving it is not this Subtask's authority.

## Amending this manifest

Amend the JSON, then re-run the checker to a zero-finding verdict:

```bash
python3 _src/tools/legacy_handoff_manifest.py --check
python3 -m unittest _src.tests.test_legacy_handoff_manifest
```

Adding a legacy mechanism to `tools.md` without adding a primitive here fails rule `LHM074`;
two primitives claiming one capability fail `LHM048`/`LHM061`.

## Related

- [`runner-transaction.md`](runner-transaction.md) — the legacy transaction bridge itself
- [`branch-merge-actions.md`](branch-merge-actions.md) — the `0038-19` typed branch/merge contract
  whose section 10 forward-mapping table this manifest generalizes
- [`issue-cutover-rollback.md`](issue-cutover-rollback.md) — cutover and rollback ledger
- [`branch-workflow.md`](branch-workflow.md), [`task-acceptance.md`](task-acceptance.md) — the
  authority boundaries this manifest preserves unchanged

