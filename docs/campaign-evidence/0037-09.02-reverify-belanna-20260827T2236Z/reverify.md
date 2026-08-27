# 0037-09.02 — post-merge re-verification and Acceptance bookkeeping (B'Elanna Torres)

**Reviewer/assignee:** `agent:belanna:0037-09.02-reverify:20260827T2236Z`, privileged Integrator, Team Voyager
**Dispatcher:** Michael, Discovery Project Lead — OFFER `1787869618214-bf8e4369`, ACCEPT `1787869659080-431f55b0`, AWARD `1787869816003-984c03b2` (re-verify), AWARD `1787870158204-892fa008` (Acceptance bookkeeping), thread `0037-09-wave`.
**Prior review:** `docs/campaign-evidence/review-0037-09.02-belanna-20260827T210115Z/review.md`, verdict ACCEPTED, reviewed baseline `3aa10521fea7b18dff9c93b252e13d2e624d7480`, Review-REF `49e85efb0b71df751c7a337d20c00a127d3ee2a4`.

## Why a re-verification was required

Between that review and this Acceptance bookkeeping, `main` absorbed a merge (`0037-09-wave-C`, commit `6b4f8bab94042246ca2a352210f0bda43bba9017`, parents `8fba67b6bdf6495e1b6562bff728761e8ea87e8c` + `016a21f484e83b4d9486e242ea...`) carrying sibling Tasks `0037-09.01`/`0037-09.03` into the same shared files my review covered. Kathryn's condition for that merge: confirm the resolution did not touch what was reviewed, or re-review the delta.

## Independent diff, reviewed tip vs merged tree

`git diff 3aa10521f 6b4f8bab9 -- <path>` for each of the six paths in the original review's exact scope:

| Path | Result |
|---|---|
| `TODO-Gabriel-Detmer-0037-09.02-20260825T041620Z.md` | empty diff |
| `TODO-jean-luc-0037-09.01-parent-integration-20260825.md` | empty diff |
| `_src/tests/fixtures/0037-09.02/cases.json` | empty diff |
| `TODO.md` | +193/-106, but the `0037-09.02` heading text itself (marker, claim reference, prerequisites) is byte-identical, just relocated (line 1018→1103) by unrelated content merged in above it |
| `_src/tests/test_issue_validate.py` | +55/-1 |
| `_src/tools/issue_validate.py` | +525/-2, 4 hunks |

## Hunk-level inspection of the two non-trivial files

`_src/tests/test_issue_validate.py`: single hunk at EOF (`@@ -501,6 +501,60 @@`), zero removed lines — a new test class appended, nothing existing touched.

`_src/tools/issue_validate.py`, 4 hunks:
1. `@@ -27,6 +27,52 @@` — new constants (`MAX_PROVENANCE_FILES`, `MAX_TRAVERSAL`, `UUID7`), purely additive.
2. `@@ -566,8 +612,479 @@` — new `_kind_of_uri` helper plus a ~470-line new provenance-checking function block; the only touched existing line is the `validate()` signature, which gains two new optional trailing kwargs (`provenance_root=None, projection_path=None`) — 1 line removed (old signature), replaced with the extended signature, zero logic altered.
3. `@@ -595,6 +1112,8 @@` — one new conditional call (`if provenance_root is not None: diagnostics.extend(_provenance_checks(...))`) inserted after the existing `_feature_closure_checks` call; nothing existing removed.
4. `@@ -617,12 +1136,16 @@` — two new argparse options (`--provenance-root`, `--projection`) and threading them into the one `validate(...)` call site; the call's closing-paren line is rewritten to add the two new kwargs, zero existing arguments changed.

**Conclusion:** every touched location is additive — new sibling-task functionality (provenance/projection checks, reading like `0037-09.03`'s scope) layered onto the same file, with zero deletions or modifications of the `IV0910`–`IV0922` rule-code implementation, the 15 named negative fixtures, or the fixed-seed property test this review actually evaluated.

## Empirical confirmation

Rebuilt an isolated detached worktree at `6b4f8bab94042246ca2a352210f0bda43bba9017` (`/tmp/09-02-reverify-wt`, removed after use) and reran, in a dedicated venv:

```
python3 -m pytest _src/tests/test_issue_validate.py -q
```

Result: **17 passed** (13 original + 4 new from the appended test class), 0 failures, 0 errors, 25.85s.

## Bookkeeping baseline for this Acceptance record

Between the merge (`6b4f8bab9`) and this bookkeeping, `main` advanced once more to `1969e055a5d9697b1db32ca15d5294b290d6f9fc` (Geordi's automation-safety governance merge, parents `54f51bbc4960bdcc33d9e9525d1b8dc8e94e300e` + `6b4f8bab9`). Independently confirmed: `git diff 6b4f8bab9 main -- _src/tools/issue_validate.py _src/tests/test_issue_validate.py _src/tests/fixtures/0037-09.02/cases.json TODO.md` is empty, and `6b4f8bab9` remains an ancestor of `main`. This Acceptance bookkeeping is therefore committed from bookkeeping base `1969e055a5d9697b1db32ca15d5294b290d6f9fc` without altering the substance re-verified above.

## Verdict

The original ACCEPTED verdict for `0037-09.02` carries forward unchanged. `Acceptance: ✓` recorded on the `TODO.md` `0037-09.02` heading only, path-isolated, per AWARD `1787870158204-892fa008`.

## Scope boundaries observed

No Acceptance recorded or implied for `0037-09.01`, `0037-09.03`, `0037-09.04`, or the parent `0037-09`. No Feature `0037` `DONE.md` move. No touch of `0037-16`, `0037-28`, `0039-01`, `0019`. No spawning. No `refs/heads/main` mutation performed directly (`git update-ref` never used); the ref advance, if any, happens only via `git -C <root> merge` from the root checkout after mandatory hygiene/preflight, per standing process.
