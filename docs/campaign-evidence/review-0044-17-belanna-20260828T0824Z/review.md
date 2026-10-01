# Mandatory checkpoint review: 0044-17 (worktree lifecycle — deletion-capable tooling)

- **Reviewer:** belanna (privileged Integrator, Team Voyager)
- **AWARD:** `1787905461614-2213331b` (jean-luc, thread `0044-17`), confirmed operative by jean-luc's clarification `1787905534625-b1959491` ("`1787905407442-b5ec6ee9` was only the pre-AWARD pin refresh and did not itself authorize work"). Prior ACCEPT of jean-luc's OFFER, DECLINE of Data's broader exclusive OFFER over an unverified authority citation (later resolved: Data's scope converged with jean-luc's; see Coordination section).
- **Architect rationale (TODO.md `0044-17`):** "**Integration review: mandatory.** This mechanism deletes checkout directories. Independent review must falsify every safety gate and confirm that branches, tags, claims, dirty data, and foreign worktrees remain intact."

## Pins (independently remeasured)

| Item | Value |
|---|---|
| Candidate branch tip (as offered) | `integrate-0044-17-data-20260828t0820z@4dad57dd437a8e2181550927ece60b778620ae28` — independently confirmed via `git rev-parse`/`git log`, not trusted from the message (Data's first pin citation was a mistyped SHA, self-corrected) |
| Target at AWARD time | `main@16664ebc8622c5bd035cee9facdce9bbe2e8c7b2` |
| Target at review time | `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81` — **drifted** during review |
| Drift cause | Unrelated `0044-12` work (11 commits, 10 files: 4 claim files, `TODO.md`, `check_policy_provenance.py`+test, a `belanna-integration-review` evidence doc, `docs/pipeline/branch-workflow.md`, `docs/pipeline/tools.md`). Zero path overlap with the `0044-17` candidate's 15-file scope. |
| Ancestor check | `16664ebc8` **is** an ancestor of `c27b8001f` (confirmed via `merge-base --is-ancestor`) — ff-relationship intact, target not invalidated |
| Merge-base(candidate, current main) | exactly `16664ebc8622c5bd035cee9facdce9bbe2e8c7b2` — confirms the candidate simply predates the disjoint drift, nothing more |
| Implementation REF | `635b9c810dc9fc2ed602116dbd13fba39c2b634d` |

Per the AWARD's explicit pre-authorization ("Conditional integration is authorized only after PASS, exact target or **nonmaterial reconciled drift**...") this is treated as nonmaterial drift: reconciled by cutting a fresh integration branch from current main and `--no-ff` merging the reviewed candidate onto it (below), rather than stopping for a fresh AWARD.

## Reconciliation

- Worktree/branch 1 (candidate-as-offered review): `integrate-0044-17-belanna-20260828T0824Z` at `.worktrees/integrate-0044-17-belanna-20260828T0824Z`, cut from `4dad57dd437a8e2181550927ece60b778620ae28` directly — used for the initial diff/test/governance review against the merge-base.
- Worktree/branch 2 (reconciliation): `integrate-0044-17-belanna-r2-20260828T0845Z` at `.worktrees/integrate-0044-17-belanna-r2-20260828T0845Z`, cut from current `main@c27b8001f`, then `git merge --no-ff 4dad57dd437a...` — **clean, zero conflicts** (git auto-merged `TODO.md`, `docs/pipeline/branch-workflow.md`, `docs/pipeline/tools.md`; the disjoint `0044-12` drift touched unrelated line ranges).
- `git diff --stat main..HEAD` on the reconciliation branch: **exactly the same 15 files** as the original candidate diff against its merge-base — no scope drift introduced by reconciliation.
- `git merge-base --is-ancestor main HEAD` on the reconciliation branch: **true** — ff-only from the root will succeed.

## Scope (15 files, independently reverified via `git diff --stat`)

`AGENTS.md`, `TODO-data-0044-17-worktree-lifecycle-20260828.md` (new), `TODO.md`, `_src/tests/fixtures/legacy_task_doctor/cases.json`, `_src/tests/test_legacy_task_doctor.py`, `_src/tests/test_publish_scripts.py`, `_src/tools/automation_safety_policy.json`, `_src/tools/legacy_task_doctor.py`, `_src/tools/legacy_task_editor.py`, `_src/tools/provision_tmp_worktree.sh`, `_src/tools/publish_public_site.sh`, `_src/tools/test_provision_tmp_worktree.py`, `docs/pipeline/branch-workflow.md`, `docs/pipeline/legacy-task-doctor.md`, `docs/pipeline/tools.md`.

## Governance-artifact placement (raised and resolved)

The candidate amends `AGENTS.md` and `docs/pipeline/branch-workflow.md` — both explicitly listed governance artifacts under `DEC-0044-012` ("changes to governance processes are always made on `main`"). Checked for a conflict: `AGENTS.md` at current `main` is **byte-identical** to `AGENTS.md` at the merge-base (`git diff 16664ebc8:AGENTS.md c27b8001f:AGENTS.md` — empty) — no concurrent divergent edit occurred while this sat on a branch.

Found direct, on-point precedent in this same repository's own history: Task `0044-14` (also a mandatory-checkpoint Task, also touching `AGENTS.md`/`docs/pipeline/branch-workflow.md`/`docs/pipeline/tools.md`) explicitly recorded: *"OFFEN, nicht Teil dieses `[x]`: AGENTS.md, docs/pipeline/branch-workflow.md, docs/pipeline/tools.md sind Governance-Artefakte nach DEC-0044-012 und muessen von der Projektleitung nach main gebracht werden (Verfahren DEC-0044-015); dieser unprivilegierte Implementierer hat keinen Ref bewegt und den Integrationsknoten nicht ueberschritten."* — and was then integrated to `main` exactly this way: implementer prepares on a branch without self-merging, a privileged Integrator reviews the checkpoint and performs the root merge (`0044-14`'s own record: "Integration nach main: 7e12f877d (nach DEC-0044-015 aus dem Root, harter Preflight und Hygienepruefung ok: true vorab)"). This is the established, precedent-confirmed mechanism for exactly this class of Task, not a violation: the governance text becomes `main`-current at the moment of this same privileged review-and-merge, and the unprivileged implementer (Data) correctly did not self-merge or cross the checkpoint. Not a blocking finding.

