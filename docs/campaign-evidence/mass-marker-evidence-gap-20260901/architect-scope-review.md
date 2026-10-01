# Independent Architect scope review — Feature 0037 production-cutover recovery

- **Verdict:** **SUPPORT — scope only; the exact candidate is stale and MUST be reconstructed/rebound before integration or marker mutation.**
- **Review type:** independent pre-mutation cross-item gate-scope review; not Task Acceptance, integration review, cutover approval, signature, release authorization, or Feature closure.
- **Reviewer persona:** `Guinan`, independent Architect.
- **Dispatching identity:** `supervisor-zed-0037-cutover-20260901`.
- **Capability class:** `privileged` (direct execution permitted; this assignment grants only the bounded Architect review authority stated in the briefing).
- **Scope ID:** `0037-cutover-governance-review-20260901`.
- **Reviewed candidate:** `0d87882bd5a2df9c3b9a9eeec515fdfd09c77450`, parent `3834400c0275d8afeb79e530d4db4dbbbb28b9b4`.
- **Candidate changed paths:** `docs/campaign-evidence/mass-marker-evidence-gap-20260901/current-baseline-0037-marker-plan.md`; `docs/dossiers/dec-0044-034-mass-marker-evidence-correction.md`.
- **Review branch/worktree:** `0037-cutover-governance-review-20260901`; `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-review-20260901`.
- **Supervisor-observed main:** `5cfc814cb7d2249a128cd34082b938aa502b9ed4`.
- **Review observations of moving main:** `4e24dc1d2df66a49adf117474380f3d32ec9f2a6`, `4778393ae948a1317b54dc81cb7214ffba5aad7b`, `a4a7f857089185457a2740aed1888977a92f84c0`, and pinned observation `a163bf71f228c8e75657ef2f62a5bc370ca3e514`. A final pre-commit observation is recorded below.

## Decision

The proposed exact marker set is the smallest justified Feature `0037`
production-cutover recovery scope:

`0037-29`, `0037-30`, `0037-31`, `0037-32`, `0037-33`, `0037-34`,
`0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`,
`0037-36`, and `0037-40`.

Changing only those 13 markers from `[x]` to `[ ]` is supported in principle,
provided it is one atomic marker-only compare-and-swap transaction against a
freshly bound current `main`. `[ ]` means that terminal completion is not
established on the authoritative lineage; it does not deny or delete underlying
implementation fragments, accepted foundations, incident history, or prose
evidence.

The exact candidate `0d87882b...` is **not integration-ready** as a
current-baseline governance package:

1. Its pinned full `TODO.md` SHA-256
   `761c011a82e64102cf546635634541cd959c58a12e0d5788e4ae34ee7b7d30d8`
   matches candidate parent `3834400c...`, but does not match the
   Supervisor-observed `main@5cfc814c...` digest
   `d6e3edc54bde0d23804b604a95d22134e6dc740b91d9850ef9e70da94516545c`
   or pinned later `main@a163bf71...` digest
   `8294ce62ccc4238efa3cc5549597688f77e36cc7c7c230a5c0728e5762e54aa9`.
2. The original `DEC-0044-034` decision selects exactly 54 markers as one atomic
   correction and rejects partial correction. Its original affected-work-unit
   population does not include `0037-29` or `0037-30`. The candidate addendum
   therefore cannot accurately characterize the 13-marker tranche as merely a
   subset already contained in that original population: it both narrows the
   original atomic transaction and adds two separately introduced marker
   projections.
3. A free-form addendum authored by a decision preparer does not itself replace
   the append-only decision mechanism required by
   `docs/pipeline/decision-record.md` for a later materially different
   decision. Before mutation, an authorized decision record must bind the exact
   13-marker tranche, expressly supersede or otherwise disposition the original
   54-marker atomicity rule for this recovery, include `0037-29` and `0037-30`,
   and bind the then-current baseline and affected gates. This review supplies
   the distinct Architect scope position only; it does not make that decision.

Accordingly, **scope remains supported**, but the exact candidate must be
reconstructed/rebound before any integration intended to activate it or any
marker correction. Integrating it unchanged as a truthful "current-baseline"
package would preserve a known-stale digest and an unresolved decision-scope
contradiction.

