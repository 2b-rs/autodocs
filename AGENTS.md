# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Capability classes, runner use, instruction precedence, and authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent-id>.md` files are active coordination claims. Marker and prerequisite semantics are defined by the header of `TODO.md`; do not invent alternative meanings.

Feature `0037` implementation must be executable by sandboxed/grunt agents. Privileged-agent availability must never be an unstated prerequisite.

## Starting work

1. Determine the capability class as required by `SANDBOX.md`; default to sandboxed/grunt.
2. Read `TODO.md` and active `TODO-<agent-id>.md` files with non-execution tools. Resume a claim only when the assignment explicitly references it or its immutable `owner_token` matches the current runtime/session token. Never infer ownership from a shared model/display name or filename such as `TODO-perplexity.md`; unmatched legacy claims belong to another session and must not be overwritten. A response/turn boundary is not a handoff: once this session mints or receives an immutable `owner_token`, that token remains this session's ownership proof for the claim until authoritative closure or explicit handoff. On every later turn, runner result, generic continuation prompt, or restored context, resume that owned `[p]` claim and its recorded next step before scanning for new work.
3. Do not abandon, defer, or replace an owned incomplete Task merely because it was not completed in one response, consumed multiple runner requests, became technically difficult, or crossed a context/tool-budget boundary. Continue until it is complete or clearly unreachable under the state rules below. Do not open a new claim while an owned Task is actionable unless multiple simultaneous Tasks are explicitly justified, disjoint, and recorded in the claim.
4. If the assignment names no Task and no claim is explicitly owned by this session, select work without asking the user: scan `TODO.md` from top to bottom and choose the first open, unclaimed Task whose start prerequisites are terminal and whose visible file/runner scope does not conflict. While Feature `0037` is unstarted, open/unclaimed/unlocked `0037-48` is its mandatory first pickup.
5. Ask the user to choose work only when no eligible Task exists or when the next action genuinely requires the human decision represented by `[u]`. The fact that the next eligible Task is substantial, unfamiliar, or belongs to a different Feature is not a reason to pause or request confirmation; claim it and work autonomously.
6. Create a collision-resistant `TODO-<agent-id>.md` with non-execution file tools; when no immutable runtime ID is supplied, mint a collision-resistant request ID, derive `owner_token: agent:<normalized-name>:<task-id>:<request-id>`, and use the same components in the filename (for example `TODO-perplexity-0037-48-<request-id>.md`). That newly recorded token is the current session's immutable ownership token for this claim and must not be reused for another Task/session. Copy the exact Task, enough Feature context to detect drift, capability class, intended write scope, runner scope, external-resource needs, and assumptions. If Git-derived base/status is unavailable, record `base_commit: pending-discovery` rather than stopping.
7. Recompare the claim with current `TODO.md`, mark the Task `[p]`, and add the claim reference. Do not overwrite another marker, Task text, claim, or runner request.
8. If the claim contains `pending-discovery`, submit the fixed claimed read-only discovery request from `SANDBOX.md`, then replace it with the returned base commit before any mutating runner request.
9. Start mutating work only when the goal is clear, prerequisites remain terminal, and file, runner, external-resource, and integration scopes are disjoint. Multiple simultaneous Tasks must each satisfy these conditions and be listed explicitly in the claim.

A user-directed activity that is not an existing Task may use `TODO-<agent-id>.md` as a temporary coordination record, but must not falsely mark an unrelated Task `[p]`.

## Autonomous backlog repair

Agents are authorized and expected to repair backlog defects encountered during assigned or autonomously selected work when the intended result is determinable from the Feature goal, recorded decisions, neighboring Tasks, prerequisites, acceptance criteria, repository evidence, and established architecture.

Agentically repairable defects include:

- an open parent Task whose children are terminal but whose package-level consistency, aggregation, validation, manifest, or closure work remains undone;
- missing, unknown, reversed, inconsistent, or insufficient prerequisite relations;
- a syntactic cycle or a semantic deadlock that a simple prerequisite-graph validator does not detect;
- acceptance or completion text requiring an artifact owned by a downstream Task that cannot start until the current item closes;
- missing integration, migration, validation, evidence, recovery, or bookkeeping work;
- an internally contradictory or operationally impossible criterion caused by an evident drafting defect;
- a Task that must be split to remain bounded, independently verifiable, and executable under the available capability class.

