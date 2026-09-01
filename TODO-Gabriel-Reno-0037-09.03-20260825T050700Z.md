# Claim: 0037-09.03

- **item:** 0037-09.03
- **owner_token:** `agent:gabriel-reno-20260825t050700z:0037-09.03:20260825T050700Z`
- **capability_class:** unprivileged
- **execution_authority:** direct (no runner queue)
- **startup_review:** Dispatcher assigned this session; parent `0037-09@f4007f447cdba3db68a0167a9acbf9bbabe6ac9e`; names `0037-09.03-20260825T050700Z` and worktree `.worktrees/0037-09.03-20260825T050700Z` were free on re-measure.
- **write_scope:**
  - `_src/tools/issue_validate.py`
  - `_src/tests/test_issue_validate.py`
  - `_src/tests/fixtures/0037-09.03/**`
  - `TODO-Gabriel-Reno-0037-09.03-20260825T050700Z.md`
  - `TODO.md` (0037-09.03 block only)
- **must_not:** Acceptance, review, checkpoint; merge to 0037-09 / Feature / main; DONE; push; uv.lock; 0037-09.04; 0041-02; runner; other claims; 0037-09-eof; 0038-10-repair.
- **binding_base:** `0037-09@f4007f447cdba3db68a0167a9acbf9bbabe6ac9e` (not `main`)
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09.03-20260825T050700Z`
- **branch:** `0037-09.03-20260825T050700Z`
- **new test module:** not used; extend `_src/tests/test_issue_validate.py`

## Assumptions

- Rule IDs continue the IV09xx series after 0037-09.02 (`IV0922`): IV0923–IV0934.
- Provenance inputs live under `provenance/` (events, runs, findings, artifact-sets, `_views`) plus an optional public projection JSON.
- Existing 0037-09.01 / 0037-09.02 diagnostics must remain unchanged.

## Progress

- claim commit `5d52557e182ee4a1436b095960155e18fc1a80d0`
- implemented IV0923–IV0934 in `_src/tools/issue_validate.py` (typed refs, provenance graph, artifact/run/finding, evidence-class, privacy/public projection)
- fixtures: `_src/tests/fixtures/0037-09.03/` (27 negative cases + valid-chain + leak token)
- validation: `python3 -m unittest _src.tests.test_issue_validate` 17/17 OK (venv `/tmp/autodocs-0037-08-venv-julian`); `py_compile` OK; `git diff --check` OK; automation_safety: `_src/tools/issue_validate.py` 0 findings (policy file has unrelated stale disposition errors)
- substantive REF `b72aefbcfc2b3e5002cf5762876de9b520951e2b`
