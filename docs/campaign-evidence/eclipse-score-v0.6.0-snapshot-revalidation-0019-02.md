# Task 0019-02 snapshot revalidation

## Contract and baseline

- Task: `0019-02`, prerequisite `0019-01` REF
  `111a5b90527cb6cb5f2b5bdcf8fad3a0237c41dd`.
- Candidate worktree: `/Users/tobias.anton/devel/.worktrees/chain-0019-02-william`.
- Candidate commit at test execution: `e4b8b6434acd94ec8052d8c5b4a3379377d51700`.
- Verification is offline and reads only the committed BOM, retained tar archives,
  and retained inventory. No upstream/network access was used.

## Environment and commands

The commands were run from the candidate worktree on 2026-08-29. Python reported
the repository's available `python3` interpreter; bytecode writing was disabled
to avoid test-output changes.

1. `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/score_source_snapshot.py --verify --repository-root . _src/spec/campaigns/eclipse-score-v0.6.0.json`
   - Exit `0`.
   - Output: `OK: retained snapshot verifies offline SHA-256=1f3595a67d8bd3ee6463144d01e5f9889609dd888e064c578c05fca098cf596f artifacts=787`.
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest _src.tests.test_score_source_snapshot`
   - Exit `0`; `Ran 1 test`; `OK`.
   - The test reconstructs selected artifacts from a temporary archive, checks
     deterministic locators/content hashes, and proves archive tampering is
     rejected with `SnapshotError`.
3. `sha256sum` over both retained archives and `inventory.json` independently
   reproduced:
   - `process_description` archive:
     `2aa2a2a9c592ad9410055c4451f3901094193edc08250772ac198ce856ebb655`.
   - `score` archive:
     `ecdbe01fe442369e1dabb41164e1c923b66695bf3b5b00a757ad9921751870ab`.
   - inventory:
     `1f3595a67d8bd3ee6463144d01e5f9889609dd888e064c578c05fca098cf596f`.

## Coverage and result

The verifier validated both BOM sources against their declared release refs,
resolved commits, archive SHA-256 values, selected source paths, archive member
safety, selected artifact presence, license notice presence, per-artifact
locators, sizes, and content SHA-256 values. It then compared the committed
inventory byte-for-byte with deterministic reconstruction. The resulting
inventory contains 787 selected artifacts across the two sources. All observed
results pass; no missing or unavailable in-scope artifact was observed.

The focused fixture additionally covers a positive reconstruction and a negative
tampered-archive case. No production code, BOM, archive, inventory, or upstream
resource was modified.

## Untested scope

This revalidation does not fetch upstream repositories, prove network
reproducibility, validate later extraction/profile behavior, certify the S-Core
content semantically, or perform acceptance/integration review. Those remain
outside Task `0019-02`'s offline snapshot contract.
