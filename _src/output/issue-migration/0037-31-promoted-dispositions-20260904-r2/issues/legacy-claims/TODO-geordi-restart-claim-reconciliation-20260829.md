# Supervisor-restart claim reconciliation — Geordi

- **Authority:** direct supervisor restart-recovery instruction, 2026-08-29.
- **Branch/worktree:** `reconcile-geordi-durable-claims-20260829` /
  `.worktrees/reconcile-geordi-durable-claims-20260829`.
- **Baseline:** `main@f57faba37c4c8bcc7c68becdf732e694e0f377e4`.
- **Write scope:** the seven named historic Geordi claim records below and this
  reconciliation record only.
- **Boundary:** append terminal state or handover evidence only. No `TODO.md`,
  `DONE.md`, Acceptance, task/product/governance change, worktree cleanup,
  or external action is authorized.

## Disposition

- `0019-02`: terminal handover; the historical recovery gate cannot be
  reconstructed and needs a fresh exact assignment if remediation is requested.
- `0037-42.02`: DEC allocation and scope-review integration records are already
  on `main`; historical claims are terminal.
- `0041-02`: the bounded non-activating supersession integration is already on
  `main` and accepted; task activation remains blocked.
- `0044-04`: review, integration, and acceptance bookkeeping are already on
  `main`; the historic review claim is terminal.
- `0044-13`: post-hoc audit is terminal advisory evidence; the task's current
  checkpoint evidence is retained separately and no further audit action exists.

Current awarded `0044-07` is not altered: its contract waits for terminal
acceptance of `0017-01` R3.

## Integration-boundary result

**VERDICT: BLOCKED — target drift.** Exact-candidate hygiene for
`3a903819a` passed across 297 registered worktrees, and the immediate root
preflight passed across 298. Before the authorized merge, `main` changed from
the pinned `f57faba37c4c8bcc7c68becdf732e694e0f377e4` to
`2236e4becc68585b1da41481f4293dd7104437fc` (`jadzia`,
`chore(claim): record terminal state for completed implementation chains`).
The equality gate stopped before any merge. This candidate is retained clean;
no repair, rebase, or foreign-state change is authorized here. A fresh exact
baseline assignment is required to integrate these claim-only dispositions.
