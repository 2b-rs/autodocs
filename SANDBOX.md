# Working Rules for Automation and AI Agents

You are an AGENT and must follow the current operating contract below.

## Scope and precedence

- Runtime system, developer, and explicit current user instructions take precedence over repository documents.
- `SANDBOX.md` is the stable bootstrap for agent capability, tool use, authority discovery, and instruction precedence.
- `AGENTS.md` is authoritative for collaboration, claims, Task bookkeeping, commits, interruptions, and handoffs.
- `PRIVILEGED.md` supplements this bundle for agents explicitly identified as privileged; it never grants privilege by itself.
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

## Autonomous resolution and human-decision boundary

Agents are authorized and expected to resolve agentically determinable defects in the active backlog rather than stopping merely because the written plan is inconsistent. This includes an unclosed parent whose children are terminal, missing aggregation or validation work, missing/reversed prerequisites, syntactic or semantic dependency cycles, and acceptance or completion text that requires a downstream artifact whose producer cannot start until the current item closes.

Use the smallest intent-preserving repair supported by the Feature goal, recorded decisions, neighboring Tasks, repository evidence, and existing architecture. An agent may clarify `TODO.md`, add or split Tasks, correct prerequisites, or replace a premature downstream-artifact requirement with a local intermediate deliverable that the downstream Task later verifies and incorporates. It must record the defect and rationale, preserve or strengthen acceptance and traceability, validate the repaired plan, and continue without asking the user.

Do not infer unlimited product or policy authority from this permission. Ask the user or use `[u]` only when the next action genuinely requires a human choice between materially different valid outcomes, authorization, credentials, external configuration, signature, policy/risk acceptance, or scope decision. Technical difficulty, unfamiliarity, an open parent Task, a drafting defect, or an agentically repairable dependency deadlock is not `[u]`.

Root `run.sh` is only a one-use executable runner request. It is never an escalation token, notification, question, reservation note, or substitute for fixing backlog state. A sandboxed agent needing executable evidence for a repair publishes a bounded request under its own active claim; a privileged agent does not publish it on the grunt's behalf.

The detailed backlog-repair and claim procedure is defined in `AGENTS.md`.

## Runner protocol for sandboxed agents

The runner is an execution service. It is not the user, and the user is not expected to execute an agent's script.

Until Feature `0037` installs and activates the versioned request queue/dispatcher, root `run.sh` is a singleton runner slot. Active Task/claim ownership serializes requests. Never overwrite an existing/pending `run.sh` or another Task's runner scope.

`run.sh` is a consumable request envelope, not a reusable project script. The runner claims it for one execution, archives the submitted content and result as evidence, and removes it from the root slot before releasing that slot. Therefore its expected post-execution state is **absent**. Never rerun, restore, copy back, or treat an archived `run.sh` as a pending request. Every retry or subsequent operation requires the owning agent to inspect the prior result, verify that the root slot is free, allocate a new unique request ID, record it in the active claim, and publish a newly generated `run.sh` for exactly one execution. Absence before any result/archive evidence means “not published or not yet reconciled”; absence after matching result/archive evidence means “consumed successfully by the runner,” not “lost.”

A pre-claim assignment lease is not required. When a sandboxed agent needs Git/base/status data for a new claim, it first selects an eligible Task, creates its collision-resistant `TODO-<agent-id>.md` with matching immutable `owner_token`, `base_commit: pending-discovery`, and a unique request ID, marks the Task `[p]`, and then publishes the fixed read-only discovery `run.sh` if the slot is free. That script declares `expected_base: discover` and may return only current commit, authority state, index/worktree status, active claims, and slot state. It must not mutate files, refs, index, or external state. The runner accepts only a script referencing the active claim/request ID, rejects conflicts, and archives/removes it before releasing the slot. The agent then replaces `pending-discovery` with the returned base commit before requesting mutation.

A sandboxed agent requests execution as follows:

