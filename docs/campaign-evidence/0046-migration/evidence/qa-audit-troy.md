# Independent QA process audit — Task 0046-05

- **Auditor:** Troy, Team Enterprise QA Manager
- **Function:** independent process audit only; not Task Acceptance or checkpoint review
- **Substantive candidate:** `9f12447450fed57f3c3f548492c74bea96f3b087`
- **Evidence/claim milestone and audit base:** `8f05909c67a12b78472349196aea550c4870b348`
- **Declared manifest digest:** `sha256:d6bb99803472f207cab4805e6fc4ffdb6a37384eb606c94602a19c3bd016af34`
- **Conclusion:** `findings`

## Positive evidence reproduced

- The pinned baseline `c55cca8786d99f91d400f720cbcec616e228a6df` is reachable. Its `TODO.md` SHA-256 independently reproduces as `sha256:97a124e4fef596616e6026acda128fcb90cff28a01b554974889137a208780d8`.
- Independent parsing finds 32 unique Feature blocks in the pinned `TODO.md`; their set equals the 32 unique manifest rows.
- Dispositions reproduce as 0 `migrated`, 1 `compatible-with-bounds` (`0046`), and 31 `deferred`.
- The canonical manifest digest independently reproduces exactly as declared. All currently populated branch and evidence refs are reachable, and every row has non-empty omissions, risk, owner, revisit trigger, recovery, and validator-result fields.
- The committed validator returns valid with zero findings. Its eight focused tests pass. Tests were run with `PYTHONDONTWRITEBYTECODE=1`; the assessed tree remained unchanged.
- The report explicitly treats the candidate as dormant, grants no activation or execution authority, labels unknown Features deferred, rejects implicit grandfathering in prose, and contains no QA or Acceptance claim.
- The milestone differs from the substantive candidate only in Wesley's claim. During this audit, the only branch change before this report was the committed Troy audit claim.

## Findings

### F-0046-05-QA-001 — builder is not reproducible from the pinned baseline alone

`build_manifest.py` reads `TODO.md` from `baseline_ref`, but resolves each `refs/heads/<feature>` through the live repository at regeneration time. Moving, creating, or deleting a Feature branch therefore changes `inventory.json`, `manifest.json`, `report.md`, and their digests while the requested baseline remains identical. The reproduction command in the report consequently does not define a one-baseline deterministic build.

Required disposition: bind branch-state input to an immutable snapshot or explicit pinned ref map included in the digest, and add a focused test proving that ambient branch movement cannot alter regeneration for the same declared inputs.

### F-0046-05-QA-002 — validator does not enforce required row bindings

The validator compares work units and mandatory gates with the inventory but does not compare `feature_branch`, does not require each row's `baseline_ref` to equal the manifest baseline, and checks evidence-ref reachability without requiring a non-empty evidence path. In independent in-memory mutations, each of the following remained `valid: true` with zero findings after correctly recomputing the manifest digest:

1. replacing Feature `0046`'s branch ref with a different reachable commit while leaving inventory unchanged;
2. removing Feature `0046`'s row-level baseline binding; and
3. blanking its WTP evidence path.

Thus a green result does not currently prove the acceptance criterion that every row binds its Feature/branch baseline and available WTP/IP evidence.

Required disposition: validate exact row-to-inventory branch object equality, row baseline equality, branch name/state vocabulary, and non-empty evidence path/ref fields; add refusal fixtures for each case.

## Boundary statement

No assessed artifact was edited or repaired. This audit grants no Acceptance, checkpoint result, integration authority, gate activation, Feature closure, or `main` mutation. The implementation owner must disposition the findings on a new candidate before relying on this audit as a passing operational QA result.
