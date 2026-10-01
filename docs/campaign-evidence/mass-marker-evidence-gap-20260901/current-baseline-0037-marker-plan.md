# Current-baseline Feature 0037 marker correction plan

This is a preparation and evidence artifact only. It changes no marker, Task
contract, prerequisite, checkpoint, Acceptance record, selector, issue item,
cutover ref, or integration state, and it grants no review, signature,
Acceptance, integration, or Feature-closure authority.

## Pinned baseline

- Branch creation base and inspected `main`: `374926174a09af1d0d3d33255a8b08993ff71dfc`.
- `TODO.md` SHA-256: `eea63e0ec7e2ca78d90a5ea1e9d477f805da5c5d186acfb97d0aa35fa5f73a42`.
- Selector: schema `agent-workflow-bootstrap@v1`, authority profile
  `legacy-lists`, authority epoch/write phase
  `legacy-writable`/`legacy-writable`, runner protocol
  `runner-request@v1`.
- Tracked canonical numeric issue files below `issues/<numeric-id>/`: `0`.
- Generated catalog `issues/_views/catalog.json`: `items: []` (`0` items).
- Refs below `refs/autodocs/cutover/0037/`: `0`.
- These facts and every complete target block below were freshly extracted from
  the same immutable object. Inventory: exactly `13`; expected markers `[x]`:
  `13`; target blocks with current `Acceptance: ✓`: `0`.
- `3879067ee534099b7767db83d784239dd7ca7954` adds only
  `TODO-worf-misc-chain-18-20260830.md` and
  `docs/campaign-evidence/0037-34/authority-cutover-and-lifecycle-summary.md`.
- `424e62116b60e351f4b74da0a44fef0b75a7eb28` adds only
  `TODO-worf-misc-chain-21-20260830.md` and
  `docs/campaign-evidence/0037-post-cutover/post-cutover-verification-and-activation-summary.md`.
  These are prose-only commits for the relevant Feature 0037 claims; they do
  not create canonical issue items, catalog entries, cutover refs, signed
  approvals, authority-switch commits, retained execution reports, or
  criterion-bound completion evidence for the markers below.

## Management direction and boundary

Verbatim user direction:

> Dann nimm es jetzt in Betrieb. Eine gute Gelegenheit, die fälschlicherweise nicht ge[x]ten Tasks loszuwerden. Du kriegst von mir dafür alle nötigen Management-Freigaben. Steuere alles ein über Assignments, die du als supervisor verschickst. Keine neuen TODO-Tasks erstellen während des übergangs, sonst bremsen wir uns nur wieder selber aus.

This direction authorizes the recovery program and assignment-based
coordination without creating new `TODO.md` Tasks. Its exact current-baseline
Management disposition is recorded as append-only `DEC-0044-035` in
`docs/dossiers/dec-0044-034-mass-marker-evidence-correction.md`. The distinct
scope review at `24262277f03f8d36333902fed4b6b25042028402` supports the exact
13-marker reach but expressly finds stale candidate
`0d87882bd5a2df9c3b9a9eeec515fdfd09c77450` non-integration-ready and requires
this reconstruction/rebinding. Before marker mutation, the Supervisor must
obtain a follow-up independent review of the exact reconstructed candidate;
only the separately assigned Integrator may then decide integration. This
Implementer plan is not Architect review, Task Acceptance, integration review,
a cutover signature, or a Feature-closure artifact.

## Exact correction unit and CAS

A later separately authorized mutation may change **only** these 13 marker
pairs, atomically, from exact `[x]` to exact `[ ]`:

`0037-29`, `0037-30`, `0037-31`, `0037-32`, `0037-33`, `0037-34`,
`0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`,
`0037-36`, and `0037-40`.

`0037-29` and `0037-30` were not in the original `DEC-0044-034` 54-marker
population. The other 11 targets are the Feature `0037` members of that
population relevant to this recovery. `DEC-0044-035` supersedes the original
exact-54/no-partial rule only for this independent exact-13 transaction. Every
other original marker remains outside this transaction and receives no truth,
repair, reopening, retention, or completion disposition here.

