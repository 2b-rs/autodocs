# Task 0037-31 bounded final migration promotion — 2026-09-04

Task: `0037-31`
Original assignment: `1788519031177-793919ee`
Promotion assignment: `1788546750193-fb7f5f95`
Atomic delegation: `1788547915174-4a5b7bc0`
Authority: `DEC-0037-034`, independent Architect review `docs/dossiers/0037-31-promotion-rework-scope-review-20260904.md`, Management recovery `decision-1788546237584-7a943594`

## Immutable baselines and scope

The same active candidate lineage continues from signed recovery commit `558326103d6f2f22d90faef2452395b73ef03133`. No branch, worktree, claim, sibling candidate, selector, authority epoch, transaction ref, or integration state was created or changed.

Frozen source commit `7dbc94db262979b41bc225d6571d610123a47814`, source tree `6a6c40de53f15245a084bbdc68b526f07ab5b534`, and legacy tree digest `95084ca98c1d84bca6215da5d8763084ebc0f2a90c5a4e9d33a3a38aa96423d8` remain pinned. The rejected run `_src/output/issue-migration/0037-31-post-delta-7dbc94db-r2/` remains the red baseline with report digest `9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e`, 930 blockers, and one warning.

The fresh immutable output is `_src/output/issue-migration/0037-31-promoted-dispositions-20260904-r2/`. It was produced through `run_migration()` and not edited after promotion.

## Signed disposition inputs

- Manifest: `provenance/migrations/issue-store/0037-31-promotion/migration-dispositions.json`
- Manifest SHA-256: `82275efcd478fe3518b33ca9f61876077ae8c3e8594f0c6ba6064d6567b079b9`
- Authority: `provenance/migrations/issue-store/0037-31-promotion/migration-disposition-authority.json`
- Authority SHA-256: `512ae4acec856e74625ea6c6dd3ad5fafd03b901fe29e51af84fc9548001fe55`
- Manifest entries: 930
- Authority entries: 930
- Unique `(finding_id, rule)` pairs: 930

Population mapping: `IMP-CLAIM-OPAQUE` 418; `IMP-CLOSURE-ACCEPTANCE-MISSING` 443; `IMP-CLOSURE-CRITERION-EVIDENCE-MISSING` 12; `IMP-CLOSURE-EVIDENCE-MISSING` 16; `IMP-CLOSURE-EVIDENCE-PLACEHOLDER` 4; `IMP-FEATURE-HEADER-MALFORMED` 3; `IMP-MARKER-UNDEFINED` 1; `IMP-REF-LOCAL-PLACEHOLDER` 14; `IMP-REF-PENDING` 11; `IMP-REF-NO-EVIDENCE-CREDIT` 8.

Disposition kinds: `retain-provenance-no-active-lease` 418; `import-open-legacy-terminal-unverified` 471; `retain-provenance-no-evidence-credit` 37; `archive-excluded-from-active-migration` 3; `import-open-undefined-marker-investigate` 1.

## Promoted result

- Status/phase: `promoted` / `promoted`
- Candidate identity: `f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10`
- Observed tree digest: `61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9`
- Report SHA-256: `c3aeb3a1f8e23f331d226d3fc87df009fe603cfbe6cac1ae406ad584fa52bb2b`
- State SHA-256: `414e63cda4b276d8d536d76feffa4dd852c6f5f69a4732431d934a42f663c9b0`
- Coverage SHA-256: `f695beb217b9b5f15f0127e4a187bf4955b90bda70ac8cbcae144a70267551ae`
- Run record SHA-256: `dc41407685fe35327e191039c29209ab1804da87dcb4a78f50d463fb6a05a171`
- Findings SHA-256: `e8a623cbbaf0c9333ef3563710b36644275766d3ff3200af075ee79b87388cf8`
- Import manifest SHA-256: `326feab74652c66d56bcf0f35068ee22a43f0d381475b899d27ec221cf6a03ee`
- Blocking after coverage: false (zero blocking findings)
- Warning count: 1, preserved separately
- `closure_json_synthesized=false`
- `credit_granted=false`
- `promotable=true`

