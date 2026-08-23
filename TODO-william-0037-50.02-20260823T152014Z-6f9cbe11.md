# Claim — 0037-50.02

- owner_token: `agent:william:0037-50.02:20260823T152014Z-6f9cbe11`
- identity: `william` (William T. Riker); role: unprivileged direct-execution implementer
- capability_class: `unprivileged`
- execution_authority: direct local execution only; no acceptance, integration, deployment, host-state operation, runner protocol, network, push, or governance mutation
- item/branch/worktree: `0037-50.02` / `0037-50.02` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-50.02`
- base_commit: `8f6e27ffc7b19b255f93399136378f27ff55289a` (`0037-50`)
- startup_review: `TODO.md` at `9dcbaaee11482f62205e1c0b7a43989477dee5d7`; `DEC-0037-001` at `0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5`; active claims checked; no branch/worktree collision; prerequisite `0037-50.01` is `[x]`.
- write_scope: `runner-host/lib/retirement_guard.sh`, `runner-host/run-loop.sh`, `runner-host/MANIFEST.json`, `_src/tests/test_run_loop_retirement_guard.py`, and this claim file only.
- expected_result: extracted singleton retirement guard proves healthy-queue rejection, sentinel exemption, restored-legacy pass-through, malformed-selector failover handling, and collision-safe same-second rejections. `FAILOVER_REQUIRED` parks/fails closed with a stable nonzero/result code. No production rollback executor call is introduced; a hermetic injected callback seam is permitted only for exactly-once/future-mapping tests.
- assumptions: shared `TODO.md` bookkeeping is outside this assignment's write scope and remains dispatcher-owned; the work is behavior-preserving/dormant until `.04`.
- next_step: inspect current runner-loop behavior and manifest/test conventions, then implement focused guard and tests.
