# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Capability classes, runner use, instruction precedence, and authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent-id>.md` files are active coordination claims. Marker and prerequisite semantics are defined by the header of `TODO.md`; do not invent alternative meanings.

Feature `0037` implementation must be executable by sandboxed/grunt agents. Privileged-agent availability must never be an unstated prerequisite.

## Starting work

1. Determine the capability class as required by `SANDBOX.md`; default to sandboxed/grunt.
2. Read `TODO.md` and active `TODO-<agent-id>.md` files with non-execution tools. Resume a claim only when the assignment explicitly references it or its immutable `owner_token` matches the current runtime/session token. Never infer ownership from a shared model/display name or filename such as `TODO-perplexity.md`; unmatched legacy claims belong to another session and must not be overwritten.
3. If the assignment names no Task and no claim is explicitly owned by this session, select work without asking the user: scan `TODO.md` from top to bottom and choose the first open, unclaimed Task whose start prerequisites are terminal and whose visible file/runner scope does not conflict. While Feature `0037` is unstarted, open/unclaimed/unlocked `0037-48` is its mandatory first pickup.
4. Ask the user to choose work only when no eligible Task exists or when the next action genuinely requires the human decision represented by `[u]`.
5. Create a collision-resistant `TODO-<agent-id>.md` with non-execution file tools; when no immutable runtime ID is supplied, mint a collision-resistant request ID, derive `owner_token: agent:<normalized-name>:<task-id>:<request-id>`, and use the same components in the filename (for example `TODO-perplexity-0037-48-<request-id>.md`). That newly recorded token is the current session's immutable ownership token for this claim and must not be reused for another Task/session. Copy the exact Task, enough Feature context to detect drift, capability class, intended write scope, runner scope, external-resource needs, and assumptions. If Git-derived base/status is unavailable, record `base_commit: pending-discovery` rather than stopping.
6. Recompare the claim with current `TODO.md`, mark the Task `[p]`, and add the claim reference. Do not overwrite another marker, Task text, claim, or runner request.
7. If the claim contains `pending-discovery`, submit the fixed claimed read-only discovery request from `SANDBOX.md`, then replace it with the returned base commit before any mutating runner request.
8. Start mutating work only when the goal is clear, prerequisites remain terminal, and file, runner, external-resource, and integration scopes are disjoint. Multiple simultaneous Tasks must each satisfy these conditions and be listed explicitly in the claim.

A user-directed activity that is not an existing Task may use `TODO-<agent-id>.md` as a temporary coordination record, but must not falsely mark an unrelated Task `[p]`.

## Performing work

- Keep going until the claimed Task is complete or clearly unreachable.
- Keep Task and claim progress accurate, including findings, assumptions, runner requests/results, validation, external state, and handoff information.
- Sandboxed agents may edit project files with non-execution tools but must route every script/process/test/generator/browser/network/package/Git operation through the runner protocol in `SANDBOX.md`.
- Prefer reviewed, tracked runner actions once available. Before then, make each `run.sh` self-contained, preflighted, bounded, idempotent where possible, and explicit about authority/base commit/write scope. Never overwrite another request in the singleton runner slot.
- Make a best-supported assumption when permitted and record it. Use `[u]` only as defined in `TODO.md`: the next action requires user/manager clarification, authorization, credentials, external configuration, or another human decision.
- A technical failure is not automatically `[u]`. Investigate from available evidence, keep `[p]` with a precise blocker when work is still reachable, or use `[w]` with the required reason when the Task should close without implementation.
- Preserve unrelated staged, unstaged, and untracked work. Use path-limited commits and never overwrite or delete another agent's work without explicit authorization.
- Update required tests, documentation, generated artifacts, and call sites. Do not claim validation that the runner or a privileged agent did not actually run successfully.

## Completing work

1. Recompare the claimed Task and Feature with current `TODO.md`. A material discrepancy is a blocker: do not overwrite it; record it and obtain resolution.
2. Validate the deliverables and disposition material findings. A sandboxed agent prepares a runner request containing all required preflight, focused validation, mutation-scope, and post-run checks.
3. Commit substantive deliverables with the configured user identity and a comprehensive Feature/Task message. Sandboxed agents request this path-limited Git operation through the runner; privileged agents may execute it directly.
4. After the substantive commit hash is known and reachable, update authoritative bookkeeping with non-execution file tools: mark `[x]` or `[w]`, add the required real `REF`, record validation/findings, and update unlocked dependencies.
5. If the Feature is terminal and closure prerequisites pass, move it from `TODO.md` to `DONE.md` with completion time and evidence.
6. Reconcile and delete `TODO-<agent-id>.md` only after its information is authoritative.
7. Commit bookkeeping separately. A sandboxed agent uses another runner request unless the approved runner transaction can safely create both commits and inject the first hash into the second. Never amend a commit to add its own hash.
8. Verify the final status and intended commit reachability through permitted tools or the runner, then pick another open, unclaimed, unlocked Task.

A runner transaction that creates both substantive and bookkeeping commits must expose both hashes, validate the intermediate and final trees, update only declared paths, and leave the claim intact on any partial failure.

## Interruptions and handoffs

Before yielding with claimed work incomplete:

- leave the Task `[p]` unless another state is justified by `TODO.md`;
- append progress, runner status/log locations, validation, remaining work, and interruption reason to both the Task and `TODO-<agent-id>.md`;
- retain the claim so ownership remains visible;
- identify temporary files, pending `run.sh`/runner requests, uncommitted changes, external state, and recovery steps.

Do not delete a live claim merely to make the working tree look clean. A sandboxed agent waiting for runner execution is still active and retains `[p]` plus its claim.

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
