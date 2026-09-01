# `0019-02` R5 integration-incident recovery

## Pinned state

- Incident baseline: `main@ef7aa528d154a9be8754ee6c6bef84f21056247b`
- Recovery authority: atomic AWARD `1787976396198-320ac09f` under BLACKOUT mandate `1787975808618-9b9f08f2`
- Integrator: Geordi La Forge (`geordi`), privileged Integrator
- Recovery branch: `integrate-0019-02-r5-incident-recovery-geordi-20260829`

## Finding

The R5 integration record committed at the incident baseline does not contain the mandatory `check_integration_hygiene.py` candidate and immediate root-preflight/postflight commands and results. Ordinary `git diff`, `git status`, snapshot verification, unit tests, or a coordinator assertion do not substitute for those checks. No later record can truthfully relabel them or fabricate their historical execution.

## Smallest conforming recovery

The five landed R5 paths are preserved byte-for-byte. The applicable governance requires the hygiene implementation to run around an integration; it does not require reverting unchanged evidence content merely to manufacture a new historical merge. Therefore the reversible, intent-preserving recovery is an additive incident/current-state record, gated as a fresh exact candidate. The original incident remains append-only in Git history.

Before this record was authored, the actual implementation validated the pinned landed state:

```text
python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs/.worktrees/integrate-0019-02-r5-incident-recovery-geordi-20260829 --candidate-ref ef7aa528d154a9be8754ee6c6bef84f21056247b
integration hygiene: PASS
integration worktree: /Users/tobias.anton/devel/autodocs/.worktrees/integrate-0019-02-r5-incident-recovery-geordi-20260829
registered worktrees: 284
```

Exit code: `0`.

The final two-path additive candidate is separately subject to candidate hygiene plus immediate root preflight, merge, and postflight. Those results are durably attached to assignment `1787976396198-320ac09f`; failure or baseline drift stops integration. This record does not claim that the missing historical gates ran.