1. Select or resume a Task under `AGENTS.md`, inspect active claims and runner-slot state with non-execution tools, and never overwrite an existing/pending request.
2. Create or update the Task claim. If command-derived base/status is unavailable, use `base_commit: pending-discovery`; this is permitted only until the fixed read-only discovery result returns.
3. Record a unique runner request ID and exclusive runner scope in the claim.
4. When the singleton slot is free, publish `run.sh` with non-execution file tools. The script must reference the active claim/request ID; the runner rejects stale, conflicting, or unclaimed requests.
5. **For sandboxed/grunt sessions whose tool calls are throttled or limited**, optimize for request economy and first-attempt completion. Before publishing, form the complete plan for one coherent Task phase and place every safely pre-authorizable process step into the same self-contained request: command-derived inspection, targeted file excerpts or counts, preflight, dependency checks, fixture setup, implementation/generation, focused and broader validation, mutation-scope checks, evidence capture, cleanup, and—when all prior gates pass—the authorized path-limited commit/bookkeeping transaction. Prefer one larger bounded read or one phased request over repeated small reads and runner round trips. Do not use direct execution to save a tool call. Use non-execution reads only when their result is needed to define the request safely; otherwise collect that information inside the forthcoming request and return it in the structured result. This optimization is not a general mandate for privileged agents or for sessions without tool-call pressure; they should use the clearest safe workflow appropriate to their capability and runtime.
6. Keep batching coherent and fail closed. A request must remain non-interactive, bounded, deterministic where possible, and safe to retry through a newly generated request. It must not combine unrelated Tasks, ownership scopes, approvals, credentials, or mutations merely to reduce request count. Later phases may branch only on declared, validated conditions and must perform no mutation if the expected base commit, authority state, active claim, working-tree scope, dependency, input, or earlier validation gate differs from the request contract.
7. At startup print:
   - a one-line purpose;
   - the script phases and goal hierarchy;
   - expected read/write paths;
   - network hosts/data, credentials, CPU workers, memory, and wall-clock bounds;
   - the expected base commit and Task/claim identity.
8. Use strict error handling, explicit temporary/output paths, mutation guards, and cleanup traps. Validate before promotion; use temporary staging and atomic replacement when writing generated artifacts.
9. For work longer than five seconds, print regular progress. End with commands/stages run, exit status, validation results, changed paths, retained logs/artifacts, and recovery guidance. Return enough bounded diagnostic context that the agent can decide the next action without another exploratory request.
10. Request runner execution and yield for its result. Do not ask the user to run the script and do not attempt to execute it directly.
11. After the runner returns, inspect the complete result. A recoverable failure may be corrected with one focused replacement request when the root cause is understood; never claim success from partial output. Do not split a known plan into serial requests merely to observe intermediate success; encode intermediate gates in one request and stop automatically at the first failed gate.
12. A response/tool/time budget ending is a routine interruption, not a human decision, capability ambiguity, or reason to request privilege. Record only actions that actually completed, retain `[p]` and the claim, state the exact automatic continuation step, and stop without a question. On the next turn, continue that step immediately unless the user explicitly redirects the Task. Never ask whether to continue and never offer privilege escalation merely to bypass the runner.

Feature `0037` Campaign A and runner installation use one designated sandboxed bootstrap agent and no concurrent Feature `0037` runner request until the queue is activated and qualified. Its first bounded runner transaction must qualify discovery, validation, path-limited commits, two-commit REF bookkeeping, failure recovery, and slot cleanup on fixtures before substantive architecture work.

Network, credentials, external service changes, signing, or elevated operations must be declared explicitly and require the applicable authorization. Never place secrets in `run.sh`, logs, claims, or tracked files.

Privileged agents may use direct execution, but must preserve the same scope, validation, traceability, and mutation-safety requirements.

## Agent startup

Before changing the repository:

1. Determine and record the agent capability class; default to sandboxed.
2. Read this file and `AGENTS.md`. If explicitly privileged, also read `PRIVILEGED.md` before acting.
3. Read `TODO.md` and active claims. First resume any incomplete claim whose immutable `owner_token` belongs to this session; a response, runner-result, or context boundary does not end ownership or authorize selecting replacement work. If no Task was assigned and no owned claim exists, deterministically select work under `AGENTS.md` instead of asking the user to choose.
4. Read the complete selected Feature/Task and prerequisites. Substantial scope, unfamiliarity, or movement to another Feature does not require confirmation when the Task is eligible.
5. Inspect relevant claims and working-tree information using permitted tools or the claimed read-only discovery request.
6. Follow the claim and state-transition procedure in `AGENTS.md`.

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
