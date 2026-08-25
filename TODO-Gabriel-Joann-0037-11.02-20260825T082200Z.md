# Claim: Subtask 0037-11.02

- owner_token: `agent:gabriel-joann-20260825t082200z:0037-11.02:20260825T082200Z`
- agent/persona: Gabriel-Joann-20260825T082200Z, unprivileged Programmer, Team Discovery
- capability_class: `unprivileged`
- execution_authority: direct local Shell/Git in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-11.02` / `0037-11.02` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-11.02`
- Feature base at start: `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a` (HEAD already on the item branch at this tip)
- prerequisite branches: `0037-05`, `0037-08`, `0037-09` already present on Feature tip; no additional merge required
- startup_review: `TODO.md` Task text, `AGENTS.md`, `SANDBOX.md`, `docs/pipeline/branch-workflow.md`, `issue_store.py`, `issue-item-v1` schema
- exact_write_scope:
  - `issues/_views/catalog.json`
  - `issues/_views/dependency-graph.json`
  - `issues/_schema/issue-catalog-v1.schema.json`
  - `issues/_schema/issue-dependency-graph-v1.schema.json`
  - `_src/tools/issue_views.py`
  - `_src/tests/test_issue_views.py`
  - `_src/tests/fixtures/0037-11.02/**`
  - `TODO-Gabriel-Joann-0037-11.02-20260825T082200Z.md`
  - only the `0037-11.02` Task block in `TODO.md` for `[p]`/`[x]` bookkeeping
- external_resources: none
- prohibitions: no Acceptance, no Integration review, no `DONE.md` Feature move, no `main`, no 0037-11.01/17.01/13, no other Features, no runner-queue
- status: `[p]` implementing catalog and dependency-graph views

## Findings and progress

- HEAD confirmed `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a`.
- A prior Joann identity `20260825T081500Z` is not reused.
- Generator is `_src/tools/issue_views.py`; views are generated-only and fail closed on stale/hand-edited bytes.
