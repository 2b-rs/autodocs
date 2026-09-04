# Claim 0037-09.04

- owner_token (current): `agent:gabriel-chapel-20260825t063000z:0037-09.04:20260825T063000Z`
- owner_token (Pike provenance only; not current lease): `agent:gabriel-pike-20260825t061300z:0037-09.04:20260825T061300Z`
- agent (current): Gabriel-Chapel-20260825T063000Z
- agent (Pike, runtime death): Gabriel-Pike-20260825T061300Z
- dispatcher: gabriel (Jean-Luc assigned Chapel takeover)
- capability_class: privileged (assigned by Jean-Luc; privilege is not independence or merge authority)
- execution_authority: privileged Programmer for implementation only. MUST NOT: Acceptance, parent/main merge, review, integration, publication, push, 0041-02
- item: 0037-09.04
- branch: `0037-09.04-20260825T061300Z`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09.04-20260825T061300Z`
- HEAD at takeover measurement: `ea09b68bdd4783928f77c7113c8eae1e087f1a4a` (must stay until this claim-only commit)
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
  - `_src/tests/fixtures/0037-09.04/**`
  - this claim
  - `TODO.md` 0037-09.04 block only
- must_not: further runtime hop; Acceptance; parent/main merge; review; integration; publication; push; 0041-02; uv.lock; reset; stash; shared root writes
- startup_review: additive takeover of Pike claim/worktree; no new branch; product remains unstaged until adopt/reject

## Takeover (2026-08-25T063000Z, Chapel)

Pike runtime died after leaving unstaged product. Measured before any mutation:

- `git status --porcelain=v1`:
  - ` M _src/tests/test_issue_validate.py`
  - ` M _src/tools/issue_validate.py`
  - ` M _src/validate.py`
  - `?? _src/tests/fixtures/0037-09.04/`
  - `?? uv.lock` (MUST NOT stage; out of write scope)
- SHA-256 at measurement:
  - `cbff948f89445cb52e9634efdf29dcb0bacff204c383a03bf8dbe18cc3fd59df` `_src/tests/test_issue_validate.py`
  - `23a7ae05d476cb1e7caeef2e1e61047b02120c8e3461ffb4a2f1ecee0e427fe0` `_src/tools/issue_validate.py`
  - `fae24442eae0abd3937068d5255b0a73b9722343f132214e5c079dfa8b38cc3e` `_src/validate.py`
  - `d82cb32261221d7250f91a099fb5baab3877b49b3913ccc8b26e079fac411b19` `_src/tests/fixtures/0037-09.04/mini-dag-one.json`
  - `0bef007b20b746388be8272d9749f2c0aa93e2aa49e0c676480680121c86e847` `_src/tests/fixtures/0037-09.04/mini-dag.json`
  - `d96164ec65d04d7defaef595284221f0b5a3ee67b3bb3941a79143e0765f2dd2` `_src/tests/fixtures/0037-09.04/cases.json`
  - `308f5f11934efda630c927ebca9f8b320fbcec115abaff9f48b67016f7fd2b21` `uv.lock` (leave untracked)
- `git diff --stat` (tracked): 645 insertions, 5 deletions across the three Python files.
- Product files remain unstaged through the claim-only takeover commit.

## Feature context

Parent 0037-09: complete strict issue, lifecycle, provenance/privacy, and derived-artifact validation. 0037-09.04 adds DAG/sole-writer/freshness/generated-view/determinism plus `_src/validate.py` staged/candidate integration. Do not weaken 0037-09.01–.03 or fixture-Git hardening.

## Adopt (2026-08-25, Chapel)

**Adopt.** Reason: unstaged Pike product implements IV0935–IV0944, architecture negative fixtures via `cases.json`, mini DAG generated-view coverage, `_src/validate.py` staged/candidate/off CLI, mutation guards, and does not weaken IV0904/prior suites. One EOF blank-line whitespace fix applied before product commit. `uv.lock` left untracked.

## Implementation complete

- takeover SHA: `7ca4f7af768517413d5dc79a38fc0a04ca958507`
- product SHA: `dd1e76a0d56434349107bd010be82783053f82f4`
- validation: 58/58 twice; py_compile; git diff --check; automation_safety PASS 0 findings
- next: bookkeeping `[x]` this commit; no Acceptance/parent merge

## Next step

None for this owner. Claim remains on branch as provenance.
