# Claim: Task 0037-22

- owner_token: `agent:gabriel-graphhtml:0037-22:20260825T114200Z`
- agent/persona: Gabriel-Graphhtml, unprivileged Programmer, Team Discovery
- dispatcher: gabriel; jean-luc `1787658051022-50ec1d09`
- capability_class: `unprivileged`
- execution_authority: direct local Shell/Git in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-22` / `0037-22` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-22`
- Feature base: `722aaa2149c78cf705db411a4142c67d92bb1c3d`
- prerequisite: `0037-12` already `[x]` on Feature tip
- exact_write_scope:
  - `tools/todo-dependency-graph.html`
  - `_src/tests/test_todo_dependency_graph.py`
  - `TODO-gabriel-graphhtml-0037-22-20260825T114200Z.md`
  - `TODO.md` (0037-22 Task block only)
- forbidden: fetching `../TODO.md`; live repository TODO.md/DONE.md as product; Acceptance; checkpoint; Feature DONE.md; main; push; 10.01/issuectl; parent 17 product; 23.01
- status: `[p]`; claim materialization only. No product mutation before claim REF.
- next_step: implement HTML consumer of `issues/_views/dependency-graph.json` after claim REF.

## Task

Implement `tools/todo-dependency-graph.html` as the internal maintainer consumer of `issues/_views/dependency-graph.json`.

- **Acceptance criteria:** Preserve filtering, counts, zoom/scroll, all state/archive/edge legends, done handling, and actionable errors; add internal item links, source/schema/tool/config digests and content-generation ID, with volatile execution-run linkage only in the external run manifest; eliminate `../TODO.md` fetching; work over documented local HTTP with only tracked assets; expose stale/missing/malformed data instead of silently disappearing.
- **Definition of Done:** Browser/DOM tests cover every state/edge class, redacted/missing endpoints, malformed/stale data, missing Graphviz assets, item navigation, keyboard/accessibility behavior, and exact catalog count/edge parity.
