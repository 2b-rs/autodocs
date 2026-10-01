# 0041-04 Enterprise coordination plan

## Pinned start

- `main@f5763cf21e98066f7e932d50a2b0e9c5802550f9`
- Task `0041-01`: `[x]`, REF `8aafc0cb4`.
- Task `0037-51`: `[x]`, current Acceptance review `b6d2bfdfe4850ad2cf7c1d898105088409e01378`.
- Task `0041-04`: `[ ]`, start prerequisites satisfied.
- `DEC-0041-007`: use a direct item-scoped Git publication path; do not restore host-runner transport and do not consume historical 0041-04 lineage as implementation input.

## Implementation package

The implementer will create the direct publication tool, hermetic disposable-repository tests, registered documentation/0041-01 compatibility note, and its own coordination claim. The interface must accept explicit repository, assigned item, source branch, canonical bare target branch, remote, and expected old object. It must fail closed before push on protected refs, force/non-fast-forward updates, assignment mismatch, dirty/unrelated state, stale expected old object, ambiguous remote, and source/target identity mismatch; preserve canonical worktree bytes; emit machine-readable outcome/recovery evidence; support dry-run, retry, and idempotent already-published state; and perform no credential discovery or authority inference.

## Verification and boundary

The child delivery must include focused hermetic tests for success and every refusal, CAS race, interruption/retry, and idempotence, plus automation safety and `git diff --check`. All remotes are disposable local repositories. The chain ends after exact-scope result verification and returns to the Project Lead. It does not enter `0041-05`, publish externally, accept work, integrate, move `main`, or exercise protected-ref, credential, release, Management, or risk authority.
