# Independent Architect scope review — `DEC-0037-034` bounded final-migration promotion rework

## Review identity and boundary

- **Reviewer:** `agent:data:architect:0037-31:1788542643434-6ef4c01c`
- **Role:** Management-instantiated Architect, Team Enterprise
- **Assignment:** `1788542643434-6ef4c01c`
- **Capability class:** `privileged`
- **Decision authority:** resolved Management decision `decision-1788542374822-d1fb0ee1`, option `authorize_bounded_promotion_rework`
- **Reviewed baseline:** signed `main@551032a98e6a6eda1e13b786b0212de5e9ff7280`, tree `e289d9df97cc0b788ac8b876afcdd587db965a39`
- **Reviewed decision:** sibling `DEC-0037-034`
- **Verdict:** **SUPPORTS WITH BINDING CONDITIONS**

This reviewer is distinct from the eventual Implementer and from reserved
Integrator Geordi. The assignment permits only this review and its sibling
decision record. It does not implement a disposition, generate production
output, accept work, perform hygiene or integration, advance `main`, switch
authority, start `0037-34.01`, publish, push, waive a blocker, or close a Task
or Feature.

## Evidence pinned and independently measured

The coordinator-created worktree was clean on the exact awarded baseline and
branch `architect-0037-31-promotion-scope-review-20260904` before mutation.
`DEC-0037-034` was unused at that baseline. The baseline commit has a good SSH
signature by `beverly@enterprise.starfleet.network`.

| Evidence | Exact identity | Review result |
|---|---|---|
| Rejected migration report | `_src/output/issue-migration/0037-31-post-delta-7dbc94db-r2/reports/migration-report.json`, SHA-256 `9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e` | `status=rejected`, 930 blocking, 1 warning |
| Candidate companion | `provenance/migrations/issue-store/0037-31-final-frozen-candidate.json`, SHA-256 `4e7f571a79c31ce4750d520ecf8b103969cd2b4f1c892ca8280bb35ad42a24c5` | `promotable=false`, `blocked-missing-authorized-dispositions` |
| Disposition contract | `docs/dossiers/dec-0037-007-legacy-migration-dispositions.md`, SHA-256 `54e5eeeaeea38620192dc0049a5f89fa71538fd159ec46009e7fd302ece633ee` | Source/digest/signature and one-to-one fail-closed contract present |
| Family policy | `docs/dossiers/dec-0037-008-real-legacy-migration-disposition-policy.md`, SHA-256 `b14fb618bf5d7857b9c4fd4e85d6f300a67496354818ea26fae216f5ae60a5f6` | Q1–Q5 non-credit mapping covers every observed family |
| Live schema | `issues/_schema/migration-dispositions-v1.schema.json` at baseline | All five selected disposition kinds already enumerated |
| Live verifier | `_src/tools/issue_import_legacy.py` at baseline | Hermetic `import_legacy(..., dispositions=...)` validates and applies entries; production `run_migration()` has no disposition input |

The retained report's `finding_summary` is `blocking=930`, `warning=1`,
`total=931`. The earlier prose that calls all 930 findings
`IMP-CLAIM-OPAQUE` is only a primary-rule shorthand and is not an exhaustive
inventory. Scope and tests must use the measured populations below.

## Exhaustive 930-finding population and selected result

| Blocking rule / reviewed subset | Count | Required disposition kind | Result invariant |
|---|---:|---|---|
| `IMP-CLAIM-OPAQUE` / `claim-blob-retained` | 418 | `retain-provenance-no-active-lease` | Retain byte-exact claim provenance; emit no active lease, ownership, or resumability |
| `IMP-CLOSURE-ACCEPTANCE-MISSING` | 443 | `import-open-legacy-terminal-unverified` | Import OPEN with `legacy-terminal-unverified`; no Acceptance or `closure.json` |
| `IMP-CLOSURE-CRITERION-EVIDENCE-MISSING` | 12 | `import-open-legacy-terminal-unverified` | Import OPEN; no criterion evidence or closure credit |
| `IMP-CLOSURE-EVIDENCE-MISSING` | 16 | `import-open-legacy-terminal-unverified` | Import OPEN; no invented reachable commit or closure credit |
| `IMP-CLOSURE-EVIDENCE-PLACEHOLDER` | 4 | `retain-provenance-no-evidence-credit` | Preserve placeholder literally; it satisfies no evidence or closure gate |
| `IMP-FEATURE-HEADER-MALFORMED` | 3 | `archive-excluded-from-active-migration` | Retain bytes outside active indexes with all parser-independent archival safety fields |
| `IMP-MARKER-UNDEFINED` | 1 | `import-open-undefined-marker-investigate` | Preserve `[~]` provenance and import OPEN for investigation |
| `IMP-REF-LOCAL-PLACEHOLDER` / local-token placeholder | 14 | `retain-provenance-no-evidence-credit` | Preserve local token literally with zero credit |
| `IMP-REF-PENDING` / typed pending placeholder | 11 | `retain-provenance-no-evidence-credit` | Preserve typed pending state literally with zero credit |
| `IMP-REF-NO-EVIDENCE-CREDIT` | 8 | `retain-provenance-no-evidence-credit` | Retain referenced history with zero evidence credit |
| **Blocking total** | **930** | — | Exactly 930 unique disposition/finding pairs; zero blockers after coverage |

