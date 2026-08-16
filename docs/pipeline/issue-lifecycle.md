# Issue Lifecycle — states, authority, evidence, decisions, and terminal records

**Status:** Draft, review-ready (Task `0037-03.01`, Feature `0037`). Until the authorized Feature-0037 cutover, committed `TODO.md`, `DONE.md`, and active `TODO-<agent-id>.md` claims remain authoritative; `issues/` is shadow data only.

## Scope

This contract defines lifecycle semantics for canonical issue items. It complements the canonical paths in `docs/pipeline/issue-store.md`, the YAML profile in `docs/pipeline/issue-yaml-profile.md`, and the `issue-item@v1` normalized-object schema. It does not define cross-worktree acquisition or recovery; that is Task `0037-03.02`.

## Legacy marker mapping

| Legacy marker | Canonical state | Meaning | Who may transition it |
|---|---|---|---|
| `[ ]` | `open` | Work has not started, or is ready to resume without an active claim | Authorized planner or eligible agent
| `[p]` | `in_progress` | Active work is claimed or implementation/investigation has begun | Claim owner; authorized recovery actor
| `[?]` | `open` with `investigation_required` decision | Material facts are unknown but are agentically investigable | Agent/reviewer
| `[u]` | `blocked` | The *next* unresolved action requires a named human decision, authority, credential, approval, signature, or policy/scope choice | Authorized human authority, after agent records the escalation
| `[w]` | `closed` with terminal disposition `wontfix` | Investigated and closed without implementation because invalid, non-reproducible, superseded, or not worth pursuing | Authorized closer, with evidence and a real commit REF
| `[x]` | `closed` with terminal disposition `completed` | Deliverable, validation/review evidence, and closure record are committed | Authorized closer, with evidence and a real commit REF

`[u]` MUST NOT be used for technical difficulty, test/command failure, an open parent, a repairable planning defect, an actionable dependency cycle, tool-budget exhaustion, or a runner request awaiting result. The issue must return to `in_progress` as soon as the named human decision is recorded.

## Transitions

| From | To | Preconditions | Authority |
|---|---|---|---|
| `open` | `in_progress` | Start prerequisites terminal; active claim created | Claiming agent or planner
| `open`/`in_progress` | `blocked` | Exact human question, options, recommendation, evidence, required authority, and unblocked work recorded | Claim owner; human owns resolution
| `blocked` | `in_progress` | Required decision/approval/credential is recorded and any conditions are satisfied | Claim owner or authorized handoff actor
| `open`/`in_progress` | `closed:completed` | All applicable criteria checked; reachable evidence; validation/review result; terminal `closure.json`; real reachable commit references | Authorized closer
| `open`/`in_progress` | `closed:wontfix` | Investigation evidence, explicit reason, terminal `closure.json`, and real reachable disposition commit | Authorized closer
| `open`/`in_progress` | `closed:superseded`/`duplicate`/`cancelled` | Terminal decision names successor/duplicate where applicable, authority, rationale, and retained history | Named decision authority
| any nonterminal | `open` | Claim released/expired or triage reopens; history retained | Authorized planner/recovery actor

A Feature may close only after each required child is terminal and after its own closure evidence is complete. A terminal item is immutable except for additive correction history that preserves the original terminal record and is authorized by an explicit decision.

## Authority matrix

| Action | Required authority | Required evidence |
|---|---|---|
| Create/renew active work | Claim owner within declared scope | Claim identity, base commit, scope, time, owner token
| Mark unknown `[?]` | Agent or reviewer | Investigation question and next probe
| Escalate `[u]` | Claim owner, then named human authority | Sentinel/decision record with question, options, recommendation, impact
| Complete `[x]` | Authorized closer | Checked `AC-NNN` criteria, validation/review outputs, closure record, real commit refs
| Wontfix `[w]` | Authorized closer | Reason, investigation evidence, closure record, real disposition commit
| Supersede/duplicate/cancel | Named decision authority | Decision record, rationale, retained relation/target
| Archive without acceptance | Named archival authority | Terminal record marking `archived-not-accepted`; no success/acceptance credit

## Criterion evidence and closure

Completion requires an item-local `closure.json` conforming to `issues/_schema/issue-closure-v1.schema.json`. Every checked `AC-NNN` criterion MUST include a reachable evidence locator: a committed repository path plus line/range or immutable artifact digest, a real reachable Git commit, or a durable external record allowed by policy. Placeholders such as `pending`, `local-*`, uncommitted shell output, or nonexistent paths do not satisfy closure evidence.

A closure must state the terminal disposition, closer identity, timestamp, item identifier, criterion evidence, validation results, commit references, and any decision reference. `completed` and `wontfix` are distinct terminal outcomes; neither superseded, duplicate, cancelled, nor archived-not-accepted may be displayed as completion.

Real commit references use full Git object IDs reachable from the review baseline. The closer follows the two-commit rule: first commit the substantive deliverable and validation artifacts, then commit the lifecycle/bookkeeping update carrying that first commit's REF. A later correction is a new additive history record, never an overwrite of the first closure assertion.

## Decisions and historical integrity

Material architecture, scope, approval, supersession, duplicate, cancellation, archival, or escalation decisions are immutable decision records conforming to `issues/_schema/issue-decision-v1.schema.json`. A decision identifies its authority, status, alternatives where applicable, rationale, date, linked item, and evidence. It may resolve a blocked issue but cannot fabricate acceptance or validation evidence.

