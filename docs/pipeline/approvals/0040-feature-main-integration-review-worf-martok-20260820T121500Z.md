# Feature 0040 — independent corrected-candidate integration review

## Decision and pinned baseline

- **Decision:** `accepted`
- **Reviewer:** `agent:worf-integrator-martok-20260820t121500z:0040-integration:20260820T121500Z`
- **Role / capability:** privileged independent Reviewer/Integrator
- **Authority reference:** current-user assignment of this exact Feature `0040` review and conditional integration, 2026-08-20; verbatim provenance in section 8
- **Review candidate:** `8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb` (`refs/heads/0040`)
- **Candidate tree:** `af2f60eeeac2350423a1c098ac4309e49bee5af6`
- **Target baseline:** `main` at `c0a274e66fd36516e748a0d309bcd35fa5b7e561`
- **Target-policy merge:** `c560fbc2fdc5bf39811a545894560f648364f49a`; its second parent is exactly the target baseline
- **Corrective substantive commit:** `74dbdac90b421128352bfc8afc7bb4b580a4c054`
- **Corrective bookkeeping commit:** `8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb`
- **Reviewed at:** `2026-08-20T12:15:00Z`

**Independence.** This session is explicitly assigned as privileged Reviewer/Integrator and is not identified in the Feature `0040` history as a claim owner, principal implementer, decisive technical author, or sole validation producer. No waiver is invoked for this review.

## 1. Contract, review batch, and policy provenance

The exact current review contract is the corrective Feature `0040` entry and Task
`0040-11` in `TODO.md`; its SHA-256 is
`6c8e9834f3cf5c23d9b4034b231b42781746f9f4d7dc2414990f2625970b15ae`.
Its required outcome is a target-policy reconciliation, English current normative
Feature documentation with all three capability classes, preserved append-only
history, and a fresh independent privileged review before Feature-to-`main`
integration.

The previous independent review at commit
`ebc6c018afe571bf847ddbaa22343e89da937fe4` is preserved and was re-read directly
from that commit. Its sole material finding was the former candidate's stale
normative two-class model against current target policy.

`main` is an ancestor of the corrected candidate. The policy merge has pinned
`main` as its exact second parent, and the changes introduced from that parent are
therefore target-origin policy only. No policy from a third branch was pulled into
the candidate. The target policy governs this integration and defines exactly
three capability classes: `sandboxed-grunt`, `unprivileged`, and `privileged`.
`unprivileged` retains direct execution but has no acceptance or integration
authority.

