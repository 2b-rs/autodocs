# Claim: supervisor restart reconciliation — Geordi durable claims

- **owner_token:** `agent:geordi:supervisor-restart-claims:20260830T000000Z-731d31ed`
- **persona / capability:** Geordi La Forge, Team Enterprise Integrator / `privileged`
- **authority:** current-user supervisor-restart instruction of 2026-08-30
- **state:** `integration_ready`
- **branch / worktree:** `integrate-geordi-supervisor-restart-claims-20260830` / `.worktrees/integrate-geordi-supervisor-restart-claims-20260830`
- **base:** `main@731d31ed493bb34c54b9c04a7a056b957e262827`

## Exact scope

- `TODO-geordi-0017-01-option-a-integration-r3-20260829.md`
- `TODO-Geordi-0044-04-review-20260825.md`
- `TODO-geordi-0044-memory-hygiene-integration-review-20260825T073926Z-a54b484c.md`
- `TODO-geordi-0044-20-1788039731603-52e3d8ff.md`
- this claim

## Boundary

Reconcile only terminal handovers for the named Geordi claims. No task marker,
Acceptance, Feature/DONE, implementation, policy, external, Memory, cleanup, or
foreign-claim change is authorized. Landing requires exact-candidate hygiene and
the immediate root preflight/equality/fast-forward/postflight chain.

## Evidence and next action

The existing terminal records for `0013-02`, `0019-02`, `0041-02`, and
`0044-13` are already main-visible. This candidate adds the remaining explicit
handover records and corrects no historical evidence. Exact five-path scope and
`git diff --check` pass. Commit, then run the integration gates.
