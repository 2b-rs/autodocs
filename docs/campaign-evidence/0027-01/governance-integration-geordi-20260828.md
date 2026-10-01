# Governance integration review — retained MAN.3 `DEC-0027-001`

**Integrator:** `agent:geordi:0027-01-governance-integration:1787908518545-c161f96f`, privileged Integrator, Team Enterprise  
**Assignment:** Project Lead `jean-luc`, OFFER `agent-inbox:1787908399456-52a5f935`, AWARD `agent-inbox:1787908518545-c161f96f`  
**Offered target:** `main@a1afbae4aa2d7174318452f6ccf1212158176955`  
**Refreshed target:** `main@3dd4e23354886134939a7a161458f3123a8c791e`, `agent-inbox:1787908664056-336132c9`  
**Candidate / corrected review:** `8772645587fd41ae873aeb9c48c061de134d581c` / `4b513b343231274aeddd426a4c4c3e7b986fa44b`

## Assembly and exact scope

- Claim-first REF: `ceb7c428b4eb3a32791c5cdb853d05e2e4d8dd6d`.
- Offered-to-current drift consists of three commits changing only `TODO-tilly-0037-11.02-ae45-20260828T082900Z.md` and `_src/tests/test_issue_views.py`. It is disjoint from the awarded six-path integration scope and was explicitly classified nonmaterial; merge `9ec539f1ab` reconciles the branch to the refreshed target.
- Candidate carry `b6d32a1643` contains byte-exact blobs for Data's claim and `docs/dossiers/dec-0027-001-man3-plan-gate-scope.md`. Its policy-origin trailer records `gov-0027-01-gate-scope-data-20260827`. Candidate `TODO.md` was not carried.
- Review carry `87bad005cd` contains byte-exact corrected blobs for Seven's claim and review dossier from `4b513b3432`. The zero-byte superseded review files from `d7e8275458` were not carried as content; their disclosed provenance remains in the corrected review.
- Before this evidence commit, refreshed-target-to-candidate delta was exactly the four awarded carry paths plus the Integrator claim. This evidence is the sixth and final awarded path. No `TODO.md`, `DONE.md`, interface, source/tool/test, Memory, or unrelated dossier path changed.

## Independent findings

- **Independence and authority — PASS.** Current roster records Data and Seven as privileged Architects and Geordi as privileged Integrator. Data authored the decision, Seven supplied the supporting scope review, and Geordi performed this integration review. Main-visible additive correction in `docs/campaign-evidence/0027-05/scope-review-currency-dec-0027-002-seven-20260828.md` supplies the corrected reading: the roster instantiates Seven's Architect role; the OFFER/AWARD assign only bounded scope. Mail is not treated as authority.
- **Record and review conformance — PASS.** `DEC-0027-001` contains the required ordered decision-record fields, four alternatives with exactly one selected, explicit affected work units/gates, no-review reason and waiver. Its SHA-256 is `c21b2d04c57a685e88bdd03e761a209b933fb089090c4f1a418c0d75ad76f495`, exactly the digest pinned by the independent review. The corrected review is non-empty, pins candidate `8772645587`, discloses the zero-byte predecessor, and returns `scope-ready-for-mutation` subject only to C-1.
- **Decision identity — PASS.** The assembled tree has exactly one header for `DEC-0027-001` and one for the already integrated `DEC-0027-002`; the abandoned SUP.8 `DEC-0027-001` remains provenance-only and is not a live dossier.
- **Single terminal allocation — PASS.** MAN.3 `DEC-0027-001` allocates `0027-11` as the sole terminal Feature integrating Task. SUP.8 `DEC-0027-002` explicitly consumes that allocation, contributes its parent prerequisite and reconciliation criteria, rejects a second terminal allocation in ALT-05, and forbids creating another `0027-11` in CON-01.
- **C-1 and activation boundary — PASS.** The carried review permits the dossier unchanged but requires the later `TODO.md` activation owner to name and record reconciliation of the foreign `[u]` versus governance `[p]` marker projections before any marker delta integrates. This integration carries no marker mutation, does not create or activate `0027-11`, and does not release that later obligation.
- **Drift and policy provenance — PASS.** Refreshed drift is disjoint. `check_policy_provenance.py` classifies `b6d32a1643` as `source-origin`, with no foreign policy commit and no missing trailer.
- **Documentation validation — PASS with disclosed repository findings.** `process_doc_doctor.py --root . --json` exited `0`, `ok: true`, with 34 repository findings. None names either newly carried `0027-01` dossier/review path; the one error is a pre-existing broken link in `docs/dossiers/0044-03-gate-scope-proposal.md`. `git diff --check` passed.

## Verdict

**PASS — ready for exact-candidate hygiene and the guarded root integration sequence.** This is an integration verdict only. It performs no Acceptance, backlog/interface activation, `0027-11` creation, Feature/`DONE.md` movement, cleanup, or scope expansion.

## Guarded integration result

- Exact candidate `c7bbdeb108fb4f89aff3d75f655ac0d695771180`: `check_integration_hygiene.py --candidate-ref` exited `0`, PASS, across 222 registered worktrees.
- Immediate root preflight exited `0`, PASS, across 222 registered worktrees.
- While the review ran, `main` advanced disjointly through `22acd85fddd7b3449e3c4078d79b813d3094f9a4`; its changes were confined to the `DEC-0044-029` claim/evidence package and `docs/pipeline/core-rules.md`, with no awarded-path overlap. The exact-candidate overlap gate passed against that live root.
- Provenance-preserving root merge: `1f0bace76f835ffb9b51f340ca34b8ee98fc6bce`, first parent `22acd85fddd7b3449e3c4078d79b813d3094f9a4`, second parent `c7bbdeb108fb4f89aff3d75f655ac0d695771180`.
- Immediate post-merge root preflight exited `0`, PASS, across 222 registered worktrees.

**Final verdict: INTEGRATED / PASS.** C-1 remains assigned to the later backlog-activation owner; no marker or interface mutation was carried.
