# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Capability classes, runner use, instruction precedence, and authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent>.md` files are active coordination claims. Marker and prerequisite semantics are defined by the header of `TODO.md`; do not invent alternative meanings.

Feature `0037` implementation must be executable by sandboxed/grunt agents. Privileged-agent availability must never be an unstated prerequisite.

## Starting work

1. Determine the capability class as required by `SANDBOX.md`; default to sandboxed/grunt.
2. Inspect `TODO.md`, prerequisites, active `TODO-<agent>.md` files, relevant working-tree state, and the runner slot/queue. A sandboxed agent may use the claimless read-only bootstrap request defined by `SANDBOX.md` only when its assignment includes the required exclusive runner lease, to discover the base commit/status needed for its claim; that request must not mutate anything.
3. Start only a Task whose goal is clear, whose start prerequisites are terminal, and whose write and runner scopes do not conflict with another active claim.
4. Create `TODO-<agent>.md` with non-execution file tools. Copy the exact Task, enough Feature context to detect drift, discovered base commit, capability class, intended write scope, runner reservation/request identity, external-resource needs, and assumptions.
5. Recompare the claim with current `TODO.md`, then mark the Task `[p]` and add a claim reference. Do not overwrite another marker, Task text, claim, or runner request.
6. Multiple simultaneous Tasks are allowed only when prerequisites are satisfied and file, runner, external-resource, and integration scopes are disjoint.

A user-directed activity that is not an existing Task may use `TODO-<agent>.md` as a temporary coordination record, but must not falsely mark an unrelated Task `[p]`.

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
6. Reconcile and delete `TODO-<agent>.md` only after its information is authoritative.
7. Commit bookkeeping separately. A sandboxed agent uses another runner request unless the approved runner transaction can safely create both commits and inject the first hash into the second. Never amend a commit to add its own hash.
8. Verify the final status and intended commit reachability through permitted tools or the runner, then pick another open, unclaimed, unlocked Task.

A runner transaction that creates both substantive and bookkeeping commits must expose both hashes, validate the intermediate and final trees, update only declared paths, and leave the claim intact on any partial failure.

## Interruptions and handoffs

Before yielding with claimed work incomplete:

- leave the Task `[p]` unless another state is justified by `TODO.md`;
- append progress, runner status/log locations, validation, remaining work, and interruption reason to both the Task and `TODO-<agent>.md`;
- retain the claim so ownership remains visible;
- identify temporary files, pending `run.sh`/runner requests, uncommitted changes, external state, and recovery steps.

Do not delete a live claim merely to make the working tree look clean. A sandboxed agent waiting for runner execution is still active and retains `[p]` plus its claim.

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
