# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Capability classes, runner use, instruction precedence, and authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent-id>.md` files are active coordination claims. Marker, prerequisite, Task-acceptance, and Feature-closure semantics are defined by the header of `TODO.md` and [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md); do not invent alternative meanings.

Feature `0037` implementation must be executable by sandboxed/grunt agents. Privileged-agent availability must never be an unstated prerequisite.

Capability classes and all sandbox-specific execution mechanics—including discovery, runner requests, network execution, and the queue dispatch lifecycle—are defined by `SANDBOX.md`. This file defines the collaboration and bookkeeping requirements shared across capability classes.

### Queue-based dispatch (`runner-queue@v1`)

Sandboxed agents reach the runner through the versioned queue, using non-execution file operations only:

- Stage the request under `.runner/drafts/<agent>/<request_id>/` with standard file-write tools.
- Publish it by an atomic same-filesystem rename to `.runner/requests/<request_id>`.
- Read the verdict from `.runner/results/<request_id>.result.json`.
- Observe lease expirations and idempotence keys; a retry of a rejected or failed request keeps its ancestry record (`retry_of`).

Requests with disjoint write scopes run in parallel; overlapping scopes are rejected (`RD-SCOPE-COLLISION`), as are unprivileged writes to governance documents (`RD-GOVERNANCE-SCOPE`). The legacy singleton `run.sh` is retired — `SANDBOX.md` retains its description for reading archived runs, not for new work.

Feature, Task, and Subtask work is carried on Git branches named after the item ID, merged upward, with claim files committed alongside work products. The branch topology, the binding base-and-merge start rule, merge authority by level, Feature integration, and the Feature-level `[u]` integration verdict are defined in [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md); the acceptance meanings it references are unchanged.

### Governance changes go on `main`; agents coordinate through the agent-inbox

Management decision `DEC-0044-012` (2026-08-21, recorded in [`docs/dossiers/dec-branching-merging-strategie.md`](docs/dossiers/dec-branching-merging-strategie.md)):

1. **Changes to governance processes are always made on `main`, and `main` is always current with respect to governance.** A governance artifact must never sit on a branch while other agents work against `main`.
2. **Agents coordinate through the agent-inbox.**

