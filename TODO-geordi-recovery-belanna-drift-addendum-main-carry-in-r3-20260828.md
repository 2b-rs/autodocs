# Integrator claim — recovery Belanna drift addendum carry-in R3

state: [p]
owner_token: agent:geordi:recovery-belanna-drift-addendum-main-carry-in-r3:1787920770185-3ac8d961
request_id: 1787920770185-3ac8d961
capability_class: privileged
base_commit: 54764c91d102fd78d710249f6c934157bba119ad
execution_authority: direct
startup_review: AGENTS.md; SANDBOX.md; docs/pipeline/roles/integrator.md; docs/pipeline/core-rules.md
write_scope: ["TODO-geordi-recovery-belanna-drift-addendum-main-carry-in-r3-20260828.md", "TODO-belanna-recovery-jean-luc-durable-claims-carryin-20260828T1135Z.md", "docs/campaign-evidence/recovery-belanna-drift-addendum-geordi-r3-20260828.md"]

- **Authority:** atomic offer award `1787920770185-3ac8d961`; fresh-pin resume `agent-inbox:1787922343894-81dac1ef`.
- **Pinned target:** `main@54764c91d102fd78d710249f6c934157bba119ad`.
- **Pinned source:** `recovery-jean-luc-durable-claims-carryin-belanna-r2-20260828T1140Z@217a5957f3660b9e82c2c07b786a5c700bf8fdd9`.
- **Exact source blob:** `868444f5c1f8aafe94cb7f79a0f27529b49720fb` at `TODO-belanna-recovery-jean-luc-durable-claims-carryin-20260828T1135Z.md`.
- **Prior R2:** `d3f6964b9` / `f09d802e41`, evidence only; no verdict or integration-only file is inherited.
- **Branch / worktree:** `integrate-recovery-belanna-drift-addendum-geordi-r3-20260828` / `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-recovery-belanna-drift-addendum-geordi-r3-20260828`.
- **Prohibited:** change recovery dispositions, product paths, Acceptance, DONE, foreign worktrees, source history, cleanup, push, or external effects.

## Intended write scope

- `TODO-geordi-recovery-belanna-drift-addendum-main-carry-in-r3-20260828.md`
- `TODO-belanna-recovery-jean-luc-durable-claims-carryin-20260828T1135Z.md`
- `docs/campaign-evidence/recovery-belanna-drift-addendum-geordi-r3-20260828.md`

## Review plan

- Carry only the exact source blob after independently comparing R2 evidence and the current target.
- Assess the addendum without inheriting R2's verdict or files; run exact-delta checks, candidate hygiene, guarded root preflight/equality, root fast-forward, and postflight.
- Stop under Mode C before root mutation on target drift, hygiene, content, or review failure.

## Final disposition

- **Verdict:** pending independent review.

## Next step

Commit this claim first, then inspect the exact source blob and candidate delta before any carry or integration action.
