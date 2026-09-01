# Working Rules for Privileged Agents

This file supplements [`SANDBOX.md`](SANDBOX.md) and [`AGENTS.md`](AGENTS.md) for agents that the current runtime or user has **explicitly** identified as privileged.

It does not grant privilege. If privilege is absent or ambiguous, follow the sandboxed/grunt rules in `SANDBOX.md` instead.

## Precedence and authority

1. Runtime system, developer, and explicit current user instructions take precedence.
2. `SANDBOX.md` defines capability classes, authority discovery, and the runner protocol.
3. `AGENTS.md` defines claims, coordination, bookkeeping, commits, interruptions, and handoffs.
4. This file defines additional conduct for explicitly privileged agents.
5. Until Feature `0037` completes its authorized cutover, `TODO.md`, `DONE.md`, and active `TODO-<agent-id>.md` claims remain authoritative.

If these instructions conflict and precedence does not resolve the conflict safely, stop the conflicting mutation and identify the exact conflict.

## Privileged capability

A privileged agent may directly use available shell, Git, test, build, generator, browser, network, and package-management tools within the runtime's actual security and approval controls. Direct execution is **not** what distinguishes this class: an `unprivileged` agent may execute just as directly (`SANDBOX.md`). What distinguishes a privileged agent is **authority** — acceptance, integration across a mandatory checkpoint, and the `DONE.md` move. Never treat the ability to run a command as evidence of that authority.

Privilege changes the execution mechanism, not the required engineering discipline. A privileged agent must still:

- inspect relevant instructions, claims, and repository state before mutation;
- use bounded and non-interactive commands;
- declare consequential network, credential, external-service, or destructive operations;
- preserve unrelated staged, unstaged, and untracked work;
- use path-limited staging and commits;
- validate changes before reporting success;
- retain traceability, evidence, and accurate Task bookkeeping;
- follow all applicable authorization, privacy, signing, and review requirements.

Never infer broader authority from the ability to execute a command.

## Relationship to sandboxed/grunt agents

Sandboxed/grunt agents perform routine work through the runner. Their active claim owns the Task scope and any runner scope recorded in that claim.

A privileged agent must not:

- resume, edit, close, or delete another session's claim unless explicitly directed to reconcile or take over that claim;
- infer ownership from an agent display name or claim filename;
- modify files inside another active claim's declared write scope without explicit coordination;
- create, replace, remove, execute, or otherwise consume root `run.sh` for a grunt-owned claim;
- publish a runner request on a grunt's behalf merely because the grunt was interrupted or exhausted its response/tool budget;
- convert a routine interruption into a privilege takeover;
- report a runner request as published or executed unless the owning agent or runner actually performed that action.

If a grunt-owned `run.sh` is pending, leave it untouched. Root `run.sh` is a one-use consumable request envelope: the runner claims it for one execution, archives its submitted content and result, and removes it before releasing the singleton slot. Its normal post-execution state is therefore absent. Never execute, restore, republish, or copy an archived request back into the slot. A retry or later phase requires the owning grunt to reconcile the prior result and publish newly generated content under a new recorded request ID after confirming the slot is free. If the slot is absent without matching result/archive evidence, preserve that discrepancy for the owning grunt to reconcile; do not recreate the request unless the user explicitly transfers runner ownership.

A tool/time/response-budget interruption leaves the grunt's Task `[p]`, claim active, and next action unchanged. The owning grunt resumes automatically on its next turn unless explicitly redirected.

## Starting privileged work

Before changing the repository:

1. Confirm that the current runtime or user explicitly identifies this agent as privileged.
2. Read `SANDBOX.md`, `AGENTS.md`, this file, the authoritative backlog entry, and all relevant active claims.
3. Inspect Git HEAD, branch, index, worktree, untracked files, and runner-slot state directly with read-only commands.
4. Determine whether the request belongs to an existing Task, is an explicit user-directed activity, or conflicts with active work.
5. For an existing Task, follow the claim procedure in `AGENTS.md`. Never appropriate an unmatched claim.
6. For an explicit user-directed activity outside the backlog, limit changes to the requested scope and create temporary coordination bookkeeping when needed to prevent collisions.
7. Recheck authority, prerequisites, claim ownership, and write-scope disjointness immediately before mutation.

Do not create a runner request merely to imitate grunt execution. Execute directly when privileged execution is appropriate, or leave a grunt-owned workflow to its owner. The request-economy batching policy for throttled or tool-call-limited sandboxed/grunt sessions does not apply to privileged agents; privileged agents should choose the clearest safe sequence of direct tools and commands rather than artificially packing unrelated or difficult-to-review work together.

## Direct execution rules

For direct commands:

- use the project root as the working directory;
- prefer read-only discovery before mutation;
- make expected base, input, output, and mutation scope explicit for consequential operations;
- bound long-running commands with a timeout;
- avoid interactive editors, pagers, prompts, servers, and unbounded watchers;
- do not expose secrets in commands, logs, claims, commits, or tracked files;
- use temporary staging and validate before promotion for generated or multi-file outputs;
- stop on unexpected authority, base, scope, dependency, credential, or validation state;
- keep recoverable failures recoverable and document retained artifacts and recovery steps.

The existence of direct execution capability is not permission to bypass required human approval, protected integration policy, signed decisions, external-service authorization, or Feature `0037` cutover gates.

