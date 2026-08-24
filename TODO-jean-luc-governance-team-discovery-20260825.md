# Coordination claim — Team Discovery roster integration

- owner_token: `agent:jean-luc:governance-team-discovery:20260825`
- assignment: direct current-user confirmation that the root roster change is theirs and Team Discovery now supports the agents
- capability_class: `privileged`
- role: Project Lead / governance integrator for this bounded user-directed change
- branch: `gov-team-discovery-jean-luc-20260825`
- worktree: `.worktrees/gov-team-discovery-jean-luc-20260825`
- base: `main@8650f59e4f1138cc583de48dea6afff71ec854c2`
- write_scope:
  - `docs/pipeline/agent-roster.md`
  - `TODO-jean-luc-governance-team-discovery-20260825.md`
- boundaries: no Task acceptance, Feature closure, unrelated cleanup, or change to another claim
- state: implementation and governance integration in progress

## Evidence and plan

- The current root worktree contained the user-authored Team Discovery block.
- The user confirmed authorship and intent on 2026-08-25.
- Re-author the exact current block in this isolated main-based governance worktree.
- Validate the roster/process documentation, commit path-limited, restore only the duplicated root roster edit, run mandatory hygiene, and fast-forward `main` from the root checkout.
