# Task 0037-31 final frozen migration gate rework — 2026-09-04

Task: `0037-31`  
Assignment: `1788519031177-793919ee`  
Same-slot successor: `1788521108922-dbc1a91c`

Lore implemented only the two repairs authorized by `DEC-0037-033`: a
conjunctive, internal reserved-staging capability in the importer and an exact
claimless assignment/source/transaction manifest proof in frozen integration
policy. Existing direct-call, live-root, claim-bound, and unrelated frozen-path
behavior remains fail-closed.

The retained red baseline is signed commit
`34ede49b3c44f878c0fd3bcbae269d11a72c64f2`. The fresh run
`0037-31-post-delta-7dbc94db-r2` against source
`7dbc94db262979b41bc225d6571d610123a47814` and tree
`6a6c40de53f15245a084bbdc68b526f07ab5b534` crossed the repaired staging gate,
generated candidate identity
`99df63c31c7ab923b62bf73cd961e80e918978f63f2028281e7e9a6937df6137`, and
retained tree digest
`261a1e0945599e728989cdade303dfd709c557c894b2fac941aac6ac00597080`.

The candidate is not promotable. After import, 930 `IMP-CLAIM-OPAQUE`
findings required signed dispositions. Neither pinned source nor award provides
that authority document, and the production orchestrator has no disposition
input. This is a newly exposed independent blocker, not permission to add a
third gate exception, infer authority, or weaken the approved importer.

The JSON companion binds the exact assignment, source, closure transaction,
allowed paths, run identity, candidate identity, report digests, and these two
companion blobs. Frozen-policy validation of that complete proof is evidence
only; it grants no claim, Task marker, Acceptance, integration, cutover, or
Feature closure.

## Same-slot rework validation

Management decision `decision-1788538399088-6195c7c7` authorized the actual
eight-entry candidate scope as an additive control-plane overlay for assignment
`1788525001126-a203ba2c`. The preserved candidate
`bbfadfaee65b443ab98cdeb6f1c4e0b71b2b2544` was merged linearly with pinned
`main` commit `f4efd55476f33ea024c54df21a34d6e380c976ef`; the resulting candidate
diff remains exactly 980 files within that authorized scope.

Post-merge focused validation passed:

```text
python3 -m pytest -q _src/tests/test_issue_import_legacy.py _src/tests/test_issue_integration_policy.py
56 passed in 557.59s (0:09:17)
```

This same-slot correction adds no sibling ref, worktree, claim, Acceptance,
integration, publication, or authority beyond the resolved scope overlay.