## Scope and blast-radius findings

The exact cross-item reach of the 13-marker correction is:

- **Task-start gates:** `0037-30`, `0037-31`, `0037-32`, `0037-33`,
  `0037-34`, `0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`,
  `0037-35.02`, `0037-36`, and `0037-40`.
- **Completion/validation gates:** the criterion-bound shadow migration,
  quiescence/freeze, frozen migration candidate, pre-cutover audit, signed
  cutover decision, prepared authority tree and rollback package, authority
  switch, clean regeneration, rollback/event replay, post-cutover audit, and
  final activation/reference validations.
- **Mandatory integration checkpoints:** `0037-34.02` and `0037-40`.
- **Authority/external-effect gates:** the authority switch, issue/claim write
  freeze, write-freeze lift, rollback point-of-no-return, and actual source
  authority.
- **Acceptance and closure gates:** every future prerequisite-closed Acceptance
  batch that would consume these markers and Feature `0037` closure.

This is complete for the proposed Feature `0037` tranche. No other Task marker,
Task text, prerequisite, checkpoint attribute, Acceptance record, incident
summary, claim, selector, issue-store artifact, or authority record belongs in
the correction transaction.

The candidate plan names the operational categories and chain reach correctly,
but its durable decision binding is incomplete for `0037-29` and `0037-30` and
contradicts the original 54-marker no-partial-correction decision. That is a
binding defect, not a reason to widen the marker transaction.

## Drift recomputation

### Bound and observed digests

- Candidate parent `3834400c...`: `TODO.md` SHA-256
  `761c011a82e64102cf546635634541cd959c58a12e0d5788e4ae34ee7b7d30d8` —
  **matches the candidate's bound digest**.
- Supervisor-observed `main@5cfc814c...`: `TODO.md` SHA-256
  `d6e3edc54bde0d23804b604a95d22134e6dc740b91d9850ef9e70da94516545c` —
  **does not match**.
- Pinned review observation `main@a163bf71...`: `TODO.md` SHA-256
  `8294ce62ccc4238efa3cc5549597688f77e36cc7c7c230a5c0728e5762e54aa9` —
  **does not match**.

### Materiality of the observed drift

Against `3834400c...`, the relevant tracked-path drift through pinned
`main@a163bf71...` was confined to `TODO.md` and, within that file, to Feature
`0050` bookkeeping/decomposition (`0050-07`, new `0050-09`, and `0050-08`
prerequisite/order). The following remained unchanged for the Feature `0037`
recovery scope:

- all 13 exact Task blocks were byte-identical to the candidate parent;
- all 13 markers remained `[x]`;
- no subset Task had `Acceptance: ✓`;
- Task text, prerequisites, checkpoint attributes, incident summaries, and
  affected Feature `0037` gate contracts were unchanged;
