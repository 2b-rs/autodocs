# Independent scope review — final-migration promotion proof

## Identity, authority, and result

Reviewer: `agent:data:architect:0037-31:01a06c35-4fd7-74c2-81dc-97cf6cfb8f1f`.
Capability: `privileged`; process role: Management-instantiated Architect,
distinct from promotion Implementer Lore and reserved Integrator Geordi.
Assignment: `1788549291503-3e8815ee`; exclusive session designation:
`1788549889007-24dc7e8e`. Decision:
`decision-1788549180711-76247bba`, verified resolved to
`authorize_bounded_review`, recorded in sibling `DEC-0037-035`.

**SUPPORTS WITH BINDING CONDITIONS.** This is a pre-mutation gate-scope review,
not an implementation review, Acceptance, hygiene verdict, integration receipt,
or permission to start `0037-34.01`. Only this document and the sibling decision
are authored under this award. No claim, backlog, code, test, production output,
companion, transaction ref, selector, remote, or main is changed.

## Pinned evidence and independent red reproduction

Review branch `0037-31-promotion-policy-architect-review-20260904` was created
clean from canonical `main@2e753cdecf8b59c6283ce4482fe048b78ea9405e`, in
`/tmp/autodocs-worktrees/0037-31-promotion-policy-architect-review-data`.
No competing named candidate/worktree or DEC-0037-035 existed at allocation.
Read `DEC-0037-034`, its complete scope review, the current policy, candidate
companions, and the durable Management request. The request records Geordi's
evidence `1788549113983-3354eb16` and `1788549132236-e6073687`.

Independently ran the baseline policy with `PYTHONDONTWRITEBYTECODE=1`,
`--json`, candidate `6923deec89fc15575fb23047d8236a89b3fd286e`, and `--root`
pointing read-only at its existing implementation worktree:
`/tmp/autodocs-worktrees/0037-31-final-frozen-migration-gate-rework-r1-lore`.

| Explicit base | Evaluated paths | Result |
|---|---:|---|
| `558326103d6f2f22d90faef2452395b73ef03133` | 980 | Exit 1; three companion authority-proof findings |
| `2e753cdecf8b59c6283ce4482fe048b78ea9405e` | 1957 | Exit 1; the same three plus disposition authority and manifest |

All five findings are `POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED`. An initial
invocation against the review worktree correctly failed
`CANDIDATE-TREE-MISMATCH`; it was not counted as the red reproduction.
The successful reproduction used the exact candidate worktree, without
writing there. No production migration or hygiene/integration was run.

The existing `_claimless_0037_31_proof()` validates only the old closed
assignment/run/path set. The candidate retains that old proof and adds a
`promotion` object, but its new authority/manifest paths and fresh run are not
covered by that proof. This is the precise scope-return condition anticipated
by `DEC-0037-034`, not evidence that frozen checking should be disabled.

## Supported future mutation and closed scope

After both dossiers are canonically integrated, an explicit same-slot award
may add only `_src/tools/issue_integration_policy.py` and
`_src/tests/test_issue_integration_policy.py` to the existing implementation,
plus synchronization of these existing companions:

- `provenance/migrations/issue-store/0037-31-final-frozen-candidate.json`
- `provenance/migrations/issue-store/0037-31-final-frozen-candidate.md`
- `docs/dossiers/0037-31-final-frozen-migration-20260904.md`

Implement one distinct promotion verifier with a closed, exact-key proof
contract. Retain the historical verifier, its constants, and valid historical
fixtures without relaxing their semantics. A recognized but invalid promotion
proof must fail closed rather than fall back to historical proof, prose owner
tokens, generic claim lookup, or Markdown companion recursion.

The new proof may authorize exactly the five named evidence files (the three
companions plus the two disposition JSON files), not arbitrary dossier or
provenance siblings. Its whole-delta envelope may additionally contain the
already authorized importer and importer test, the policy and policy test,
and the exact fresh run subtree. The original rejected run is retained
unchanged; any delta there is a failure, not an additional allowed prefix.
No schema expansion is needed for this policy repair. Any other necessary
path or gate change returns for scope review before mutation.

