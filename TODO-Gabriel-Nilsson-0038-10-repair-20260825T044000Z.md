# Claim — Task 0038-10 repair (immutable per-attempt results / current pointer)

request_id: 20260825T044000Z
owner_token: agent:gabriel-nilsson-20260825t044000z:0038-10-repair:20260825T044000Z
task_id: 0038-10
feature_id: 0038
capability_class: unprivileged
execution_authority: direct local Shell/Git in the item worktree only; not sandboxed-grunt; no runner queue
startup_review: Dispatcher briefing for Gabriel-Nilsson-20260825T044000Z, Team Discovery, Programmer. Read AGENTS.md/SANDBOX.md collaboration rules via session context. Re-measured: no `refs/heads/0038-10-repair-20260825T044000Z`; no worktree dir; binding base `4231f93b24cbd9aa056305ffa5a147ac316c783c` is a reachable commit (`feat(0038-10): persist immutable attempt results`). Worktree created from that exact base. First mutation this session is this claim plus the 0038-10 TODO marker/claim pointer only.
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

## Next step after this commit

Stop. Later turns may repair `_src/tools/runner_transaction.py` and tests under this claim; not this commit.
