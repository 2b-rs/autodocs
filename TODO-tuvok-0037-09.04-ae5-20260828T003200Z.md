# Claim: 0037-09.04 AE-5 evidence follow-up

- **owner_token:** `agent:tuvok-0037-09-ae5:0037-09.04-ae5:20260828T003200Z`
- **persona:** distinct unprivileged Programmer (Tuvok); not gabriel, Chapel, Belanna, or privileged integrator
- **capability_class:** unprivileged
- **execution_authority:** direct Git/tests in this item-owned worktree; no runner queue
- **item:** 0037-09.04 AE-5 follow-up (not a second DAG product implementation)
- **branch:** `0037-09.04-ae5-20260828T003200Z`
- **worktree:** `.worktrees/0037-09.04-ae5-tuvok-20260828T003200Z`
- **base:** remesured `main@c7cff3af1bdef6f965b1e64f34df8a0489658fce` (matches dispatcher pin)
- **write_scope:** `_src/tests/test_issue_validate_dag_ae5.py`; this claim file. No `TODO.md` Acceptance; no `issue_validate.py` unless tests required it (they call existing `_dag_structural_diagnostics`).
- **must_not:** accept work; stamp `Acceptance: ✓`; `[x]` 09 parent; Feature `DONE.md`; integration checkpoint; 0037-16/28/30/31; 0039-01; 0019; spawn others; geordi; Chapel worktree; advance `refs/heads/main`; weaken IV0935/IV0937; restamp 09.01–.03

## Dispatch provenance

Discovery PL AWARD via gabriel. Verbatim dispatch prompt is the parent briefing for this session (unprivileged Programmer, four mandatory fields, AE-5 deliverable). No separate user mailbox body.

Chapel product `dd1e76a0d` already on main; 09.04 `[x]`; no Acceptance. First-review belanna `6dc2b68191ce826b5f7990e4b12fb9d32d0be2ff` INCONCLUSIVE solely for AE-5.

## AE-5 record (to be filled after tests)

- **invariant IV0935:** A stage graph is IV0935-clean iff every `depends_on` target exists, no stage depends on itself, and the directed `depends_on` graph is acyclic.
- **invariant IV0937:** A stage list is IV0937-clean iff stage ids are unique and each output path has at most one distinct writer stage id.
- **oracles:** `reference_dfs_cycle_oracle` / `oracle_iv0935`; `oracle_iv0937`
- **domain:** exhaustive directed graphs on n∈{1,2,3} labeled nodes (2^(n²) including self-loops); exhaustive n→n output assignments n∈{1,2,3} (n^n); plus 17 adjacent multi-output/dup-id cases and 2 unknown-dep/clean-chain neighbors
- **seed/replay:** none (finite enumeration)
- **executed_cases:** 581 (530 graphs + 32 writer maps + 17 adjacent writer + 2 adjacent cycle)
- **validation:** `/tmp/ae5-tuvok-venv/bin/python -m unittest _src.tests.test_issue_validate_dag_ae5 -v` → 5 tests OK (0.028s). Product `_src/tools/issue_validate.py` unchanged.
- **follow-up disposition on this branch:** implementation complete (`[x]` of this AE-5 follow-up only; 09.04 parent marker and Acceptance untouched).
