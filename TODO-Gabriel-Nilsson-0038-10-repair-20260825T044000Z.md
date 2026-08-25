# Claim — Task 0038-10 repair (immutable per-attempt results / current pointer)

request_id: 20260825T044000Z
owner_token: agent:gabriel-linus-20260825t045800z:0038-10-repair:20260825T045800Z
prior_owner_token_provenance_only: agent:gabriel-nilsson-20260825t044000z:0038-10-repair:20260825T044000Z
prior_owner_token_bryce_provenance_only: agent:gabriel-bryce-20260825t045000z:0038-10-repair:20260825T045000Z
task_id: 0038-10
feature_id: 0038
capability_class: unprivileged
execution_authority: direct local Shell/Git in the item worktree only; not sandboxed-grunt; no runner queue
startup_review: Dispatcher briefing for Gabriel-Linus-20260825T045800Z, unprivileged Programmer. Work only in `/Users/tobias.anton/devel/autodocs/.worktrees/0038-10-repair-20260825T044000Z` branch `0038-10-repair-20260825T044000Z`. Stay in this single session. Path-limited additive claim-only takeover first (no code). Then independent inspect of 46 tests. Confirm/reject d712bbb95 in a second claim/TODO-only commit. Do not reset. MUST NOT: merge, Acceptance, push, 0041-02, Airiam/Sato tree, uv.lock. HEAD may be `0f49010c` (unauthorized inspect adopt). `1d800dfa1` is Bryce provenance only. `9c3b8e412` is not a valid handoff close.
state: [p]
binding_base: 4231f93b24cbd9aa056305ffa5a147ac316c783c
canonical_branch: 0038-10-repair-20260825T044000Z
canonical_worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0038-10-repair-20260825T044000Z
start_pin: 4231f93b24cbd9aa056305ffa5a147ac316c783c
do_not_base_on: main
merged_prerequisite_tips: none this turn (claim-only first commit; no merge of later Feature 0038 work)

## Exact Task (from backlog)

> **0038-10** PREREQ: 0038-10:0038-01, 0038-10:0038-02, 0038-10:0037-45 Standardize immutable per-attempt results and an atomic mutable current pointer.

**Acceptance criteria:** Every attempt writes `result.json` with Task/request/base/authority, per-phase RC/status/duration, aggregate verdict, exact actions, structured findings, path counts/digests, commits, cleanup/recovery state, and evidence references before an atomic `current.json` pointer changes. A retained script or free-text `run-current.log` is never interpreted as pending/completed state; partial attempts use explicit lifecycle markers.

**Definition of Done:** Success, failure, timeout, cancellation, crash, retry, tamper, and pointer-update fixtures are deterministic; an empty archive or overwritten current log cannot erase the last immutable attempt result.

## Prior implementation evidence (retained; not deleted)

