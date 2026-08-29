# Integration claim — `0019-02` independent snapshot revalidation evidence integration R5

- **item_id:** `0019-02-evidence-integration-r5`
- **owner_token:** `agent:obrien:0019-02-evidence-integration-r5:1787974624781-94456e73`
- **state / status:** `[p]` / `[p]`
- **capability_class / role:** `privileged` / independent Integrator
- **execution_authority:** atomic AWARD `1787974624781-94456e73` from Project Lead `jean-luc`
- **planned_duration:** 35 minutes
- **branch:** `integrate-0019-02-evidence-obrien-r5-20260829`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0019-02-evidence-obrien-r5-20260829`
- **target baseline:** `main@55b32ba6e9b1135f1f6117ed4a032cf70cecaccf`
- **candidate source:** `chain-0019-02-william@7ba6481dcf` / preserved R4 candidate `b2c2a2767f5dba860ad22e993f240fbf2c4dadfd` / preserved R3 commit `95f333ed8cd37b7c4baa1ca64e0ba6070e290fbc`
- **write scope:**
  - `TODO-wesley-0019-02-revalidation-20260829.md`
  - `TODO-william-0019-02-chain-20260829T023000Z.md`
  - `docs/campaign-evidence/eclipse-score-v0.6.0-snapshot-revalidation-0019-02.md`
  - `TODO-obrien-0019-02-evidence-integration-20260829.md`
  - `docs/campaign-evidence/0019-02/integration-obrien-20260829.md`
- **prohibitions:** no TODO/product authoring, Acceptance, markers, production bytes, enter 0019-04, publish, or clean foreign state

## Integration contract

Apply candidate source delta (three claim/evidence paths) onto fresh target `main@55b32ba6e9b1135f1f6117ed4a032cf70cecaccf`. Verify historic product bytes equal current main and rerun recorded offline verifier and unit tests. Run mandated candidate hygiene and root preflight, record independent verdict, and advance main only if every gate passes and exact target is unchanged.

## Verification results

- Offline verifier: `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/score_source_snapshot.py --verify --repository-root . _src/spec/campaigns/eclipse-score-v0.6.0.json` exited 0 (787 artifacts verified).
- Unit test: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest _src.tests.test_score_source_snapshot` exited 0 (1 test passed).
- Scope check: Only the 5 permitted claim and evidence paths modified.