## Working near an active grunt claim

When asked to inspect or improve instructions while a grunt claim is active:

1. Treat the grunt's claim, Task marker, declared files, and runner slot as protected coordination state.
2. Prefer changes outside that scope.
3. If the requested change necessarily touches the claim's scope, explain the collision and obtain explicit user direction before modifying it.
4. Never publish or execute the grunt's next runner request.
5. After instruction-only changes, tell the user and owning grunt exactly what changed; do not imply that the grunt's Task advanced.

Emergency intervention is limited to preventing clear damage or security exposure. Preserve evidence, make the smallest safe intervention, and record why normal ownership could not be respected. Emergency action never creates Task or Feature acceptance.

## Privileged Task and Feature acceptance review

Privilege permits direct execution but does not grant acceptance authority. A privileged session may begin an acceptance review only when the current user or a registered authority explicitly assigns the exact Task, prerequisite-closure batch, or Feature baseline. Do not autonomously select work merely because it is `[x]`/`[w]` and awaiting acceptance.

Before review, verify and record:

- current privilege and exact assignment/authority reference;
- reviewer competence, independence, and conflicts;
- exact Task/Feature contract and candidate baseline;
- complete acceptance-package identity and evidence accessibility;
- absence of a competing review assignment;
- required specialist authorities that remain separate from work-product acceptance.

The reviewer must normally be independent of the claim owner, principal implementer, decisive technical author, and sole validation producer. A current user or registered authority may grant a bounded exception that names the conflict, scope, reason, duration, and compensating controls; never infer a waiver from urgency, staffing, or privilege.

Follow [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md) in full. At minimum:

1. pin the exact normative contract, commits/tree, manifests, validation profiles/results, authority epoch, and review scope;
2. compute the transitive prerequisite closure and stop only at current, reachable, non-invalidated acceptance records;
3. topologically review every non-accepted prerequisite before the target;
4. inspect all criteria, meaningful work-product changes, direct/derived/external/evidence scopes, findings, security/privacy/safety/authority interfaces, migration and recovery behavior;
5. independently evaluate and rerun focused, policy, negative/canary, failure/recovery, and risk-based broader validation in an isolated exact candidate where feasible;
6. use deterministic whole-population checks where possible and record any justified sampling method, seed, strata, size, boundaries, and escalation;
7. record exactly `accepted`, `rejected`, or `inconclusive`, preserving findings and prior attempts append-only;
8. commit review evidence first, then use a separate path-isolated bookkeeping commit for `Acceptance: ✓` with the real review REF and required digests.

Critical/major findings, unmet criteria, non-accepted prerequisites, missing authority, stale/mixed evidence, or unbounded scope prohibit acceptance. `Rejected` normally routes actionable corrective work back to `[p]`; `inconclusive` retains `[x]`/`[w]` unless substantive rework is required. The same reserved slot remains occupied. If producer and reviewer cannot resolve a technical disagreement through evidence and bounded correction, use the documented trilateral round in [`docs/pipeline/integration-flow-control.md`](docs/pipeline/integration-flow-control.md). Neither outcome is `[u]` unless that round leaves an exact non-delegable product, policy, material-architecture, authority, material-risk, external-effect, public-release, or waiver question as the sole next action. Ordinary findings, test or hygiene failures, stale candidates, bounded rework, reviewer selection, and capacity are not Management questions.

Acceptance binds exact contract, work products, validation, prerequisites, reviewer assignment, and authority epoch. A relevant change or new material finding creates an additive invalidation and impact analysis; it never deletes history. Invalidation propagates to affected dependent acceptance and Feature aggregate acceptance.

A Feature moves to `DONE.md` only after a separately assigned aggregate review verifies every active Task/Subtask has current accepted disposition, the Feature goal and Definition of Done are met, integration and Feature-level negative/recovery checks pass, findings/risks and specialist decisions are dispositioned, and an exact aggregate manifest/review record is committed. Privileged implementation capability or child checkbox totals are insufficient.

## Commits and completion

Privileged agents may commit directly only when the user requested the check-in or the claimed Task requires it under `AGENTS.md`.

Before committing:

- review the exact diff and staged paths;
- exclude unrelated work;
- run focused validation and any required policy checks;
- use the configured repository identity;
- write a comprehensive Feature/Task-oriented commit message.

For substantive Task completion, create one carrying commit whose tree contains the deliverable, terminal marker, and finalized claim, and whose message contains `Task-ID` and `Base-Ref` trailers. Do not record the carrying commit's object ID in that tree. Never amend a commit to add its own hash.

Do not mark implementation complete merely because direct execution succeeded. Acceptance criteria, Definition of Done, validation, evidence, claim reconciliation, and required approvals must all be satisfied for `[x]`/`[w]`. Do not mark work-product acceptance merely because implementation completed; acceptance requires the separate assigned review above.

## Handoff

When yielding incomplete privileged work, record:

- current Task and claim ownership;
- completed and uncompleted actions;
- direct commands and validation actually run;
- changed, staged, untracked, and temporary paths;
- external state or credentials used without revealing secrets;
- blockers and the exact next action;
- whether any active grunt scope or runner slot remains untouched.

Do not ask the user whether to continue solely because a response/tool/time budget ended. Preserve accurate state and resume the recorded next action on the next turn unless explicitly redirected.
