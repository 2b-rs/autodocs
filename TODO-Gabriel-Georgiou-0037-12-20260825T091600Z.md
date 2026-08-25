# Claim 0037-12

- owner_token: `agent:gabriel-georgiou-20260825t091600z:0037-12:20260825T091600Z`
- capability_class: unprivileged
- execution_authority: direct Git/file ops in item worktree only
- item: 0037-12
- branch: 0037-12
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-12`
- base Feature tip: `6c337c154954e4df081e47087a2919fd54b69633` (after 15.01 merge)
- merged prerequisite tips (already ancestors of Feature tip):
  - 0037-08 `15b50c7c0b4943b12cf703a7f9b612bb3388d948`
  - 0037-09 `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a`
  - 0037-11.02 `472fcbeb51dfff20ccd10195ec745c7d53887daf`
  - 0037-39 `b092d59356aabc6e699399a3a9b92c7cca609b5a`
  - 0037-05: no live branch; treated as already on Feature/main lineage
- write_scope:
  - `tools/todo-graph-core.js`
  - `tools/todo-graph-embed.js`
  - `tools/todo-dependency-graph.html`
  - tests for those files
  - this claim
  - 0037-12 TODO.md block
- out of scope: issuectl (10.04), schema transforms (15.02), event replay (15.03), issue_reimport (15.01), generated TODO/DONE views (11.01)
- stop: implementation `[x]` only; no Acceptance, checkpoint, main, DONE Feature, or push
- startup_review: Feature tip contains validated `issues/_views/dependency-graph.json` schema from 11.02; core currently parses TODO.md — this Task replaces that.

## Next
Commit claim, mark `[p]`, implement JSON adapter + Python/JS parity tests.

## Takeover
2026-08-25 additive takeover by Gabriel-Vance-20260825T092000Z (`agent:gabriel-vance-20260825t092000z:0037-12:20260825T092000Z`). This token is **not** reused. This file is preserved untracked-then-committed as provenance.
