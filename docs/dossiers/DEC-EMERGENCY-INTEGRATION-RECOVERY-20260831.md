# DEC-EMERGENCY-INTEGRATION-RECOVERY-20260831

- **Status:** decided — execute bounded recovery and activate flow control
- **Date:** 2026-08-31
- **Authority:** current repository owner, explicit interactive authorization
- **Executor:** `mancons`, Management Consulting recovery coordinator

## Observed facts

The displaced `main` at `b314d0eb458a28cb67d096ede2b6b105541c1b95` had orphan root `2268a9de9f79bf320eff815bc8c7d991a00374df` and no merge base with the repository's delivery lineage rooted at `2040d0ef31e7bdfd57cfb1265bbb5e2b555ee55e`. The local `main` reflog showed the last source-history tip before `reset: moving to origin/main` was `7fa42d73bd33c07193fc49c49429074d338a1a31`. The fleet had hundreds of branches/worktrees and a large review queue because dispatch admission was not bounded by integration capacity.

## Decision

1. Freeze new dispatch and all integration/publication ref movement during recovery.
2. Preserve the displaced publication lineage at branch and tag `preserved/publication-main-20260831` / `recovery/publication-main-20260831`.
3. Preserve the recovered source tip at branch and tag `preserved/source-main-pre-publication-reset-20260831` / `recovery/source-main-pre-publication-reset-20260831`.
4. Restore source-history `main` to reflog-proven tip `7fa42d73bd33c07193fc49c49429074d338a1a31`.
5. Replay the validated reaper optimization and terminal-claim lifecycle onto that lineage.
6. Activate reserved Integrator capacity, WIP limits, pull-based review admission, end-to-end dispatcher accountability, canonical ancestry receipts, and strict source/publication separation.
7. Reconcile and drain historical work in controlled batches; do not heuristically merge, accept, rename, or delete it.

## Waiver

For this incident only, the repository owner's direct instruction authorizes `mancons` to perform the root-checkout recovery and governance commits on `main`, despite the ordinary worktree and role-separation rules. The waiver does not authorize deletion of preserved refs, weakening Acceptance, heuristic claim finalization, worktree deletion outside the conservative reaper predicates, or publication to `main`.

## Compensating controls

- Both displaced and restored tips are retained under branch and tag refs.
- No untracked root material is deleted or staged.
- Only independently identified commits are replayed.
- The fleet remains frozen until post-recovery validation and explicit release.
- Canonical integration now requires exact candidate ancestry evidence.

## Verbatim authorizing prompt

> I assign the execution of this plan to you. You may control supervisor, access the agent-inbox queue and the raw files, you can impersonate as management consulting (mancons in the roster), instruct team members at will, sign of management decisions (as far as needed to execute this plan), and trigger all necessary work. One hint from my side: I used to believe that flow control would come naturally if dispatchers had the duty to run implementation, unit test, and integration in sequence, but I must have missed something important. Whatevre that is, you may change the processes that led to this mess. Good luck!
