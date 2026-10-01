# 0037-17 parent package verification (Dax, 2026-08-28)

Persona: unprivileged Programmer `dax-0037-17-parent-20260828` (Jadzia Dax; not gabriel, not Culber/Stamets/Rhys, not Neelix/Odo/Quark AE follow-ups).
owner_token: `agent:dax-0037-17-parent-20260828:0037-17:20260828T060352Z`
Baseline: `main@7d6d71475796d3afdacff585d25059e2059e73b3` (remeasured immediately before branch cut; matches AWARD pin).
Branch: `0037-17-parent-dax-20260828`
Worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17-parent-dax-20260828`
Git author note: host identity is `gabriel` / `gabriel@discovery.starfleet.network`; persona is Dax (same leak class as Neelix/Odo/Quark AE follow-ups).
Jean-luc HOLD `1787894028274`: no `memory_append`; `logs/agent-memory/**` not touched.

Children on this tip: `0037-17.01` REF `995c025b1bc4de575473dab95256db0ab61f8b17`, `0037-17.02` REF `71189ce1141743f71ff2c94a11bd264ef6e890bf`, `0037-17.03` REF `91b848933fb055d4c51ee62ceba0a1d6e2b8e619` — all `[x]` with `Acceptance: ✓`. Those lines were not restamped.

## Verdict

No package-level source defect. All three Subtask suites pass on this main tip. Shared causal-chain coverage lives in `_src/tests/test_provenance_query.py` (`_seed_causal` plus forward/reverse, regeneration, and identity-stability cases) together with store overwrite/collision tests and views rebuild-from-sources tests. No product edit.

## Commands and results

Worktree cwd: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17-parent-dax-20260828`. `uv run python` created a local `.venv/` (gitignored) and an untracked `uv.lock` that is **not** part of this Task.

| Command | Result |
|---|---|
| `uv run python _src/tests/test_provenance_store.py` | 23/23 OK, 0.093s, STORE_EXIT=0 |
| `uv run python _src/tests/test_provenance_views.py` | 15/15 OK, 0.615s, VIEWS_EXIT=0 |
| `uv run python _src/tests/test_provenance_query.py` | 12/12 OK, 1.225s, QUERY_EXIT=0 |
| `python3 -m py_compile` on the three tools + three test modules | PASS, PY_COMPILE=0 |
| `git diff --check` on those six paths | PASS, no product delta |
| `uv run python _src/tools/automation_safety.py --json --path` those six paths | FAIL, 8 findings, 0 policy errors, 2 unresolved critical AUTO007, 6 advisory AUTO010 |

Scoped `automation_safety` FAIL is **pre-existing** on landed 17.03 tests: AUTO007 on `test_line_symbol_movement_does_not_invalidate_file_commit_trace` (`mkdir`/`write_text` under the hermetic `tempfile` fixture root, not the repository tree). AUTO010 advisories are exclusive-create crash cleanup and disposable `_views` deletes in tests/store. This is not a DoD/causal-chain failure and is not a second-implementer rewrite of 17.01–17.03.

## DoD / acceptance mapping (package)

- **DoD:** All three Subtasks pass shared causal-chain fixtures: store 23, views 15, query 12 including `_seed_causal` forward+reverse, identical answers after index regeneration (`test_identical_after_index_regeneration_and_read_only`), hermetic closed-item rebuild (`test_hermetic_closed_item_survives_later_activity_and_index_rebuild`). No writer mutates an existing event/artifact-set identity: `test_overwrite_attempt_rejected`, `test_collision_rejects_different_payload`, `test_duplicate_id_different_digest_collision_for_artifact_set`, `test_does_not_write_immutable_sources`.
- **Acceptance criteria:** Storage remains exclusive-create immutable (`provenance_store`); indexes under `provenance/_views/` are rebuilt from sources and may be deleted (`shutil.rmtree` then rebuild in views/query tests); reverse query results are derived from validated forward events (`query_trace` reverse vs `_seed_causal` writers), not duplicated link stores.

Product files edited: **no**.
