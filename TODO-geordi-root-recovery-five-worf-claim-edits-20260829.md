# Root recovery claim — five Worf claim edits

- **item_id:** `root-recovery-five-worf-claim-edits`
- **owner_token / assignment_id:** `1788027167726-7b0c9c8e`
- **state / status:** `[p]` / `in_progress`
- **capability_class / role:** `privileged` / Integrator
- **authority:** atomic award `1788027167726-7b0c9c8e`; resolved Management
  decision `decision-1788018228677-a6ccf91f`, Option A
- **branch / worktree:** `root-recovery-five-worf-claim-edits` /
  `/Users/tobias.anton/devel/autodocs/.worktrees/root-recovery-five-worf-claim-edits`
- **pinned baseline:** `main@a0a8b0929ccf971be1d55ec6e08f196430e111cd`
- **write scope:**
  - `TODO-worf-0037-10-chain-20260828.md`
  - `TODO-worf-0037-11-20260828.md`
  - `TODO-worf-0037-11.01-20260828.md`
  - `TODO-worf-0037-13-20260828.md`
  - `TODO-worf-0039-03-20260829.md`
  - `docs/pipeline/branch-workflow.md`
  - `TODO-geordi-root-recovery-five-worf-claim-edits-20260829.md`
- **prohibitions:** no Task Acceptance, `TODO.md`/`DONE.md`, Feature state,
  unrelated path, preserved-tag deletion, adoption of the five dirty edits into
  `main`, or cleanup beyond restoring the exact five root paths to `main` bytes

## Startup verification

The item worktree and shared root were both pinned to
`a0a8b0929ccf971be1d55ec6e08f196430e111cd`. The item worktree was clean. The
shared root had exactly five unstaged tracked divergences, matching the awarded
scope, with no staged tracked divergence. The snapshot will be created through
an isolated temporary index and retained only by a named `preserved/*` tag; its
commit will not be placed in the registry branch ancestry.

## Required sequence

1. Capture and tag the exact five dirty-path bytes.
2. Append the preservation registry row on this branch.
3. Restore only those five shared-root paths to pinned `main` bytes.
4. Run candidate hygiene and the immediate hard root preflight.
5. Integrate only the registry/claim candidate, then run immediate root
   postflight. Stop on drift, unexpected tracked state, or any nonzero or
   indeterminate gate.