For such a defect, the owning agent must:

1. retain or create the appropriate active claim and keep the affected item `[p]` while repairing it;
2. record the defect, evidence, affected items, and why the correction is determinable without a human decision;
3. derive the smallest intent-preserving correction and preserve or strengthen acceptance, traceability, authority, privacy, recovery, and validation requirements;
4. amend `TODO.md`, including adding/splitting Tasks or correcting prerequisites when necessary, without overwriting another active claim or concurrent material change;
5. replace premature downstream-artifact requirements with explicit local intermediate deliverables—such as a contract, candidate, manifest, digest list, or evidence bundle—that the downstream Task later verifies and incorporates;
6. validate identifiers, prerequisite endpoints and direction, cycles, markers, affected criteria, and the repaired execution order;
7. continue the repaired Task without requesting confirmation.

When all children of a parent Task are terminal, the parent is itself the next eligible package-closure item if its declared prerequisites are terminal. It does not close automatically and must not be skipped; perform its own consistency, aggregation, validation, evidence, and bookkeeping criteria.

This authority does not permit an agent to choose between materially different valid product architectures, weaken acceptance to make work pass, invent approval, accept security/privacy/release risk, expose credentials, change externally controlled configuration, or appropriate another session's claim. Use `[u]` only when such a human decision or authorization is the sole next action. Technical difficulty, unfamiliarity, a drafting defect, an open parent, or an agentically repairable dependency deadlock is not `[u]`.

Root `run.sh` is an executable request envelope only. Never use it as an escalation token, notification, question, reservation note, or substitute for accurate claim and backlog state.

## Performing work

- Keep going until the claimed Task is complete or clearly unreachable.
- Keep Task and claim progress accurate, including findings, assumptions, runner requests/results, validation, external state, and handoff information.
- Sandboxed agents may edit project files with non-execution tools but must route every script/process/test/generator/browser/network/package/Git operation through the runner protocol in `SANDBOX.md`.
- Prefer reviewed, tracked runner actions once available. Before then, make each `run.sh` self-contained, preflighted, bounded, idempotent where possible, and explicit about authority/base commit/write scope. When a sandboxed/grunt session's tool calls are throttled or limited, maximize useful work per request: package all safely preplanned inspection, targeted reads/counts, preflight, implementation/generation, validation, evidence, cleanup, and gated commit/bookkeeping steps for one coherent phase rather than iterating through many small tool calls or runner requests. Collect command-derived information inside that request when it is not needed to design the request safely. This request-economy optimization does not apply to privileged agents or require over-batching in sessions without tool-call pressure. Never bypass the runner to save a tool call, combine unrelated scopes, or permit mutation after a failed gate. Never overwrite another request in the singleton runner slot.
- Treat each root `run.sh` as a one-use consumable request. The runner archives its submitted content/result and removes the root file after execution; removal is required slot cleanup, not permission to reuse the old request. For a retry or next phase, first reconcile the matching result, then mint and record a new request ID and publish newly generated content only after confirming the slot is free. Never restore an archived request or assume an absent post-result `run.sh` is still pending.
- Make a best-supported assumption when permitted and record it. Use `[u]` only as defined in `TODO.md`: the next action requires user/manager clarification, authorization, credentials, external configuration, or another human decision.
- A technical failure is not automatically `[u]`. Investigate from available evidence, keep `[p]` with a precise blocker when work is still reachable, or use `[w]` with the required reason when the Task should close without implementation.
- Preserve unrelated staged, unstaged, and untracked work. Use path-limited commits and never overwrite or delete another agent's work without explicit authorization.
- Update required tests, documentation, generated artifacts, and call sites. Do not claim validation that the runner or a privileged agent did not actually run successfully.

## Completing work