- `DONE.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `docs/pipeline/**`,
  `issues/**`, and `agent-workflow.json` had no candidate-parent-to-pinned-main
  tracked change in the measured relevant path set.

Thus the observed drift does **not** change the supported 13-marker scope or its
blast radius. It does make the candidate's exact full-file CAS stale. The
correct response is reconstruction/rebinding, not ignoring the digest and not
loosening the CAS to an unreviewed partial-file edit.

## Operational-premise review

At pinned `main@a163bf71f228c8e75657ef2f62a5bc370ca3e514`:

- `agent-workflow.json` selected `authority_profile=legacy-lists`;
- `authority_epoch=legacy-writable` and `write_phase=legacy-writable`;
- `runner_protocol=runner-request@v1`;
- tracked canonical numeric issue paths below `issues/<numeric-id>/`: `0`;
- `issues/_views/catalog.json` items: `0`;
- refs below `refs/autodocs/cutover/0037`: `0`.

The production cutover premise is therefore **not established**. Prose
summaries, claims, `[x]` markers, tool availability, or shadow policy files do
not prove production activation. Production is cut over only when the exact
selector/authority state, real canonical issue items and generated views,
cutover/reference refs, signed/authorized lineage, and the actual authoritative
source all demonstrate the same transition. On the observed lineage they do
not.

The two cited summary commits were independently checked:
`3879067ee534099b7767db83d784239dd7ca7954` and
`424e62116b60e351f4b74da0a44fef0b75a7eb28` each add only a claim plus a prose
summary. Neither creates canonical items, catalog entries, cutover refs,
authority-switch commits, retained executions, or criterion-bound cutover
evidence.

Marker provenance also confirms that `0037-29` and `0037-30` came from separate
bulk-marker commits (`65e0d24c574...` and `67ae8a6f7c8...`), not from the
original `DEC-0044-034` 54-marker incident population. This reinforces the need
for explicit current decision binding rather than an asserted subset relation.

## Preservation of foundational work

The marker-only repair correctly preserves foundational Feature `0037` work:

- every currently accepted Feature `0037` Task/Subtask observed on the pinned
  lineage is outside the 13-marker set;
- none of the 13 target blocks carries current `Acceptance: ✓`;
- accepted foundations including `0037-03`, `0037-14`, `0037-49`, and the other
  accepted Feature `0037` nodes remain byte-for-byte and marker-for-marker
  untouched;
- non-target implementation-complete nodes are also untouched even where they
  do not yet carry Acceptance, because this review does not infer that their
  product is absent or reopen work beyond the production-cutover evidence gap.

Any implementation that changes an accepted or non-target marker, removes an
Acceptance record, rewrites a contract, or deletes underlying work exceeds the
supported scope and must abort.

## Fail-closed conditions

No integration intended to activate this governance preparation and no marker
mutation may proceed unless all of the following are true at one exact,
immutable current-main candidate:

1. A newly bound baseline records the exact `main` object and full `TODO.md`
   SHA-256 immediately before candidate creation.
2. All 13 exact Task blocks remain byte-identical to the reviewed blocks and
   all 13 expected old markers remain `[x]`.
3. A conforming, authorized append-only decision explicitly governs this exact
   13-marker transaction, includes `0037-29` and `0037-30`, and resolves the
   conflict with the original exact-54/no-partial-correction decision.
4. The decision and this distinct Architect review are ancestors of the exact
   correction candidate as required by the active DAG/integration policy.
5. Selector, authority epoch/write phase, canonical issue items, catalog/views,
   cutover refs, signatures, transaction evidence, and actual source authority
   are remeasured from the same pinned object; any evidence of a real cutover or
   legitimate terminal evidence for a target requires renewed analysis.
6. The resulting diff is exactly 13 `[x]` to `[ ]` marker pairs in `TODO.md` and
   no other byte changes.
7. Task text, prerequisites, checkpoints, Acceptance history, incident
   summaries, foundational work, claims, selector/config, `issues/**`, and all
   non-target markers are unchanged.
8. Required integration authority, hygiene, ancestry, review, and commit
   provenance checks pass against that exact candidate. This scope review is
   not a substitute for any of them.

Any mismatch is a no-write stop. Do not manually finish a partial correction,
do not compensate with extra markers, do not reset history, and do not restore
`[x]` merely to unblock scheduling. Retry only by rebuilding from a newly pinned
baseline and renewing any decision/review whose reach or evidence changed.

## Methods and validation

Read-only methods used from the repository root or the owned review worktree:

- `git rev-parse`, `git worktree list --porcelain`, `git status --short`;
- `git show`, `git diff-tree`, `git diff`, `git log -S`, `git blame`;
- `git merge-base --is-ancestor`, `git ls-tree`, `git for-each-ref`;
- SHA-256 computation of `TODO.md` at exact Git objects;
- deterministic Python extraction/comparison of the 13 complete Task blocks,
  their markers, and Acceptance presence;
- deterministic inspection of `agent-workflow.json`, canonical numeric issue
  paths, `issues/_views/catalog.json`, and cutover refs;
- review of `SANDBOX.md`, `PRIVILEGED.md`, `AGENTS.md`,
  `docs/pipeline/decision-record.md`, candidate `0d87882b...`, and prior
  independent review `68e9e71fa`.

No network, credential, external service, mutation of production state, Task
Acceptance procedure, integration, signature, issue-store cutover, or cutover
reference creation was used. The review validates scope and fail-closed
preconditions only.

## Context supplied and not supplied

Supplied by the Supervisor: the exact candidate and parent, Supervisor-observed
main, exact 13-marker proposal, audit conclusion that production had no real
canonical items/catalog/cutover refs and remained legacy-authoritative, the
bounded branch/worktree/write scope, management direction, the requirement for
an independent Architect persona, and explicit prohibitions on mutation,
Acceptance, integration, publication, signing, and Feature closure.

Not supplied: a desired verdict, hidden implementation patch, acceptance
conclusion, complete private/external evidence, credentials, signatures,
cutover authorization, authority to mutate outside this review file, or
permission to reconcile the stale baseline by changing the candidate governance
files. Repository evidence and local refs were reviewed independently; absence
of committed authoritative evidence is not a claim that no uncommitted or
external fragment exists.

## Verbatim briefing and material prompts

```text
SUPERVISOR ASSIGNMENT — independent Architect scope review for the Feature 0037 production cutover recovery.

Supervisor/dispatching identity: `supervisor-zed-0037-cutover-20260901`.
Reviewer persona to assume explicitly: `Guinan`, independent Architect. This persona is distinct from the Supervisor and from the preparer of candidate `0d87882bd5a2df9c3b9a9eeec515fdfd09c77450`.
Capability class: `privileged`.
Item/scope ID: `0037-cutover-governance-review-20260901` (assignment-scoped recovery work; do not create a new TODO Task).
Branch: `0037-cutover-governance-review-20260901`.
Owned worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-review-20260901`.
Exact review target: `0d87882bd5a2df9c3b9a9eeec515fdfd09c77450` (`docs(DEC-0044-034): bind current Feature 0037 marker recovery`), parent `3834400c0275d8afeb79e530d4db4dbbbb28b9b4`.
Current main observed by Supervisor immediately before dispatch: `5cfc814cb7d2249a128cd34082b938aa502b9ed4`.
Sole permitted write path: `docs/campaign-evidence/mass-marker-evidence-gap-20260901/architect-scope-review.md`.
Read scope: candidate `0d87882b…`, its two changed files, current `main`, `TODO.md`, `DONE.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `docs/pipeline/**`, and relevant existing Feature 0037 evidence/tool state as needed.

Goal:
1. Independently review the exact current-baseline addendum and plan carried by `0d87882b…` for the proposed exact 13-marker correction:
   `0037-29`, `0037-30`, `0037-31`, `0037-32`, `0037-33`, `0037-34`, `0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`, `0037-36`, `0037-40`.
2. Determine whether the proposed `[x]` → `[ ]` marker-only CAS correction is the smallest justified gate-scope repair, whether the cross-item blast radius is fully named, and whether foundational accepted work is correctly preserved.
3. Recompute drift against current `main@5cfc814c…` (and re-read current main immediately before committing). Explicitly report whether the candidate’s bound `TODO.md` digest `761c011a82e64102cf546635634541cd959c58a12e0d5788e4ae34ee7b7d30d8` still matches current `main`, and whether any Task text, prerequisite, checkpoint, Acceptance, incident summary, selector, issue-store state, or affected gate has materially changed.
4. Review the operational premise: production is not cut over unless the selector/authority state, real canonical issue items/views, cutover refs, and actual source authority show it; prose summaries and `[x]` markers are not evidence.
5. Produce a clear verdict: SUPPORT, REJECT, or INCONCLUSIVE. If drift requires reconstruction, distinguish “scope remains supported” from “the exact candidate is stale and must be reconstructed/rebound before integration.” State precise fail-closed conditions.
6. Record in the review: distinct reviewer persona, dispatching identity, this verbatim briefing, what context was and was not provided, exact reviewed candidate and current-main observations, methods/commands, findings, and review boundaries.
7. Commit the sole review file on the named branch with complete check-in provenance and `Task-ID`/`Base-Ref` trailers. Return exact branch, commit SHA, parent/base, changed paths, verdict, drift result, validation results, and whether the worktree is clean.

Required branch/worktree mechanics:
- Never mutate the shared root checkout `/Users/tobias.anton/devel/autodocs`.
- Create/use only the named owned worktree.
- Base the review branch so the review commit carries the exact candidate being reviewed (normally branch from `0d87882b…`), while separately measuring current `main` drift.
- Preserve all unrelated work. Use path-limited staging/commit.
- Before consequential actions, use the agent inbox tools available to you as required by repository policy.

You MUST NOT:
- edit `TODO.md`, `DONE.md`, either candidate governance file, selector/config, `issues/**`, claims, schemas, tools, tests, or any path except the sole review file;
- create a new TODO Task;
- change markers or Acceptance records;
- implement the issue-store cutover;
- cross an integration checkpoint, merge/cherry-pick/rebase into `main`, advance `main`, push, publish, sign a cutover ref, or move Feature 0037 to `DONE.md`;
- treat this scope review as Task Acceptance, integration review, or cutover authorization.

Management/user authorization context (verbatim material prompt):
> Dann nimm es jetzt in Betrieb. Eine gute Gelegenheit, die fälschlicherweise nicht ge[x]ten Tasks loszuwerden. Du kriegst von mir dafür alle nötigen Management-Freigaben. Steuere alles ein über Assignments, die du als supervisor verschickst. Keine neuen TODO-Tasks erstellen während des übergangs, sonst bremsen wir uns nur wieder selber aus.

Immediate continuation prompt:
> go ahead

Context supplied by Supervisor: production audit found no real canonical issue items, empty catalog, legacy-writable/legacy-lists authority, no cutover refs, and identified the exact 13 unsupported Feature 0037 markers above. Candidate `0d87882b…` is a governance preparation only. Current `main` has advanced since its parent. Context not supplied: no answer or desired verdict, no hidden implementation patch, no acceptance conclusion, and no authorization to mutate beyond the sole review file.
```

## Review boundary

This record supports only the architectural scope and the stated fail-closed
controls. It grants no Task or Feature Acceptance, checkpoint verdict,
integration authority, cutover authorization, signature, publication, external
effect, marker mutation, issue-store activation, write-freeze lift, or Feature
closure. The review commit remains off `main` until a separately authorized
Integrator decides its ancestry and integration handling.

## Final pre-commit observation

Immediately before staging and committing this review, `refs/heads/main` was
re-read as `151349b6d4eb223304ffad0be94b1d6bbb661364` and every measurement in this paragraph was made against
that immutable object. Its `TODO.md` SHA-256 was
`8294ce62ccc4238efa3cc5549597688f77e36cc7c7c230a5c0728e5762e54aa9` (not the candidate-bound digest); all 13
reviewed Task blocks were byte-identical to `3834400c...`: `true`;
all 13 expected old markers were `[x]`: `true`. The selector
remained `legacy-lists` / `legacy-writable` /
`legacy-writable` / `runner-request@v1`; canonical
numeric issue paths: `0`; catalog items: `0`; cutover refs:
`0`. Before staging, the review worktree contained only the untracked
authorized review path. The staged-path and diff checks below were required to
pass before the carrying commit.

---

# Exact-candidate follow-up — reconstructed Feature 0037 recovery governance

- **Follow-up verdict:** **SUPPORT** for exact candidate `419a924226f48af14f5c22e6665dc05be8e9fa14` as the governance/review ancestor of a later separately prepared marker-only transaction.
- **Reviewer persona:** `Guinan`, independent Architect, continuing the prior review lineage.
- **Dispatching identity:** `supervisor-zed-0037-cutover-20260901`.
- **Capability class:** `privileged`.
- **Review type:** exact-candidate cross-item gate-scope follow-up; not Task Acceptance, integration review, cutover approval, signature, publication, marker mutation, or Feature closure.
- **Reviewed candidate:** `419a924226f48af14f5c22e6665dc05be8e9fa14` on reconstruction branch `0037-cutover-governance-rebind-20260901`.
- **Candidate topology:** merge commit with first parent/current-main base `374926174a09af1d0d3d33255a8b08993ff71dfc` and second parent/prior-review lineage `24262277f03f8d36333902fed4b6b25042028402`.
- **Follow-up branch/worktree:** `0037-cutover-governance-followup-review-20260901`; `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-followup-review-20260901`.

## Follow-up decision

Candidate `419a9242...` satisfies the architectural pre-mutation governance
requirements from the prior review. It genuinely joins the exact current-main
baseline and the independent prior-review lineage, changes exactly the three
reported governance/evidence paths from its first parent, and performs no
`TODO.md`, marker, Acceptance, selector, authority, issue-store, checkpoint,
integration, ref, or Feature-closure mutation.

`DEC-0044-035` resolves the prior blocking defect:

1. It is a separately identified `decision-record@v1` Management disposition,
   appended after the preserved original `DEC-0044-034` record.
2. `authority:repository-owner:autodocs` is the deciding Management identity.
   The authority-reference field explicitly limits Data to Governance Decision
   Recorder and Implementer and denies Data the deciding, Architect-review,
   integration, acceptance-review, and cutover-signing roles.
3. It binds first parent `374926174a09af1d0d3d33255a8b08993ff71dfc`
   and full `TODO.md` SHA-256
   `eea63e0ec7e2ca78d90a5ea1e9d477f805da5c5d186acfb97d0aa35fa5f73a42`.
4. It creates exactly one independent 13-marker transaction, explicitly names
   `0037-29` and `0037-30` as outside the original 54-marker population, and
   identifies the other 11 as the relevant Feature `0037` members.
5. It supersedes the old exact-54/no-partial atomicity rule only to authorize
   this exact-13 transaction. It expressly makes no truth, retention,
   reopening, repair, credit, or later-disposition decision for the remaining
   original markers.
6. It requires exact `[x]` to `[ ]` header-marker-only CAS, exact base and
   full-file digest, complete-block equality, zero target Acceptance, unchanged
   authority/item/catalog/ref premises, genuine decision/review ancestry, and a
   no-write stop on any mismatch.
7. It fully names the 13 work units, 12 affected successor Task-start gates,
   criterion-bound validations, prerequisite-closed Acceptance, mandatory
   checkpoints `0037-34.02` and `0037-40`, authority/write-freeze/source gates,
   release activation, and Feature `0037` closure.
8. It preserves Task text, prerequisites, checkpoints/verdicts, Acceptance
   history, accepted foundations, incident summaries, claims, selectors,
   issues, integration/closure state, and all unrelated markers.

The record’s field order/cardinality, timestamp, registered-authority identity,
Management role, alternatives (one selected and three rejected), consequences,
work-unit/gate references, review participation, and `Waiver: none` conform to
the checked `decision-record@v1` structure. Its
`authority-tailoring-or-waiver` trigger is read narrowly as Management’s
explicit override of the prior decision’s transaction-authorization constraint;
it is not a role, independence, credential, signing, Acceptance, or integration
waiver. The record itself confirms `Waiver: none` and preserves those authority
boundaries. This review grants no broader interpretation.

## Exact plan and preservation findings

The current-baseline plan contains exactly 13 fenced complete Task blocks. A
deterministic extraction using the next Task or Feature heading as the block
boundary proved every block byte-identical to `TODO.md` at `37492617...`:

`0037-29`, `0037-30`, `0037-31`, `0037-32`, `0037-33`, `0037-34`,
`0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`,
`0037-36`, and `0037-40`.

All 13 begin with exact `[x]`; none contains current `Acceptance: ✓`. The
candidate’s `TODO.md` is byte-identical to its first parent and has the bound
SHA-256. The candidate preserves all 38 current accepted Feature `0037`
Task/Subtask blocks observed on the base; none is a target. Accepted foundations
including `0037-03`, `0037-14`, `0037-49`, and every other accepted Feature
`0037` node remain unchanged.

At the exact base:

- selector schema/profile: `agent-workflow-bootstrap@v1` / `legacy-lists`;
- authority epoch/write phase: `legacy-writable` / `legacy-writable`;
- runner protocol: `runner-request@v1`;
- tracked canonical numeric issue paths: `0`;
- catalog items: `0`;
- refs below `refs/autodocs/cutover/0037`: `0`.

These facts independently confirm that the authoritative source remains the
legacy lists and that prose summaries or `[x]` markers are not production
cutover evidence.

## Ancestry, changed paths, and prohibited-state verification

Both ancestry checks returned success:

- `374926174a09af1d0d3d33255a8b08993ff71dfc` is candidate parent 1 and an
  ancestor of `419a9242...`;
- `24262277f03f8d36333902fed4b6b25042028402` is candidate parent 2 and an
  ancestor of `419a9242...`.

Exactly three paths differ from parent 1:

- `docs/campaign-evidence/mass-marker-evidence-gap-20260901/architect-scope-review.md`;
- `docs/campaign-evidence/mass-marker-evidence-gap-20260901/current-baseline-0037-marker-plan.md`;
- `docs/dossiers/dec-0044-034-mass-marker-evidence-correction.md`.

A path-restricted diff found no change to `TODO.md`, `DONE.md`, `AGENTS.md`,
`SANDBOX.md`, `PRIVILEGED.md`, `agent-workflow.json`, `issues/**`, or
`docs/pipeline/**`. `DEC-0044-035` was absent from the first parent and occurs
as one decision heading in the candidate dossier; other candidate mentions are
references from the plan.

## Live-main drift

Initial follow-up measurement found live `main` exactly equal to the candidate
base `374926174a09af1d0d3d33255a8b08993ff71dfc`, with matching `TODO.md`
digest, byte-identical target blocks, all target markers `[x]`, zero target
Acceptance, unchanged legacy authority projection, zero canonical numeric issue
paths, zero catalog items, and zero cutover refs. No initial drift was present.

The mandatory final live-main re-read immediately before the follow-up carrying
commit is recorded below. SUPPORT remains valid only if any later drift is
unrelated and leaves every target block/marker/Acceptance, authority selector,
canonical issue/catalog/ref state, governing decision, and affected gate
unchanged. Full-file `TODO.md` drift still invalidates the candidate’s exact CAS
binding even when architecturally unrelated: in that case the scope remains
supported but marker mutation requires a freshly rebound transaction package.

## Fail-closed boundary

This SUPPORT verdict authorizes no marker write or integration. A later marker
candidate must stop without writing unless it descends from the exact Management
disposition, candidate `419a9242...`, this follow-up review, and the integration
base; matches a freshly applicable full-file `TODO.md` digest; contains exactly
13 `[x]` to `[ ]` header-marker replacements and no other byte change; and
reproves complete-block equality, zero target Acceptance, unchanged target
contracts/gates, legacy authority/item/catalog/ref premises, and required
independent integration authority.

Any target-block, marker, Acceptance, selector/authority, canonical issue,
catalog, cutover-ref, governing-decision, affected-gate, or ancestry drift
invalidates this exact-candidate support for integration. Harmless unrelated
drift may leave the architectural scope supported, but it never waives the
full-file CAS: reconstruction/rebinding and renewed exact-candidate review are
required before mutation. No partial completion, manual compensation, history
rewrite, added marker, restored `[x]`, or self-integration is permitted.

## Follow-up methods and validation

Read-only verification used `git show`, `git diff`, `git diff-tree`, `git log`,
`git grep`, `git rev-parse`, `git merge-base --is-ancestor`, `git ls-tree`,
`git for-each-ref`, SHA-256 calculation, and deterministic Python parsing of
the decision fields/lists and exact Task blocks. `git diff --check` passed for
the candidate delta. The candidate commit carries `Task-ID` and `Base-Ref`
trailers and a tracked verbatim provenance receipt. No test suite was required
because the candidate changes governance/evidence prose only; behavioral
validation consisted of exact-tree, exact-block, exact-digest, structural, and
operational-state checks.

## Follow-up briefing — verbatim

```text
Follow-up Architect review assignment. Review the exact reconstructed candidate `419a924226f48af14f5c22e6665dc05be8e9fa14` on branch `0037-cutover-governance-rebind-20260901`.

Remain persona `Guinan`, independent Architect, capability class `privileged`, under the same bounded scope and prohibitions as the prior assignment. Supervisor identity remains `supervisor-zed-0037-cutover-20260901`. This is assignment-scoped recovery; create no TODO Task.

Candidate facts reported by the recorder, which you must verify independently:
- first parent/current-main base: `374926174a09af1d0d3d33255a8b08993ff71dfc`;
- second-parent review lineage: `24262277f03f8d36333902fed4b6b25042028402`;
- bound `TODO.md` digest: `eea63e0ec7e2ca78d90a5ea1e9d477f805da5c5d186acfb97d0aa35fa5f73a42`;
- exactly three paths changed from first parent;
- stale preparer addendum replaced with conforming append-only Management disposition `DEC-0044-035` in the existing decision dossier;
- the disposition explicitly creates the independent exact-13 transaction, includes `0037-29` and `0037-30`, and supersedes original DEC-0044-034 exact-54/no-partial atomicity only as needed for this 13-marker recovery;
- no `TODO.md`, marker, selector, issue item, Acceptance or authority mutation.

Task:
1. Independently inspect the exact candidate and both parents.
2. Verify `DEC-0044-035` conforms to `decision-record@v1`, faithfully records Management authority rather than assigning it to the recorder, resolves the old 54-vs-13 conflict, does not silently adjudicate the remaining old markers, binds the exact base/digest, and completely names the 13-item blast radius and fail-closed semantics.
3. Verify the current-baseline plan is byte-accurate for all 13 complete Task blocks at base `37492617…`, all are `[x]`, none has current Acceptance, foundational accepted work is preserved, and selector/item/catalog/cutover-ref facts are accurate.
4. Verify genuine ancestry of both the current-main base and your prior review commit.
5. Re-read live current `main` immediately before your follow-up commit. Distinguish harmless unrelated drift from material invalidation. If the candidate baseline has already drifted in any target block, target marker, target Acceptance, selector/authority/canonical issue state, governing decision, or affected gate, return INCONCLUSIVE/REJECT as appropriate and do not bless integration.
6. Append (do not rewrite) a clearly labeled exact-candidate follow-up section to your existing file only: `docs/campaign-evidence/mass-marker-evidence-gap-20260901/architect-scope-review.md`. Record exact candidate, methods, findings, live-main drift, verdict SUPPORT/REJECT/INCONCLUSIVE, fail-closed boundary, and this follow-up briefing verbatim.
7. Commit that sole-path append on the existing review/rebind lineage. You may create a follow-up branch/worktree if needed, but do not alter the reconstruction branch destructively. Return exact branch/tip/base, changed path, verdict, live-main observation, validation, ancestry, and clean status.

You MUST NOT edit any other path, `TODO.md`, markers, Acceptance, selectors, issues, decision/plan files, claims, tools, tests, schemas, main, or refs; must not integrate, push, publish, cut over, sign, accept, or close Feature 0037. This remains Architect scope review, not integration review or Task Acceptance.

Management prompt remains verbatim:
> Dann nimm es jetzt in Betrieb. Eine gute Gelegenheit, die fälschlicherweise nicht ge[x]ten Tasks loszuwerden. Du kriegst von mir dafür alle nötigen Management-Freigaben. Steuere alles ein über Assignments, die du als supervisor verschickst. Keine neuen TODO-Tasks erstellen während des übergangs, sonst bremsen wir uns nur wieder selber aus.

Immediate continuation prompt:
> go ahead
```

## Final follow-up pre-commit observation

Immediately before path-limited staging and commit, live `main` was re-read as
`374926174a09af1d0d3d33255a8b08993ff71dfc` and exactly matched the candidate base. Its `TODO.md` SHA-256 was
`eea63e0ec7e2ca78d90a5ea1e9d477f805da5c5d186acfb97d0aa35fa5f73a42`. Target blocks equaled the bound base:
`true`; all target markers were `[x]`:
`true`; target Acceptance count remained zero:
`true`. Selector/authority state equaled the bound
base: `true`
(`legacy-lists` / `legacy-writable` /
`legacy-writable` / `runner-request@v1`); canonical numeric issue
paths: `0`; catalog items: `0`; cutover refs: `0`.
Relevant base-to-live-main changed paths: `none`. No material invalidation
was present. Before staging, the follow-up worktree differed from candidate
`419a9242...` only by this append to the authorized review file.
