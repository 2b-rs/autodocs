# Integration claim — DEC-0044-027-C001 G3 correction

- **item_id:** `0044-12-g3`
- **owner_token:** `agent:geordi:0044-12-g3-integration:1787906610153-087a8baf`
- **state / status:** `[p]` / `[p]`
- **capability_class / role:** `privileged` / independent Integrator
- **execution_authority:** exact-scope independent review and conditional integration only
- **planned_duration:** 30 minutes
- **branch:** `integrate-0044-12-g3-geordi-20260828t0844z`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0044-12-g3-geordi-20260828t0844z`
- **target baseline:** `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81`
- **candidate:** `gov-0044-12-g3-saru-20260828@e2686812b840817298d037dd95c9a5e080d51630`
- **substantive correction:** `41c57c1a6b60b0e35b0b68dd9c4f487a13e3ce40`
- **authority:** OFFER `agent-inbox:1787906555886-310a2957`; AWARD `agent-inbox:1787906610153-087a8baf` from Project Lead `jean-luc`
- **write scope:** this integration claim/evidence and the assigned candidate's append-only `DEC-0044-027-C001`, evidence, and claim paths only; conditional root fast-forward after all gates pass
- **review scope:** correction schema, prior-block digest and byte preservation, activation SHA ancestry/trailer, exact path scope, evidence, candidate hygiene, root preflight/equality guards, and postflight
- **prohibitions:** no product/tool/policy mutation, Task Acceptance, `0044-13`, Feature/DONE movement, `memory_append`, cleanup, ref deletion, repair, or unrelated work

## Integration contract

Review the pinned candidate independently against the pinned target. Stop and record a blocking verdict on target drift, material change, schema or evidence finding, scope mismatch, hygiene failure, or preflight failure. Only a passing exact candidate may advance `main` by root `git merge --ff-only`, followed immediately by postflight.
