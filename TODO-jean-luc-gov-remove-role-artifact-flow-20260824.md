# Claim: gov-remove-role-artifact-flow-20260824

- owner_token: `agent:jean-luc:gov-remove-role-artifact-flow-20260824:20260824T155000+0200`
- capability_class: `privileged`
- execution_authority: direct local Git and validation; governance integration authority as Projektleitung
- assignment: explicit user authorization on 2026-08-24 to remove `docs/pipeline/role_artifact_flow.png`
- branch: `gov-remove-role-artifact-flow-20260824`
- worktree: `.worktrees/gov-remove-role-artifact-flow-20260824`
- base_commit: `e6efba401c5c683962706ef0647a86e14c624642`
- status: `in progress`
- write_scope:
  - `docs/pipeline/role_artifact_flow.png`
  - `TODO-jean-luc-gov-remove-role-artifact-flow-20260824.md`
- prohibitions: no unrelated cleanup, no Acceptance changes, no `TODO.md`/`DONE.md` mutation
- validation: pending root hard preflight and integration hygiene
- next_step: commit the authorized deletion, restore the matching root file from its unchanged index, run hygiene, and fast-forward merge through the root checkout