Immediately before mutation, the operator must compare-and-swap against both
pinned values above and prove every exact block below is byte-identical. The
transaction must preserve accepted foundational Feature `0037` work and all
Task text, prerequisites, checkpoint attributes and verdicts, Acceptance
history, incident summaries, claims, selectors, issue artifacts, integration
state, Feature closure state, and unrelated markers. No marker not listed above
may change. Any mismatch aborts before writing. This package itself changes no
marker, selector, authority, issue item, Acceptance, checkpoint verdict,
integration state, write freeze, cutover ref, or Feature closure.

## Exact before blocks

The following 13 complete Task blocks were re-extracted verbatim from
`TODO.md` at the pinned baseline. Their inventory, markers, byte content, and
absence of current target Acceptance are validation preconditions, not inferred
from the stale candidate.

```markdown
- [x] **0037-29** PREREQ: 0037-29:0037-14, 0037-29:0037-15, 0037-29:0037-16, 0037-29:0037-21 Execute repeated non-authoritative shadow migrations from pinned committed legacy sources and resolve every importer/schema finding.
  - **Acceptance criteria:** Each run uses Git blobs, fresh `_src/output/issue-migration/<run-id>/issues/` and `<run-id>/reports/` roots, and recorded source/candidate/tool/schema/artifact identities; includes every newly committed legacy change; regenerates views/reports; links each mismatch to a bounded issue or signed disposition; and is visibly non-authoritative. Manual shadow edits are discarded, not reconciled.
  - **Definition of Done:** At least two increasing source-watermark runs plus one schema/tool-change rerun converge to zero unexplained loss/duplication and a passing retained report; prior run/report/finding links remain queryable.
```