The separate `IMP-ARCHIVED-NOT-ACCEPTED` finding is warning-only. It remains
archived and receives no evidence, Acceptance, or closure credit, but it must
not be smuggled into the blocking disposition count or used to claim 931/930
coverage.

## Exact future implementation scope

One later, separately awarded Implementer may change only the following
repository-relative paths or fresh-ID patterns in one active candidate ref and
worktree. The actual assignment must enumerate the resolved concrete paths;
patterns here are architecture bounds, not write authority.

1. `_src/tools/issue_import_legacy.py` — add the minimal `run_migration()` and
   production CLI disposition-path input, validate it before candidate
   promotion, pass it to the existing import/apply pipeline, and record its
   digest/coverage in state and report output. Existing reservation, canonical
   staging, source-ref/baseline CAS, immutable-run, and atomic promotion checks
   remain conjunctive.
2. `_src/tests/test_issue_import_legacy.py` — cover production-path red, green,
   adjacent, and property obligations below. Existing hermetic disposition
   tests are retained.
3. One concrete signed authority source below
   `provenance/migrations/issue-store/0037-31-promotion/` whose basename is
   fixed by the implementation assignment and whose content is exactly
   `migration-disposition-authority@v1`.
4. One concrete `migration-dispositions@v1` JSON below the same
   `provenance/migrations/issue-store/0037-31-promotion/` directory, plus at
   most one human-readable digest/count companion if the assignment names it.
5. `issues/_schema/migration-dispositions-v1.schema.json` and its existing
   fixtures only if a test proves the live schema cannot express a required
   field already enforced by runtime. All selected kinds already exist, so an
   enum or successor-schema expansion is out of scope absent that proof.
6. A never-before-used concrete
   `_src/output/issue-migration/<fresh-0037-31-run-id>/` subtree created only by
   `run_migration()`. The run ID is fixed before execution and cannot equal,
   replace, or nest under `0037-31-post-delta-7dbc94db-r2`.
7. The existing candidate companions
   `provenance/migrations/issue-store/0037-31-final-frozen-candidate.json`,
   `provenance/migrations/issue-store/0037-31-final-frozen-candidate.md`, and
   `docs/dossiers/0037-31-final-frozen-migration-20260904.md`, updated to cite
   both the preserved rejected run and the fresh promoted run.
8. Append-only evidence on one existing or expressly allocated
   `refs/autodocs/cutover/0037/<transaction-id>` history. The assignment must
   pin the ref's expected old object and permitted evidence paths. CAS failure
   is a no-write stop; no new transaction ref may be inferred by the
   Implementer.

No second importer, generic disposition directory, broad `_src/output` write,
legacy source edit, or blanket finding suppression is necessary or permitted.
`_src/tools/issue_integration_policy.py` is outside scope unless an independent
red test proves the already integrated exact companion proof cannot represent
the fresh run. Such a finding requires scope return, not opportunistic editing.

## Authority, signature, and field binding

Every disposition entry must use the current schema/runtime required fields:
`finding_id`, `finding_rule`, `source_locator`, `item`, `source_commit`,
exactly one of `source_blob_digest` or `referenced_field_digest`, `kind`,
`reason`, `deciding_identity`, `deciding_role`, `authority_ref`, `decided_at`,
non-empty `evidence_refs`, `payload_digest`, `signature_material`, and
`signature_verified=true`. Archive exclusions additionally require
`archive_retention_justification`, `parser_independent_archival_safe=true`, and
`cannot_participate_in_active_state_reason`.