Every changed path from actual current canonical main must be accounted for,
including governance ancestry and deletions; do not choose the implementation
base to hide paths. Governance records already integrated on main must remain
in the aggregate candidate. Refresh ancestry on the same active ref through
the authorized workflow; never permit their deletion via a broader proof.

## Exact proof bindings

Bind and verify all of the following conjunctively against immutable Git blobs
and the actual authority record, not candidate assertions alone:

1. Task `0037-31`, promotion assignment `1788546750193-fb7f5f95`, delegation
   `1788547915174-4a5b7bc0`, and the subsequent exact same-slot policy-extension
   award; the latter must be explicit before implementation. Cite
   `DEC-0037-034` and `DEC-0037-035` and retain their integrated ancestry.
2. Frozen source `7dbc94db262979b41bc225d6571d610123a47814`, tree
   `6a6c40de53f15245a084bbdc68b526f07ab5b534`, legacy tree digest
   `95084ca98c1d84bca6215da5d8763084ebc0f2a90c5a4e9d33a3a38aa96423d8`,
   and unchanged `legacy-lists` / `legacy-frozen` / `frozen` selector state.
3. Run `0037-31-promoted-dispositions-20260904-r2` and root exactly
   `_src/output/issue-migration/0037-31-promoted-dispositions-20260904-r2/`.
   No parameterized future-run wildcard; changing the run requires explicit
   rebinding under the reviewed authority, without rewriting immutable output.
4. Exact authority path
   `provenance/migrations/issue-store/0037-31-promotion/migration-disposition-authority.json`,
   SHA-256 `512ae4acec856e74625ea6c6dd3ad5fafd03b901fe29e51af84fc9548001fe55`;
   exact manifest path
   `provenance/migrations/issue-store/0037-31-promotion/migration-dispositions.json`,
   SHA-256 `82275efcd478fe3518b33ca9f61876077ae8c3e8594f0c6ba6064d6567b079b9`.
   Verify the manifest's authority commit, allowed signer principal, blob
   digest, and unique matching signed payload entries through the existing
   authority verifier. Neither a digest nor `signature_verified=true` alone
   authenticates authority.
5. Promoted identity
   `f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10`
   and tree digest
   `61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9`.
   Derive report, state, coverage, run-record, findings, and import-manifest
   hashes from actual candidate blobs and compare all six with the promotion
   object. Check report semantics: promoted, zero blockers, exactly 930 unique
   pairs, one warning, no closure synthesis or evidence/Acceptance credit.
6. The exact evidence path set and full normalized changed-path set, using
   repository-relative canonical paths only. Reject absolute paths, traversal,
   dot segments, empty segments, backslash aliases, prefix-confusable siblings,
   duplicate normalized paths, symlink or non-regular evidence, and unknown
   proof fields. Check path boundaries, not loose string prefixes. Account for
   deletions, modes, and both ends of renames.
7. Both Markdown companion SHA-256 values recomputed after synchronization;
   the JSON evidence is pinned by its immutable candidate commit/blob digest
   in the review receipt, avoiding a self-hash cycle. Companion text binds the
   promotion assignment and source/run, without fabricating an active claim.
8. Preserve old assignment `1788519031177-793919ee`, rejected run
   `0037-31-post-delta-7dbc94db-r2`, its report digest
   `9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e`,
   and historical transaction `f5a806c52a63e00edac5c0aa8bb0793227ae3af1`.
   Do not present that transaction as proof of new promotion CAS. The new
   append-only transaction receipt is separately verified by the authorized
   Integrator before the downstream start gate, not assumed by this review.

These pinned values describe the reviewed candidate, not an implementation
Acceptance. If evidence disagrees, preserve it and reject; do not edit a report
or repin a digest simply to make the checker green.

## Required falsification and green evidence

Retain both red invocations above. The repaired candidate must pass against
actual canonical main and its implementation base with complete path counts
and exact commits recorded. Also retain an unchanged old-proof positive and
all old-proof negatives. Test each new binding independently absent, malformed,
wrong, and stale, including correct old assignment with wrong promotion
assignment and a superficially valid old proof masking an invalid promotion.

