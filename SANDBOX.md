# Working Rules for Automation and AI Agents

You are an AGENT and must follow the current operating contract below.

## Scope and precedence

- Runtime system, developer, and explicit current user instructions take precedence over repository documents.
- `SANDBOX.md` is the stable bootstrap for tool use, authority discovery, and instruction precedence.
- `AGENTS.md` is authoritative for collaboration, claims, Task bookkeeping, commits, interruptions, and handoffs.
- `TODO.md` is authoritative for the current Feature/Task backlog, identifiers, markers, prerequisites, acceptance criteria, and Definition of Done. `DONE.md` contains terminal Features and retained history.
- `docs/pipeline/` is authoritative for the implemented operational processes in its documented scope.
- If two applicable instructions conflict and precedence does not resolve the conflict safely, stop mutating the repository, identify the exact conflicting provisions, and ask the user. Do not silently choose the more convenient rule.

## Current backlog authority

Until Feature `0037` completes its authorized cutover:

- committed `TODO.md`, `DONE.md`, and active `TODO-<agent>.md` claim files are authoritative;
- `issues/` is non-authoritative shadow or implementation data;
- agents must not maintain both representations or infer that cutover occurred from the mere presence of `issues/`.

A later cutover must update this file, `AGENTS.md`, and the machine-readable authority selector in the same reviewed authority-switch sequence. Do not use future issue-store instructions before that switch.

## Tool use

- Use the editor, file, search, terminal, and other tools actually available in the current runtime directly and responsibly.
- The user will not execute scripts or commands on an agent's behalf. Do not create `run.sh` and yield expecting the user to run it.
- An agent may create and execute a bounded script itself when that is the safest or clearest way to complete a Task, subject to the current sandbox, network, security, and approval controls.
- Prefer the most direct tool, keep commands bounded, and use parallel work only for independent operations with disjoint write scopes.
- A recoverable tool failure may receive one or two focused attempts when the root cause is understood. Report blocking failures accurately; do not abandon otherwise reachable work merely because one tool invocation failed.
- Never expose secrets, bypass sandbox or repository protections, overwrite unrelated work, or claim validation that was not run successfully.

## Agent startup

Before changing the repository:

1. Read this file and `AGENTS.md`.
2. Read the complete target Feature/Task and its prerequisites in `TODO.md`.
3. Inspect active `TODO-<agent>.md` claims and relevant working-tree changes.
4. Follow the claim and state-transition procedure in `AGENTS.md`.

Further project and maintenance information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
