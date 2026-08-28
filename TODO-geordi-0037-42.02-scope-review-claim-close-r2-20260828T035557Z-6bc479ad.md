# Retry claim — canonicalize terminal 0037-42.02 scope-review claim

- **item_id:** `0037-42.02-scope-review-claim-close-r2`
- **owner_token:** `agent:geordi:0037-42.02-scope-review-claim-close-r2:1787889357484-6bc479ad`
- **state / status:** `[x]` / `[x]`
- **capability_class / role:** `privileged` / Integrator
- **execution_authority:** direct execution and exact assigned lifecycle-bookkeeping retry only
- **planned_duration:** 30 minutes
- **branch:** `0037-42.02-scope-review-claim-close-geordi-20260828-r2`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-42.02-scope-review-claim-close-geordi-20260828-r2`
- **baseline:** `main@8275b2a2ed7a30a94cc06e57576e8a59a8e79b4a`
- **authority:** existing Jean-Luc AWARD `agent-inbox:1787888943720-f96510c1`; retry instruction `agent-inbox:1787889357484-6bc479ad`; Jadzia owner disposition `agent-inbox:1787888778285-e456e619`
- **write scope:** `TODO-jadzia-0037-42.02-scope-review-20260827.md`; this retry claim
- **carried substantive source:** exact one-line change from `175fe0cc0a840a22e904624066134b833889785a`
- **prohibitions:** all original prohibitions remain; no stale-candidate merge, dossier, verdict, `TODO.md`, `DONE.md`, governance, Acceptance, checkpoint, product, foreign cleanup, worktree deletion, external effect, or scope expansion

## Preserved prior blocked verdict

The first exact candidate `7ebbfcb5d8b4a41b25274f38d42d5a11e545afea` and root preflight each passed across 237 worktrees, but `main` moved from awarded `ebd6122f7de5318a088698efdc431a451c60bea7` to `8275b2a2ed7a30a94cc06e57576e8a59a8e79b4a` before the merge equality gate. Prior claim-only blocked record: `bc0e5e3c84fee602f7a1afb8e572092802f76baf`. No merge occurred in that attempt. This retry preserves that verdict and does not reuse the stale candidate as a merge target.

## Next step

Commit this retry claim before carrying the exact one-line change. Re-run focused validation, candidate hygiene, guarded root pre/postflight, and stop on any finding or baseline drift.

## Completion evidence

Claim-first commit `a66fbf067a6f3f95dd3a8eddca070ee812d38a9a` preceded the carried change. Cherry-pick commit `59dee303e1a2a89c0b565a3a6c943e43fe6af0a5` applies only the verified one-line insertion/deletion to `TODO-jadzia-0037-42.02-scope-review-20260827.md`; postimage SHA-256 is `ea0b9ef675a42b3875528df034fc40560373fb4de68bdf5d9a58d507449b3527`. Focused legacy doctor parsing reports state `x` at line 9. Its remaining target finding, `LTD-CLAIM-FIELDS-MISSING`, is pre-existing and outside the awarded one-line scope. `git diff --check` passed.

## Final next step

Run exact-candidate hygiene and guarded root preflight against current baseline `8275b2a2ed7a30a94cc06e57576e8a59a8e79b4a`; fast-forward only on exact equality and passing gates, then run immediate root postflight.
