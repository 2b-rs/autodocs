# Claim: 0017-01 correction integration

- **owner_token:** `agent:geordi:0017-01-correction-integration:1788031760990-45e2f3f6`
- **persona:** Geordi La Forge, privileged Integrator, Team Enterprise
- **item_id:** `0017-01-correction-integration`
- **process:** Task bookkeeping correction integration
- **state:** `integration-ready`
- **assignment:** priority offer `1788031760990-45e2f3f6`; atomically awarded to Geordi
- **capability_class:** `privileged`
- **execution_authority:** direct, limited to the awarded integration and mandatory hygiene gates
- **branch:** `integrate-0017-01-correction-geordi-20260829`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0017-01-correction-geordi-20260829`
- **base_commit:** `7dc7e48e20d0866767b1ee5c0972d2b6ff42e47b`
- **candidate_source:** `0017-01-tasha-claim-recovery-20260829T192508Z@c79457e7e9a06061ed4f1416876bd7e72245b954`
- **startup_review:** `AGENTS.md`; `SANDBOX.md`; `docs/pipeline/roles/integrator.md`; `docs/pipeline/core-rules.md`; `docs/pipeline/branch-workflow.md`

## Exact write scope

- `TODO.md`
- `TODO-tasha-0017-01-20260829T023600Z.md`
- `TODO-geordi-0017-01-correction-integration-20260829.md`
- `docs/campaign-evidence/0017-01/correction-integration-geordi-20260829.md`

## Authority boundary and plan

- Both outside-chain predecessor assignments are terminal accepted; the integration baseline is repinned to current `main@7dc7e48e20d0866767b1ee5c0972d2b6ff42e47b`.
- Reconcile only the candidate's canonical governance-path correction and Tasha's terminal implementation handoff, plus this claim and exact evidence.
- Preserve `0017-01` and `0017-02` at `[x]`, preserve both explicit no-Acceptance boundaries, and leave `0017-03` unstarted.
- Prohibited: Acceptance, marker changes beyond the exact path correction, risk-strategy or risk-register mutation, `0017-02` reopening, `0017-03` start, Feature or `DONE.md` closure, foreign cleanup, push, or scope expansion.

## Verified candidate

- Candidate tip delta is exactly `TODO.md` and Tasha's claim; the claim blob matches the source candidate.
- The `TODO.md` change only replaces two stale governance paths with canonical paths that exist on the baseline.
- `0017-01` and `0017-02` remain `[x]` with explicit no-Acceptance boundaries; `0017-03` remains unstarted.