The importer change fails `source-repaired` before loading authority material, preventing unverifiable repair claims from changing diagnostic precedence. The authority test binds the current `DEC-0037-034` signed material and confirms that architecture-only or contradictory payloads remain unverified by the production verifier.

## Validation evidence

Focused/full candidate importer suite:

```text
python3 -m pytest -q /private/tmp/autodocs-worktrees/0037-31-final-frozen-migration-gate-rework-r1-lore/_src/tests/test_issue_import_legacy.py
44 passed in 98.61s (0:01:38)
```

The suite includes the red/green production path, wrong-digest and unmatched adjacent negatives, wrong-family mappings, signed authority mismatch cases, deterministic run/path containment, immutable-run and CAS failures, and AE-5 properties. Named finite properties include 64 acceptance-ref membership cases, 24 candidate set/sequence cases, 1,821 exhaustive real finding identities, six entry-order permutations plus three missing-field cases with replay seed `37029`, and four runtime deciding-role type cases.

Explicit property replay:

```text
pytest selectors: 64-case membership; 24-case set/sequence; 1,821-identity exhaustive domain; seed 37029 ordering/missing fields; four runtime role types
5 passed in 6.48s
```

The exact generated evidence check independently measured 930 manifest entries, 930 authority entries, 930 unique finding/rule pairs, all ten expected rule populations, zero blockers after coverage, one warning, and false closure/evidence-credit flags.

## Boundaries

This candidate is ready only for independent review. It grants no Acceptance or integration credit and does not update the cutover transaction ref. Geordi alone retains authority for exact-candidate transaction-ref CAS, independent policy review, integration hygiene, source integration, and reachability receipt. `0037-34.01` remains stopped until those downstream gates complete.

## DEC-0037-035 promotion-policy extension

The exact same-slot extension award is `1788578218939-4aee4c00`, held by `miles2-0037-programmer-20260904`. Governance ancestry was refreshed on the existing candidate branch by signed merge commit `5fe43cccdbd38a42767bb25506765f20f2234574`, whose parents are the pre-extension candidate `6923deec89fc15575fb23047d8236a89b3fd286e` and canonical `main@7e78a076737193811b8ab84e02e09000b69c9135`. No sibling candidate, worktree, claim, transaction ref, selector, or main ref was created or moved.

`_src/tools/issue_integration_policy.py` now recognizes a separate exact-key `0037-31-promotion-policy-proof@v1` object. It validates the complete normalized canonical delta, all five evidence files, both exact implementation/test pairs, the exact r2 subtree, and the already-retained r1 subtree. The r1 subtree is not newly authorized: every r1 blob must equal the pinned pre-extension candidate. Absolute, traversal, dot-segment, backslash, empty, duplicate, prefix-confusable, foreign, missing, non-regular, symlink, and altered retained paths fail closed. A recognized invalid promotion proof never falls through to the historical verifier or generic authority lookup.

The verifier binds the exact authority and disposition digests, verifies the allowed-signers-backed authority commit and principal through the production importer verifier, requires 930 unique signed canonical authority records, and recomputes all six r2 report hashes from candidate blobs. Report semantics require promoted status, the exact candidate identity/tree, 930 unique covered pairs, zero post-coverage blockers, exactly one warning alongside the retained 930-source-finding population, no closure/claim/approval emission, no evidence credit, and a single covered run record. The historical assignment, rejected run, report hash, and closure transaction remain conjunctively pinned and unchanged.

### Adversarial completion evidence

