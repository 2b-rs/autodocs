# Working Rules for Automation and AI Agents

You are an AGENT and must follow the current operating contract below.

## Scope and precedence

- Runtime system, developer, and explicit current user instructions take precedence over repository documents.
- `SANDBOX.md` is the stable bootstrap for agent capability, tool use, authority discovery, and instruction precedence.
- `AGENTS.md` is authoritative for collaboration, claims, Task bookkeeping, commits, interruptions, and handoffs.
- `PRIVILEGED.md` supplements this bundle for agents explicitly identified as privileged; it never grants privilege by itself.
- `TODO.md` is authoritative for the current Feature/Task backlog, identifiers, implementation markers, prerequisites, acceptance criteria, Definition of Done, and current `Acceptance: ✓` records. `DONE.md` contains aggregate-accepted Features plus retained pre-policy history.
- `docs/pipeline/` is authoritative for implemented operational processes in its documented scope.
- If applicable instructions conflict and precedence does not resolve the conflict safely, stop mutating the repository, identify the exact conflict, and request clarification.

## Default execution gate — sandboxed unless explicitly privileged

A session is sandboxed/grunt unless the current runtime or user explicitly grants privileged capability. Tool availability does not grant privilege. A sandboxed/grunt agent may directly edit files under `/tmp`, but that is not execution authority: scripts, shell commands, Git, tests, generators, browsers, package managers, network clients, and every other execution-capable action must use its claim-bound runner. Runtime tool-policy denial is a host/platform control; repository checks can validate claim declarations but cannot configure or guarantee that denial.

## Agent capability classes

A capability class answers **two independent questions**, and both must be
answered before work starts:

1. **Execution** — may this session run scripts, shell commands, tests,
   generators, browsers, package managers, network clients and Git **directly**,
   or must it route them through the runner?
2. **Authority** — may this session create, change or invalidate
   `Acceptance: ✓`, act as acceptance reviewer, perform an integration that
   crosses a node marked `Integration review: mandatory`, or move a Feature to
   `DONE.md`?

The two are orthogonal. Being able to run a command says nothing about being
allowed to decide. There are three classes:

| Class | Execution | Authority |
|---|---|---|
| `sandboxed-grunt` | runner only | none |
| `unprivileged` | direct | none |
| `privileged` | direct | full |

- **Sandboxed/grunt agent** (`sandboxed-grunt`, legacy spelling `sandboxed/grunt`): performs routine project work but must not execute scripts, shell commands, tests, generators, browsers, package managers, network clients, or Git commands directly. It may use available non-execution file/editor/search tools and may request execution through the less-restricted runner. It may complete implementation at `[x]`/`[w]` and prepare review evidence, but must never create/change/invalidate `Acceptance: ✓`, act as acceptance reviewer, or move a Feature to `DONE.md`.
- **Unprivileged agent** (`unprivileged`): may execute available tools directly within the runtime's actual security and approval controls, and therefore does **not** use the runner protocol. Its authority is exactly that of a sandboxed/grunt agent: it may complete implementation at `[x]`/`[w]` and prepare review evidence, and must never create/change/invalidate `Acceptance: ✓`, act as acceptance reviewer, cross a mandatory integration checkpoint, or move a Feature to `DONE.md`. Direct execution is a capability, never a grant of authority.
- **Privileged agent** (`privileged`): may execute available tools directly **and** holds the acceptance and integration authority the other two classes lack, subject to [`PRIVILEGED.md`](PRIVILEGED.md) and [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md).

An agent is privileged, and an agent is unprivileged rather than sandboxed, only
when the current runtime or user explicitly says so. If the class is **absent,
ambiguous, unrecognized, or contradicts these definitions** — for example a
designation that is neither of the three names, or one that claims direct
execution while also claiming acceptance authority is withheld in a way these
definitions do not model — do **not** stop and do not ask before starting: act
as a sandboxed agent, record the received designation and the conflict verbatim
in the claim, and continue. Falling back is always safe, because the sandboxed
class is the most restricted one. Never infer privilege from the presence of a
terminal-like tool.

Because execution and authority are separate, a class is never sufficient on its
own to decide who may review or accept work; that is governed by the process
roles in [`docs/pipeline/process-roles.md`](docs/pipeline/process-roles.md).

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

Sandboxed agents use non-execution file tools for collaboration-suggestion entries required by `AGENTS.md`; they must not publish a runner request solely to append such an entry.

## Runner protocol for sandboxed agents

The runner is an execution service. It is not the user, and the user is not expected to execute an agent's script.

### Current procedure — queue dispatch (`runner-queue@v1`)

The versioned request queue/dispatcher is active. The live bootstrap selector `agent-workflow.json` carries `"runner_protocol":"runner-queue@v1"`, and **the queue is the sole mutation authority**. The runner host operates in multi-worker continuous mode, accepting asynchronous drafts and processing ready queue requests under `.runner/`.

