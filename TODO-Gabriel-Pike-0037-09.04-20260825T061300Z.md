# Claim 0037-09.04

- owner_token: `agent:gabriel-pike-20260825t061300z:0037-09.04:20260825T061300Z`
- agent: Gabriel-Pike-20260825T061300Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer (Team Discovery)
- item: 0037-09.04
- branch: `0037-09.04-20260825T061300Z`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09.04-20260825T061300Z`
- binding_base: parent `0037-09` @ `e0ed8a52b9640c20cd48f7e062f339a1c78ebf37`
- merged_prerequisite_tips: already ancestors of binding base
  - `0037-09.01` @ `d699c977f511a1c3f159533118f3e72ef71f5209`
  - `0037-09.02` @ `3aa10521fea7b18dff9c93b252e13d2e624d7480`
  - `0037-09.03-20260825T050700Z` @ `016a21f484e83b4d9486e242ea0165f59ba19bdb`
  - fixture git hardening r2 @ `14128cc7ad765bcbd8b291f085c092b37710fc12`
- write_scope:
  - `_src/tools/issue_validate.py`
  - `_src/validate.py`
  - `_src/tests/test_issue_validate.py`
  - focused existing validate tests if needed
  - `_src/tests/fixtures/0037-09.04/**`
  - this claim
  - `TODO.md` 0037-09.04 block only
- must_not: Acceptance/review/checkpoint; parent/Feature/main/DONE; push; uv.lock; 0041-02; policy/governance; other claims
- startup_review: names free; worktree created from binding base; no write to shared root

## Feature context

Parent 0037-09: complete strict issue, lifecycle, provenance/privacy, and derived-artifact validation. 0037-09.04 adds DAG/sole-writer/freshness/generated-view/determinism plus `_src/validate.py` staged/candidate integration. Do not weaken 0037-09.01–.03 or fixture-Git hardening.

## Next step

Implement IV0935+ DAG and generated-view checks; fixtures; validate.py integration; tests; close `[x]` on this branch.
