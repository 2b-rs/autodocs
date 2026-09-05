# 0037-31 final frozen migration candidate — promoted disposition r2

- Task: `0037-31`
- Original frozen assignment: `1788519031177-793919ee`
- Same-slot promotion assignment: `1788546750193-fb7f5f95`
- Atomic delegation: `1788547915174-4a5b7bc0`
- Source: `7dbc94db262979b41bc225d6571d610123a47814`
- Source tree: `6a6c40de53f15245a084bbdc68b526f07ab5b534`
- Preserved rejected run: `0037-31-post-delta-7dbc94db-r2`
- Fresh promoted run: `0037-31-promoted-dispositions-20260904-r2`
- Result: `promoted`, `promotable=true`, pending independent review and integration

The original rejected run remains the immutable red baseline: 930 blocking findings and one warning, with report SHA-256 `9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e`.

Under `DEC-0037-034`, the fresh production run applies a signed, source-bound `migration-dispositions@v1` manifest to exactly 930 unique blocking finding pairs. Coverage is complete and deterministic: zero blockers remain, the single `IMP-ARCHIVED-NOT-ACCEPTED` warning is preserved, `closure_json_synthesized=false`, `credit_granted=false`, and no active lease, Acceptance, closure, or evidence credit is invented.

The promoted candidate identity is `f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10`; its observed tree digest is `61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9`. The migration report and state digests are `c3aeb3a1f8e23f331d226d3fc87df009fe603cfbe6cac1ae406ad584fa52bb2b` and `414e63cda4b276d8d536d76feffa4dd852c6f5f69a4732431d934a42f663c9b0` respectively.

This is implementation evidence only. It creates no Acceptance, integration verdict, transaction-ref update, publication, cutover, or permission to start `0037-34.01`. Geordi retains the reserved independent CAS/review/integration slot.

## Closed promotion-policy proof extension

- Policy-extension award: `1788578218939-4aee4c00`
- Governing decision: `DEC-0037-035`
- Canonical validation baseline: `d40d104519625fe019e0fccf04b9b32c49ac4562`
- Pre-extension candidate: `6923deec89fc15575fb23047d8236a89b3fd286e`

The separate `0037-31-promotion-policy-proof@v1` object binds the parent assignment, delegation, exact extension award, frozen source/tree, signed disposition authority and manifest, all six immutable r2 reports, promoted identity/tree, complete normalized canonical delta, and synchronized companions. The historical `claimless-frozen-assignment-proof@v1` remains unchanged. A recognized invalid promotion proof fails closed and cannot fall back to the historical proof, a generic claim, or Markdown recursion. The retained r1 output is admissible only when every candidate blob remains byte-identical to the pinned pre-extension candidate; it grants no new authority.

## DEC-0037-036 exact interrupted-r1 retention

Management decision `decision-1788580603368-b52b66df` selected `exact_evidence_retention`; the distinct Architect review and `DEC-0037-036` are canonical at `d40d104519625fe019e0fccf04b9b32c49ac4562`. The retained r1 evidence is bound exclusively by predecessor `6923deec89fc15575fb23047d8236a89b3fd286e`, root tree `93e1703e2103fd304ec2f22fa4f6f2b83008179a`, exactly 975 `100644 blob` entries, and SHA-256 `0bb49bee19793152d0b87f677a5793f642057e3db9ab6722194810d3ac217620` of the complete canonical `git ls-tree -r` serialization. Prefix membership, byte comparison, count equality, an unpinned ancestor, reconstructed content, or matching reports cannot authorize retention. Any absent, extra, changed-path, changed-mode/type/blob, alias, symlink, non-regular entry, wrong tree, or wrong manifest fails closed. Retention grants no promotion, closure, Acceptance, evidence, validation-gate, or transaction credit.