`docs/pipeline/process-roles.md` was inspected in full for its authority mapping:
it is English; declares the three classes; keeps Management outside the agent role
model; limits integration/acceptance authority to an explicitly assigned
privileged Integrator; and preserves the separation between execution capability
and authority. The only detected German word is inside an unchanged historical
source filename. Searches found no current normative two-class assertion in
`AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `process-roles.md`,
`branch-workflow.md`, or `task-acceptance.md`. Historical two-class statements
remain explicitly labelled superseded evidence.

## 2. Prerequisite-acceptance closure

The exact Feature closure edge is `0040:0039-01`. The candidate's legacy
`TODO.md` projection still renders `0039-01` as `[u]`, but that projection is not
accepted as decisive. The canonical Task branch and canonical Feature branch were
examined directly:

| Required evidence | Result |
| --- | --- |
| Current `0039-01` acceptance review | `5c75893795ab7d8a7edd1a8583c26f627ace3662` exists and is reachable from the acceptance bookkeeping `f268f5610d18b09da15bb1edcd12a78664126529` |
| Current acceptance record | `refs/heads/0039-01:TODO.md` preserves the malformed historical record's additive invalidation and a later current `Acceptance: ✓` whose Review REF is exactly `5c75893795ab7d8a7edd1a8583c26f627ace3662` |
| Upward Task integration | `f268f5610d18b09da15bb1edcd12a78664126529` is reachable from canonical Feature branch `0039` at `cdeb9a1324370ed1de7a22af527600d1e78e522b` |
| Authority and review content | The independently authored review record names the current-user assignment, the accepted `0039-04` boundary, the corrected work product, contract/manifest/prerequisite digests, and focused passing validation |

`cdeb9a1324370ed1de7a22af527600d1e78e522b` is not an ancestor of the pinned
`main`/`0040` candidate. That does **not** invalidate the closure gate: this is a
Feature prerequisite, not an upward-merge edge. The accepted Task has been
integrated into its canonical Feature branch as required by the branch workflow.
The `DONE.md` `0040` record independently states this relation. The static
legacy doctor cannot resolve cross-branch accepted Task state and consequently
reports `LTD-TERMINAL-UNSATISFIED-PREREQ` for the stale projection; it is not a
material closure failure after the direct reachability and authority review above.

The review stops at this current, reachable, non-invalidated acceptance boundary;
no non-accepted prerequisite remains in the Feature `0040` closure batch.

## 3. Checkpoints, authority, and historical evidence

- All ten historical Feature tasks have terminal dispositions. The only mandatory
  checkpoints are `0040-05` and `0040-09`.
- `0040-05` retains the current-user-authorized acceptance at review REF
  `063a85998f90197b698b9672e816ffaba7e5fb15`. It was neither changed nor
  re-issued.
- The old `0040-09` aggregate acceptance is historical and not relied on as
  current acceptance for the corrected candidate. This review is the expressly
  required fresh independent integration review after the material target-policy
  merge and English role-model correction.
- The historical `[u]` verdicts, management ratification `DEC-0040-007`, and
  finite waiver endpoint `DEC-0040-008` remain append-only. The ratification and
  waiver records were inspected; neither is invented or altered here.
- The corrective candidate creates no external effect, publication, SSH/remote
  change, or `0019` change. `0019-10` remains outside this review and was not
  reviewed or integrated.

## 4. Work-product manifest and scope

The deterministic manifest is the complete Git comparison
`c0a274e66fd36516e748a0d309bcd35fa5b7e561..8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb`
rendered by `git diff --name-status`; its SHA-256 is
`2a09426a0da1a7387d96e212c36576cd7b6798bf2fe2a293101cfcbf03eb1730`.
The candidate tree hash above binds the exact file bytes. The 43 changed paths
are confined to Feature history/evidence, Feature policy/process documentation,
the target-policy merge, legacy-task doctor support, and the earlier safety
repair:

```text
AGENTS.md
DONE.md
TODO-worf-k-ehleyr-0040-repair-20260820T001000Z-5c2bc79f.md
TODO.md
_src/run-loop.sh
_src/tools/automation_safety_policy.json
_src/tools/legacy_task_doctor.py
_src/tools/process_doc_doctor.py
docs/dossiers/0040-05-cross-item-scope-review.md
docs/dossiers/0040-08-0038-03-retrospective.md
docs/dossiers/0040-09-integration-package.md
docs/dossiers/0040-10-automation-safety-scope-and-dispositions.md
docs/dossiers/0040-main-integration-repair-20260820T001000Z.md
docs/dossiers/0040-management-closure-provenance.md
docs/dossiers/re-intake-evidence-traceability-and-roles.md
docs/pipeline/README.md
docs/pipeline/approvals/0040-05-review.md
docs/pipeline/approvals/0040-09-integration-rereview-20260819T220406Z.md
docs/pipeline/approvals/0040-09-integration-review-20260819.md
docs/pipeline/approvals/0040-09-integration-review-picard-20260820T080227Z.md
docs/pipeline/approvals/0040-09-provenance-correction-20260819T220406Z.md
docs/pipeline/approvals/0040-feature-closure-20260820T090000Z.md
docs/pipeline/automation-safety.md
docs/pipeline/decision-record.md
docs/pipeline/legacy-task-doctor.md
docs/pipeline/process-roles.md
docs/pipeline/tools.md
logs/validate-automation-safety/0040-10/consistency-checks.txt
logs/validate-automation-safety/0040-10/final-full-scan.json
logs/validate-automation-safety/0040-10/final-policy.json
logs/validate-automation-safety/0040-10/final-run-loop.json
logs/validate-automation-safety/0040-10/final-worktree-full-scan.json
logs/validate-automation-safety/0040-10/focused-tests.txt
logs/validate-automation-safety/0040-10/interim-run-loop.json
logs/validate-automation-safety/0040-10/policy-tests.txt
logs/validate-automation-safety/0040-10/post-stage-full-scan.json
logs/validate-automation-safety/0040-10/pre-change-run-loop.json
logs/validate-automation-safety/0040-10/pre-remediation-baseline-provisioners.json
logs/validate-automation-safety/0040-10/remediation-focused-policy.json
logs/validate-automation-safety/0040-10/remediation-run-loop-unpolicyed.json
logs/validate-automation-safety/0040-10/remediation_consistency_check.py
logs/validate-automation-safety/0040-10/run-loop-policy.json
logs/validate-automation-safety/0040-10/targeted-scanner-tests.txt
logs/validate-automation-safety/0040-10/validation-summary.md
```

No undeclared candidate worktree edits were present before this review evidence
was created.

## 5. Independent validation

| Command / inspection | Result |
| --- | --- |
| `python3 _src/tools/process_doc_doctor.py` | PASS: 0 errors; 33 pre-existing advisory warnings |
| Authority-document three-class and legacy-two-class searches | PASS: all three current classes present; no current normative two-class assertion in corrected scope |
| English/document inspection of `docs/pipeline/process-roles.md` | PASS; only unchanged historical filename contains a German word |
| Direct `0039-01` object, acceptance, branch-integration, and review-evidence reachability checks | PASS |
| `git merge-base --is-ancestor main candidate` and exact merge-parent check | PASS |
| `git diff --check main..candidate` | PASS |
| `git fsck --no-reflogs --no-dangling` | PASS |
| `python3 -m unittest _src.tests.test_automation_safety` | 120/121 pass; the sole failure is known `AUTO010` for `_src/tools/runner_transaction.py` |
| Equality of `runner_transaction.py`, its test, and `automation_safety.py` between target and candidate | PASS; the one unit-test failure is target-identical and remains the documented minor `F-0040-09-004` owned by Feature `0038` |
| Equality of safety inputs and `_src/validate.py` between accepted pre-repair candidate `d5a65d3a770e7996432f18b5c37cf25c180a3c89` and this candidate | PASS; the historical full live safety scan therefore remains applicable to unchanged safety inputs |

A fresh full and path-scoped `automation_safety.py` invocation was attempted in
this isolated worktree but was killed by the host (`Killed: 9`) before producing a
result. It is not reported as a pass. It is not a Feature `0040` blocker because
the safety inputs and gate are byte-identical to the accepted candidate with the
retained full-scan evidence, while the independently rerun policy, documentation,
closure, diff, and object-integrity checks pass. The target-identical unit failure
remains a non-`0040` minor finding and no new material finding was discovered.

The broad `legacy_task_doctor.py --json` output is non-passing (258 errors and 130
warnings) because of unrelated repository bootstrap/claim inventory findings. It
also cannot resolve the accepted cross-branch `0039-01` state described above.
It is recorded as context only; it was not used to claim a global pass.

## 6. Findings and disposition

- **`F-0040-09-004` — minor, carried, target-identical.** The unit-test failure
  concerning `AUTO010` in `_src/tools/runner_transaction.py` is outside Feature
  `0040`, byte-identical in the integration target, and remains owned by Feature
  `0038`. It does not contradict the corrected-candidate contract.
- **Validation host limitation — observation.** Standalone automation-safety
  invocations were killed before result production. The retained historical live
  result remains attributable because the scanned inputs are unchanged; future
  host diagnosis belongs outside this Feature review.

No critical or major finding remains. The prior rejection's policy incompatibility
is corrected, the closure prerequisite is valid, and no current authority or
English-scope contradiction was found.

## 7. Final verdict

**Accepted.** The corrected Feature `0040` candidate satisfies its current
reconciliation contract and the required fresh independent integration review.
It is safe to integrate this exact reviewed descendant into pinned `main`, then
perform the separate path-isolated closure bookkeeping: reconcile the two terminal
Feature-0040 claim records, remove the corrective reopening from `TODO.md`, and
add an append-only re-integration/closure record to `DONE.md`.

This acceptance does not approve publication, external effects, the unfinished
Feature `0019` checkpoint, or any unrelated Task. It does not rewrite historical
acceptance, closure, decision, or rejection evidence.

## 8. User-prompt provenance (verbatim)

```text
You are **Worf Integrator Martok 20260820T121500Z**, a privileged Reviewer/Integrator subagent. Be concise in your final report.