The canonical payload digest excludes only transport signature material as the
live verifier defines. Each payload digest must occur exactly once in the
signed `migration-disposition-authority@v1` `entries` array with matching
authority reference, identity, and role. `signature_material` must bind the
exact good SSH-signed Git commit, authority document path, authority blob
SHA-256, and allowed signer principal. A boolean `signature_verified` value,
mail notice, role label, capability class, branch name, or assignment ID alone
is not authority.

The source commit for all 930 entries is
`7dbc94db262979b41bc225d6571d610123a47814`; the source tree is
`6a6c40de53f15245a084bbdc68b526f07ab5b534`. A source-blob digest binds the
whole named legacy blob. A referenced-field digest binds the exact live
verifier preimage for field-class rules. The generator and verifier must derive
these values rather than accept hand-entered substitutes.

## CAS, invalidation, candidate, and transaction contract

Immediately before authority generation, manifest finalization, run
reservation, import, promotion, evidence commit, policy review, and transaction
append, re-read and compare:

- `refs/heads/main` and the frozen source ref/object/tree;
- `agent-workflow.json` authority epoch/profile/write phase and bundle digest;
- importer, schema, tests, disposition manifest, authority blob and signer;
- canonical history root, prior immutable run inventory, run ID, reservation,
  staging path and destination relation;
- the one active assignment candidate, changed-path manifest, and Geordi's
  reserved integration slot; and
- the cutover transaction ref expected old object.

Drift in any value stops before write or promotion. A run that reserved or
wrote output is retained with its actual interrupted/rejected state and is
never edited; retry uses a fresh run ID on the same active candidate ref.
Candidate corrections append linearly. Explicit atomic same-slot supersession
must name and preserve the displaced ref and worktree association, retain the
assignment and review history, and transfer rather than duplicate the
Integrator reservation.

## Mandatory falsification matrix

### Red baseline

- Reproduce the exact retained report digest and all ten blocking populations,
  totaling 930, from the unchanged source; verify the separate one-warning
  population.
- Production `run_migration()` without dispositions remains rejected and
  non-promotable.
- A Q4 terminal imported closed, any synthesized `closure.json`, any claim
  lease, or any evidence/Acceptance credit is an unconditional failure.

### Green candidate

- The signed manifest contains exactly the 930 unique blocking IDs and applies
  the table mapping exactly.
- Coverage reports exactly 930 unique pairs, no missing/extra blocker, zero
  blockers after coverage, `closure_json_synthesized=false`, and
  `credit_granted=false`.
- One fresh production run becomes promotable through the existing atomic
  staging/rename path, while the original rejected run remains byte-identical.
- Repeating derivation before reservation yields byte-identical normalized
  manifest/authority payloads and finding mapping; repeating an already used
  run ID is rejected.

### Adjacent negatives

For each of the ten rows, test wrong kind, wrong rule, wrong item, wrong locator,
wrong source commit, wrong source-blob/field digest, missing required field,
unknown field, missing/duplicate/conflicting finding ID, extra/nonblocking ID,
many-to-one mapping, empty evidence, malformed timestamp, payload-digest drift,
wrong authority entry, absent/bad/disallowed signature, wrong principal/path/
blob digest, and authority payload appearing zero or twice. Test the three
archive-only fields independently.

Also reject absent disposition input, a path outside the assigned concrete
manifest, symlink/alias/path replacement, mutable or changed input after
preflight, noncanonical history root, reused/pre-existing/nested run ID,
missing/wrong reservation or lock, source-ref/baseline regression, dirty source,
selector drift, prior-run drift, candidate-scope escape, transaction CAS
failure, and any attempt to mutate the rejected run in place.

### Exhaustive/property evidence

Use fixed seeds and record executed case counts for:

1. the Cartesian boundary of ten reviewed population rows × allowed/disallowed
   kinds × blob/field digest class × matching/mismatching ID/rule/item/locator ×
   complete/missing/duplicate coverage;
2. authority material across commit validity × path/blob/principal agreement ×
   unique payload occurrence × allowed signer outcome;
3. production orchestration across source/CAS state × history/staging/run-ID
   class × disposition-input identity × interruption point × promotion result;
   and
