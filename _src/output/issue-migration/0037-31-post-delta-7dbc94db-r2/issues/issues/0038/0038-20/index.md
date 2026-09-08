---
schema_version: "1.0"
id: "0038-20"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-02"
  - "0038-18"
  - "0038-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1878"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-20:0038-19, 0038-20:0038-18, 0038-20:0038-02 Implement the branch/merge typed actions in the legacy transaction runner as a retirement-safe bridge. REF: `2d510d08ed0cc86964cec4a9be99fe719edffadf`

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-talax (0038-20-Commit)`). Abgenommene Baseline `2d510d08ed0cc86964cec4a9be99fe719edffadf`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 7 Fehlschläge/51 bestanden am eigenen REF, ererbt von der damals ungefixten geteilten Abhängigkeit (0038-10-Fix landete erst 2026-08-25); dieselben 7 Tests gegen aktuellen main erneut gefahren: 7/7 grün.
  - **Closure (2026-08-20):** Added `BranchMergeTransaction`/`branch-merge-v1` (`base-branch`, `merge-prereqs`) to `_src/tools/runner_transaction.py`, implementing the `0038-19` contract (`docs/pipeline/branch-merge-actions.md`) on the `0038-02`/`0038-18` machinery: sequential non-octopus 2-parent merges in a disposable detached worktree, CAS publication only onto the item's own not-yet-integrated branch, structural rejection of any Task→Feature/Feature→`main`/`integrate-checkpoint` attempt (`BMA-AUTHORITY-VIOLATION`/`BMA-ACTION-UNSUPPORTED`), append-only same-owner-token claim-record auto-union vs. `BMA-CLAIM-FOREIGN-TOKEN` fail-closed on a genuine foreign claim, and `recover_transaction` support for `branch-published`/`branch-unpublished` interrupted states. Salvaged and completed substantial uncommitted work already present in the worktree from an orphaned prior attempt (no live claim existed); found it sound against the contract and added the missing test coverage and documentation rather than rewriting it. Added `BranchMergeTransactionTests` (12 tests, own real-Git fixture) to `_src/tools/test_runner_transaction.py` covering every DoD-listed category plus `integrate-checkpoint` non-implementation. Documented the profile in `docs/pipeline/runner-transaction.md` and cataloged it in `docs/pipeline/tools.md`. Validation: `py_compile` clean; `BranchMergeTransactionTests` 12/12 pass; full-file suite (58 tests) shows 5 pre-existing failures/errors confirmed unrelated to this Task (reproduce identically with `runner_transaction.py` stashed back to its pre-Task state — a macOS `/tmp`→`/var/folders` symlink interaction with `_open_directory_nofollow` in the unrelated `RunnerTransactionTests` fixtures). Claim: `TODO-seven-talax-0038-20-20260820T180328Z.md`.

## Acceptance criteria

- **AC-001** Add `base-branch` and `merge-prereqs` to `_src/tools/runner_transaction.py` per the `0038-19` contract, reusing the `0038-18` validation/commit profile and the `0038-02` journal/lock/signal/resume/rollback guarantees for 2-parent merge commits. Enforce Subtask→Task authority for sandboxed manifests and reject Task→Feature, Feature→`main`, acceptance-record, and Feature `[u]` verdict actions. Auto-union conflicting claim records append-only without rewriting a foreign `owner_token`
- **AC-002** record each merged source branch/tip in claim and journal
- **AC-003** fail closed when expected parent base, declared source tips, owner token, or read/write scope differs from the request contract. Document in `docs/pipeline/runner-transaction.md`

## Definition of Done

Hermetic tests in `_src/tools/test_runner_transaction.py` cover base-off-parent, single and multiple prerequisite merges, claim-record union on conflict, 2-parent merge journaling/rollback and crash-resume, sandboxed Task→Feature rejection, undeclared-source/stale-tip rejection, and preservation of unrelated bytes; focused tests plus path-limited substantive and separate REF bookkeeping commits pass through the runner.
