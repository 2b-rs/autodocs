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

- [p] claim + TODO marker
- implement + fixtures + tests
- substantive / bookkeeping commits
