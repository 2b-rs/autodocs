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
