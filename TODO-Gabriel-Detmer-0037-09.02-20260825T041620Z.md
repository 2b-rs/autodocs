# Claim 0037-09.02

- owner_token: `agent:gabriel-detmer-20260825t041620z:0037-09.02:20260825T041620Z`
- agent: Gabriel-Detmer-20260825T041620Z
- capability_class: unprivileged
- execution_authority: direct local Shell/Git/tests in the item worktree only
- item: 0037-09.02
- branch: 0037-09.02
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09.02`
- binding_base: `854d43a2bee04463a899ba9e604dc70cf33690f1` (parent Task branch `0037-09`)
- start_pin: base `854d43a2bee04463a899ba9e604dc70cf33690f1`
- write_scope:
  - `_src/tools/issue_validate.py`
  - `_src/tests/test_issue_validate.py`
  - `_src/tests/fixtures/0037-09.02/**`
  - `TODO-Gabriel-Detmer-0037-09.02-20260825T041620Z.md`
  - `TODO.md` (0037-09.02 block only)
- must_not: Acceptance; integration checkpoint; merge into 0037-09 / Feature 0037 / main; DONE.md; push; runner queue; 0037-09.03/09.04/0041-02; overwrite a foreign claim; memory_append

## Feature context

Parent **0037-09**: strict issue, lifecycle, provenance/privacy, and derived-artifact validation sharing `_src/tools/issue_validate.py`.

This Subtask: lifecycle, claim, authority/signature, criterion-evidence, closure, archive, and commit-reference validation. Do not weaken 0037-09.01 structural rules.

## startup_review

Re-measured 2026-08-25:
- no `refs/heads/0037-09.02` before branch creation
- no worktree dir before `git worktree add`
- ancestors of `854d43a2`: 0037-03.01 `f3adcde91487f774d29b80985f54a5736da556bd`, 0037-03.02 `536c824f095f1563b9c565378afecabb4ff07bf1`, 0037-08 `15b50c7c0b4943b12cf703a7f9b612bb3388d948` / substantive `4376be766decd03830a5feeec7dcc6b41cfd87ce`, 0037-09.01 `d699c977f511a1c3f159533118f3e72ef71f5209`

Deviation: none. Implementation stays in `issue_validate.py` (shared diagnostics/config).

## Progress

- 2026-08-25: worktree/branch created from binding base; claim authored.
- 2026-08-25: implemented IV0910–IV0922 lifecycle/claim/closure/signature/evidence checks in `_src/tools/issue_validate.py`; negative fixtures `_src/tests/fixtures/0037-09.02/cases.json`; tests in `_src/tests/test_issue_validate.py`. `uv run python _src/tests/test_issue_validate.py` → 13 OK. Did not weaken 0037-09.01 rules.
- 2026-08-25 continuation (Gabriel-Owosekun-20260825T043500Z, same owner_token): disposition coverage for completed/wontfix/superseded/duplicate/cancelled/archived-not-accepted; removed unreachable nested completed check. Tests 13/13 OK. Substantive REF `d2fd153a97f21003583fabaa62f74618cd874df5`. Implementation complete `[x]` on this Subtask branch only; claim kept; no Acceptance/merge/push.