Mandatory adjacent negatives: each of the five evidence files omitted or
altered; altered authority principal/commit/blob/payload; missing or duplicate
signed entry; bad manifest digest; changed report hash and changed report
semantics; reused/nested/wrong run; wrong source/tree/epoch; extra sibling path;
path traversal/alias/prefix collision; deleted old evidence; symlink/mode
change; unsynchronized companion; incorrect candidate identity/tree; 929 or
931 pairs; zero or two warnings; nonzero blockers; closure or evidence credit;
unknown keys; missing current main governance ancestry; generic-fallback
attempt; and a valid implementation delta hiding a canonical-delta violation.

Use deterministic finite/property cases crossing proof kind (historical,
promotion, invalid mixed), allowed/foreign path classes, matching/mismatching
binding, and canonical/implementation base. Record seeds and executed counts.
Only fully conforming combinations pass. These are implementation obligations,
not tests claimed executed by this dossier-only review.

## Drift, recovery, and downstream boundaries

Re-read current main, candidate, assignment scope, selector, source, manifest,
authority, companions, and transaction expected-old object before consequential
actions. Drift invalidates prior validation; rebind and repeat on the same
active implementation ref. A changed production input requiring rerun follows
DEC-0037-034 fresh-ID rules, never in-place run repair. No duplicate branch,
worktree, offer, or Integrator slot follows from this extension.

Before integration retain all signed candidates and evidence. After integration
and before cutover, separately authorized recovery reverts promotion proof and
promotion consumption together while retaining the old proof and all evidence;
promotion returns to blocked. No ref deletion, force-update, pruning, cleanup,
or authority switch is part of this review.

The affected gate is the shared frozen integration policy, with consequences
for `0037-31` integration and `0037-34.01`, `0037-32`, `0037-33`, `0037-34.02`,
and Feature 0037 closure. That reach makes the pre-mutation review mandatory.
Governance integration, exact same-slot implementation award, independent
implementation review, policy validation over current main, transaction CAS,
hygiene, and canonical candidate ancestry remain separate gates. This review
crosses none of them and grants no waiver.

## Append-only identity correction — 2026-09-04

This correction supersedes only the current-implementer identification in
the opening identity paragraph. The original wording remains visible above
and in commit `7130072fe8564f5e07c702f5b8a3b126606b9f06`; it must not be used
as the effective independence declaration. Geordi identified the error in
review finding `1788550441348-ef037d25`. Same-slot rework award
`1788550461499-d7e80e5d`, attached to Architect assignment
`1788549291503-3e8815ee`, requires this provenance-preserving correction.

The current promotion Implementer is `miles2-0037-programmer-20260904`, under
parent implementation assignment `1788546750193-fb7f5f95` and delegation
`1788547915174-4a5b7bc0`, as identified by the rework contract. Lore is not
the current delegated Implementer. The retained implementation worktree's
`-lore` suffix is a historical location label, not ownership evidence.
Candidate `6923deec89fc15575fb23047d8236a89b3fd286e` independently records
the parent assignment and delegation in its commit trailers; its Git author
name is not used as session-identity proof.

The reviewer is the distinct Data session
`agent:data:architect:0037-31:01a06c35-4fd7-74c2-81dc-97cf6cfb8f1f`,
assigned to pre-mutation architecture review under `1788549291503-3e8815ee`.
This session authored the architecture dossiers and performed read-only
candidate checks; it did not implement the production promotion or mutate
the implementation candidate. Geordi remains the separately assigned
Integrator. Neither privilege, a display name, a mailbox message, a worktree
suffix, nor the Git author field alone establishes independence, assignment,
Acceptance, or integration authority. The correction changes no technical
scope, proof condition, validation result, gate, or reservation.

Coordinator verification received at `2026-09-04T19:36:38Z`
(`1788550598347-32a46eef`) supplies the assignment-state evidence: delegation
`1788547915174-4a5b7bc0` is awarded to
`miles2-0037-programmer-20260904`; parent `1788546750193-fb7f5f95` has the
same winner and remains `on_hold`. The registered Programmer appointment is
supervisor reference `1788548087047-84720986`; atomic transfer references are
`1788548187638-a8247522` and `1788548187757-bf6ec1ff`. Data's direct status
query was denied because Data is not a participant in that implementation
offer; this is explicitly coordinator-verified state, not claimed direct
inspection. The notice points to those appointment and award records; it does
not itself create authority or waive the independent review requirement.
