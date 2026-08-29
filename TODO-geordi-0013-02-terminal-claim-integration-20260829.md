# Claim: 0013-02 terminal claim provenance integration

- **owner_token:** `agent:geordi:0013-02-terminal-claim-integration:1788031628485-f483f778`
- **persona:** Geordi La Forge, privileged Integrator, Team Enterprise
- **item_id:** `0013-02-terminal-claim-integration`
- **process:** Process Claim provenance integration
- **state:** `[p]`
- **assignment:** priority offer `1788031628485-f483f778`; atomic award accepted by Geordi
- **capability_class:** `privileged`
- **execution_authority:** direct, limited to the awarded integration and mandatory hygiene gates
- **branch:** `integrate-0013-02-terminal-claim-geordi-20260829`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0013-02-terminal-claim-geordi-20260829`
- **base_commit:** `51de9c0113e8dc11303308c99fdc1db36898c983`
- **candidate_source:** `0013-02@04e0770da70c8b635379ca71e61b4fc2d766bf5e`
- **startup_review:** `AGENTS.md`; `SANDBOX.md`; `docs/pipeline/roles/integrator.md`; `docs/pipeline/core-rules.md`; `docs/pipeline/branch-workflow.md`

## Exact write scope

- `TODO-beverly-0013-02-1787972130857-fe98737a.md`
- `TODO-geordi-0013-02-terminal-claim-integration-20260829.md`
- `docs/campaign-evidence/0013-02/terminal-claim-integration-geordi-20260829.md`

## Authority boundary and plan

- Current `main` already contains product/candidate integration `179e8dce47c14835f476bc0c1870984e5b16fa9c`; Task `0013-02` remains `[u]` pending an authorized decision and exact-revision approval.
- Integrate only Beverly's terminal claim handoff from candidate `04e0770da70c8b635379ca71e61b4fc2d766bf5e`, plus this claim and exact integration evidence.
- Verify exact paths and semantic boundary, run candidate hygiene, run the immediate root preflight, advance `main` through the authorized root merge, and run the immediate postflight.
- Prohibited: product/source/authority decisions, baseline approval, Acceptance, `TODO.md` mutation, starting `0013-03`, Feature or `DONE.md` closure, cleanup, push, or scope expansion.
