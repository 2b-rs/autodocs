# CLAUDE.md — Project guidance for Claude Code

Project: **ara::\* API reference for the AUTOSAR Adaptive Platform (R25-11).**
The HTML tree in this repository is a **generated build artifact**. See
[`README.md`](README.md) for the public overview.

## Collaboration & agent rules

This repo defines its own multi-agent collaboration contract. Read and follow it:

@AGENTS.md

Related authority documents (read when relevant — not auto-loaded):

- [`SANDBOX.md`](SANDBOX.md) — capability classes, authority discovery, runner protocol.
- [`PRIVILEGED.md`](PRIVILEGED.md) — extra rules for explicitly privileged agents.
- [`TODO.md`](TODO.md) / [`DONE.md`](DONE.md) — authoritative backlog and completed history.
- [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md) — branch topology per backlog item, base-and-merge start rule, merge authority, Feature integration, and the `[u]` integration verdict.
- [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md) — privileged Task acceptance and Feature aggregate closure.

## Golden rule: never hand-edit generated HTML

The `*.html` files (and generated CSS/JS/assets) are **build output**. Do not edit them directly. Change the sources under [`_src/`](_src/), then regenerate:

```bash
python3 _src/generate.py && python3 _src/validate.py
```

- Maintenance guide: [`_src/WARTUNG.md`](_src/WARTUNG.md)
- Conventions: [`_src/KONVENTIONEN.md`](_src/KONVENTIONEN.md)

## Repository shape

- `_src/` — sources and build tooling (the real editing surface); `_src/tools/` holds
  reusable project scripts.
- Generated tree: `index.html`, `en/`, `es/`, `fr/`, … (per-language), plus `modules/`,
  `namespaces/`, `classes/`, `services/`.
- `docs/pipeline/` — authoritative docs for implemented operational processes.
- `output/logs/<task-or-claim>/<request-id>/` — bounded, git-ignored execution logs.

## Publication

The public deploy repo `2b-rs/autodocs` (GitHub Pages:
<https://2b-rs.github.io/autodocs/>) contains **only** the built HTML/CSS/asset files —
the `_src/` sources and build tools are not pushed there.

## Working conventions

- Preserve unrelated staged, unstaged, and untracked work; use path-limited commits.
- Never persist secrets/credentials in commands, logs, claims, commits, or tracked files.
- Carry Feature/Task/Subtask work on Git branches named after the item ID; base off the parent branch and merge in done-but-unintegrated prerequisite branches as the first step; commit claim files alongside work products so they travel with merges. Merges that cross no integration checkpoint may be done by a grunt; crossing a node the architect marked `Integration review: mandatory`, plus Feature closure and `DONE.md` moves, are privileged-only. See [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md).