1. Recompare the claimed Task and Feature with current `TODO.md`. Concurrent material drift or another owner's conflicting change is a blocker: do not overwrite it; record it and obtain resolution. An intrinsic, agentically determinable backlog defect is handled under **Autonomous backlog repair** and is not by itself a human blocker.
2. Validate the deliverables and disposition material findings. A sandboxed agent prepares a runner request containing all required preflight, focused validation, mutation-scope, and post-run checks.
3. Commit substantive deliverables with the configured user identity and a comprehensive Feature/Task message. Sandboxed agents request this path-limited Git operation through the runner; privileged agents may execute it directly.
4. After the substantive commit hash is known and reachable, update authoritative bookkeeping with non-execution file tools: mark `[x]` or `[w]`, add the required real `REF`, record validation/findings, and update unlocked dependencies.
5. If the Feature is terminal and closure prerequisites pass, move it from `TODO.md` to `DONE.md` with completion time and evidence.
6. Reconcile and delete `TODO-<agent-id>.md` only after its information is authoritative.
7. Commit bookkeeping separately. A sandboxed agent uses another runner request unless the approved runner transaction can safely create both commits and inject the first hash into the second. Never amend a commit to add its own hash.
8. Verify the final status and intended commit reachability through permitted tools or the runner, then immediately pick and start the next open, unclaimed, unlocked Task under the startup rules. Do not ask for confirmation merely because the next Task belongs to another Feature.

A runner transaction that creates both substantive and bookkeeping commits must expose both hashes, validate the intermediate and final trees, update only declared paths, and leave the claim intact on any partial failure.

## Interruptions and handoffs

Before yielding with claimed work incomplete:

- leave the Task `[p]` unless another state is justified by `TODO.md`;
- append progress, runner status/log locations, validation, remaining work, and interruption reason to both the Task and `TODO-<agent-id>.md`;
- retain the claim so ownership remains visible;
- identify temporary files, pending `run.sh`/runner requests, uncommitted changes, external state, and recovery steps;
- treat response/tool/time-budget exhaustion as an automatic-continuation interruption: do not ask the user whether to continue, choose another Task, execute a script, or grant privilege; do not record a planned action as completed; resume the recorded next step immediately on the next turn unless explicitly redirected.

Do not delete a live claim merely to make the working tree look clean. A sandboxed agent waiting for runner execution is still active and retains `[p]` plus its claim. A missing runner request that was planned but not actually published remains the owning agent's next action; it is not a `[u]` condition.

## Collaboration improvement suggestions

When an agent gains a concrete insight during its work that could make future agent cooperation safer, clearer, faster, or less conflict-prone, it must record the insight immediately in the suggestion log below rather than relying on conversation memory or waiting until Task completion.

A suggestion:

- is an append-only proposal, not active policy and not authority to disregard the current rules;
- must be concise and actionable, naming the observed situation, proposed improvement, expected benefit, and any risk or tradeoff;
- must include the date, proposing agent/session or claim token, and related Feature/Task when available;
- must not contain secrets, personal data, unsupported accusations, or large execution logs;
- must not rewrite or delete another agent's suggestion;
- must not modify active instruction text as though the proposal were already approved;
- should reference retained evidence or the claim progress log when the insight arose from a failure or race;
- must be added with non-execution file tools by sandboxed agents; no runner request is needed solely to append a suggestion.

High-value suggestions include opportunities to turn repeatedly needed manual or ad hoc work into a durable project tool. If an agent creates or discovers a command, parser, validator, report helper, migration aid, or other automation that is likely to help later Tasks or agents, it should immediately suggest productizing it as a documented, tested, tracked script—normally under `_src/tools/` and linked from the applicable `docs/pipeline/` catalog. The suggestion should identify the repeated workflow, current evidence or prototype, proposed interface, inputs/outputs and side effects, validation needs, ownership/maintenance expectations, and candidate callers. Do not confuse such a reusable tool with root `run.sh`: each `run.sh` is a one-use runner request and must never become the reusable implementation.

If concurrent edits make a safe append impossible, record the suggestion in the active claim immediately and reconcile it into this log at the next safe opportunity. A maintainer may later accept a suggestion by integrating it into the appropriate authoritative section, record its disposition, and retain or move the original entry for traceability.

### Suggestion log

<!-- Append new suggestions below. Format:
- YYYY-MM-DD — proposer: `<agent/session-or-owner-token>`; scope: `<Feature/Task or general>`
  - **Observation:** ...
  - **Suggestion:** ...
  - **Expected benefit:** ...
  - **Risk/tradeoff:** ...
  - **Evidence:** `<claim/path/ref or none>`
  - **Disposition:** pending
-->

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
