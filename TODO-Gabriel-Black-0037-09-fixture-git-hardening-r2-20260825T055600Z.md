# Claim: 0037-09-fixture-git-hardening-r2

- owner_token: agent:gabriel-black-20260825t055600z:0037-09-fixture-git-hardening-r2:20260825T055600Z
- identity: Gabriel-Black-20260825T055600Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer, Team Discovery
- item: user-directed repair `0037-09-fixture-git-hardening-r2` (not a backlog Task; do not change `TODO.md`)
- branch: `0037-09-fixture-git-hardening-r2-20260825T055600Z`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09-fixture-git-hardening-r2-20260825T055600Z`
- binding_base: `dc88cd4c0467a57a99d70e6a1af5444eda734b5b` (rejected R1 fix tip; not `main`)
- write_scope:
  - `TODO-Gabriel-Black-0037-09-fixture-git-hardening-r2-20260825T055600Z.md` (this claim)
  - `_src/tests/test_issue_validate.py`
- out_of_scope: `TODO.md`, `automation_safety_policy.json`, governance/DEC, Acceptance/review/checkpoint, parent/Feature/`main` merge, `DONE.md`, push, `uv.lock`, `0037-09.04`, `0041-02`, other claims, `_src/tools/issue_validate.py`

## Startup review

- Dispatcher named branch/worktree free. Re-measured 2026-08-25T05:56Z: `refs/heads/0037-09-fixture-git-hardening-r2-20260825T055600Z` and the worktree path were absent. R1 branch `0037-09-fixture-git-hardening-20260825T053100Z` still occupies `dc88cd4c04` in a separate worktree.
- Created this worktree from binding base only (`git worktree add -b … dc88cd4c04`).
- Inbox: broadcasts only; no conflicting claim on this repair. `memory_append` hold observed; no memory write.

## Intended product

1. In `fixture_add`, after path containment and immediately BEFORE `run_isolated_git(..., 'add', ...)`, call `_assert_fixture_identity(repo)`.
2. Regression: intended/foreign disposable repos and a redirected `intended/.git` gitdir file — exception before mutation; foreign index and relevant bytes byte-identical.
3. Extend existing hostile-env regression with safe read-only ROOT fingerprints: index via `git write-tree` / `ls-files --stage` (read-only), `git status --porcelain`, selected tracked file bytes/hashes before/after. Do not intentionally mutate live ROOT.
4. 20+ new tests green; `py_compile`; `git diff --check`; exact `automation_safety` scan on `issue_validate.py` AND the test file PASS 0 findings. No policy change or suppression.

## Progress

- Claim-only commit first (this file). Product follows in a later commit.
