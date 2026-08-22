# Claim: Task 0037-46.01

- owner_token: agent:seven:0037-46.01:20260822T105729Z
- agent: Seven (Dispatcher, zed/Sonnet), unprivileged capability class for this claim
- base: main @ 388018fdd
- branch: 0037-46.01 (cut from main at 388018fdd)
- worktree: .worktrees/0037-46.01

## Task text (copied from TODO.md at base)

- [ ] **0037-46.01** PREREQ: 0037-46.01:0037-07, 0037-46.01:0038-16.01 Implement and test the approved conflict-safe runner queue, dispatcher, complete action registry, and structured result protocol without activating it.
  - **Acceptance criteria:** Implement `_src/tools/runner_dispatch.py`, `_src/runner/actions-v1.json`, schemas, and a rigorously ignored `.runner/` runtime root. Sandboxed agents build complete requests under `.runner/drafts/<agent>/<request-id>/` and publish only by same-filesystem atomic rename to `.runner/requests/...`; the dispatcher ignores drafts/incomplete entries, validates manifest/member digests, and atomically claims ready requests. Results/logs/cancellation/leases are immutable or append-only under `.runner/`, never tracked or treated as source, and clean-tree/commit guards exclude only declared runtime paths. Enforce typed actions/arguments, base/epoch/ref/dependency/resource/network/credential/read/write preflight, timeout/worker limits, isolated temporary roots, mutation guards, progress/results, cleanup, retry identity, and no secret persistence. The reviewed registry must cover every action identified by `0037-37`: discovery; fetch/recheck; protected integration/push/PR; validators/tests/probes/generators/builds/browsers; package/tool provisioning; external policy setup; signature creation through approved handles and verification; path-limited commits; two-commit REF closure; claim `git update-ref` CAS; approval/cutover ref creation and append CAS; detached worktrees/temporary refs; exact-tree cutover; rollback/ref cleanup; and recovery. Generic shell action is forbidden.
  - **Definition of Done:** Source/fixture tests run through the qualified legacy runner and cover draft visibility, concurrent publication/claiming, stale base/epoch/ref, scope collision, unknown/generic action, unavailable dependency/credential, network denial, timeout/cancel, partial mutation, crash/restart, tampered result, retry, every Git/ref action's rollback, and claim retention; the implementation commit does not change the live runner protocol.

## Prerequisite state at claim time (verified against main @ 388018fdd)

- `0037-07` — `[x]`, integrated via `b13257241` (per-kathryn), the owner-signed architecture approval.
- `0038-16.01` — `[x]`, restored by repair commit `27930dc9c` after regression `4b95d99db`.

Both prerequisite branches are already ancestors of main at this base; no separate prerequisite merge is required before starting (verified: `git merge-base --is-ancestor 0037-07 main` and same for `0038-16.01` both true at base commit).

## Write scope

- `_src/tools/runner_dispatch.py` (new)
- `_src/runner/actions-v1.json` (new)
- `_src/runner/*.schema.json` or equivalent schema files (new, under `_src/runner/`)
- `_src/tests/test_runner_dispatch.py` or equivalent fixture/unit tests (new)
- `.runner/` runtime root: created and exercised only inside this worktree, must be gitignored, never committed as source
- `TODO.md`: only this Task's own marker/bookkeeping lines

Out of scope: no change to the live legacy `run.sh` protocol; no activation of the dispatcher (that is `0037-46.02`); no governance artifacts (`AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `docs/pipeline/*`) unless a documented autonomous-backlog-repair defect requires it, per `AGENTS.md`.

## Assumptions

- The `[u]` "sole named authority" bootstrap regime from `0037-49`/`0037-07` is the review-package baseline this Task's action registry must match one-for-one against the action list enumerated in the acceptance criteria.
- This is a single bounded work package as already decomposed by the architect (Feature 0037 backlog); not further split without a discovered defect.

## Status

Marking `[p]` in TODO.md on this branch at claim time. Dispatched to an implementer subagent under this claim; Dispatcher (Seven) retains ownership and the `owner_token` above.
