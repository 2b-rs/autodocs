# Independent integration review claim — Task 0038-31

- `owner_token: agent:data-geordi-20260822t203511z:0038-31-review:20260822T203511Z`
- `agent_id`: `Data-Geordi-20260822T203511Z`
- `persona`: Geordi
- `process_role`: Integrator
- `capability_class`: `privileged`
- `runtime`: `zed/gpt-5.6-sol`
- `assignment_authority`: dispatcher `Data`; exact briefing retained verbatim in the review report under `DEC-0044-013`.
- `independence`: distinct from dispatcher persona Data and implementer `Harry-Dax-20260822T183800Z`; no candidate authorship, decisive technical disposition, or sole validation-production role.
- `item`: Task `0038-31`, mandatory integration-checkpoint re-review after rejected review `0db2a4fd9de266519c3aea75845256588126f137`.
- `candidate_branch`: `0038-31`
- `candidate_tip`: `7ab79af32ec3d1fd83964049b773cad9e8c077e4`
- `substantive_ref`: `94bab196df7786f57e97994dd73f822cb50556e0`
- `review_branch`: `review-0038-31-data-geordi-20260822T203511Z`
- `review_worktree`: `/Users/tobias.anton/devel/autodocs/.review-worktrees/0038-31-data-geordi-20260822T203511Z`
- `review_base`: `main@3d8467b097120302d80f5ffccfae06c1e3dd095a`
- `initial_write_scope`: this claim and `docs/campaign-evidence/review-0038-31-20260822-data-geordi/report.md` only.
- `conditional_write_scope`: `TODO.md` only if the verdict is `accepted`, in a separate path-limited acceptance-bookkeeping commit after the review-evidence commit.
- `prohibited`: no candidate/product fix; no Feature or main integration; no `DONE.md`; no push; no `run.sh`; no movement of `refs/heads/main`; no mutation of the root checkout.
- `external_resources`: none.

## Startup and baseline

- Read the repository authority, privileged-review, acceptance, and process-role instructions.
- Announced to agent-inbox as `Data-Geordi-20260822T203511Z`, role `Integrator`, runtime `zed/gpt-5.6-sol`; read and acknowledged startup mail.
- Root hard preflight passed at `3d8467b097120302d80f5ffccfae06c1e3dd095a`: tracked worktree and index clean, `HEAD == refs/heads/main`.
- Pre-mutation integration hygiene passed with 116 registered worktrees.
- Review branch/worktree created from current main without merging candidate content.

## Required independent validation

- Pin exact Task contract, candidate tree/commits, digests, manifest, authority epoch, and transitive non-accepted prerequisite closure.
- Inspect the complete candidate delta and prior rejection bottom-up.
- Independently prove red-before-green for Index 1 / Worktree 2 with a preceding new copy and colliding line numbers: old behavior reports one finding, corrected behavior reports two.
- Test neighboring cases: worktree copy after existing; Index 2 / Worktree 1; multiple colliding code locations in one file.
- Determine whether the construction is general rather than case-specific; rerun focused and relevant full suites plus clean-tree finding-set comparison.
- Record exactly `accepted`, `rejected`, or `inconclusive`; do not repair a rejection or inconclusive result.

## Current state

- Status: independent review complete; verdict `accepted` against exact candidate `7ab79af32ec3d1fd83964049b773cad9e8c077e4`.
- Prior major F1 is closed by independent old/new hermetic proof (1→2), neighboring cases, a stronger two-collision-group case (2→4), and a 10,000-case deterministic property run.
- Focused suite: 14/14 passed. Full module: 135 tests with only the byte-proven pre-existing `0038-33` aggregate-control failure. Live gate: `PASS`, 73 findings / 38 advisory / 24 disposed critical / 0 unresolved / 0 policy errors. Clean-tree finding identity is unchanged before/after.
- Contract SHA-256: `5333dc95dfb6b48dc4b9e1968506f10fb9d03dff860ee1c9caaa03ea96b72067`.
- Work-product manifest SHA-256: `3b280ec5e9b2072e153355f1004c850bfb455b228028f427cfa56f8bd6d36e74`.
- Prerequisite-acceptance SHA-256: `70d563a79cfe6134a8cbefd7d6819d5f1fbf2a8c5914dd886d877589785a2d8d`.
- Review evidence: `docs/campaign-evidence/review-0038-31-20260822-data-geordi/report.md` (pending evidence commit at this update).
- Next action: commit the two review-evidence paths, then add the exact `Acceptance: ✓` record to `TODO.md` in a separate path-limited commit referencing the real evidence REF.
