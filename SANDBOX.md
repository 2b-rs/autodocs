# Working Rules for Automation and AI Agents

You are an AGENT and must follow the current operating contract below.

## Scope and precedence

- Runtime system, developer, and explicit current user instructions take precedence over repository documents.
- `SANDBOX.md` is the stable bootstrap for agent capability, tool use, authority discovery, and instruction precedence.
- `AGENTS.md` is authoritative for collaboration, claims, Task bookkeeping, commits, interruptions, and handoffs.
- `TODO.md` is authoritative for the current Feature/Task backlog, identifiers, markers, prerequisites, acceptance criteria, and Definition of Done. `DONE.md` contains terminal Features and retained history.
- `docs/pipeline/` is authoritative for implemented operational processes in its documented scope.
- If applicable instructions conflict and precedence does not resolve the conflict safely, stop mutating the repository, identify the exact conflict, and request clarification.

## Agent capability classes

There are two agent classes:

- **Sandboxed/grunt agent:** performs routine project work but must not execute scripts, shell commands, tests, generators, browsers, package managers, network clients, or Git commands directly. It may use available non-execution file/editor/search tools and may request execution through the less-restricted runner.
- **Privileged agent:** may execute available tools directly within the runtime's actual security and approval controls.

An agent is privileged only when the current runtime or user explicitly says so. If the class is absent or ambiguous, act as a sandboxed agent. Never infer privilege from the presence of a terminal-like tool.

Feature `0037` is designed to be implemented entirely by sandboxed/grunt agents. A Task that cannot be completed through non-execution tools plus the runner is not execution-ready.

## Current backlog authority

Until Feature `0037` completes its authorized cutover:

- committed `TODO.md`, `DONE.md`, and active `TODO-<agent-id>.md` claim files are authoritative;
- `issues/` is non-authoritative shadow or implementation data;
- agents must not maintain both representations or infer cutover from the presence of `issues/`.

A later cutover must update this file, `AGENTS.md`, and the machine-readable authority selector in the same reviewed authority-switch sequence.

## Runner protocol for sandboxed agents

The runner is an execution service. It is not the user, and the user is not expected to execute an agent's script.

Until Feature `0037` installs and activates the versioned request queue/dispatcher, root `run.sh` is a singleton runner slot. Active Task/claim ownership serializes requests. Never overwrite an existing/pending `run.sh` or another Task's runner scope.

A pre-claim assignment lease is not required. When a sandboxed agent needs Git/base/status data for a new claim, it first selects an eligible Task, creates its collision-resistant `TODO-<agent-id>.md` with matching immutable `owner_token`, `base_commit: pending-discovery`, and a unique request ID, marks the Task `[p]`, and then publishes the fixed read-only discovery `run.sh` if the slot is free. That script declares `expected_base: discover` and may return only current commit, authority state, index/worktree status, active claims, and slot state. It must not mutate files, refs, index, or external state. The runner accepts only a script referencing the active claim/request ID, rejects conflicts, and archives/removes it before releasing the slot. The agent then replaces `pending-discovery` with the returned base commit before requesting mutation.

A sandboxed agent requests execution as follows:

1. Select or resume a Task under `AGENTS.md`, inspect active claims and runner-slot state with non-execution tools, and never overwrite an existing/pending request.
2. Create or update the Task claim. If command-derived base/status is unavailable, use `base_commit: pending-discovery`; this is permitted only until the fixed read-only discovery result returns.
3. Record a unique runner request ID and exclusive runner scope in the claim.
4. When the singleton slot is free, publish `run.sh` with non-execution file tools. The script must reference the active claim/request ID; the runner rejects stale, conflicting, or unclaimed requests.
5. Make the script non-interactive, bounded, deterministic where possible, and safe to rerun. It must fail closed on an unexpected base commit, authority state, working-tree scope, dependency, or input.
6. At startup print:
   - a one-line purpose;
   - the script phases and goal hierarchy;
   - expected read/write paths;
   - network hosts/data, credentials, CPU workers, memory, and wall-clock bounds;
   - the expected base commit and Task/claim identity.
7. Use strict error handling, explicit temporary/output paths, mutation guards, and cleanup traps. Validate before promotion; use temporary staging and atomic replacement when writing generated artifacts.
8. For work longer than five seconds, print regular progress. End with commands/stages run, exit status, validation results, changed paths, retained logs/artifacts, and recovery guidance.
9. Request runner execution and yield for its result. Do not ask the user to run the script and do not attempt to execute it directly.
10. After the runner returns, inspect the complete result. A recoverable failure may be corrected with one focused replacement request when the root cause is understood; never claim success from partial output.

Feature `0037` Campaign A and runner installation use one designated sandboxed bootstrap agent and no concurrent Feature `0037` runner request until the queue is activated and qualified. Its first bounded runner transaction must qualify discovery, validation, path-limited commits, two-commit REF bookkeeping, failure recovery, and slot cleanup on fixtures before substantive architecture work.

Network, credentials, external service changes, signing, or elevated operations must be declared explicitly and require the applicable authorization. Never place secrets in `run.sh`, logs, claims, or tracked files.

Privileged agents may use direct execution, but must preserve the same scope, validation, traceability, and mutation-safety requirements.

## Agent startup

Before changing the repository:

1. Determine and record the agent capability class; default to sandboxed.
2. Read this file and `AGENTS.md`.
3. Read `TODO.md` and active claims. If no Task was assigned, deterministically select work under `AGENTS.md` instead of asking the user to choose.
4. Read the complete selected Feature/Task and prerequisites.
5. Inspect relevant claims and working-tree information using permitted tools or the claimed read-only discovery request.
6. Follow the claim and state-transition procedure in `AGENTS.md`.

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