## Independent validation

Four suites cited by Data's evidence, independently rerun **twice** — once against the candidate as offered, once against the reconciled (main+candidate) state — both times matching exactly:

| Suite | Claimed | Independently observed (both runs) |
|---|---|---|
| `_src.tools.test_provision_tmp_worktree` | 32/32 | 32/32 OK |
| `_src.tests.test_legacy_task_doctor` | 59/59 | 59/59 OK |
| `_src.tests.test_legacy_task_editor` | 54/54 | 54/54 OK |
| `_src.tests.test_publish_scripts` | 12/12 | 12/12 OK |

`bash -n _src/tools/provision_tmp_worktree.sh` — OK. `py_compile` on all changed `.py` files — OK. `git diff --check` on the full candidate range — clean.

### Falsifying every safety gate (Architect's explicit demand)

Read `_src/tools/test_provision_tmp_worktree.py`'s new `AcceptedLifecycleTests` class in full (105 lines) and cross-referenced every refusal branch in `remove_completed_worktree()`/`finalize_accepted_claims()`/`reap_sweep()` against a named adversarial test:

| Safety gate | Test |
|---|---|
| Dirty/uncommitted tree refused | `test_remove_completed_refuses_dirty_worktree` |
| Active exact-item `TODO-*` claim refused (not yet finalized) | `test_remove_completed_refuses_active_exact_item_claim` |
| Locked worktree refused | `test_remove_completed_refuses_locked_worktree` |
| Live process cwd refused | `test_remove_completed_refuses_live_process_cwd` (spawns a real `sleep 30` subprocess inside the target, confirms refusal, confirms the worktree survives) |
| Rename collision refused before any rename (atomicity) | `test_finalize_collision_refuses_before_any_rename` |
| Finalize without Acceptance refused | `test_finalize_refuses_without_acceptance` |
| Exact-item-only rename (unrelated claim untouched) | `test_finalize_renames_only_exact_item_claim_byte_identically` |
| Successful removal retains the branch | `test_remove_completed_removes_only_worktree_and_retains_branch` |
| Fallback keeps: unmerged-but-accepted, dirty, locked, unaccepted `DONE-*`, historical prerequisite claim, outside-root, just-requested-target, claimless-without-terminal-evidence | 8 distinct named `ReapSweepTests` cases, each asserting the worktree/branch survives |
| Fallback reaps only clean+accepted+unlocked+`main`-reachable+process-free | `test_reaps_accepted_clean_main_reachable_worktree` |
| Concurrent different items don't collide | `test_concurrent_different_items_do_not_collide` |

