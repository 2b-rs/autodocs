# Integration claim — 0044-12 provenance-carry retry R2

- **item_id:** `0044-12`
- **owner_token:** `agent:geordi:0044-12-integration-r2:1787904941886-44fdae32`
- **state / status:** `[x]` / `[x]`
- **capability_class / role:** `privileged` / Integrator
- **execution_authority:** direct, exact-scope provenance-carry rebuild, review-currency reassessment, and conditional checkpoint integration
- **planned_duration:** 35 minutes
- **branch:** `integrate-0044-12-geordi-r2-20260828t0830z`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-0044-12-geordi-r2-20260828t0830z`
- **target baseline:** `main@16664ebc8622c5bd035cee9facdce9bbe2e8c7b2`
- **authority:** RETRY AWARD R2 `agent-inbox:1787904941886-44fdae32` from Project Lead `jean-luc`
- **carried history:** product `47331dca23e77288f6d5c690c165a522e9f01a23`; accepted independent review `97e813e0247e7e0740058d6624e726d22b1d01b2`; historic reviewed catch-up `79f552cc95758dafeb885258538f498f42befb14`; blocked evidence `5a5a88489c7995d1e930550f80bf93bb002881fa`; blocked candidate `244049bbb471067c8c1d13a63baa304070592b76` is preserved but is not a merge target.
- **startup review:** pinned baseline resolves locally; retry is independently assigned from the historic implementation and accepted-review authors; current Task remains marked mandatory integration checkpoint.
- **write scope:** this claim and its bounded integration evidence; the exact no-ff carry merge; only necessary exact `TODO.md` reconciliation; no product, review, policy, memory, or unrelated path edits.
- **prohibitions:** no amend/rewrite of the blocked candidate or retained history; no Task Acceptance, G3 Architect correction, `0044-13` work, Feature/DONE movement, `memory_append`, Memory cleanup, ref deletion, or unrelated mutation; preserve the Memory hold.

## Retry contract

Commit this claim before carriage. From the pinned target, make an explicit no-fast-forward carry of `79f552cc95758dafeb885258538f498f42befb14` with commit trailer exactly `Policy-Origin-Branch: main`. Then rerun review-currency checks, the policy-provenance gate, focused tests, candidate hygiene, immediate root preflight/equality guards, authorized root `--ff-only` merge, and immediate postflight. Stop and record `VERDICT: BLOCKED` on any new finding or target drift.

## Review-currency evidence — ready for guarded root integration

- Claim commit `ff748ffa355b65121ff74e9b474debfd8e278315` preceded the fresh carry. Carry candidate `054024476b55f02d60f2dc7a0d52c48c148c52bf` is an explicit two-parent no-ff merge of that claim line and the assigned historic catch-up, with the sole required trailer `Policy-Origin-Branch: main`.
- The pinned target still resolved to `16664ebc8622c5bd035cee9facdce9bbe2e8c7b2` during review. The product, accepted independent review, and blocked evidence remain reachable; the prohibited candidate `244049bbb471067c8c1d13a63baa304070592b76` is not an ancestor of this candidate or `main`.
- Rechecked G1/G2 directly against the pinned `DEC-0044-027` on `main`: CON-02 exists and the superseded `integration:repository-main` reference is absent. G3 remains an assigned Architect follow-up and is not altered.
- `policy-provenance-report@v2` reports no missing/malformed trailer. Its foreign-branch classifications are the intentionally reviewed historic carry and its no-ff descendants; their recorded trailers and declared no-ff absorption preserve the required topology. This differs from R1's new candidate-attributable missing-trailer finding.
- Validation: isolated-cache `py_compile` passed; focused `python3 -m unittest test_check_policy_provenance -v` passed 21/21; `git diff --check` passed. Candidate hygiene (`check_integration_hygiene.py --candidate-ref HEAD`) returned `ok: true`, with no findings.
- **VERDICT: READY FOR GUARDED ROOT INTEGRATION.** No Task Acceptance, G3 correction, product repair, Memory action, or unrelated mutation occurred.

## Supervisor-restart terminalization

The reviewed retry candidate `054024476b55f02d60f2dc7a0d52c48c148c52bf` and its carry evidence `c27b8001fcd7b6a504aaf7fe36c481711d5e9d81` are ancestors of current `main@8948a602320c7c0781ed9a578a42b664dfd2eff4`. This historic retry has no remaining authorized root action; later G3 work is recorded separately. Any new change needs a fresh exact assignment.