**Capability class:** `privileged` (direct execution permitted; do not use, create, or wait for `run.sh`).

**Exact assignment:** Independently review the repaired Feature `0040` candidate and, only if all current gates pass, integrate `0040` into `main` and perform the authoritative Feature closure bookkeeping. This exact integration-review assignment is authorized by the user: “A privileged integrator subagent shall be started to review & merge back the features that are ready.”

**Worktree / branches:** Create and use an isolated worktree at `/Users/tobias.anton/devel/autodocs/.worktrees/0040-integration-worf-martok-20260820T121500Z`, checked out from canonical candidate branch `0040` at `8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb`. Integration target is `main` at `c0a274e66fd36516e748a0d309bcd35fa5b7e561`. Do not touch the canonical dirty checkout or `/.../.worktrees/0040`.

**Write scope:** isolated-worktree changes only, limited to `0040` integration/review/acceptance evidence, exact authoritative backlog/closure bookkeeping required by an approved integration, claim files, and any merge-conflict resolution strictly necessary to carry the approved candidate into `main`. New documentation must be English. Preserve exact user-authored quotes/provenance verbatim; do not translate historical provenance.

**Required review baseline/context:**
- Prior rejected review: `docs/pipeline/approvals/0040-feature-main-integration-review-worf-picard-20260820T000400Z.md`, commit `ebc6c018afe571bf847ddbaa22343e89da937fe4`. Its material finding was stale two-class policy versus target’s three-class policy.
- Corrective implementation: target-policy merge `c560fbc2fdc5bf39811a545894560f648364f49a`, substantive `74dbdac90b421128352bfc8afc7bb4b580a4c054`, bookkeeping `8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb`.
- The corrective docs and claim state historical acceptance is stale for this changed candidate, so perform a fresh independent review. Do not self-assume acceptance from prior records.
- `0040` has closure prerequisite `0040:0039-01`. There is an apparent projection conflict: `main`/the repaired candidate’s `TODO.md` shows an older `[u]` record, while canonical branch `0039` includes `0039-01` as `[x]` with current `Acceptance: ✓`, integrated at `cdeb9a1324370ed1de7a22af527600d1e78e522b`. Compute the actual prerequisite-acceptance closure, validate ancestry/reachability/authority, and decide from current authoritative evidence. Do not treat either statement alone as decisive. If it is stale, malformed, invalidated, or genuinely ambiguous, preserve history and issue a new append-only `inconclusive`/`[u]` verdict rather than integrating.
- The target branch’s policy governs. Confirm that only target-branch policy was pulled into the candidate, and that the current three-capability-class authority remains intact after any merge.
- `0019` is not ready: its `0019-10` public-website publication/checkpoint gate remains separate and must not be reviewed/integrated here.

