# Claim 0037-17.03

- owner_token: agent:gabriel-rhys-20260825t085000z:0037-17.03:20260825T085000Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer, Team Discovery
- item: 0037-17.03
- branch: 0037-17.03
- worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-17.03
- base: 4184756f6de7d017e4e803df28947c66d6c9aff5 (Feature 0037 after 17.02 merge)
- merged_prereq_tips:
  - 0037-17.02 already ancestor via Feature merge `a4d9e8ac5a92ab8458f018fc497c7549e36ed8a3` (product REF `71189ce1141743f71ff2c94a11bd264ef6e890bf`)
- write_scope: `_src/tools/provenance_query.py`, `_src/tests/test_provenance_query.py`, this claim file, `TODO.md` 0037-17.03 block only for `[p]`/`[x]`
- not_in_scope: provenance/_views writers (0037-17.02); event store (0037-17.01); migrations; importer; live issues/; generated TODO/DONE; Acceptance; Integration review; DONE.md Feature move; main; push
- startup_review: assigned item; Feature tip 4184756f6 is worktree HEAD; 0037-17.02 is `[x]` ancestor; implementation start prerequisites satisfied
- queries: read-only; do not edit indexes, event store, or views on disk except tests writing disposable fixture roots

## Progress

- 2026-08-25T08:50:00Z worktree created from 4184756f6; claim minted.
- Product REF `91b848933fb055d4c51ee62ceba0a1d6e2b8e619`. Validation: `python3 _src/tests/test_provenance_query.py` 7 tests OK; `test_provenance_views.py` OK.
- Successors `0037-10.04` and `0037-23.01` remain `[ ]` (other open prerequisites). Parent `0037-17` remains `[ ]`.