```markdown
- [x] **0037-30** PREREQ: 0037-30:0037-03, 0037-30:0037-10, 0037-30:0037-14, 0037-30:0037-15, 0037-30:0037-20, 0037-30:0037-21, 0037-30:0037-28, 0037-30:0037-29, 0037-30:0037-43, 0037-30:0037-44 Reconcile active legacy claims/work, staged or uncommitted backlog edits, new-store leases, and handoffs before the final source watermark.
  - **DEC-0037-002 execution model:** Reconcile direct processes and every Task-ID-bound background Runner job; the accepted `0037-21` job-control contract is a start prerequisite.
  - **Acceptance criteria:** Inventory each active agent session/task/owner identity/capability class/base commit/instruction-contract version/runner request or result/authority epoch/write scope/expiry and discrepancy; merge or explicitly preserve uncommitted task text; require every session to stop, every legacy/new-store claim to be signed-released or closed, and every runner request to be terminal with reconciled results before the freeze; as the final pre-freeze operation, atomically bump `agent-workflow.json` to a new `legacy-frozen` epoch/capability set enforced by `0037-43`, record its bundle/source digests in the quiescence barrier, and prove no pre-cutover session may mutate or resume after the switch; never activate a dormant candidate `claim.json` or `refs/autodocs/claims/*` before/at cutover; never overwrite another agent; and block reused IDs, dirty/staged backlog state, stale ambiguous ownership, overlapping scopes, or simultaneous ownership in both models. New claims may be created only after both `0037-40` activation/reference commits complete and lift the write freeze.
  - **Definition of Done:** Signed reconciliation/quiescence report is bound to the exact final `legacy-frozen` selector/instruction/source digests and clean committed legacy source watermark; no later ordinary Feature work or agent pickup is permitted—only the named transaction-bound operators for `0037-31`, `0037-34.01`, `0037-32`, `0037-33`, and `0037-34.02` may run, without claims or item writes; every known session, `TODO-<agent-id>.md`, and claim ref is stopped/released/dispositioned and no active work is orphaned, dual-owned, or carried stale across cutover.
```

```markdown
- [x] **0037-31** PREREQ: 0037-31:0037-20, 0037-31:0037-25, 0037-31:0037-28, 0037-31:0037-29, 0037-31:0037-30 Produce the final frozen migration candidate and reconciliation evidence without switching authority.
  - **Acceptance criteria:** Freeze legacy writes at a named source commit with zero active claims; clean-import with approved schema/tool; include final committed Feature `0037`; replay only authorized provenance events; regenerate every declared view/graph/i18n/page/HTML artifact and report; compare IDs/text/states/edges/criteria/refs/counts/hashes and public privacy projection; any source change outside the predeclared cutover-control evidence refs invalidates the candidate and requires a new run. Record completion evidence on the cutover transaction ref while this Task remains `[p]`; the authorized patch materializes its closure.
  - **Definition of Done:** Immutable candidate/source artifact sets, passing migration report, complete validation/trace bundle, generated diff review, and transaction-ledger entry identify one exact unchanged candidate/source pair; no rollback success is claimed before `0037-35.02`.
```

```markdown
- [x] **0037-32** PREREQ: 0037-32:0037-34.01 Conduct an independent signed pre-cutover audit of the exact frozen candidate and prepared final authority tree.
  - **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.
  - **Acceptance criteria:** A sandboxed audit agent submits the exact pre-cutover runner profile from `issues/_policy/audit-profiles.json`: all mandatory checks/high-risk items (including Feature `0021` and placeholders), all authority/privacy boundaries, and deterministic seeded samples meeting each state/type minimum. A registered quality signer who did not author the candidate independently reviews the retained results, verifies the deterministic control-closure delta, absence of evidence/acceptance/authority inflation, exact agent-instruction bundle/authority epoch/stale-client guards, policy-semantic continuity for owned-work resumption, parent closure, autonomous backlog repair, `[u]` boundaries, collaboration/tooling suggestions, and one-use non-escalation runner semantics, graph/public-projection/i18n/HTML parity, and the hermetic causal chain in both candidate and exact prepared authority tree, and records stable findings against exact artifact digests. Any candidate/profile/policy change invalidates the audit. Evidence is written to the transaction/approval refs while this Task remains `[p]`; the required post-cutover reference commit materializes its closure.
  - **Definition of Done:** SSH-signed audit recommendation, command/result manifest, sample inventory, and closed finding log meet every profile threshold, pass bootstrap/role verification, and identify the unchanged candidate, or explicitly block cutover.
```

```markdown
- [x] **0037-33** PREREQ: 0037-33:0037-31, 0037-33:0037-32, 0037-33:0037-34.01 Obtain the signed process/security/release cutover decision for the exact candidate and prepared patch.
  - **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.
  - **Acceptance criteria:** Registered process, security/privacy, and release signers review source/candidate/control-base commits, patch/artifact digests, migration/validation/audit reports, generated diff, residual limitations, exact public projection, complete `SANDBOX.md`/`AGENTS.md`/`PRIVILEGED.md`/`agent-workflow.json` capability/runner/phase/epoch switch, zero-privileged-agent execution profile, grunt first-attempt qualification and stale-client results, non-bypassable integration-gate evidence, zero active sessions/claims, write freeze, signed point-of-no-return implications, post-activation forward recovery, support, and frozen-window rollback/event replay. Approval commits branch from the recorded control base onto dedicated immutable refs and do not advance integration HEAD; each record names package/policy revision, exact digests, validity/revocation, and conditions. Rejection/change keeps legacy authority and opens bounded remediation; no candidate/patch author self-approves. Because the legacy source is frozen, waiting/approval state is recorded on the transaction ref while this Task remains `[p]`, not by changing `TODO.md` to `[u]`.
  - **Definition of Done:** Bootstrap-verified SSH-signed approval refs authorize one unchanged patch and control base; the post-cutover reference commit later materializes this Task's closure.
```

```markdown
- [x] **0037-34** PREREQ: 0037-34:0037-34.01, 0037-34:0037-34.02 Complete prepared and authorized atomic authority cutover.
  - **Acceptance criteria:** Preparation and execution remain separate; the executed patch is byte-identical to the authorized patch except fields that must record the resulting cutover commit through the required follow-up reference commit.
  - **Definition of Done:** Both Subtasks complete with one authority at every committed state and retained rollback/event-replay material.
```

```markdown
- [x] **0037-34.01** PREREQ: 0037-34.01:0037-20, 0037-34.01:0037-21, 0037-34.01:0037-31, 0037-34.01:0037-42 Prepare the exact authority-switch patch and rollback package without applying it.
  - **DEC-0037-002 execution model:** The prepared bundle pins the accepted direct-execution role/capability/job-control contract before cutover.
  - **Acceptance criteria:** In a detached temporary worktree, derive the final authority tree from the unchanged candidate plus the schema-validated transaction-ledger closure delta for `0037-31` and `0037-34.01`; mark `TODO.md`/`DONE.md` generated; activate issue validation/regeneration while claims remain frozen; atomically switch `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, and `agent-workflow.json` to one new contract version, authority epoch, `issue-store-frozen` capability phase, and qualified grunt-runner protocol/action-registry version and update process/tool entry points; remove obsolete legacy parser/owner/dual-write paths; fill every knowable migration-record field; and generate inverse rollback plus post-cutover event export/replay commands. Record the unchanged integration control-base commit/tree, patch SHA-256, candidate/artifact-set digests, expected file list/modes, instruction-bundle digests/epoch, fresh/stale-agent validation results, approval-ref topology, and the exact post-cutover closure/reference operations excluded from the patch. Do not modify the integration branch or authority.
  - **Definition of Done:** Prepared patch/final-authority-tree and rollback artifact sets reproduce byte-for-byte in a clean worktree, validate, differ from the candidate only by the declared closure/authority delta, and are ready for independent audit by `0037-32`.
```

```markdown
- [x] **0037-34.02** PREREQ: 0037-34.02:0037-33, 0037-34.02:0037-34.01 Apply the authorized patch as the atomic authority-switch commit.
  - **Integration review: mandatory.** **Rationale (architect):** this is the atomic authority-switch boundary.
  - **Acceptance criteria:** Verify integration HEAD equals the authorized control base, clean index/worktree, candidate/patch/approval digests, policy revision/signature validity, zero active claims, enforced issue-write freeze, and complete file list before applying. One commit applies the exact independently audited final authority tree, makes `issues/` authoritative and all legacy lists/catalogs/graphs/public payloads generated, activates validation/regeneration but keeps claim/item writes disabled by the `issue-store-frozen` selector and command fencing through `0037-40`, retains source/migration/audit/rollback evidence, and leaves no legacy parser/owner path. A follow-up reference commit records the actual cutover hash/UTC time and closes `0037-32`, `0037-33`, `0037-34.02`, and aggregate Task `0037-34` without amending or weakening authorized content; no dual-authority gap exists.
  - **Definition of Done:** Cutover and follow-up reference commits match authorization; immediate post-commit validation reports exactly one authority, one consistent artifact lineage, and zero stale/obsolete paths.
```

```markdown
- [x] **0037-35** PREREQ: 0037-35:0037-35.01, 0037-35:0037-35.02 Complete clean-cutover regeneration verification and rollback rehearsal.
  - **Acceptance criteria:** Verification and rollback use isolated clean/detached worktrees and retained run/artifact evidence; neither rewrites production history.
  - **Definition of Done:** Both Subtasks have signed passing transaction-ledger evidence against the actual cutover commit and identify exact environment, commands, inputs, outputs, and hashes; their issue closures are deferred to `0037-40`.
```

```markdown
- [x] **0037-35.01** PREREQ: 0037-35.01:0037-34.02 Rebuild every derived issue view, graph, i18n artifact, page model, language tree, index, and validation artifact from a clean checkout of the mandatory post-cutover reference integration commit.
  - **Acceptance criteria:** Install only locked/tracked dependencies and approved system-tool versions; use a fresh sandboxed-agent fixture to read bootstrap state and submit the qualified runner request before the documented DAG; compare instruction/source/catalog/view/public/tree/artifact counts and hashes; prove a fresh agent discovers only `issues/`, every legacy cached instruction/command is rejected actionably, and there is no source mutation, fixture leakage, absent stage, network-only dependency, fallback translation, mixed run, or unexplained diff.
  - **Definition of Done:** Retained clean-run report exits zero, a second run satisfies declared byte/semantic determinism, and all output artifact sets link to the exact post-reference integration HEAD and cutover; signed completion evidence is appended to the transaction ref without writing issue state.
```

```markdown
- [x] **0037-35.02** PREREQ: 0037-35.02:0037-34.02 Rehearse rollback and post-cutover event preservation from the mandatory post-cutover reference integration commit in an isolated temporary ref/worktree.
  - **Acceptance criteria:** Execute every rollback case in the fixed audit profile using development-test provenance/control events only (authoritative issue writes remain frozen), prove the prepared inverse patch applies to the exact post-reference HEAD and every permitted transaction-ref-only frozen successor, apply it, restore the matching legacy `SANDBOX.md`/`AGENTS.md`/`PRIVILEGED.md`/`agent-workflow.json` authority epoch and instructions, prove issue-store-cached commands are rejected with legacy recovery guidance, export/replay compatible provenance events without duplication/loss, validate exactly one authority, then discard the temporary ref. Do not move the real integration branch, erase immutable events, or claim rollback for an untested path.
  - **Definition of Done:** Retained rollback report and before/after artifact sets prove authority restoration, event preservation/exactly-once replay, cleanup, and deterministic recovery; injected conflict/failure cases stop safely; signed completion evidence is appended to the transaction ref without writing issue state.
```

```markdown
- [x] **0037-36** PREREQ: 0037-36:0037-34, 0037-36:0037-35 Conduct an independent signed post-cutover audit and authorize closure only if authority, views, provenance, claims, and generated trees remain consistent.
  - **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.
  - **Acceptance criteria:** A sandboxed audit agent submits the exact post-cutover runner profile from `issues/_policy/audit-profiles.json`, including every mandatory grunt-runner/capability/instruction-bootstrap/authority/view/graph/privacy/link/i18n check, fresh/stale-agent fixtures, fixed high-risk trace, deterministic seeded strata, and claim/item-write freeze assertion. A registered independent quality signer reviews the retained results, verifies approval/candidate/cutover/reference/clean-run/rollback lineage, and routes any threshold failure through actual rollback rather than accepting drift.
  - **Definition of Done:** SSH-signed audit addendum and command/sample manifest meet every profile threshold, pass signer/role validation, link final authority state/reports/residual limitations/support/rollback obligations/exact commits/artifact sets, and append authorization for the exact `0037-40` activation delta to the transaction ref. This Task remains `[p]` until `0037-40` materializes its closure; it alone authorizes that activation.
```

```markdown
- [x] **0037-40** PREREQ: 0037-40:0037-36 Apply the signed post-cutover closure/activation delta and lift the write freeze.
  - **DEC-0037-002 verification:** As the single terminal integrating Task, prove direct Programmer/Tester operation and a synthetic Runner long job including progress, cancellation, recovery, and the negative rule that Runner status cannot grant authority.
  - **Integration review: mandatory.** **Rationale (architect):** this is Feature `0037`'s terminal integration and activation checkpoint.
  - **Acceptance criteria:** Verify the append-only transaction-ref head by compare-and-swap, exact cutover/reference/clean-run/rollback/audit artifact digests, independent quality signature/role, and unchanged frozen issue tree. The activation commit materializes closures for `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` and regenerates all derived views. A required follow-up reference commit records the activation hash, closes `0037-40` and Feature `0037`, regenerates `TODO.md`/`DONE.md`/catalog/graph outputs, verifies one authority, a newly incremented `issue-store-writable` instruction epoch/capability set, successful fresh-agent doctor, rejected legacy commands and all pre-activation epochs, and zero unexplained diff, and only then lifts the issue/claim write freeze. The signed authorization explicitly accepts that this is the routine legacy-rollback point of no return and names `0037-44` as the post-activation recovery path. Any mismatch leaves the freeze active and triggers frozen-window rollback/remediation.
  - **Definition of Done:** Both activation and follow-up commits match the signed delta, pass the full issue/regeneration validator from clean checkouts, move the Feature to generated `DONE.md` with real refs, and record the exact transaction-ref terminal object; no ordinary issue mutation occurs before the freeze is lifted.
```

## Affected gates

The correction fails closed the current Feature 0037 chain gates represented by
these markers: Task starts `0037-30`, `0037-31`, `0037-32`, `0037-33`,
`0037-34`, `0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`,
`0037-35.02`, `0037-36`, and `0037-40`; the criterion-bound shadow,
quiescence, candidate, audit, approval, cutover, regeneration, rollback, and
activation validations; mandatory integration checkpoints `0037-34.02` and
`0037-40`; the authority switch, write-freeze lift, and Feature `0037` closure.
Existing prerequisite text remains authoritative; this list describes the
cross-item reach and does not amend those contracts.

## Decision, review, ancestry, drift, rollback, and retry

- **Decision prerequisite:** append-only Management disposition `DEC-0044-035`
  must remain reachable and unchanged for this exact baseline and exact set.
- **Review prerequisites:** the correction candidate must genuinely descend
  from Guinan's independent scope-review commit
  `24262277f03f8d36333902fed4b6b25042028402` and from the exact current-main
  baseline above. The Supervisor must obtain a later supporting independent
  exact-candidate review after this reconstruction. Neither review is Task
  Acceptance, an integration verdict, a signature, or Feature closure.
- **Integration prerequisite:** only the separately assigned Integrator may
  cross the applicable checkpoint or advance `main`; textual copies of a
  decision or review do not satisfy ancestry.
- **Before write:** re-read `refs/heads/main`, recompute the full `TODO.md`
  digest, extract the exact 13-block inventory, and compare every byte and every
  `[x]` marker with this artifact. Recheck absence of target Acceptance,
  selector/authority/write-phase/runner state, numeric issue items, catalog,
  cutover refs, superseding governance, and evidence of legitimate target
  completion. Any drift is a no-write stop; it never authorizes a partial
  correction or relaxed CAS.
- **Atomicity:** prepare and verify an exact 13-pair marker-only `TODO.md` diff,
  with zero other byte changes, then use an integration-authorized current-main
  CAS transaction. A failed CAS is a no-op; retry only after rebinding a fresh
  baseline and renewing any decision or review whose evidence or reach changed.
- **Interrupted or partial application:** do not complete or compensate by
  ad-hoc edits. Keep the candidate unintegrated, retain failure evidence, leave
  the integration target unchanged, and re-derive from current `main`.
- **After integration:** if the correction is later proven wrong, restoration
  is append-only and separately authorized against exact then-current Task
  evidence and graph state. Never reset or rewrite history, and never restore
  `[x]` merely to unblock scheduling.

## Check-in provenance receipt

The following is the complete user-authored prompt that materially requested,
authorized, and triggered this governance reconstruction, preserved verbatim:

```text
SUPERVISOR ASSIGNMENT — reconstruct and rebind the Feature 0037 marker-recovery governance package on current main.

Dispatching identity: `supervisor-zed-0037-cutover-20260901` acting as Supervisor under the repository owner's explicit Management authorization quoted below.
Assigned persona/role: `Data`, privileged Governance Decision Recorder and Implementer. You record the already-authorized Management disposition; you are not the independent Architect reviewer and not the Integrator.
Capability class: `privileged`.
Scope ID: `0037-cutover-governance-rebind-20260901` (assignment-scoped recovery; DO NOT create a TODO Task).
Branch: `0037-cutover-governance-rebind-20260901`.
Owned worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-rebind-20260901`.
Named downstream Integrator reservation for this one chain: persona `Picard`, to be separately dispatched by the Supervisor after independent exact-candidate review. Do not integrate yourself.

Permitted write paths — exactly these three:
1. `docs/dossiers/dec-0044-034-mass-marker-evidence-correction.md`
2. `docs/campaign-evidence/mass-marker-evidence-gap-20260901/current-baseline-0037-marker-plan.md`
3. `docs/campaign-evidence/mass-marker-evidence-gap-20260901/architect-scope-review.md`

Exact inputs:
- stale preparation candidate: `0d87882bd5a2df9c3b9a9eeec515fdfd09c77450`;
- independent Architect review commit: `24262277f03f8d36333902fed4b6b25042028402` by persona `Guinan`, verdict SUPPORT scope only, requiring reconstruction/rebinding;
- latest current `main` must be discovered and pinned immediately before branch/worktree creation and rechecked before commit;
- old governing record is the existing `DEC-0044-034` exact-54/no-partial decision in the first permitted path.

Required outcome:
1. Create the named worktree/branch from then-current `main`. Never write in the shared root checkout.
2. Preserve actual ancestry of the independent review commit `24262277…`: merge that review lineage into the reconstruction branch off current main (no main advance), resolving the three permitted paths so the final tree contains the original review byte-for-byte unless an append-only carriage note is strictly necessary. Do not fake ancestry by merely copying text. No other changed paths may enter the result.
3. Replace the stale 2026-09-01 preparer addendum with a conforming append-only `decision-record@v1` Management disposition (do not rewrite/delete the original 54-marker record). The new disposition must:
   - identify the repository owner/current user as Management deciding authority and Data only as recorder;
   - quote the user authorization verbatim;
   - bind exact current-main object and full `TODO.md` SHA-256;
   - govern exactly these 13 markers: `0037-29`, `0037-30`, `0037-31`, `0037-32`, `0037-33`, `0037-34`, `0037-34.01`, `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`, `0037-36`, `0037-40`;
   - state explicitly that `0037-29` and `0037-30` were not in the original 54-marker population, while the other 11 are the Feature 0037 members relevant here;
   - expressly supersede the original `DEC-0044-034` exact-54/no-partial atomicity rule only to the extent needed to authorize this independent exact-13 recovery transaction;
   - state that the other original markers are outside this transaction, are not changed or newly credited, and their truth/repair disposition is not decided here;
   - specify exact `[x]` → `[ ]` marker-only CAS semantics, all fail-closed conditions, affected work units/gates, alternatives, consequences, rollback/retry, and the required review/integration ancestry;
   - preserve accepted foundational Feature 0037 work and all Task text, prerequisites, checkpoints, Acceptance history, incident summaries, claims, selectors, issue artifacts and unrelated markers;
   - state that this governance package changes no marker, selector, authority, issue item, Acceptance, checkpoint verdict, integration state or Feature closure.
4. Rebuild `current-baseline-0037-marker-plan.md` against the same exact current-main object and digest. Re-extract all 13 complete Task blocks verbatim. Recompute selector/authority state, canonical numeric issue count, catalog count, and `refs/autodocs/cutover/0037/*` count. Preserve the exact management boundary and clearly name the decision/review prerequisites.
5. Carry `architect-scope-review.md` with genuine ancestry from `24262277…`. It may continue to say the old candidate was stale; do not change its verdict. The Supervisor will request a follow-up exact-candidate review afterward.
6. Validate: exact 13 inventory, all expected `[x]`, no current Acceptance on targets, exact block extraction, current selector/item/catalog/ref facts, no unintended path changes, `git diff --check`, commit ancestry includes `24262277…`, commit ancestry includes the current-main base, provenance completeness, and clean worktree.
7. Commit with path-limited staging and complete provenance, including `Task-ID` and `Base-Ref` trailers. Return branch, exact tip, base, parent/merge topology, changed paths, bound digest, operational counts/state, validation, and clean status.

You MUST NOT:
- edit `TODO.md`, `DONE.md`, any authority selector/config, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `docs/pipeline/**`, `issues/**`, claims, tools, tests, schemas or any path outside the three permitted paths;
- create a new TODO Task;
- change any marker or Acceptance record;
- implement/import/regenerate/cut over the issue store;
- sign a cutover ref, cross an integration checkpoint, merge to/advance `main`, push, publish, or move Feature 0037 to `DONE.md`;
- self-review, self-accept, or treat the Management record as Architect review/integration approval.

Management authorization (verbatim):
> Dann nimm es jetzt in Betrieb. Eine gute Gelegenheit, die fälschlicherweise nicht ge[x]ten Tasks loszuwerden. Du kriegst von mir dafür alle nötigen Management-Freigaben. Steuere alles ein über Assignments, die du als supervisor verschickst. Keine neuen TODO-Tasks erstellen während des übergangs, sonst bremsen wir uns nur wieder selber aus.

Continuation prompt:
> go ahead

Architect finding you must disposition faithfully: the 13-marker scope is supported, but `0d87882b…` is stale; its digest no longer matches main; original DEC-0044-034 required atomic 54 and omitted `0037-29`/`0037-30`; a conforming authorized append-only decision must expressly bind the exact 13 and resolve that conflict before mutation. Do not weaken this finding or imply the old candidate is integration-ready.
```
