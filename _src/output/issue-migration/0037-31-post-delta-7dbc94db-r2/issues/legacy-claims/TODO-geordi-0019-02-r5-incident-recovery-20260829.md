# Integration incident-recovery claim — `0019-02` R5

- **item_id:** `0019-02-r5-integration-incident-recovery`
- **owner_token:** `agent:geordi:0019-02-r5-integration-incident-recovery:1787976396198-320ac09f`
- **state / status:** `[p]` / `[p]`
- **capability_class / role:** `privileged` / independent Integrator
- **execution_authority:** atomic AWARD `1787976396198-320ac09f`; BLACKOUT mandate `1787975808618-9b9f08f2`
- **branch:** `integrate-0019-02-r5-incident-recovery-geordi-20260829`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0019-02-r5-incident-recovery-geordi-20260829`
- **pinned incident baseline:** `main@ef7aa528d154a9be8754ee6c6bef84f21056247b`
- **write scope:** the five landed R5 claim/evidence paths, this claim, and `docs/campaign-evidence/0019-02/integration-incident-recovery-geordi-20260829.md`
- **prohibitions:** no product/BOM/archive/inventory bytes, `TODO.md`, Acceptance, markers, Feature state, publication, credentials, external systems, or `0019-04`

## Incident and recovery

Commit `ef7aa528d154a9be8754ee6c6bef84f21056247b` landed five R5 claim/evidence paths while its committed integration record lacked the mandatory `check_integration_hygiene.py` candidate and immediate root-preflight/postflight evidence. Those historical checks cannot be reconstructed retroactively. The incident remains preserved append-only in Git history and in the unchanged five landed paths.

The smallest rule-conforming recovery is additive because the binding rule requires the actual checks before each integration but does not require neutralizing unchanged evidence content solely to replay history. Before authoring this record, the actual hygiene implementation passed against the pinned landed state:

`python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs/.worktrees/integrate-0019-02-r5-incident-recovery-geordi-20260829 --candidate-ref ef7aa528d154a9be8754ee6c6bef84f21056247b`

Exit `0`: `integration hygiene: PASS`; `registered worktrees: 284`.

The exact additive candidate, immediate root preflight, root merge, and immediate root postflight remain Integrator-owned execution gates. Their durable results are recorded in assignment `1787976396198-320ac09f`; any drift, non-zero/indeterminate hygiene result, or unrelated root state is a stop.

## Supervisor-restart terminal handover — 2026-08-29

**State / status:** `[w]` / `terminal handover`. The historical recovery
candidate is no longer actionable on its pinned baseline. Current `main`
contains recovery commit `5b06f31d7f7fbc69649406518773c3b5a72b57c2`, but no
record demonstrates the required candidate hygiene, immediate root preflight,
authorized merge, and root postflight for that recovery candidate. Those checks
cannot be inferred or recreated. The preserved R5 paths are unchanged; any
remediation needs a fresh exact assignment and current baseline.