Publication workflow, using non-execution file tools only:

1. Compose the request draft under `.runner/drafts/<agent>/<request_id>/` with `manifest.json` and `request.json`.
2. Publish it atomically to `.runner/requests/<request_id>` with a single same-filesystem rename.
3. Read the verdict and outputs from `.runner/results/<request_id>.result.json`; each result carries its own SHA-256 digest.

Scope isolation and collision guards:

- Concurrent requests with **disjoint** `write_scopes` are processed in parallel. Proven under Task `0037-46.02` with a synchronized-start fixture pair whose execution windows overlap.
- Concurrent requests with **overlapping** `write_scopes` are rejected with `RD-SCOPE-COLLISION`.
- Unprivileged attempts to mutate governance documents (`AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, `docs/pipeline/`) are rejected with `RD-GOVERNANCE-SCOPE`. Governance changes travel the route defined by `DEC-0044-012`.
- Observe lease expirations and idempotence keys. A retry of a previously rejected or failed request keeps its ancestry record (`retry_of`).

### Transition phase — after the epoch bump, before singleton retirement

Between the epoch bump (Task `0037-46.02`, step 4) and the retirement of the legacy singleton (step 5), exactly one protocol accepts mutations, and it is the queue:

- From the moment `runner-queue@v1` is active in the selector, **the queue is the sole mutation authority**.
- Writes to the legacy singleton slot `run.sh` are admissible in this phase **only for the final retirement transaction itself** — the operation that shuts the old path down. No other use is valid.

Both protocols are therefore never accepting mutations at the same time, and there is never a moment in which neither does. Once retirement is complete, direct writes to `run.sh` are rejected outright.

### [Legacy / Deprecated] Singleton slot (`runner-request@v1`)

**The following describes the retired singleton procedure. It is retained so that archived runs, evidence and claim records stay readable. Do not apply it to new work** — active agents use the queue procedure above. The single exception is the retirement transaction named in the transition rule.

Under that procedure, root `run.sh` was a singleton runner slot. Active Task/claim ownership serialized requests. An existing or pending `run.sh`, or another Task's runner scope, was never to be overwritten.

`run.sh` is a consumable request envelope, not a reusable project script. The runner claims it for one execution, archives the submitted content and result as evidence, and removes it from the root slot before releasing that slot. Therefore its expected post-execution state is **absent**. Never rerun, restore, copy back, or treat an archived `run.sh` as a pending request. Every retry or subsequent operation requires the owning agent to inspect the prior result, verify that the root slot is free, allocate a new unique request ID, record it in the active claim, and publish a newly generated `run.sh` for exactly one execution. Absence before any result/archive evidence means “not published or not yet reconciled”; absence after matching result/archive evidence means “consumed successfully by the runner,” not “lost.”

A pre-claim assignment lease is not required. When a sandboxed agent needs Git/base/status data for a new claim, it first selects an eligible Task, creates its collision-resistant `TODO-<agent-id>.md` with matching immutable `owner_token`, `base_commit: pending-discovery`, and a unique request ID, marks the Task `[p]`, and then publishes the fixed read-only discovery `run.sh` if the slot is free. That script declares `expected_base: discover` and may return only current commit, authority state, index/worktree status, active claims, and slot state. It must not mutate files, refs, index, or external state. The runner accepts only a script referencing the active claim/request ID, rejects conflicts, and archives/removes it before releasing the slot. The agent then replaces `pending-discovery` with the returned base commit before requesting mutation.

A sandboxed agent requests execution as follows:

Root `run.sh` is a parameterless execution envelope by design. The legacy runner always invokes it with exactly zero positional command-line parameters. No agent may request, invite, or depend on the runner, user, operator, or any other party supplying arguments at execution time. A request that requires `$1`, `$2`, `"$@"`, an argument prompt, or an uncontracted environment value is invalid and must not be published. The script must be complete and non-interactive when written: every required Task ID, claim path, request ID, expected base, scope, input, output, option, and bound is embedded as a safely quoted literal or read from an explicitly declared, preflighted repository input. A value learned from an earlier result is reconciled into the claim and embedded in a newly generated one-use request with a fresh request ID; it is never supplied as a later invocation parameter. Future queued actions carry data in their validated request manifests, but root `run.sh` remains parameterless.

1. Select or resume a Task under `AGENTS.md`, inspect active claims and runner-slot state with non-execution tools, and never overwrite an existing/pending request.
2. Create or update the Task claim. If command-derived base/status is unavailable, use `base_commit: pending-discovery`; this is permitted only until the fixed read-only discovery result returns.
3. Record a unique runner request ID and exclusive runner scope in the claim.
4. When the singleton slot is free, publish `run.sh` with non-execution file tools. The script must reference the active claim/request ID; the runner rejects stale, conflicting, or unclaimed requests.
5. **For sandboxed/grunt sessions whose tool calls are throttled or limited**, optimize for request economy and first-attempt completion. Before publishing, form the complete plan for one coherent Task phase and place every safely pre-authorizable process step into the same self-contained request: command-derived inspection, targeted file excerpts or counts, preflight, dependency checks, fixture setup, implementation/generation, focused and broader validation, mutation-scope checks, evidence capture, cleanup, and—when all prior gates pass—the authorized path-limited commit/bookkeeping transaction. Prefer one larger bounded read or one phased request over repeated small reads and runner round trips. Before reading, editing, or verifying bulk/repetitive data through conversation context, search for a task-specific deterministic tool under `_src/tools/`; if none exists, create one small task-scoped Python tool that performs the extraction/transformation/validation and returns only a bounded verdict plus retained artifact paths. Do not use direct execution to save a tool call. Use non-execution reads only when their result is needed to define the request safely; otherwise collect that information inside the forthcoming request and return it in the structured result. This optimization is not a general mandate for privileged agents or for sessions without tool-call pressure; they should use the clearest safe workflow appropriate to their capability and runtime.
6. Keep batching coherent and fail closed. A request must remain non-interactive, bounded, deterministic where possible, and safe to retry through a newly generated request. It must not combine unrelated Tasks, ownership scopes, approvals, credentials, or mutations merely to reduce request count. Later phases may branch only on declared, validated conditions and must perform no mutation if the expected base commit, authority state, active claim, working-tree scope, dependency, input, or earlier validation gate differs from the request contract.
7. At startup print:
   - a one-line purpose;
   - the script phases and goal hierarchy;
   - expected read/write paths;
   - network hosts/data, credentials, CPU workers, memory, and wall-clock bounds;
   - the expected base commit and Task/claim identity.
8. Use strict error handling, explicit temporary/output paths, mutation guards, and cleanup traps. Validate before promotion; use temporary staging and atomic replacement when writing generated artifacts.
9. Use strict output bounding. Redirect complete compiler, generator, validator, test, browser, package-manager, and child-process stdout/stderr to task/request-scoped files under ignored `output/logs/<task-or-claim>/<request-id>/`; never replay full logs into runner stdout, claims, or Markdown. Conversation-facing stdout contains only phase status, pass/fail, exit codes, counts, and retained log/artifact paths or digests: at most one progress line per phase or 60 seconds and a final verdict of at most ten lines. On failure, include at most one targeted excerpt capped at 20 lines and 8 KiB, plus the full log path. End with commands/stages run, exit status, validation results, changed-path counts, retained evidence, and recovery guidance, so the agent can choose the next action without another exploratory request.
10. Request runner execution and yield for its result. Do not ask the user to run the script and do not attempt to execute it directly.
11. After the runner returns, inspect and reconcile the complete result immediately. Update the active claim with the actual outcome and retained evidence; correct any premature or inaccurate progress statement; replace `pending-discovery` with the exact returned base when applicable; mark the prior request ID consumed regardless of success or failure; and, when further runner work is already defined, mint and record a fresh request ID, verify the slot is free, and publish the newly generated request without waiting for user acknowledgement. These are routine protocol steps, not human gates. A status preamble is not a checkpoint: do not end a turn merely by saying what must be reconciled or published. Yield as "awaiting runner" only after the corresponding request file was actually published. A recoverable failure may be corrected with one focused replacement request when the root cause is understood; never claim success from partial output. Do not split a known plan into serial requests merely to observe intermediate success; encode intermediate gates in one request and stop automatically at the first failed gate.
12. A response/tool/time budget ending is a routine interruption, not a human decision, capability ambiguity, or reason to request privilege. Record only actions that actually completed, retain `[p]` and the claim, state the exact automatic continuation step, and stop without a question. On the next turn, continue that step immediately unless the user explicitly redirects the Task. Never ask whether to continue and never offer privilege escalation merely to bypass the runner.

Required runner preparation and reconciliation are work, not user checkpoints. A brief status preamble may explain them, but the agent must perform every currently available step in the same turn. Yield as awaiting the runner only after the request was actually published; a planned but unpublished request is not pending. Before any interruption, record runner status and log locations, temporary files, pending requests/results, recovery steps, and the exact continuation action in the Task and claim. A sandboxed agent waiting for execution remains active and retains `[p]` plus its claim; a missing request that was merely planned remains the owning agent's next action and is not a `[u]` condition.

Feature `0037` Campaign A and runner installation use one designated sandboxed bootstrap agent and no concurrent Feature `0037` runner request until the queue is activated and qualified. Its first bounded runner transaction must qualify discovery, validation, path-limited commits, two-commit REF bookkeeping, failure recovery, and slot cleanup on fixtures before substantive architecture work.

The prohibition on network clients applies to the sandboxed agent's direct tools, not categorically to the less-restricted runner. The runner supports outbound network operations, and a sandboxed agent may include them in a parameterless `run.sh` when the active Task and claim declare the external-resource scope and applicable authorization already exists. The request must name exact hosts/endpoints, purpose, data sent and received, privacy classification, credential handles without secret values, time/size/rate bounds, expected side effects, validation, and retry/recovery behavior. A public read-only fetch within an already authorized Task scope does not require a new user checkpoint merely because it uses the network. New credentials, non-public data disclosure, external mutation, unapproved hosts, material cost, or policy/risk acceptance still require the applicable human authorization. The fixed pending-discovery request is a special network-free profile and must never be generalized into a network prohibition for later Task requests. Never place secrets in `run.sh`, logs, claims, or tracked files.

### Validation, commits, implementation completion, and acceptance boundary

A sandboxed agent routes validation and Git operations through the runner. A request that validates or commits deliverables must preflight the expected authority, base commit, active claim, and working-tree scope; perform focused validation and mutation-scope checks; preserve unrelated work; and fail closed before mutation or commit when a gate differs from the request contract.

Substantive commits must be path-limited and use the configured user identity and comprehensive Feature/Task message required by `AGENTS.md`. Runner requests that create commits must carry the complete check-in provenance required by `AGENTS.md` and fail closed when required provenance is unavailable.

After the substantive commit hash is known and reachable, the agent updates implementation bookkeeping as required by `AGENTS.md`: `[x]`/`[w]`, real `REF`, validation/findings, and implementation-claim finalization. Bookkeeping is committed separately unless an approved runner transaction safely creates both commits and injects the first hash into the second. Such a transaction must expose both hashes, validate the intermediate and final trees, update only declared paths, and leave the active claim intact on any partial failure. Never amend a commit to add its own hash.

A sandboxed runner request must reject any manifest or generated change that adds, modifies, invalidates, or removes Task/Feature acceptance credit or moves a Feature to `DONE.md`. Grunts stop at implementation completion and may emit a bounded acceptance package for later independent review. Acceptance is a separately and explicitly assigned privileged action under `docs/pipeline/task-acceptance.md`; it is never inferred from runner success or requested through generic shell/bookkeeping actions.

Branch, base, and merge operations are Git operations and route through the runner under the same preflight, scope, provenance, and fail-closed rules as commits (see `docs/pipeline/branch-workflow.md`). A branch/merge request bases off the declared parent branch, merges only the declared done-but-unintegrated (`[x]`/`[w]`) prerequisite branches, preserves every carried claim file, records the merged tips in the active claim, and fails closed when the expected base, active claim, owner token, or declared scope differs from the request contract. A sandboxed request may perform only merges that cross **no integration checkpoint** (typically Subtask→Task); it must reject any merge across a node marked `Integration review: mandatory`, any `Feature→`main``/`DONE.md` closure, any creation or alteration of acceptance records or the `Integration review` attribute, and any `[u]` integration verdict — those are architect or privileged-integrator actions.

Final implementation status and intended commit reachability must be verified through the runner before the sandboxed agent treats `[x]`/`[w]` as authoritative. That verification is not `Acceptance: ✓`.

Privileged agents may use direct execution, but must preserve the same scope, validation, traceability, and mutation-safety requirements.

## Agent startup

Before changing the repository:

1. Determine and record the agent capability class; default to sandboxed.
2. Read this file, `AGENTS.md`, and the Task-acceptance boundary in `docs/pipeline/task-acceptance.md`. If explicitly privileged, also read `PRIVILEGED.md` before acting.
3. Read `TODO.md` and active claims. First resume any incomplete claim whose immutable `owner_token` belongs to this session; a response, runner-result, or context boundary does not end ownership or authorize selecting replacement work. If no Task was assigned and no owned claim exists, deterministically scan the entire backlog under `AGENTS.md` instead of asking the user to choose. Skip blocked items and foreign active claims while scanning; one occupied dependency chain never blocks disjoint eligible work elsewhere.
4. Read the complete selected Feature/Task and prerequisites. Substantial scope, unfamiliarity, movement to another Campaign/Feature, or a blocked preceding textual item does not require confirmation when another Task is eligible. Only after a complete global scan finds no eligible work may the agent use the short `SENTINEL.md` retrigger reminder for the owning session of a blocking foreign claim; never use `run.sh` for that notification.
5. Inspect relevant claims and working-tree information using permitted tools or the claimed read-only discovery request.
6. Follow the claim and state-transition procedure in `AGENTS.md`.

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