4. one-active-candidate state across linear correction, interruption, explicit
   supersession, stale sibling, and duplicated Integrator reservation.

Only the single fully conforming row in each applicable domain may pass. Stable
diagnostic codes and deterministic pair ordering are part of the retained
evidence.

## Rollback, downstream gate, and exclusions

Before integration, preserve the active ref and abandon the unintegrated
candidate if necessary. After integration but before authority cutover, revert
the production disposition interface, fresh promoted companion, and transaction
promotion evidence as one bounded unit; retain signed authority, manifest,
rejected/promoted/interrupted runs, decisions, reviews, commits, refs, and
audit history. Reversion must make the same 930 findings blocking again. It may
not delete, force-update, prune, or reconstruct a ref.

`0037-34.01` remains stopped until an independently assigned Integrator proves
the exact implementation candidate is an ancestor of canonical `main`, the
fresh run is promoted with zero blockers, the 930-pair and one-warning counts
match, all signatures/digests/CAS values are current, and the append-only
transaction evidence is reachable. Green tests or this review alone do not
satisfy that start gate.

Explicitly excluded: changing `TODO.md`, `DONE.md`, claims, markers,
prerequisites, Acceptance, selector/profile/epoch, legacy source files,
unrelated issue/schema/tool/test paths, prior run output, publication trees,
remote state, release policy, or Feature closure; starting `0037-34.01`;
creating a sibling correction candidate; broadening claimless transactions;
accepting residual risk; performing integration/hygiene; advancing `main`;
push, publication, cleanup, ref deletion, force-update, or garbage collection.

## Conclusion

The scope is bounded without a further Management choice. `DEC-0037-034` is
supported only with every condition above: exact 930-entry source-bound
coverage, preserved warning semantics, minimal production input, fresh
immutable run, synchronized narrow tests, one active candidate, append-only
transaction CAS, independent integration, and a still-closed `0037-34.01`
start gate. Any need to weaken a mapping, authorize a signer not already
registered, edit legacy source, broaden paths, waive blockers, or proceed with
nonzero blockers returns to Management before mutation.

## Additive distinct scope review — exact interrupted-r1 evidence retention (2026-09-05)

### Identity, authority, and separation

- **Reviewer:** `data`
- **Role:** Management-instantiated privileged Architect, independent of Implementer `miles2-0037-programmer-20260904` and Integrator `Geordi`
- **Assignment:** `1788581652660-b2c6bd14`
- **Starting ref:** signed `7e78a076737193811b8ab84e02e09000b69c9135` on retained branch `0037-31-promotion-policy-architect-review-20260904`
- **Management authority:** durable `decision-1788580603368-b52b66df`, resolved `2026-09-05T04:12:46Z`, option `exact_evidence_retention`; operative notice `1788581566919-22af5e6c`
- **Verdict:** **SUPPORTS ONLY THE EXACT EVIDENCE-RETENTION EXCEPTION BELOW, WITH BINDING FAIL-CLOSED CONDITIONS**

This is the distinct pre-mutation Architect scope review required by the cross-item gate-scope rule. It is additive to the earlier review and decides only the reach of the selected evidence-retention disposition. It supplies no implementation, integration, hygiene, Acceptance, promotion, transaction, publication, Task-closure, Feature-closure, push, or `main`-mutation authority.

### Independently derived closed allow-set

The only authorized interrupted-r1 content is the complete recursive Git tree rooted at:

`_src/output/issue-migration/0037-31-promoted-dispositions-20260904-r1/`

The authoritative source is predecessor commit `6923deec89fc15575fb23047d8236a89b3fd286e`. Its exact subtree object is `93e1703e2103fd304ec2f22fa4f6f2b83008179a`. Independent `git ls-tree -r` measurement produced exactly **975** entries, all and only mode `100644`, type `blob`; the SHA-256 of the complete canonical `git ls-tree -r` serialization, which binds every repository-relative path, mode, type, and blob OID in order, is `0bb49bee19793152d0b87f677a5793f642057e3db9ab6722194810d3ac217620`. Candidate `28bd8f3186f4637cdd051eb70bb76a57ef0829f8` resolves the same root to the same tree object and has an empty path-limited diff against `6923deec89fc15575fb23047d8236a89b3fd286e`.

