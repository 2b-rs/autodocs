# Claim 0037-11.02

- **item:** `0037-11.02`
- **owner_token:** `agent:gabriel-joann-20260825t081500z:0037-11.02:20260825T081500Z`
- **agent:** `Gabriel-Joann-20260825T081500Z`
- **capability_class:** `unprivileged`
- **execution_authority:** direct Git/Python in item worktree; no runner; no privileged acceptance
- **startup_review:** Feature base pin `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a` (`refs/heads/0037`). Prerequisites `0037-08` (`15b50c7c0b4943b12cf703a7f9b612bb3388d948`) and `0037-09` (same pin) are ancestors. `0037-05` work is already on `0037` (`eade8f5361` / `f05ce02a7c`). No extra prereq merges.
- **write_scope:** `issues/_views/catalog.json`, `issues/_views/dependency-graph.json`, generators under `_src/`, matching tests/schema/goldens, this claim, `TODO.md` 0037-11.02 block only
- **must_not:** Acceptance, checkpoints, `main`, `DONE.md`, push, `0037-17.01`, `0037-11.01` generated lists, `0041-02`, `0011-0018`, `0033`, `uv.lock`, hop
- **branch:** `0037-11.02`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-11.02`

## Deliverables

- `_src/tools/issue_views.py`
- `issues/_schema/issue-catalog-v1.schema.json`
- `issues/_schema/issue-dependency-graph-v1.schema.json`
- `_src/tests/test_issue_views.py`
- `_src/tests/fixtures/0037-11.02/`
- generated `issues/_views/catalog.json` and `issues/_views/dependency-graph.json`

## Validation

`python -m unittest _src.tests.test_issue_views -v` (9 tests, OK)

## Closure

- **product REF:** `bdffd04e8f6221490b5fb773673804936bbf330d`
- **disposition:** implementation complete `[x]`; no acceptance credit