- **AE-2 baselines:** pre-change candidate `6923deec89fc15575fb23047d8236a89b3fd286e`; canonical baseline `7e78a076737193811b8ab84e02e09000b69c9135`; implementation candidate is the signed commit reported with Assignment `1788578218939-4aee4c00`.
- **AE-3 falsification:** the independently retained baseline invocations in the integrated Architect review are red: implementation base evaluates 980 paths with three `POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED` findings; canonical main evaluates 1,957 paths with five such findings. The repaired candidate must make both exact boundaries green without changing the old proof.
- **AE-4 adjacent cases:** (1) a complete promotion proof with exact bindings is accepted, while any one missing static binding is rejected; neighboring dimension is field presence/exact identity. (2) canonical relative paths are accepted, while traversal, dot segments, backslashes, absolute paths, a prefix-confusable r20 subtree, a missing authority file, or an altered retained r1 blob is rejected; neighboring dimension is normalized path membership and retained identity. Additional adjacent cases cover invalid promotion plus valid historical proof (rejected), wrong authority/report digest, wrong pair/warning/blocker/credit semantics, and non-regular evidence.
- **AE-5 property evidence:** deterministic finite domains enumerate all 22 required proof fields as independently absent, eight canonical/alias path forms, evidence omission and prefix collision, and recognized-promotion fallback behavior. The existing importer suite additionally retains its 64 membership, 24 set/sequence, 1,821 finding-identity, seed `37029` ordering/missing-field, and four deciding-role property domains.

Focused policy command before final candidate validation:

```text
python3 -m pytest -q _src/tests/test_issue_integration_policy.py
20 passed in 54.88s
```

## DEC-0037-036 exact interrupted-r1 retention

Management decision `decision-1788580603368-b52b66df` selected `exact_evidence_retention`; the distinct Architect review and `DEC-0037-036` are canonical at `d40d104519625fe019e0fccf04b9b32c49ac4562`. The retained r1 evidence is bound exclusively by predecessor `6923deec89fc15575fb23047d8236a89b3fd286e`, root tree `93e1703e2103fd304ec2f22fa4f6f2b83008179a`, exactly 975 `100644 blob` entries, and SHA-256 `0bb49bee19793152d0b87f677a5793f642057e3db9ab6722194810d3ac217620` of the complete canonical `git ls-tree -r` serialization. Prefix membership, byte comparison, count equality, an unpinned ancestor, reconstructed content, or matching reports cannot authorize retention. Any absent, extra, changed-path, changed-mode/type/blob, alias, symlink, non-regular entry, wrong tree, or wrong manifest fails closed. Retention grants no promotion, closure, Acceptance, evidence, validation-gate, or transaction credit.

### DEC-0037-036 real adversarial rework evidence

The production verifier reads the complete candidate `git ls-tree -r` serialization, verifies its SHA-256, exact root tree, count, every canonical path, `100644` mode, `blob` type, and blob OID, and passes the resulting exact set to the canonical-delta envelope. No r1 prefix predicate exists in the authorization path. The real test matrix executes five mutated Git candidates (absent, extra, changed blob, executable mode, symlink), wrong-tree and wrong-manifest cases, and 978 set neighbors: each of the 975 exact entries absent, plus extra-under-prefix, prefix-confusable sibling, and foreign path.

Authority tests invoke the production allowed-signers-backed verifier on the real authority commit, then reject wrong principal, commit, blob digest, and path. The record oracle rejects missing, duplicate, and payload-drift signed records. Report tests independently exercise 929 and 931 coverage pairs; zero/two warnings; blocking and credit drift; wrong source tree, run identity, disposition digest, candidate identity, and run source. Empty, null, and incomplete recognized promotion proofs are exercised through the real frozen policy and cannot fall back to historical proof. A 12-case proof-kind × canonical/implementation-boundary × matching/mismatching cross-product demonstrates that canonical-only foreign paths cannot be masked by an otherwise valid implementation delta.

Executed focused suite before candidate check-in:

```text
python3 -m pytest -q _src/tests/test_issue_integration_policy.py
22 passed in 61.67s
```
