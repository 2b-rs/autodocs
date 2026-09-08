# Claim: 0037-09-fixture-git-hardening

- owner_token: agent:gabriel-ortegas-20260825t053100z:0037-09-fixture-git-hardening:20260825T053100Z
- identity: Gabriel-Ortegas-20260825T053100Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer, Team Discovery
- item: user-directed repair `0037-09-fixture-git-hardening` (not a backlog Task; do not change `TODO.md` markers)
- branch: `0037-09-fixture-git-hardening-20260825T053100Z`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09-fixture-git-hardening-20260825T053100Z`
- binding_base: `0037-09@5994536998816c2091be4ebd19323889b0461f0a` (not `main`)
- write_scope:
  - `TODO-Gabriel-Ortegas-0037-09-fixture-git-hardening-20260825T053100Z.md` (this claim)
  - `_src/tests/test_issue_validate.py`
- out_of_scope: `TODO.md` markers, `automation_safety_policy.json`, governance/DEC, Acceptance/review/checkpoint, parent/Feature/`main` merge, `DONE.md`, push, `uv.lock`, `0037-09.04`, `0041-02`, other claims, `_src/tools/issue_validate.py`

## Startup review

- Dispatcher named the worktree/branch free. Re-measured 2026-08-25T05:31Z: neither `refs/heads/0037-09-fixture-git-hardening-20260825T053100Z` nor the worktree path existed. Created worktree from binding base only.
- `HEAD` at claim-only commit will be recorded after first commit.
- Inbox: broadcast-only traffic; no conflicting claim on this repair. `memory_append` hold observed; no memory write.

## Optional existing safety test (justification BEFORE product mutation)

- A separate existing safety-test module is **not** added.
- Reason: write scope is only `_src/tests/test_issue_validate.py` plus this claim. Hostile `GIT_*` / template / signing / hooks regression belongs in the same file that owns fixture Git, so the 17 existing `issue_validate` tests and the new fail-closed proofs share one helper.
- No other test file will be created or edited.

## Intended product

Central fixture Git helper in `_src/tests/test_issue_validate.py`:

1. Fully strip ambient `GIT_*` from the subprocess environment.
2. Set `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` to `os.devnull`.
3. Disable prompt, signing, hooks, and templates (env + `GIT_CONFIG_COUNT` keys + empty in-fixture template dir + `GIT_CEILING_DIRECTORIES`).
4. After `git init`, require `--show-toplevel` and `--absolute-git-dir` to equal the temp fixture root and `<root>/.git`.
5. Path containment of every mutation target under the fixture root before `add`/`commit`.
6. `git add -- <enumerated paths>` only — never `git add .`.
7. Verify the new commit object and HEAD resolve inside the fixture git dir.

Regression coverage in the same file: hostile `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` / `GIT_COMMON_DIR`, plus config/hooks/template/signing injection. Must fail closed (raise, no silent foreign mutation). Intended fixture, foreign repo, and autodocs `ROOT` HEAD unchanged.

Existing 17/17 issue_validate tests must stay green.

Validation: `py_compile`, `git diff --check`, `automation_safety.py --path` on `issue_validate.py` and the test file. No policy/suppression bypass. If Criticals remain after real hardening: leave incomplete, record exact scanner output; do not self-dispose.

## Assumptions

- Unprivileged session may create the assigned worktree/branch and commit only in that worktree.
- `issue_validate.py` is read-only; fixture isolation is a test-side defect.
- Claim-only commit first, then product commit, then close/bookkeeping note in this claim (no `TODO.md`).

## Completion

- Claim SHA: `7de8ca995ec6459c6fd3be475704ca9058004e1c`
- Product SHA: `e7e68f2be06728fb5b38ca0937610790af97213b`
- Validation:
  - `python3 -m py_compile _src/tests/test_issue_validate.py` exit 0
  - `uv run python _src/tests/test_issue_validate.py -v` → Ran 20 tests, OK (original 17 plus 3 isolation tests)
  - `git diff --check -- _src/tests/test_issue_validate.py` exit 0
  - `python3 _src/tools/automation_safety.py --path _src/tools/issue_validate.py --path _src/tests/test_issue_validate.py` → PASS scanned=2 findings=0 unresolved-critical=0 (no policy edit)
- `uv.lock` appeared in worktree from `uv run` and was not staged.
- No `TODO.md` marker change. Not merged to parent/main.