- Historical implementation `[x]` REF: `4231f93b24cbd9aa056305ffa5a147ac316c783c` (this branch's binding base).
- Prior claim (carried, not deleted): `TODO-terra-1-0038-10-20260819T000000Z-6666b30b762f.md` (`owner_token: agent:terra-1:0038-10:20260819T000000Z-6666b30b762f`).
- Completion evidence text from later `TODO.md` on `main` (copied for provenance; this branch is **not** based on `main`):
  - `4231f93b24cbd9aa056305ffa5a147ac316c783c` adds immutable no-follow per-attempt results, atomic SHA-256-bound task current pointers, strict recovery/finalization binding and locking, explicit phase/action lifecycle evidence, and 46 hermetic fixtures covering success, failure, timeout, cancellation, crash, retry, tampering, same-request rerun, and pointer boundaries.

This repair reopens implementation ownership under a new owner_token. It does not invalidate the historical REF or rewrite prior review/acceptance records.

## This-turn constraint (dispatcher)

THIS TURN: first commit is the claim ONLY. Path-limited commit of claim + 0038-10 TODO block only. Then STOP.

Do not edit `runner_transaction.py` or tests yet. Do not add `uv.lock`.

MUST NOT: Acceptance, review, checkpoint; other 0038 Tasks including 0038-33; Feature/main/DONE; push; change governance process; delete old claim/review history; reset existing branches; 0041-02; 0037-09.02.

## Write scope (this commit)

- `TODO-Gabriel-Nilsson-0038-10-repair-20260825T044000Z.md` (this file)
- `TODO.md` (0038-10 marker/claim pointer and retained `[x]` evidence only)

## Explicit takeover (2026-08-25T04:50:00Z)

- Dispatcher: gabriel
- From: Gabriel-Nilsson-20260825T044000Z
- To: Gabriel-Bryce-20260825T045000Z
- At: 2026-08-25T04:50:00Z
- Nilsson `owner_token` `agent:gabriel-nilsson-20260825t044000z:0038-10-repair:20260825T044000Z` is provenance only.
- Current ownership: `agent:gabriel-bryce-20260825t045000z:0038-10-repair:20260825T045000Z`
- Filename of this claim is unchanged (`TODO-Gabriel-Nilsson-0038-10-repair-20260825T044000Z.md`).

## Recorded deviation (does not authorize retroactively)

Product mutation occurred **before** this takeover.

- Unstaged `_src/tools/runner_transaction.py` (+41/−4) SHA-256 `d018cd46881caf8fbd29cf955a9082dfea3f822ab70424ceb6bc65f4edcddfde` was later committed as `d712bbb95a8f9bfea5b546919561bad442a45fdb` by a **second Nilsson-labeled workflow agent that was NOT the original claim session**.
- Bookkeeping commit: `9c3b8e412622c9402b6fa21fbf185b2066af962b`
- This record documents the deviation; it does not authorize it retroactively.
- New owner may inspect/adopt that committed diff **only after** this claim-follow-up commit. This turn does not inspect or adopt the product.

## Next step after this commit

Inspect/adopt committed repair `d712bbb95` only after this claim commit is on the branch. No Acceptance. No product mutation this turn.

## Diagnosis (2026-08-25)

Review `4fddf329efdd53ec65d9639e7210d2585bbf37c9` reproduced 46 ran, 5 failed, 2 errors. All seven touched `_current_pointer_status` or `_atomic_write` via `_open_directory_nofollow`. `Transaction` uses `root.resolve()` (`/private/var/folders/...`); tests pass unresolved `TemporaryDirectory` (`/var/folders/...`). macOS `/var` is a symlink; `O_NOFOLLOW` on that component yields `[Errno 20] Not a directory: 'var'`. Pointer status then reported `invalid` after an otherwise successful attempt.

## Repair

`_open_directory_nofollow` follows a directory symlink only when the target stays under the current physical prefix (OS aliases such as `/var` -> `/private/var`). Escaping links still fail. Tests unchanged. Docs unchanged.

Substantive repair REF: `d712bbb95a8f9bfea5b546919561bad442a45fdb`

## Validation

- `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py`: 46/46 OK in 100.264s
- `python3 -m py_compile _src/tools/runner_transaction.py`
- `git diff --check` clean for the repair file

## Independent inspect-and-adopt (2026-08-25, Gabriel-Bryce-20260825T045000Z)

**Verdict: ADOPT** quarantined candidate `d712bbb95a8f9bfea5b546919561bad442a45fdb`.

**Not a valid handoff close:** `9c3b8e412622c9402b6fa21fbf185b2066af962b` remains invalid as a close/handoff; it is not this session's implementation-close REF.

**Independent finding:** `_open_directory_nofollow` at `4231f93b2` opened every path component from `/` with `O_NOFOLLOW`. `Transaction` uses `Path.resolve()` on the repo root (physical `/private/var/...` on macOS), so live attempts already wrote results. `_current_pointer_status` and `_atomic_write` (and hermetic fixtures) pass unresolved `TemporaryDirectory` paths whose lexical prefix is `/var` → `/private/var`. `O_NOFOLLOW` on that alias yields `ENOTDIR` (`Not a directory: 'var'`), so pointer validation reported `invalid` after an otherwise successful attempt. Candidate `d712bbb95` follows a directory symlink only when `os.path.realpath` of the link target stays under the current physical prefix; escaping runtime-parent links still raise. That matches the observed macOS prefix-alias failure without relaxing in-tree nofollow.

**Independent validation (this session, worktree HEAD including candidate):**
- `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py`: **46 ran, 0 failed, 0 errors, OK in 110.438s**
- `python3 -m py_compile _src/tools/runner_transaction.py`: pass
- `git diff --check` (worktree and `d712bbb95^..d712bbb95`): clean

No product mutation in this commit. Marker stays `[p]` pending separately authorized closure; product SHA adopted is `d712bbb95`.

## Explicit takeover (2026-08-25T04:58:00Z)

- Dispatcher: gabriel
- From: Gabriel-Bryce-20260825T045000Z
- To: Gabriel-Linus-20260825T045800Z
- At: 2026-08-25T04:58:00Z
- Nilsson `owner_token` `agent:gabriel-nilsson-20260825t044000z:0038-10-repair:20260825T044000Z` is provenance only.
- Bryce `owner_token` `agent:gabriel-bryce-20260825t045000z:0038-10-repair:20260825T045000Z` is provenance only.
- Current ownership: `agent:gabriel-linus-20260825t045800z:0038-10-repair:20260825T045800Z`
- Filename of this claim is unchanged (`TODO-Gabriel-Nilsson-0038-10-repair-20260825T044000Z.md`).
- `1d800dfa1` is Bryce provenance only (claim takeover commit), not this session's authority.

## Inspect-runtime violation (recorded; no retroactive authority)

- Worktree HEAD at takeover: `0f49010c596fda6c00bf677ef85046fbecad261a` (`docs(0038-10): adopt d712bbb95 after independent inspect`).
- That commit was an unauthorized adopt by **Gabriel-Bryce-20260825T045000Z-inspect**, not the session that wrote `1d800dfa1`.
- Quarantine candidate remains `d712bbb95a8f9bfea5b546919561bad442a45fdb`.
- `9c3b8e412622c9402b6fa21fbf185b2066af962b` is **not** a valid handoff close.
- This record documents the inspect-runtime violation; it does **not** authorize `0f49010c` or `d712bbb95` retroactively.
- This commit is claim-only: **no product/code mutation**.

## Next step after this commit

Independently inspect code, run all 46 tests in `_src/tools/test_runner_transaction.py`, `py_compile`, and `git diff --check`. Then additive claim/TODO-only confirm or reject of `d712bbb95` with concrete finding and test counts. No new code unless a new defect is proven.

## Independent inspect-and-confirm (2026-08-25, Gabriel-Linus-20260825T045800Z)

**Verdict: CONFIRM** quarantine candidate `d712bbb95a8f9bfea5b546919561bad442a45fdb`.

Takeover SHA (this session, claim-only): `634e4804e91e65ecfeb865f72c0a47ab7f472c21`

**Finding (independent):** `_open_directory_nofollow` at `4231f93b2` opened every path component from `/` with `O_NOFOLLOW`. `Transaction` uses `Path.resolve()` so live repo roots already sit on the physical prefix (`/private/var/...` on this macOS). `_current_pointer_status` / `_atomic_write` and the 46 hermetic fixtures pass unresolved `TemporaryDirectory` paths whose lexical prefix is `/var` → `/private/var`. `O_NOFOLLOW` on that alias yields `ENOTDIR` (`Not a directory: 'var'`), so pointer validation reported `invalid` after an otherwise successful attempt. Candidate `d712bbb95` follows a directory symlink only when `os.path.realpath` of the link target stays under the current physical prefix (`_path_is_relative_to`); escaping runtime-parent links still raise. That matches the observed macOS prefix-alias failure without relaxing in-tree nofollow. No new defect found.

**Independent validation (this session, worktree HEAD including candidate):**
- `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py`: **46 ran, 0 failed, 0 errors, OK in 106.359s**
- `python3 -m py_compile _src/tools/runner_transaction.py`: pass
- `git diff --check` (worktree and `d712bbb95^..d712bbb95`): clean

No product mutation in this commit. Marker stays `[p]`. `9c3b8e412` is not a valid close. `1d800dfa1` is Bryce provenance only. `0f49010c` remains an inspect-runtime adopt without retroactive authority; this confirmation is independent of that commit.

## Gaps

- No Acceptance, review, or checkpoint (out of scope).
- Feature/main/DONE not updated.
- Other 0038 Tasks not mutated.
- `9c3b8e412` is not a valid close.
- No new code in this commit.
