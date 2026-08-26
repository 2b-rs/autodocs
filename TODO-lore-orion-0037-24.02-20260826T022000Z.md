# Claim — 0037-24.02

- owner_token: `agent:lore-orion-20260826t022000z:0037-24.02:20260826T022000Z`
- agent: `Lore-Orion-20260826T022000Z`
- capability_class: `unprivileged`
- execution_authority: direct local Git, Python, and Node within the assigned worktree and exact write scope; no privileged authority
- item: `0037-24.02`
- branch: `0037-24.02`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-24.02`
- base_commit: `dd12a1dd519a306f54600923a9af42d97a68a01d`
- startup_review: canonical `refs/heads/0037` matched the base; `0037-12`, `0037-23.02`, and `0037-24.01` were `[x]`; target was `[ ]`; no target claim, branch, or worktree collision was observed
- status: implementation claimed; claim commit pending
- intended_write_scope: `_src/i18n/ui.json`; `_src/data/issue-graph-public.{de,en,es,pt,fr,ru,ar,hi,ko,zh,nl}.json`; `tools/todo-graph-core.js`; `tools/todo-graph-embed.js`; `tools/todo-dependency-graph.html`; `_src/i18n_translate.py`; `_src/generate.py`; `_src/validate.py`; `_src/tests/test_issue_graph_i18n.py`; `_src/tests/fixtures/issue-graph-i18n/**`; this claim; exact `TODO.md` block for `0037-24.02`
- external_resources: none
- assumptions: production translation population and review remain owned by `0037-38`; fixture translations may be complete only for hermetic tests
- prohibitions: no Acceptance, checkpoint verdict, integration, protected-ref advance, `DONE.md`, push, root mutation, foreign cleanup, or edits outside the declared scope
- next_step: commit this claim and exact `[p]` marker, then inspect assigned producers/consumers and implement the bounded i18n join