Governance artifacts are at minimum: decision records (`DEC-*`), the authority files `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, everything under `docs/pipeline/`, and the marker and prerequisite contract in the `TODO.md` header. Ordinary work products are **not** governance artifacts and continue to travel on item branches exactly as described in [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md).

This is an exception to the one-branch-per-item rule above, and it exists because governance is *shared* state. Shared state held on a private branch cannot be coordinated, only reconstructed afterwards — the same failure class `DEC-0044-008` already rejected for provenance. The concrete trigger: a decision record drafted on a branch took an ID that a parallel line of work had already assigned on `main`, producing two append-only records under one identifier that answered the same question in opposite ways. `main` is the only place where an allocation point for identifiers can exist at all. Before allocating a new `DEC-` identifier, check it against `main`.

Coordination duties that follow from (2): the mailbox is not a telephone — nothing is pushed, and a recipient sees mail only on its next turn. A coordination step is complete when the **answer** has arrived, not when the message was sent. Read the inbox before any consequential action: a merge to `main`, an acceptance, or the allocation of a new identifier. Addresses are case-sensitive. Acknowledge (`ack`) what you acted on, so senders can tell their message arrived instead of concluding your session is dead.

### Agents mutate only in item-owned worktrees; the root checkout is not written to

Management decisions `DEC-0044-010` and `DEC-0044-015` (recorded in [`docs/dossiers/dec-branching-merging-strategie.md`](docs/dossiers/dec-branching-merging-strategie.md)):

1. **Every mutation happens inside a worktree the agent owns for its item** — normally `.worktrees/<item-id>`, or an equally isolated path it provisioned itself. The shared root checkout `/Users/tobias.anton/devel/autodocs` is **never written to**: no authoring, no `git add`, no `git commit`, no `commit -a`, no cleanup, no reset. It is a read reference and the directory where `main` happens to be checked out. This includes governance artifacts: "governance lives on `main`" states which *branch*, not which *directory* — author the change in an item-owned worktree on a branch cut from `main`.
2. **Only one exception, and only the last step:** advancing `refs/heads/main`. `git update-ref` on `refs/heads/main` is **prohibited** — it moves the ref past the index and files of the worktree where `main` is checked out and leaves that worktree stale, which is exactly the damage these decisions exist to prevent (mechanism reproduced under Task `0044-14`). `main` is advanced **from the root checkout** with `git -C <root> merge --ff-only <branch>` (or `--no-ff` where `DEC-0044-008` requires a real merge commit), because a merge moves ref, index and files together. Only a privileged integrator or the Projektleitung may do this; no unprivileged worker moves `refs/heads/main` at all.
3. **Before any integration, and mandatorily before that ref advance, run the pre-integration hygiene check:** `python3 _src/tools/check_integration_hygiene.py --repo <integration-worktree>`. It is read-only and inspects every registered worktree for an index differing from `HEAD`, foreign staged trees, tracked-file divergence in the worktree checking out `main`, and the stale-after-ref-move signature. A non-zero exit is a stop, not a warning; exit `2` (the check could not run) is a failure, never a pass. It is a *complement to*, not a replacement for, the hard preflight in the root (`git diff --quiet`, `git diff --cached --quiet`, `HEAD` is `refs/heads/main`) — ordinary unstaged work on item branches and untracked files are intentionally outside this check. A failing preflight means **abort**, not tidy up: recovering the root is a separate, separately authorized operation.
4. **State that exists in no branch is snapshotted as a `preserved/*` tag before it is cleared.** Those tags are unreachable except through the tag itself, so deleting one can destroy the only copy of something. Never prune or garbage-collect them; removal requires explicit authorization from the current user for the named tag. The current tags, what each holds, and how to recover from one are documented in [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md) → *Preserved snapshot tags and recovery*; anyone taking a new snapshot appends its row there in the same commit.

The full rationale, the confirmed mechanism with its hermetic fixture, the finding codes, and the recovery commands are in [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md).

## Starting work

1. Determine the capability class as required by `SANDBOX.md`; default to sandboxed/grunt.
2. Read `TODO.md` and active `TODO-<agent-id>.md` files. Resume a claim only when the assignment explicitly references it or its immutable `owner_token` matches the current runtime/session token. Never infer ownership from a shared model/display name or filename such as `TODO-perplexity.md`; unmatched legacy claims belong to another session and must not be overwritten. A response/turn boundary is not a handoff: once this session mints or receives an immutable `owner_token`, that token remains this session's ownership proof for the claim until authoritative closure or explicit handoff. On every later turn, execution result, generic continuation prompt, or restored context, resume that owned `[p]` claim and its recorded next step before scanning for new work.
3. Do not abandon, defer, or replace an owned incomplete Task merely because it was not completed in one response, consumed multiple execution attempts, became technically difficult, or crossed a context/tool-budget boundary. Continue until it is complete or clearly unreachable under the state rules below. Do not open a new claim while an owned Task is actionable unless multiple simultaneous Tasks are explicitly justified, disjoint, and recorded in the claim.
4. If the assignment names no Task and no claim is explicitly owned by this session, select work without asking the user: scan all of `TODO.md` from top to bottom and choose the first open, unclaimed Task whose implementation start prerequisites are satisfied under `TODO.md` and whose visible file/execution scope does not conflict. A blocked item, a Task already claimed by another session, or the blocked successor of that Task is skipped for this scan; it does not block the scanning agent or the remainder of the backlog. Continue across package, Campaign, and Feature boundaries. While Feature `0037` is unstarted, open/unclaimed/unlocked `0037-48` is its mandatory first pickup.
5. Ask the user to choose work only when no eligible Task exists anywhere or when the next action genuinely requires the human decision represented by `[u]`. The fact that one dependency chain is occupied, the next textual Task is blocked, or the next eligible Task is substantial, unfamiliar, or belongs to a different Feature is not a reason to pause or request confirmation; claim the first globally eligible item and work autonomously. Do not wait for another session's claim when disjoint eligible work exists.
6. Create a collision-resistant `TODO-<agent-id>.md`; when no immutable runtime ID is supplied, mint a collision-resistant request ID, derive `owner_token: agent:<normalized-name>:<task-id>:<request-id>`, and use the same components in the filename (for example `TODO-perplexity-0037-48-<request-id>.md`). That newly recorded token is the current session's immutable ownership token for this claim and must not be reused for another Task/session. Copy the exact Task, enough Feature context to detect drift, `capability_class`, `execution_authority`, `startup_review`, intended write scope, applicable execution scope, external-resource needs, and assumptions. Record base/status discovery according to the capability-specific procedure in `SANDBOX.md`.
7. Recompare the claim with current `TODO.md`, mark the Task `[p]`, and add the claim reference. Do not overwrite another marker, Task text, claim, or execution request.
8. Complete any capability-specific discovery required by `SANDBOX.md` before mutation.
9. Start mutating work only when the goal is clear, implementation start prerequisites remain satisfied (including any explicit acceptance-before-start gate), and file, execution, external-resource, and integration scopes are disjoint. Multiple simultaneous Tasks must each satisfy these conditions and be listed explicitly in the claim. Before the first mutation of any qualifying cross-item gate scope, also satisfy the **Cross-item gate-scope review exception** below; backlog-repair authority does not bypass that startup mutation gate.
10. Before the first mutating change, establish the item's branch per [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md): base the Task branch off its Feature branch, or the Subtask branch off its Task branch; then merge in every done-but-unintegrated (`[x]`/`[w]`) prerequisite branch so its work products **and** claim files are present, and record each merged branch tip in the claim. Commit the claim file on the item's branch alongside the deliverables; it travels upward with every merge and is not deleted at `[x]`/`[w]`.

A user-directed activity that is not an existing Task may use `TODO-<agent-id>.md` as a temporary coordination record, but must not falsely mark an unrelated Task `[p]`.

## Dispatching a subagent

A session that spawns another agent is its **dispatcher** and is answerable for
the briefing being complete. A subagent never inherits the dispatcher's
capability class, authority, claim, or write scope implicitly.

Capability classes are defined in [`SANDBOX.md`](SANDBOX.md); which class a
process role requires, and which authority it does **not** confer, is defined in
[`docs/pipeline/process-roles.md`](docs/pipeline/process-roles.md). The branch
and worktree a briefing must name follow
[`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md). This rule
was established by decision `DEC-CAP-002` in
[`docs/dossiers/dec-capability-classes.md`](docs/dossiers/dec-capability-classes.md).

Every briefing must state, explicitly:

1. the **capability class**, as one of the exact names in `SANDBOX.md`
   (`sandboxed-grunt`, `unprivileged`, `privileged`);
2. the **item ID** and the branch/worktree to work in;
3. the **write scope** as exact paths;
4. what the subagent must **not** do — at minimum whether it may accept work,
   cross an integration checkpoint, or move a Feature to `DONE.md`.

The capability-class default in `SANDBOX.md` exists for a runtime that cannot
report its class. It is **not** a substitute for an assignment the dispatcher
failed to make. Omitting the class silently downgrades the subagent to
`sandboxed-grunt` and routes it onto the runner protocol, where it will queue on
the singleton `run.sh` slot it does not need — serializing agents that could
have run in parallel.

A briefing that orders direct execution — Git, branch, merge, commit, tests — but
states or defaults to `sandboxed-grunt` is **internally contradictory**. The
receiving session does not silently resolve it: it applies the safe default,
records the contradiction and the received briefing verbatim in its claim, and
reports the contradiction back to its dispatcher. It does not upgrade its own
class to make the order executable.

Route work through the runner **only** when the capability class actually
requires it. An `unprivileged` or `privileged` session never waits on the
`run.sh` singleton and never treats a foreign request in that slot as a blocker.

## Autonomous backlog repair

Agents are authorized and expected to repair backlog defects encountered during assigned or autonomously selected work when the intended result is determinable from the Feature goal, recorded decisions, neighboring Tasks, prerequisites, acceptance criteria, repository evidence, and established architecture, subject to the cross-item gate-scope review exception below.

Agentically repairable defects include:

- an open parent Task whose children are terminal but whose package-level consistency, aggregation, validation, manifest, or closure work remains undone;
- missing, unknown, reversed, inconsistent, or insufficient prerequisite relations;
- a syntactic cycle or a semantic deadlock that a simple prerequisite-graph validator does not detect;
- acceptance or completion text requiring an artifact owned by a downstream Task that cannot start until the current item closes;
- missing integration, migration, validation, evidence, recovery, or bookkeeping work;
- an internally contradictory or operationally impossible criterion caused by an evident drafting defect;
- a Task that must be split to remain bounded, independently verifiable, and executable under the available capability class.

### Cross-item gate-scope review exception

Use the canonical `cross-item-blast-radius` predicate from [`decision-record@v1`](docs/pipeline/decision-record.md#2-wann-ein-datensatz-verpflichtend-ist): the exception applies when the **actual declared behavior** of a gate can block the start, validation, acceptance, integration, publication, or closure of another work unit, or can change that other unit's contract. A shared path, technical difficulty, unfamiliarity, green validation, or a merely hypothetical cross-item effect of an ordinary bug is not enough.

Before the first mutation that implements, activates, widens, narrows, affirmatively retains, or removes a gate scope meeting that predicate, both of the following must already exist:

1. a conforming `decision-record@v1` naming and justifying the affected work units and gates; and
2. a supporting scope review by a management-instantiated **Architect** whose identity is distinct from the Implementer's identity.

Affirmative retention is an in-scope decision to preserve existing, already-contested gate behavior; passive inheritance is not affirmative retention. The Architect's scope review tests the proposed reach and authority before mutation. It is not Task acceptance, an integration review, an integration verdict, or `Acceptance: ✓`, and a green validation result does not prove that the scope is correct, complete, or authorized.

Keep the Task `[p]` while bounded preparation remains, including identifying affected units and gates, preparing the decision record, or obtaining the assigned Architect's review. Use `[u]` only when the Architect assignment, authority decision, dissent resolution, or management exception is the sole next action; never mutate the qualifying scope while that gate is unmet.

For such a defect, the owning agent must:

1. retain or create the appropriate active claim and keep the affected item `[p]` while repairing it;
2. record the defect, evidence, affected items, and why the correction is determinable without a human decision;
3. derive the smallest intent-preserving correction and preserve or strengthen acceptance, traceability, authority, privacy, recovery, and validation requirements;
4. amend `TODO.md`, including adding/splitting Tasks or correcting prerequisites when necessary, without overwriting another active claim or concurrent material change;
5. replace premature downstream-artifact requirements with explicit local intermediate deliverables—such as a contract, candidate, manifest, digest list, or evidence bundle—that the downstream Task later verifies and incorporates;
6. validate identifiers, prerequisite endpoints and direction, cycles, markers, affected criteria, and the repaired execution order;
7. continue the repaired Task without requesting confirmation whenever the cross-item gate-scope review exception is either inapplicable or already satisfied; otherwise continue all bounded preparation under `[p]` and stop before the qualifying mutation.

When all children of a parent Task are `[x]`/`[w]`, the parent is itself the next eligible package-completion item if its declared implementation start prerequisites are satisfied. It does not complete or become accepted automatically and must not be skipped; perform its own consistency, aggregation, validation, evidence, and bookkeeping criteria, then route the parent and any unaccepted children through privileged acceptance.

An open parent with implementation-complete children is not, by itself, a prerequisite defect. Do not remove dependencies on the parent, bypass its start-gate role, or mark it `[x]`/`[w]` or accepted merely by aggregating child states. Claim the parent, read its complete current acceptance criteria and Definition of Done, perform its declared package-level work, and complete its implementation only with the required committed deliverables, validation, evidence, and real REF. Acceptance remains a separate privileged review. Amend the backlog only when the parent's own requirements are contradictory, impossible, incomplete, or semantically deadlocked; record the specific defect and preserve the intended parent gate.

This authority does not permit an agent to choose between materially different valid product architectures, weaken acceptance to make work pass, invent approval, accept security/privacy/release risk, expose credentials, change externally controlled configuration, or appropriate another session's claim. Use `[u]` only when such a human decision or authorization is the sole next action. Technical difficulty, unfamiliarity, an ordinary drafting defect that does not meet the canonical cross-item predicate, an open parent, or an agentically repairable dependency deadlock is not `[u]`. A qualifying latent gate-scope defect is also not `[u]` while bounded preparation remains; it becomes `[u]` only when the authority assignment, decision, dissent resolution, or management exception described above is the sole next action.


If a complete global scan finds no eligible Task solely because remaining work is gated by one or more foreign active claims, do not appropriate those claims and do not set `[u]`. Recheck that no disjoint work exists, then write the short retrigger reminder defined by `SENTINEL.md`, naming the blocking Task/claim and telling the user which owning session must be retriggered. This reminder is the notification path for an otherwise idle agent; it is not permission to alter the foreign claim or remain idle when globally eligible work exists.

## Performing work

- Keep going until the claimed Task is complete or clearly unreachable.
- Keep Task and claim progress accurate, including findings, assumptions, execution requests/results, validation, external state, and handoff information.
- Treat required bookkeeping and execution preparation as work, not as a user checkpoint. Correcting a claim or progress log, reconciling completed execution, and preparing the next fully defined action are ordinary authorized steps. A brief status preamble may explain them, but the agent must perform all currently available steps in the same turn and must not stop merely to announce what it needs to do, ask permission, or wait for acknowledgement.
- Follow the capability-specific tool and execution rules in `SANDBOX.md`. Its sandboxed-agent runner protocol is the sole authority for runner request preparation, publication, reconciliation, network use, and the root `run.sh` lifecycle.
- Make a best-supported assumption when permitted and record it. Use `[u]` only as defined in `TODO.md`: the next action requires user/manager clarification, authorization, credentials, external configuration, or another human decision.
- A technical failure is not automatically `[u]`. Investigate from available evidence, keep `[p]` with a precise blocker when work is still reachable, or use `[w]` with the required reason when the Task should close without implementation.
- Preserve unrelated staged, unstaged, and untracked work. Use path-limited commits and never overwrite or delete another agent's work without explicit authorization.
- Update required tests, documentation, generated artifacts, and call sites. Do not claim validation that the runner or a privileged agent did not actually run successfully.

## Implementation completion and privileged acceptance

Implementation completion and work-product acceptance are separate lifecycles:

- `[x]` and `[w]` mean that implementation or the non-implementation disposition is committed with the required evidence and real `REF`; they satisfy ordinary implementation start gates but do not satisfy Feature closure.
- The implementation owner finalizes the implementation claim at `[x]`/`[w]` and continues normal queue work. Waiting for acceptance is not `[u]`, does not retain the implementation write scope, and is not permission to self-accept.
- Sandboxed/grunt agents must never create, change, invalidate, or remove `Acceptance: ✓`, represent themselves as acceptance reviewers, request generic runner acceptance, or move a Feature to `DONE.md`. They may prepare a complete acceptance package and correct review findings under a new or resumed implementation claim.
- A Task or Feature acceptance review starts only when the current user or registered authority explicitly assigns the exact scope to a currently privileged session. Acceptance is never selected autonomously merely because `[x]`/`[w]` work is waiting.
- The privileged reviewer must normally be independent of the claim owner, principal implementer, decisive technical author, and sole validation producer. Any exception requires an explicit bounded authority waiver; privilege alone is not authority or independence.
- A reviewer a session **spawned itself** may satisfy that independence, under three conditions (management decision `DEC-0044-013`, 2026-08-21). The subagent must **assume the reviewer persona explicitly**; that persona must be **distinct from the persona of the agent that created it**; and the **briefing prompt and the context handed to it must be recorded** with the review. The record names the dispatching identity, the reviewer persona, the verbatim briefing, and what context the reviewer was and was not given. An unrecorded self-spawned reviewer does not satisfy `TK-1`: without the briefing text nobody can tell afterwards whether the reviewer was pointed at the answer. The rule exists because the failure mode is real — a session that had correctly recognized the same situation earlier in its own run failed to recognize it later the same day.
- The reviewer follows [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md): pin the exact contract/baseline, compute and inspect the transitive non-accepted prerequisite closure, review bottom-up, inspect work products and findings, independently evaluate/rerun validation, preserve authority boundaries, and record `accepted`, `rejected`, or `inconclusive` append-only.
- Acceptance evidence is committed before a separate path-isolated bookkeeping commit adds `Acceptance: ✓` with the real review REF and required digests. Material baseline change invalidates current acceptance through an additive record and impact analysis; history is never deleted.
- A Feature moves to `DONE.md` only when its work is terminal, every integration checkpoint within it has a current passing integration review — including the Feature aggregate review when the Feature node itself is flagged `Integration review: mandatory` — and every required transitive `[x]`/`[w]` predecessor induced into those Task-Acceptance batches has its own current accepted disposition. Which nodes independently trigger integration review is the architect's declared decision (see the `TODO.md` header), not a blanket rule that every Task independently triggers review. It does not exempt unmarked predecessors from prerequisite-closed Acceptance; the `DONE.md` move is always a privileged act.
- The **architect** is an authority instantiated by management: it subdivides a Feature into bounded, context-rich work packages so implementers need minimal reasoning, reviews the resulting tasks, and flags the most critical ones `Integration review: mandatory` with recorded rationale. Checkpoint placement is exclusively Architect authority. An Architect may add the attribute at decomposition or later, including while a node is `[x]`/`[w]`, but only before that node has current Acceptance. Current Acceptance closes that window; later addition, removal, or movement requires separately authorized append-only invalidation or reopening first, and history is never rewritten. Sandboxed/grunt implementers never set, clear, or move it; a node touching an irreversible migration, external effect, credential/security boundary, or public release that is left unflagged carries an explicit architect **no-checkpoint justification**. Architect, implementer, and integrator are distinct roles, defined together with their capability-class mapping, separation rules, and personas in [`docs/pipeline/process-roles.md`](docs/pipeline/process-roles.md); **privilege is not independence**, and any decision whose reach extends beyond the deciding agent's own work unit requires a recorded decision (`TK-2`) even when the node carries no checkpoint. Every Feature breakdown must include exactly one integrating task, flagged `Integration review: mandatory`, as the Feature's review floor. Management (the current user or a registered authority) may waive that floor or override a `[u]` verdict only by an explicit, recorded authorization naming authority, scope, reason, and compensating controls — never an autonomous agent action.
- Merges only move work upward; their authority follows the architect's **integration checkpoints**, not the hierarchy level (see [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md)). A merge crossing no checkpoint is grunt-eligible (typically **Subtask→Task**, including parallel subtasks from different agents); a merge crossing a node marked `Integration review: mandatory`, and the `Feature→`main``/`DONE.md` closure, require the privileged *integrator*. In the linear case a grunt chains Task branches and a privileged agent integrates the last one at closure, reviewing any intermediate checkpoint as its boundary is crossed.
- Feature integration is where the privileged integrator merges the required work into the Feature branch, reviews each marked checkpoint, and expands each checkpoint's Task-Acceptance assignment through the complete transitive prerequisite closure until current valid Acceptance boundaries. Every included `[x]`/`[w]` node — marked or unmarked — receives its own bottom-up decision and, on approval, its own `Acceptance: ✓` record before the dependent checkpoint can be accepted. An unmarked node does not independently trigger integration review and missing Acceptance does not block ordinary successor implementation. The integrator then reconciles carried predecessor claims and, only with all checkpoint reviews and induced Acceptance batches current, integrates the Feature into `main` and moves it to `DONE.md`.
- If the integrator cannot approve the work at a checkpoint, it does not silently fix or force it through. It records a `[u]` **integration verdict** beneath that node (verdict author, authority reference, timestamp, rejected items, reason, integration-branch tip) and hands resolution to an explicit user interaction. It never clears its own `[u]` verdict without the user's decision; markers and acceptance records keep their own true state.

## Completing implementation work

1. Recompare the claimed Task and Feature with current `TODO.md`. Concurrent material drift or another owner's conflicting change is a blocker: do not overwrite it; record it and obtain resolution. An intrinsic, agentically determinable backlog defect is handled under **Autonomous backlog repair** and is not by itself a human blocker.
2. Validate the deliverables and disposition material findings under the capability-specific execution rules in `SANDBOX.md`.
3. Commit substantive deliverables with the configured user identity and a comprehensive Feature/Task message, using path-limited operations that preserve unrelated work. A sandboxed/grunt agent performs every Git-history mutation—including branch creation, merge, commit, tag, reset, rebase, and push—only through its active claim-bound runner request; direct Git execution is prohibited.
4. After the substantive commit hash is known and reachable, update authoritative implementation bookkeeping: mark `[x]` or `[w]`, add the required real `REF`, record validation/findings, and update implementation-start dependencies. Do not add acceptance credit.
5. When the item reaches `[x]`/`[w]`, recheck every deferred (`[d]`) successor that named it as a prerequisite: its blocker may now be gone. Set each rechecked successor to `[ ]`, `[p]`, `[x]`, or `[u]` as its actual state requires, or leave `[d]` with the still-open blocker named. Two agents rechecking the same deferred item concurrently is tolerated — a deferred item can be looked at again at any time. `legacy_task_doctor` reports a deferred item whose prerequisites have all become terminal (`LTD-DEFERRED-STALE`) and one that names no prerequisite at all (`LTD-DEFERRED-UNVERIFIABLE`); the tool is the net, this step is the duty.
6. For branch-based work, keep the implementation `TODO-<agent-id>.md` committed on the item's branch: it is carried upward by merges and is reconciled and removed by the privileged integrator during Feature integration (see [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md)), not at `[x]`/`[w]`. In a non-branch legacy flow, reconcile and delete it only after its information is authoritative. Either way, finishing at `[x]`/`[w]` ends the agent's active ownership and write-scope lease and returns it to queue work; the persisted claim artifact is provenance, not a lingering lease, and acceptance waiting never keeps ownership active.
7. Commit implementation bookkeeping separately unless the capability-specific execution procedure in `SANDBOX.md` permits a safe transaction that creates both commits and injects the substantive hash into the bookkeeping commit. Never amend a commit to add its own hash.
8. If this session was separately and explicitly assigned as the privileged acceptance reviewer, complete the independent acceptance procedure and its separate evidence/bookkeeping commits. Otherwise stop at `[x]`/`[w]`; do not infer assignment.
9. Move a Feature to `DONE.md` only through the separately authorized aggregate-acceptance path described above; implementation terminality or a closure-eligible advisory is insufficient.
10. Verify final status and intended commit reachability, then immediately pick and start the next open, unclaimed, implementation-unlocked Task under the startup rules. Do not ask for confirmation merely because the next Task belongs to another Feature.

### Check-in provenance

Every agent check-in or commit performed on behalf of a user must carry durable provenance:

- Preserve and reproduce verbatim the full text of every user-authored prompt that materially requested, authorized, corrected, or triggered the included artifacts. Retain prompt order, line breaks, code blocks, and corrections; do not summarize them. Do not include system, developer, or internal prompts.
- Put that provenance directly in the substantive commit message when practical. Otherwise, commit a tracked UTF-8 provenance receipt atomically with the artifacts, and name the receipt path and its digest in the commit message. A bookkeeping commit references the substantive provenance instead of duplicating it unless separately prompted.
- For a script- or process-triggered check-in, also record the executable or process name and the execution date as an unambiguous ISO-8601 timestamp including its timezone. If no user prompt directly triggered it, state that fact rather than inventing a prompt, and record the durable trigger or input reference.
- If required prompt text is unavailable, do not fabricate it or complete the check-in. Record the blocker and recover or request the authoritative source.
- Never persist secrets, credentials, or restricted personal data merely to satisfy verbatim provenance. Stop and obtain sanitized authorization or input, and explicitly record any authorized redaction rather than silently altering the prompt.

## Interruptions and handoffs

Before yielding with claimed work incomplete:

- leave the Task `[p]` unless another state is justified by `TODO.md`;
- append progress, execution or assigned acceptance-review status/log locations, validation, remaining work, and interruption reason to the applicable Task history and coordination record;
- retain the claim so ownership remains visible;
- identify temporary files, pending execution requests or results, uncommitted changes, external state, and recovery steps;
- treat response/tool/time-budget exhaustion as an automatic-continuation interruption: do not ask the user whether to continue or choose another Task; do not record a planned action as completed; resume the recorded next step immediately on the next turn unless explicitly redirected.

Do not delete a live claim merely to make the working tree look clean. Pending execution does not end ownership: the Task remains `[p]` and the agent retains its claim.

## Collaboration improvement suggestions

When an agent gains a concrete insight during its work that could make future agent cooperation safer, clearer, faster, or less conflict-prone, it must record the insight immediately in the suggestion log below rather than relying on conversation memory or waiting until Task completion.

A suggestion:

- is an append-only proposal, not active policy and not authority to disregard the current rules;
- must be concise and actionable, naming the observed situation, proposed improvement, expected benefit, and any risk or tradeoff;
- must include the date, proposing agent/session or claim token, and related Feature/Task when available;
- must not contain secrets, personal data, unsupported accusations, or large execution logs;
- must not rewrite or delete another agent's suggestion;
- must not modify active instruction text as though the proposal were already approved;
- should reference retained evidence or the claim progress log when the insight arose from a failure or race.

High-value suggestions include opportunities to turn repeatedly needed manual or ad hoc work into a durable project tool. If an agent creates or discovers a command, parser, validator, report helper, migration aid, or other automation that is likely to help later Tasks or agents, it should immediately suggest productizing it as a documented, tested, tracked script—normally under `_src/tools/` and linked from the applicable `docs/pipeline/` catalog. The suggestion should identify the repeated workflow, current evidence or prototype, proposed interface, inputs/outputs and side effects, validation needs, ownership/maintenance expectations, and candidate callers. Do not confuse a reusable project tool with a capability-specific execution request or other temporary coordination artifact.

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

- 2026-08-16 — proposer: `agent:perplexity:0037-49:20260816-1608`; scope: `Feature 0037 / Task 0037-49`
  - **Observation:** The 0037-49 prerequisites (SSH signing config, allowed_signers, authorities.json, credential handle, runner service) required multi-step manual setup with no machine-verifiable gate. Each future agent or operator attempting the approval flow must rediscover the required state from prose docs alone.
  - **Suggestion:** Productize `_src/tools/manage_approval_readiness.py` as a first-class tracked tool with tests, link it from `docs/pipeline/tools.md`, and mandate that `--check --json` passes (EXIT=0) as a stated prerequisite for `0037-07`. Companion doc `docs/pipeline/issue-approval-setup.md` should be kept in sync with the script's check list.
  - **Expected benefit:** Any agent or operator can verify readiness in one command rather than reading and manually cross-checking five policy files. Reduces risk of approval attempts against a misconfigured environment. Makes the prerequisite machine-enforceable.
  - **Risk/tradeoff:** Script must be kept in sync with policy file schemas; schema drift will produce false OKs. Suggest adding a schema version field to each policy file and asserting it in the script.
  - **Evidence:** `_src/tools/manage_approval_readiness.py` (commit c8250ebd); `docs/pipeline/issue-approval-setup.md` (same commit); live check EXIT=0 at ef350b4f.
  - **Disposition:** pending

- 2026-08-16 — proposer: `agent:zed:runner-transaction-suggestion:20260816`; scope: `general / legacy singleton runner`
  - **Observation:** Grunt-authored one-use `run.sh` requests repeatedly hand-code generation, validation, bookkeeping mutation, claim deletion, staging, and commits. The current Task `0036-05` request mutates `TODO.md` and removes claims before validation, treats a missing Task as a successful warning, and can include unrelated pre-staged files in its commit. Existing `_src/tools/task_bookkeeping_closure.py` only edits bookkeeping files and does not provide transaction preflight, validation gating, atomic promotion, index isolation, commit, or recovery guarantees.
  - **Suggestion:** Productize a tested stdlib-only `_src/tools/runner_transaction.py` (or narrowly extend the existing closure helper) with a declarative manifest and explicit `preflight`, `generate`, `validate`, `promote`, `commit-substantive`, `commit-bookkeeping`, and `finalize-claim` phases. It should fail closed on any nonzero phase or structured error finding; verify exact base/authority/owner token/claim/REF and declared read-write scopes; stage through a temporary index or equivalent path-limited mechanism; preserve the exact claim until final commit verification; emit bounded structured evidence; and support dry-run plus injected-failure tests. Add a small, policy-reviewed `run.sh` envelope template that invokes only this tool with a task-scoped manifest, then nudge grunts through `SANDBOX.md`, `docs/pipeline/tools.md`, examples, and validation/lint rejection of ad hoc closure sequences.
  - **Expected benefit:** Centralizes the destructive workflow into one auditable fail-closed implementation, prevents partial closure and unrelated-index commits, reduces repetitive generated shell, and gives grunts a shorter first-attempt-safe request format.
  - **Risk/tradeoff:** A generic transaction engine can become an unsafe shell escape or conflict with the approved Feature `0037` typed-action queue. Keep phase actions allowlisted and argument-vector based, prohibit arbitrary shell strings, version the manifest, and design it as a legacy bootstrap adapter whose semantics can be reused by or retired into Task `0037-46.01` rather than creating a competing permanent runner protocol.
  - **Evidence:** `run.sh:8-46`; `_src/tools/task_bookkeeping_closure.py:1-27,36-125`; `SANDBOX.md:54-79,88-96`; `docs/pipeline/agent-execution.md:9-20`.
  - **Disposition:** pending

- 2026-08-20 — proposer: `agent:seven-bellana:0038-14-repair:20260820T041725Z`; scope: `Feature 0038 / Task 0038-14 repair, general / automation_safety.py policy schema`
  - **Observation:** `_src/tools/automation_safety_policy.json` disposition entries can only stay valid while their `owner_task` names a currently open (non-`x`/`w`) Task — `_validate_dispositions()` unconditionally rejects `owner_task <terminal>` regardless of `expires_after_task`. This is correct for findings that genuinely still need code remediation, but it has no representation for a finding that has already been **proven** safe (e.g. `_src/tools/sync_to_devel.sh`'s `AUTO001` finding, fault-injection-proven by `0038-14` at `92ab55f49e19025b543fedce8627c9f7fac64815`): the instant its owning Task closes, the disposition expires exactly like an unaddressed one, even though no further code change is expected or possible. The only available repair is to re-point `owner_task` to a different currently-open Task, which is misleading bookkeeping (it looks like open work remains) and guarantees the same expiry recurs whenever that new custodian Task closes, unless yet another live Task is found. This exact gap caused Task `0038-14`'s closure to silently break 19 dispositions (not the 5 it flagged), confirmed by `python3 _src/tools/automation_safety.py --json` returning `verdict: FAIL` with 38 policy errors before this repair.
  - **Suggestion:** Add a third disposition `kind`, e.g. `"proven-closed"`, whose validity is anchored to an immutable `owner_ref` (a reachable commit SHA carrying the fault-injection/proof evidence) instead of a live Task ID, plus a `proof_summary` field long enough to be independently reviewable. Such an entry does not expire when a Task closes — it expires only if the evidence commit becomes unreachable, the `evidence_sha256` no longer matches (code changed), or a reviewer explicitly invalidates it. Keep `blocking-task` and `narrow-suppression` exactly as they are for genuinely open remediation.
  - **Expected benefit:** Removes a whole class of "Task closes → gate breaks repo-wide" incidents (this is the second occurrence of that pattern in Feature `0038`/`0040`, after the `0038-03`/`run-loop.sh` incident); lets a fully proven finding be closed once instead of perpetually re-parked under whichever Task happens to still be open; makes the policy file honestly reflect which findings need more work versus which are done.
  - **Risk/tradeoff:** A permanent-looking disposition kind must not become a silent rubber stamp — require the `owner_ref` commit to actually contain retrievable proof (test names/output, not just prose) and keep the check that `evidence_sha256` still matches the live finding, so a later edit to the flagged line still re-opens it. Schema/tool change is itself a Task, not something this suggestion authorizes unilaterally.
  - **Evidence:** `_src/tools/automation_safety.py:2757-2848` (`_validate_dispositions`); `_src/tools/automation_safety_policy.json` (pre-repair state, commit `58d781595` on branch `0038-14`); `TODO.md` Feature `0038` Task `0038-14` completion/escalation note and this repair's note beneath it.
  - **Disposition:** pending

- 2026-08-22 — proposer: `agent:Kathryn-Harry-20260822T003000Z:qa-sweep-20260822`; scope: `general / main-integration path-loss detection`
  - **Observation:** Commit `4b95d99db` (DEC-0044-012, 2026-08-21, direct commit to `main`) silently deleted 4869 lines of already-integrated work from three unrelated, already-`[x]`/`[w]` items (`0038-16.01`, `0043-02`, `0038-28`) — likely a commit made from a stale root-checkout working tree. It went unnoticed for hours and was found only by chance (Seven's report, repaired via `27930dc9c`). A 30-day history sweep of `main` (`git log --numstat` deletion-excess ranking over 534 non-merge commits, plus a first-parent diff for all 35 merge commits in the window) found no second occurrence, but the check was manual and one-off.
  - **Suggestion:** Add a machine check, run (a) as a pre-advance gate before any commit or merge moves `refs/heads/main`, and (b) as a periodic (e.g. daily) standing report, that: for every path introduced by a branch tip recorded as `[x]`/`[w]` in `TODO.md`/`DONE.md` and reachable as an ancestor of the new `main` tip, confirms the path still exists on the new tip and has not shrunk implausibly (e.g. >80% line-count drop) without the commit message naming that path. On a pre-advance-gate hit: **block the advance**, do not auto-heal, and emit a structured finding naming the path, the losing commit, and the owning item; report it to the committing/merging agent and via agent-inbox to the current project lead. On a periodic-report hit (gate bypassed or not run): same structured finding, delivered as a standing report, not a silent log line.
  - **Expected benefit:** Turns a rare, high-damage, hours-to-notice failure mode into an immediate, addressed one; gives the periodic report as a net under a gate that can be skipped or bypassed by direct-to-main commits (which DEC-0044-012 explicitly permits for governance artifacts) — matching the "hook is a net, not the gate" philosophy already adopted for provenance in DEC-0044-008.
  - **Risk/tradeoff:** A naive line-count-drop heuristic will false-positive on legitimate large deletions (retirements, translations, migrations) — this sweep hit five such cases (`ac2e9f5376`, `2d6493cafb`, `3660701735`, `505caf6f75`, `0f21b9f14b`), all correctly explained by their commit messages. Any implementation needs either a message-based allowlist/justification field or human override at the gate, and must be scoped to paths traceable to a recorded `[x]`/`[w]` branch tip — it cannot police free-form deletions outside that traceable set. Building it is a Task, not authorized by this suggestion alone.
  - **Evidence:** `4b95d99db` / `27930dc9c` (this repository, `main`); this sweep's report at `docs/campaign-evidence/qa-sweep-20260822/report.md` (branch `qa-sweep-20260822`, worktree `.worktrees/qa-harry-20260822T003000Z`), which lists all inspected commits and their disposition.
  - **Disposition:** pending

- 2026-08-23 — proposer: `kathryn` (Projektleiter, interaktive Session); scope: `general / Koordination bei Sessionwechseln und Wartelagen` (beobachtet an `0037-46.02`, `0044-04`)
  - **Observation (drei verwandte Vorfaelle eines Tages):** (a) `Harry` lief ein Heredoc im Root-Checkout statt im Reviewworktree, weil ein `cd` aus einem frueheren Tool-Aufruf nicht persistierte (`F-HARRY-R4-SELF-001`, selbst gemeldet und bereinigt); mir schlug am selben Tag ein Preflight fehl, weil er im Zweig- statt Root-Worktree lief. (b) Adas `0044-04`-Korrektur lag 7,5 h fertig auf dem Branch, waehrend alle auf eine angekuendigte Tip-Meldung warteten, die die inzwischen beendete Session nie mehr absetzen konnte. (c) Mailbox-Weckrufe fuehrten Turns derselben Session ausserhalb des sichtbaren Gespraechsfadens aus; die Antworten sahen wie eine parallele Zweitinstanz aus, erzeugten eine Doppelantwort an `harry`, und die Projektleitung haette beinahe den eigenen Prozess beendet (PID-Verwechslung, vom Berechtigungsfilter gestoppt).
  - **Suggestion:** Drei Arbeitsregeln: (1) In Umgebungen ohne garantiert persistentes Arbeitsverzeichnis ist ein `cd`-basierter Worktree-Wechsel keine Isolationsmassnahme — mutierende Git-/Datei-Operationen nur mit absoluten Pfaden bzw. `git -C <abs>`. (2) Wer eine Meldung ankuendigt, benennt den **erwarteten Commit/Tip vorher**, damit Wartende selbst am Repository nachmessen koennen, statt auf eine Meldung zu warten, die eine beendete Session nicht mehr senden kann; Wartende messen nach spaetestens 30 min selbst nach. (3) Vor jeder „fremde Instanz unter meinem Namen"-Diagnose die Prozessliste gegen die eigene Session-ID pruefen (`ps aux | grep claude`, `--resume <id>`); erst danach koordinieren oder gar beenden.
  - **Expected benefit:** Verhindert Root-Checkout-Verletzungen durch stillen cwd-Verlust, stundenlange tote Wartelagen auf unmoegliche Meldungen, und Fehlreaktionen auf die eigenen Weckruf-Turns (bis hin zum Selbstabschuss).
  - **Risk/tradeoff:** Regel (2) verlagert Last auf den Ankuendigenden; bei echten Ueberraschungs-Commits gibt es keinen vorab nennbaren Tip — dann gilt die 30-min-Nachmesspflicht des Wartenden. Reine Arbeitsregeln, keine Werkzeugaenderung; ein spaeterer Task kann (1) als Lint fuer Runner-/Subagent-Skripte haerten.
  - **Evidence:** agent-inbox `1787483881414-d51c8e0f` (harrys Selbstbefund und Wartelagen-Analyse); Commit `c8d3c1672` (7,5 h unentdeckt); Doppelantworten `1787483931987`/`1787483963069`; PID-Vorfall in der kathryn-Session vom 2026-08-23 (kill 42491, vom Klassifikator blockiert).
  - **Disposition:** pending

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).

- 2026-08-22 — proposer: `kathryn` (Projektleiter); scope: `general / check_integration_hygiene.py FOREIGN_STAGED_TREE at scale`
  - **Observation:** The mandatory pre-integration hygiene check scans **every** registered worktree — currently 108 — and reports `FOREIGN_STAGED_TREE` for any whose index differs from `HEAD`. Today that produced a false blocker with real cost: at 14:47Z `Harry-Neelix-20260822T164100Z` was stopped from starting Task `0043-05` because `.worktrees/0038-30` had a differing index. That worktree belonged to `Kathryn-Icheb-20260822T144500Z`, which was simply **mid-commit** on an unrelated Task; it finished at 14:52Z and the same check then returned `PASS`/exit `0` with the same 108 worktrees. Harry correctly did not touch the foreign worktree and correctly escalated. Nothing was wrong, and the escalation was still the right call — which is exactly the problem.
  - **Why it will get worse:** the probability that *at least one* of N concurrently active agents is inside the few-second window between `git add` and `git commit` grows with N. At 108 registered worktrees and several dispatchers running parallel workers, a transient index state in any one of them can stop an unrelated agent's start. The check cannot distinguish "an agent is committing right now" from "someone left a foreign staged tree behind", because both look identical in a single instantaneous sample.
  - **Suggestion:** Give the check a way to tell transient from stale. Cheapest form: re-sample a worktree that trips `FOREIGN_STAGED_TREE` after a short delay and only report it if it is still divergent — a commit in flight resolves in seconds, an abandoned staged tree does not. A second, complementary form: report the offending worktree's index mtime, so a reader can immediately see "0.4s old" versus "11 hours old" without re-running anything. Consider also scoping the blocking severity to worktrees that are actually relevant to the integration being attempted, and reporting the rest as advisory — Harry's `0043-05` start had no relationship whatsoever to `0038-30`.
  - **Expected benefit:** Removes a class of false stops that scales with team size, without weakening the check: a genuinely abandoned foreign staged tree still trips it, because it is still divergent on the second sample. Keeps the escalation path meaningful — an agent that escalates should be reporting something real.
  - **Risk/tradeoff:** A re-sample adds latency to a gate that runs before every integration, and a poorly chosen delay could let a *fast* bad state through. The mtime variant is free and non-blocking but only informs a human; it does not fix an automated gate. Neither should weaken `MAIN_WORKTREE_DIRTY` or the stale-after-ref-move signature, which are not transient by nature. Building this is a Task, not authorized by this suggestion.
  - **Evidence:** agent-inbox messages `1787410058910-05fe30e3` (`harry-neelix-20260822t164100z`) and `1787410081892-9805b8f0` (`harry`), both 2026-08-22; `1787410364248-8bca2cf0` (`kathryn-icheb-20260822t144500z`) showing the owning agent's completion at 14:52Z; check re-run at 14:54Z: `PASS`, exit `0`, 108 registered worktrees.
  - **Disposition:** pending
