# Coordination claim — Jean-Luc durable restart recovery (2026-08-29)

- `item_id: jean-luc-restart-recovery-20260829T074500Z-ea9b`
- `owner_token: agent:jean-luc:restart-recovery:20260829T074500Z-ea9b`
- `capability_class: privileged`
- `process_role: Project Lead`
- `execution_authority: direct current-user instruction to re-evaluate the named durable claims and record terminal state or handoff`
- `branch: recovery-jean-luc-durable-claims-20260829`
- `worktree: /Users/tobias.anton/devel/autodocs/.worktrees/recovery-jean-luc-durable-claims-20260829`
- `base: main@26f34aa56ce6287424d5bcb9440cd394b47b60ad`
- `status: terminal; integrated on main@a9daae857301ec00eebfa72565172f00143e764e`

## Exact write scope

- this coordination claim
- `TODO-jean-luc-0037-08-integration-20260825.md`
- `TODO-jean-luc-0037-09.01-parent-integration-20260825.md`
- `TODO-jean-luc-0037-39-integration-20260825.md`
- `TODO-jean-luc-0037-39-contract-repair-20260824T162000Z.md`
- `TODO-jean-luc-0037-46.02-governance-20260823T134915Z.md`
- `TODO-jean-luc-0037-51-20260824T072000Z.md`
- `TODO-jean-luc-0038-management-decision-20260825T211222Z.md`
- `TODO-jean-luc-0044-02-integration-20260824T232213Z.md`
- `TODO-jean-luc-0044-07-marker-repair-20260829T002500Z.md`
- `TODO-jean-luc-0044-13-containment-20260828T194500Z-01a049e4.md`

## Contract

Revalidate every runtime-projected durable claim named by the current user
against current `main`, its Task marker, reachable substantive/integration
evidence, current decision state, and any separately owned continuation. Append
only a current restart-recovery disposition. Do not resume terminal work,
appropriate a separate implementation/review assignment, change a Task marker,
perform Acceptance or integration, mutate `main`, or change product/governance
artifacts.

## Startup findings

- Runtime reports no agent with `exit_class: killed` and an open claim.
- The eight older coordination/implementation claims already state terminal or
  released dispositions and their cited completion refs remain ancestors of
  `main@26f34aa56ce6287424d5bcb9440cd394b47b60ad`.
- The `0044-07` stale-marker repair is coordination-complete. Beverly's later
  implementation candidate `0b9045779700f71b6b231d6bb1e8bbb1045f1cbb`
  remains off `main`; exact Acceptance assignment request
  `decision-1787978453230-6c52bb77` is pending.
- The `0044-13` containment claim is terminal at integrated recovery baseline
  `4688eb1cc9863600c6951ba02164a4a21a193068`; Task implementation and
  Acceptance remain separate from that claim.

## Historical handoff action — completed

Commit this claim-first record, append current revalidation to every named
claim, validate exact path scope and ancestry, then hand the claim-only candidate
to an independent Integrator for main carry-in. No other action is authorized.

That handoff completed through Integrator assignment
`1787989763780-71110142`. The terminal claim/evidence candidate
`a9daae857301ec00eebfa72565172f00143e764e` is now on `main`; no remaining
integration or implementation action is authorized by this claim.

## Result

- All ten runtime-projected `TODO-jean-luc-*` claims associated with the nine
  named work items were revalidated against
  `main@26f34aa56ce6287424d5bcb9440cd394b47b60ad`.
- No old implementation or integration token is actionable. Eight claims remain
  terminal with reachable refs; the `0044-07` marker-repair token hands off to
  Beverly's separate review-state candidate and pending Management request; the
  `0044-13` containment token remains terminal and separate from Task work.
- No Task marker, Acceptance record, product/governance artifact, external
  system, or existing branch/ref was changed.
- Independent Integrator claim-only carry-in completed at
  `main@a9daae857301ec00eebfa72565172f00143e764e`; the implementation lease is
  released and this recovery claim has no remaining action.