This satisfies the Architect's rationale: every refusal branch named in the script has a corresponding named adversarial test, not just a happy-path pass. No gap comparable to the AE-4 pattern found in `0037-11.02` was found here — the test author already applied that discipline.

### Governance/hygiene checks (full-repo, three-way isolation)

- `process_doc_doctor.py`: main-only = `{documents: 156, errors: 1, findings: 33}`; merged (main+candidate) = **identical**, `{documents: 156, errors: 1, findings: 33}`. Zero delta.
- `legacy_task_doctor.py`: main-only = 961 findings (964 raw, 3 collapse in dedup by missing `line`); merged = 887 findings. Per-rule diff: the **only** rule with a nonzero count delta is `LTD-CLAIM-TERMINAL-RETAINED`: 74 → 0. This rule is deliberately retired by this candidate (obsolete under the new TODO-stays-TODO-until-Acceptance design; `docs/pipeline/legacy-task-doctor.md` and the fixture `cases.json` are updated to match). Zero new finding types, zero other rule-count changes — the entire delta is the intended, disclosed rule retirement.
- `automation_safety.py` (full repo, both runs took >2 minutes — matches Data's own disclosed observation that the full scan is slow): main-only = `FAIL {advisory: 58, disposed_critical: 13, findings: 84, policy_errors: 40, unresolved_critical: 11}`; merged = `FAIL {advisory: 60, disposed_critical: 20, findings: 88, policy_errors: 30, unresolved_critical: 6}`. **Net improvement** (policy_errors −10, unresolved_critical −5): manually inspected the `automation_safety_policy.json` diff and confirmed the seven pre-existing `AUTO001` dispositions on `provision_tmp_worktree.sh` are re-pointed from a now-terminal `owner_task: 0038-16` to the still-open `0044-08` with correct updated `line`/`evidence_sha256` for each moved symbol, plus two new, narratively consistent dispositions for the two new functions (`finalize_accepted_claims`, `remove_completed_worktree`). The improvement is consistent with this candidate incidentally repairing a disposition-staleness regression that current `main` had independently accumulated (0038-16 going terminal) — not evidence of anything hidden.
- Both `check_integration_hygiene.py` runs (candidate-as-offered, and the exact reconciliation merge commit `bd55c3bc76b29da209a45547b963584f04f95c05` about to be merged): **PASS**, exit 0.

## Verdict: **PASS**

Every named safety gate in the deletion-capable tooling has independent, reproduced, fault-injection-style test evidence. No regression in any governance/hygiene dimension checked; one disclosed, fully-isolated, intentional rule retirement (74 findings) and an incidental repair of stale AUTO001 dispositions. Drift was disjoint and nonmaterial, reconciled cleanly with an exact 15-file scope preserved. Governance-artifact placement matches established, precedent-confirmed practice in this repository (`0044-14`). Proceeding to root ff-only merge per the AWARD.

## Scope boundaries observed

No Task Acceptance recorded. No `TODO→DONE` claim finalization performed. No cleanup/removal of any existing worktree. No Feature/DONE move. `memory_append` not called. No branch/tag deletion. No external effects beyond the authorized root merge below.
