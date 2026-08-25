# Claim 0037-15.03

- **owner_token:** `agent:gabriel-owo-20260825t091000z:0037-15.03:20260825T091000Z`
- **agent:** Gabriel-Owo-20260825T091000Z
- **capability_class:** unprivileged
- **execution_authority:** direct Git/tools in item worktree; stop at `[x]`; no Acceptance; no checkpoint; no main; no DONE Feature; no push
- **item:** 0037-15.03
- **branch:** 0037-15.03
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-15.03`
- **base:** `d02005baa830e257e38b5d4783d2a721eacac9c0` (Feature `0037`; already contains 0037-14 and 0037-17.01)
- **merged_prereq_tips:** none additional (`0037-14` and `0037-17.01` already ancestors of Feature `0037`; `0037-06.02` contract is on this baseline)
- **startup_review:** Task was `[ ]` at Feature tip. Prerequisites terminal: 0037-06.02, 0037-14, 0037-17.01. Write scope: exactly-once authorized event replay + conflict reporting over fresh shadow candidates, tests, this claim, 0037-15.03 TODO block.
- **write_scope:** `_src/tools/issue_event_replay.py`, `_src/tests/test_issue_event_replay.py`, this claim, `TODO.md` 0037-15.03 markers only
- **do_not:** mutate `issue_reimport.py` (15.01), schema transforms (15.02), or issuectl (10.04); shared root checkout; `refs/heads/main`; Acceptance / DONE.md
- **validation:** `python3 _src/tests/test_issue_event_replay.py` 12/12 PASS
- **next:** close at `[x]` after product REF is known

## Progress

- Provisioned `.worktrees/0037-15.03` on branch `0037-15.03` reset to Feature `0037` (`d02005baa`) after provisioner had fallen back to `main`.
- Implemented `_src/tools/issue_event_replay.py`: authority, base/source/item checks, provenance-only writes, stable `RPL-` findings with explicit dispositions.
- Tests cover compatible replay, identical duplicate, collision, deletion, stale base, unauthorized event, changed item, overwrite, concurrent claim, zero-loss after re-import, batch collision, CLI report.
