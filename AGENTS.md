# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Capability classes, runner use, instruction precedence, and authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent-id>.md` files are active coordination claims. Marker, prerequisite, Task-acceptance, and Feature-closure semantics are defined by the header of `TODO.md` and [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md); do not invent alternative meanings.

Feature `0037` implementation must be executable by sandboxed/grunt agents. Privileged-agent availability must never be an unstated prerequisite.

Capability classes and all sandbox-specific execution mechanics—including discovery, runner requests, network execution, and the root `run.sh` lifecycle—are defined by `SANDBOX.md`. This file defines the collaboration and bookkeeping requirements shared across capability classes.

Feature, Task, and Subtask work is carried on Git branches named after the item ID, merged upward, with claim files committed alongside work products. The branch topology, the binding base-and-merge start rule, merge authority by level, Feature integration, and the Feature-level `[u]` integration verdict are defined in [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md); the acceptance meanings it references are unchanged.

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
- The reviewer follows [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md): pin the exact contract/baseline, compute and inspect the transitive non-accepted prerequisite closure, review bottom-up, inspect work products and findings, independently evaluate/rerun validation, preserve authority boundaries, and record `accepted`, `rejected`, or `inconclusive` append-only.
- Acceptance evidence is committed before a separate path-isolated bookkeeping commit adds `Acceptance: ✓` with the real review REF and required digests. Material baseline change invalidates current acceptance through an additive record and impact analysis; history is never deleted.
- A Feature moves to `DONE.md` only when its work is terminal and every integration checkpoint within it has a current passing integration review — including the Feature aggregate review when the Feature node itself is flagged `Integration review: mandatory`. Which nodes are checkpoints is the architect's declared decision (see the `TODO.md` header), not a blanket per-Task acceptance requirement; the `DONE.md` move is always a privileged act.
- The **architect** is an authority instantiated by management: it subdivides a Feature into bounded, context-rich work packages so implementers need minimal reasoning, reviews the resulting tasks, and flags the most critical ones `Integration review: mandatory` — with recorded rationale — at decomposition. Sandboxed/grunt implementers never set, clear, or move it; a node touching an irreversible migration, external effect, credential/security boundary, or public release that is left unflagged carries an explicit architect **no-checkpoint justification**. Architect, implementer, and integrator are distinct roles, defined together with their capability-class mapping, separation rules, and personas in [`docs/pipeline/process-roles.md`](docs/pipeline/process-roles.md); **privilege is not independence**, and any decision whose reach extends beyond the deciding agent's own work unit requires a recorded decision (`TK-2`) even when the node carries no checkpoint. Every Feature breakdown must include exactly one integrating task, flagged `Integration review: mandatory`, as the Feature's review floor. Management (the current user or a registered authority) may waive that floor or override a `[u]` verdict only by an explicit, recorded authorization naming authority, scope, reason, and compensating controls — never an autonomous agent action.
- Merges only move work upward; their authority follows the architect's **integration checkpoints**, not the hierarchy level (see [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md)). A merge crossing no checkpoint is grunt-eligible (typically **Subtask→Task**, including parallel subtasks from different agents); a merge crossing a node marked `Integration review: mandatory`, and the `Feature→`main``/`DONE.md` closure, require the privileged *integrator*. In the linear case a grunt chains Task branches and a privileged agent integrates the last one at closure, reviewing any intermediate checkpoint as its boundary is crossed.
- Feature integration is where the privileged integrator merges the required work into the Feature branch, adds review findings and `Acceptance: ✓` records at each integration checkpoint, reconciles and removes the carried predecessor claim files, and — on approval, with every checkpoint passed — integrates the Feature into `main` and moves it to `DONE.md`. Unflagged work carries no acceptance record.
- If the integrator cannot approve the work at a checkpoint, it does not silently fix or force it through. It records a `[u]` **integration verdict** beneath that node (verdict author, authority reference, timestamp, rejected items, reason, integration-branch tip) and hands resolution to an explicit user interaction. It never clears its own `[u]` verdict without the user's decision; markers and acceptance records keep their own true state.

## Completing implementation work

1. Recompare the claimed Task and Feature with current `TODO.md`. Concurrent material drift or another owner's conflicting change is a blocker: do not overwrite it; record it and obtain resolution. An intrinsic, agentically determinable backlog defect is handled under **Autonomous backlog repair** and is not by itself a human blocker.
2. Validate the deliverables and disposition material findings under the capability-specific execution rules in `SANDBOX.md`.
3. Commit substantive deliverables with the configured user identity and a comprehensive Feature/Task message, using path-limited operations that preserve unrelated work. A sandboxed/grunt agent performs every Git-history mutation—including branch creation, merge, commit, tag, reset, rebase, and push—only through its active claim-bound runner request; direct Git execution is prohibited.
4. After the substantive commit hash is known and reachable, update authoritative implementation bookkeeping: mark `[x]` or `[w]`, add the required real `REF`, record validation/findings, and update implementation-start dependencies. Do not add acceptance credit.
5. For branch-based work, keep the implementation `TODO-<agent-id>.md` committed on the item's branch: it is carried upward by merges and is reconciled and removed by the privileged integrator during Feature integration (see [`docs/pipeline/branch-workflow.md`](docs/pipeline/branch-workflow.md)), not at `[x]`/`[w]`. In a non-branch legacy flow, reconcile and delete it only after its information is authoritative. Either way, finishing at `[x]`/`[w]` ends the agent's active ownership and write-scope lease and returns it to queue work; the persisted claim artifact is provenance, not a lingering lease, and acceptance waiting never keeps ownership active.
6. Commit implementation bookkeeping separately unless the capability-specific execution procedure in `SANDBOX.md` permits a safe transaction that creates both commits and injects the substantive hash into the bookkeeping commit. Never amend a commit to add its own hash.
7. If this session was separately and explicitly assigned as the privileged acceptance reviewer, complete the independent acceptance procedure and its separate evidence/bookkeeping commits. Otherwise stop at `[x]`/`[w]`; do not infer assignment.
8. Move a Feature to `DONE.md` only through the separately authorized aggregate-acceptance path described above; implementation terminality or a closure-eligible advisory is insufficient.
9. Verify final status and intended commit reachability, then immediately pick and start the next open, unclaimed, implementation-unlocked Task under the startup rules. Do not ask for confirmation merely because the next Task belongs to another Feature.

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

Further information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