**Review procedure:** Read `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `TODO.md`, `DONE.md`, `docs/pipeline/branch-workflow.md`, `docs/pipeline/task-acceptance.md`, the full 0040 contract/decision/evidence/review history, relevant claims, and exact branches. Create an immutable review claim before mutations. Review bottom-up and independently rerun focused documentation/process/graph/ancestry checks on the isolated exact candidate. Verify all acceptance/checkpoint/closure requirements, policy provenance, scope, and English requirements. Record a complete English review package and a separate bookkeeping commit only if accepted.

**If accepted:** merge `0040` into `main` with a non-force, path-safe operation; retain/resolve claims according to policy; update authoritative `TODO.md`/`DONE.md` only as the closure procedure requires; commit review evidence before acceptance/closure bookkeeping; validate exact main tip/reachability and working-tree scope. Never push or publish any website content.

**If not accepted/inconclusive:** do not merge to `main`, do not move anything to `DONE.md`, do not repair substantive work yourself. Record an append-only English review verdict and give Worf a precise escalation/corrective scope.

**You must not:** use or wait for `run.sh`; alter SSH/remotes; push/force-push; publish external content; modify Feature `0019`; delete/rewrite rejected/closure/decision history; accept on behalf of the implementation owner without completing an independent review. No claim of success unless commit/review validation proves it.

**Provenance:** user-authored material authorization text to retain verbatim where required:

"ok then go ahead. use the correct key next time. Reopen the completed task/branch and let subagents perform the corrective action(s). After these things have been resolved, check again whether the 0039-01 blocker is resolved. if so, proceed to integration. A privileged integrator subagent shall be started to review & merge back the features that are ready."

Report commits, review verdict, validation commands/results, whether `main` changed, remaining blockers, and any escalation.
```