Feature `0021` remains **archived-not-accepted**. Its historical records are retained for traceability, but it receives no completion/acceptance credit; specifically, local placeholders `local-20260815-0021-06` through `local-20260815-0021-08` are not valid evidence.

## Fixture expectations

`issues/_schema/fixtures/issue-lifecycle/` contains valid completed and wontfix closures, valid decisions, and invalid examples for missing criterion evidence, placeholder refs, invalid dispositions, invalid decision authority, and missing required decision fields. Validation first checks JSON Schema and then applies repository-level reachability/path checks that JSON Schema cannot express.
# Claim and Recovery Protocol

This section governs active ownership of Git-native issue items. It supplements the lifecycle rules above; it is not the Feature-0006 typed-claim or curation workflow contract.

## Claim record

An active item claim is stored at the canonical item-local `claim.json` path and validates against `issues/_schema/issue-claim-v1.schema.json`. It binds one item to one owner identity, clone/worktree identity, exact base commit, declared write scopes, issuance/expiry timestamps, a lease nonce, and a digest of the compare-and-swap (CAS) ref payload. Claim records are append-only evidence: release, expiry, handoff, takeover, and integration rejection are recorded as events; they never erase an earlier owner’s record.

A claim permits work only within its declared repository-relative scopes. It is not completion evidence and cannot make generated output authoritative.

## Same-clone acquisition

Within a clone, claim acquisition uses the local ref `refs/autodocs/claims/<item-id>` as the serialization point. The claimant reads the current ref, validates the candidate claim, writes the claim object, computes its SHA-256 digest, and atomically updates the ref only if its expected old value still matches:

```text
old = git rev-parse -q --verify refs/autodocs/claims/<item-id> || zero
assert candidate.base_commit == HEAD
assert candidate not expired
assert no active local claim overlaps candidate.write_scopes
write canonical claim.json candidate
new = sha256(canonical-json(candidate))
git update-ref refs/autodocs/claims/<item-id> new old
if update-ref failed: re-read ref and candidate state; do not overwrite
```

The object named by the ref is the canonical claim payload/digest representation selected by the claim tooling. An update failure means another local contender won; the loser must re-fetch/re-read and either choose a disjoint item/scope or await release/expiry. No time-of-check/time-of-use assumption may substitute for the CAS operation.

## Independent clones and integration

Independent clones cannot use a local ref as a shared mutex. A claimant first fetches the protected integration branch, rechecks item state, prerequisite state, active integrated claims, and overlapping scopes, then promptly integrates its `claim.json` plus claim-ref update to that protected branch. The integration service/reviewer rejects a candidate when any of these are true:

- Its `base_commit` is stale relative to the protected branch policy.
- An unexpired integrated claim exists for the same item.
- An unexpired claim has the same or overlapping declared write scope.
- A competing claim from another clone is unmerged or cannot be ordered without an authority decision.
- Its CAS-ref digest does not match canonical claim bytes or its claimed ref transition.

After integration, every clone must fetch/recheck before performing an irreversible operation or publishing a new request. Two disconnected clones may each obtain a locally valid claim before either integrates; Git alone provides no repository-only guarantee of pre-merge exclusivity. The protected integration rule detects and serializes the conflict when connectivity returns.

## State table

| State | Meaning | Permitted next action |
|---|---|---|
| `proposed` | Candidate claim not yet acquired/integrated | Validate and CAS acquire, or abandon |
| `active` | Unexpired claim acquired and integrated | Work, renew, hand off, or release |
| `renewing` | Owner is extending expiry with same nonce/scope | CAS update after fetch/recheck |
| `released` | Owner explicitly relinquished lease | New claimant may acquire after recheck |
| `expired` | Expiry time passed; no work may continue | Record release or authority-approved takeover |
| `takeover-pending` | Expired claim awaits named authority decision | No new owner work until decision recorded |
| `superseded` | Handoff/takeover accepted; prior record retained | New claim references predecessor |
| `rejected` | Integration or CAS validation failed | Re-fetch/recheck and resolve conflict |

## Renewal, handoff, expiry, and takeover

Renewal retains item, owner, clone/worktree identity, base policy, and lease nonce; it updates only allowed temporal/audit fields through CAS after fetch/recheck. Handoff creates a new claim linked to the predecessor and requires explicit release by the prior owner or an authority decision. A crash is not implicit release: once expiry passes, the item enters `expired` and blocks new work until an explicit release event or an authority-approved takeover is integrated. Takeover never deletes the expired claim or its evidence.

When the remote/protected branch is unavailable, an owner may perform only reversible local investigation within its existing unexpired scope. It MUST NOT claim global exclusivity, start a conflicting irreversible mutation, renew against unavailable integration state, or treat a local ref as cross-clone proof. On recovery it fetches/rechecks and submits the pending claim/release/handoff decision for integration.

## Merge-time rules and race fixtures

Merge-time validation checks JSON Schema, canonical-path identity, base freshness, expiry, nonce continuity, exact CAS digest, same-item uniqueness, and overlap of active write scopes. It rejects stale bases, duplicate claims, overlapping scopes, malformed releases, and competing unmerged claims. Repository-level validation also verifies that `base_commit` is reachable and timestamps satisfy `issued_at < expires_at`; JSON Schema alone cannot prove these conditions.

Fixtures under `issues/_schema/fixtures/issue-claim/` cover two worktrees contending for one item, two clones with protected-branch integration, expiry and authority-approved takeover, stale base rejection, overlapping scope rejection, and failed CAS/integration. They are contract fixtures; they do not promise that a disconnected repository can prevent a conflict before merge.