The allow-set is therefore the exact 975-entry manifest encoded by tree `93e1703e2103fd304ec2f22fa4f6f2b83008179a` at `6923deec89fc15575fb23047d8236a89b3fd286e`, including each exact path, `100644` mode, and blob OID. The directory prefix is descriptive only and is never an authorization rule. Equality to any unpinned predecessor, matching bytes under a different path, a reconstructed tree, tree-size equality, count equality, report equality, or generic prefix membership cannot substitute for this exact manifest and exact root tree.

### Binding rejection predicates

The retention exception must reject before promotion or canonical write if any of the following is observed:

1. any one of the 975 authorized paths is absent;
2. any additional path appears below or is mapped into the r1 prefix;
3. any authorized path, mode, type, or blob OID differs from the pinned manifest;
4. the resolved root tree differs from `93e1703e2103fd304ec2f22fa4f6f2b83008179a`;
5. an entry is non-regular, executable, a symlink, submodule, alias, redirected path, case-folded substitute, or otherwise not the exact `100644 blob` entry;
6. validation falls back to prefix, count, byte-equality, report identity, or an unpinned ancestor instead of checking the complete exact manifest and root tree; or
7. the policy cannot bind its result to the exact current report/candidate identities and fail closed on drift.

No accepted match grants promotion, closure, Acceptance, evidence-gate, or transaction credit to r1. It establishes only that the immutable interrupted-run evidence may remain present without being treated as a new canonical promotion output.

### Mandatory implementation and test boundary remains open

Management selected retention, not a waiver. Geordi's report-binding finding `I31-POL-002` (`1788580420588-7d4c6f1a`) and test-evidence finding `I31-POL-003` (`1788580420670-756930fa`) remain mandatory same-slot repairs. The implementation must bind the policy result to the exact report and candidate evidence rather than accepting an internally valid but unrelated tree. It must include deterministic negative coverage for every absent, extra, changed-path, changed-mode, changed-type, changed-blob, wrong-tree, alias/symlink, and generic-prefix-fallback case. Because the contract asserts exact membership and multiplicity over a set, it also requires exhaustive or generative property evidence over the 975-entry allow-set and adjacent one-mutation cases, with the invariant/oracle, finite domain or generation domain, seed/replay input where applicable, and actual executed case count recorded. Existing tests that only demonstrate the happy-path equality are insufficient.

The original rejected run, all historical proof/evidence, the exact valid r2 proof, candidate `28bd8f3186f4637cdd051eb70bb76a57ef0829f8`, predecessor `6923deec89fc15575fb23047d8236a89b3fd286e`, their lineage and review history, and Geordi's existing reservation must remain preserved. No ref deletion, force-update, sibling correction candidate, replacement worktree, extra run, output rewrite, or reservation expansion follows from this review.

### Cross-item reach and authorized sequencing

The affected shared gate is the `0037-31` frozen canonical promotion policy whose result controls canonical integration and the downstream start of `0037-34.01` and later cutover work. The smallest authorized correction is therefore:

1. land this exact Architect review and the already durable Management resolution into canonical governance before any qualifying policy mutation;
2. issue an explicit same-slot rework contract against the sole active Miles2 candidate lineage, limited to the exact policy/report-binding/test repair paths authorized by the coordinator;
3. append corrections linearly, preserve r1/r2/rejected evidence unchanged, and validate the complete closed allow-set plus all mandatory negatives/property cases;
4. obtain a separate independent review of the exact repaired candidate; and
5. let the reserved Integrator perform the ordinary pinned-candidate hygiene and integration process without expanding the reservation.

Until all of those conditions are satisfied, `0037-31` canonical promotion and the `0037-34.01` start gate remain blocked. This review does not alter any Task marker, prerequisite, Acceptance record, transaction state, selector/profile/epoch, source or output bytes, candidate ref, reservation, or canonical branch.

### Scope conclusion

The selected disposition is architecturally bounded and supported only as exact evidence retention: precisely the 975 paths, their exact `100644` modes and blob OIDs, canonical manifest digest `0bb49bee19793152d0b87f677a5793f642057e3db9ab6722194810d3ac217620`, and root tree `93e1703e2103fd304ec2f22fa4f6f2b83008179a` from `6923deec89fc15575fb23047d8236a89b3fd286e`. Any absent, extra, changed, aliased, non-regular, unbound, or prefix-fallback case is outside authority and must stop. Report binding and adversarial test proof remain separate mandatory work; no promotion or closure credit is conferred.
