# Integration claim — retained MAN.3 `DEC-0027-001` governance

- **item_id:** `0027-01-governance-integration`
- **owner_token:** `agent:geordi:0027-01-governance-integration:1787908518545-c161f96f`
- **state / status:** `[x]` / `[x]`
- **capability_class / role:** `privileged` / independent Integrator
- **execution_authority:** exact-scope assembly, independent integration review, and conditional guarded governance integration only
- **planned_duration:** 25 minutes
- **branch:** `integrate-0027-01-man3-geordi-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0027-01-man3-geordi-20260828`
- **offered / awarded target baseline:** `main@a1afbae4aa2d7174318452f6ccf1212158176955`
- **refreshed exact target:** `main@3dd4e23354886134939a7a161458f3123a8c791e`, authorized by Project Lead drift determination `agent-inbox:1787908664056-336132c9`
- **candidate / review:** `8772645587fd41ae873aeb9c48c061de134d581c` / `4b513b343231274aeddd426a4c4c3e7b986fa44b`
- **authority:** OFFER `agent-inbox:1787908399456-52a5f935`; AWARD `agent-inbox:1787908518545-c161f96f` from Project Lead `jean-luc`
- **carry scope:** `TODO-data-0027-01-20260827T011751Z-a33e0189.md`; `docs/dossiers/dec-0027-001-man3-plan-gate-scope.md`; `TODO-seven-0027-01-scope-review-20260827.md`; `docs/dossiers/review-dec-0027-001-man3-plan-gate-scope-seven-20260827.md`
- **Integrator write scope:** this claim; `docs/campaign-evidence/0027-01/governance-integration-geordi-20260828.md`; conditional guarded root merge only after PASS
- **review scope:** record/review conformance; unique `DEC-0027-001` versus main-visible `DEC-0027-002`; sole MAN.3 allocation of `0027-11` with SUP.8 consumption; main-visible authority correction; C-1 treatment without marker mutation; exact scope; current-main drift; candidate hygiene; root preflight and postflight
- **prohibitions:** no `TODO.md`/backlog/interface mutation; no activation or creation of `0027-11`; no Acceptance; no `DONE.md` movement; no cleanup/deletion; no scope widening; no zero-byte superseded review content except Git ancestry/provenance

## Startup review

- Claim created at the exact awarded baseline before candidate content inspection.
- Read-only startup sampling observed `refs/heads/main@3dd4e23354886134939a7a161458f3123a8c791e`, three commits ahead of the awarded baseline. The drift is pending bounded assessment under the stop-on-drift contract; no candidate content has been carried or reviewed.

## Integration contract

Carry only the four named corrected candidate/review paths. Stop and record a blocking verdict on conflict, unexpected path, material drift, or nonzero gate. Only a passing final candidate may advance `main` through the repository-authorized guarded merge and immediate postflight.

## Review result

- **Baseline reconciliation:** nonmaterial drift from `a1afbae4aa` to `3dd4e23354` affected only `TODO-tilly-0037-11.02-ae45-20260828T082900Z.md` and `_src/tests/test_issue_views.py`; reconciled by merge `9ec539f1ab` after explicit refreshed-target authority.
- **Assembly:** exact candidate blobs carried in `b6d32a1643`; exact corrected review blobs carried in `87bad005cd`. Candidate `TODO.md` and zero-byte superseded review content were not carried.
- **Evidence:** `docs/campaign-evidence/0027-01/governance-integration-geordi-20260828.md`.
- **Verdict:** PASS; ready for exact-candidate hygiene and conditional guarded root integration. No prohibited mutation occurred.
- **Integration:** candidate hygiene PASS; root preflight PASS; `main` merge `1f0bace76f835ffb9b51f340ca34b8ee98fc6bce`; immediate root postflight PASS. Final concurrent drift through first parent `22acd85fdd` was disjoint from all six awarded paths and the machine overlap gate passed.
