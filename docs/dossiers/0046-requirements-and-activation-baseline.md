# Feature `0046` requirements and activation baseline

**Baseline:** `requirements-baseline@v1`, pinned to Feature tip `ff7f7e8bad6de50d157c48b6fbeca29269ea8309` and Architect candidate `4bff5e5095f26ba8c4849dbf9e9b9de83041ec92`.

**Authority and status:** This Requirements Engineer work product derives from [`DEC-0046-001`](dec-0046-worktree-topology-and-integration-plan.md), the candidate [`WTP@v1`](../pipeline/worktree-topology-plan.md), and the reconciled Feature proposal. It records requirements and observations only. It does not reinterpret architecture, activate a gate, approve a plan, grant authority, cross a checkpoint, or migrate another Feature.

## 1. Normative language and trace rule

“Must” is testable; “must not” is a refusal condition; “may” is an explicitly bounded option. Every requirement below has at least one downstream owner. Downstream work records its requirement IDs in tests, schemas, manifests, reports, or review evidence. A requirement changes only by an additive superseding baseline with impact analysis; IDs are never reused.

The machine-comparable forward map is retained as [`requirements-trace.tsv`](../campaign-evidence/0046-measurement-baseline/requirements-trace.tsv); the reverse task view is in §9.

## 2. WTP requirements

| ID | Requirement | Verification | Downstream |
|---|---|---|---|
| `RQ-WTP-001` | A WTP must bind immutable Git REF, reproducible content digest, Feature ID, schema, canonicalization, and digest-algorithm versions. Neither REF nor digest may substitute for the other. | Positive identity fixture; unreachable REF, digest/version mismatch refusals. | `0046-02`, `0046-04`, `0046-06`, `0046-07` |
| `RQ-WTP-002` | It must contain exactly one node per executable Task/Subtask, one retained read-only `main` node, complete typed edges, and no partial governed graph. | Set equality, endpoint, topology, and partial-graph tests. | `0046-02`, `0046-04`, `0046-06` |
| `RQ-WTP-003` | Each node must declare unique branch/worktree ownership, owner role, capability class, non-empty write/read scope, phase, lifecycle, provisioner, predecessor constraints, and recovery reference. | Schema plus semantic uniqueness and completeness checks. | `0046-02`, `0046-04`, `0046-06` |
| `RQ-WTP-004` | Every intersecting write scope must have a closed time-aware class: `concurrent-exclusive`, `ordered-predecessor`, `claim-carry`, or `reconciliation`; unknown or omitted relations fail closed. | Pairwise overlap matrix, sequential-pass/concurrent-fail fixtures. | `0046-02`, `0046-04`, `0046-06` |
| `RQ-WTP-005` | Structural, authority, scope, checkpoint, recovery, algorithm, status, or topology changes are blocking; only enumerated operational observations may be refreshable. | Pointer-class coverage and structural-drift fixtures. | `0046-02`, `0046-04`, `0046-06` |
| `RQ-WTP-006` | A withdrawn/incompatible WTP, unreproducible identity, duplicate active branch/worktree, partial graph, unknown overlap, or impossible recovery reference is invalid and not refreshable. | One stable refusal code per invalid class. | `0046-02`, `0046-04`, `0046-06` |
| `RQ-WTP-007` | The WTP must declare all checkpoints, exactly one terminal integrating Task, validation profile, activation state, migration/recovery premises, and the no-implicit-grandfathering rule. | Graph/checkpoint and lifecycle semantic checks. | `0046-02`, `0046-04`, `0046-05`, `0046-06`, `0046-07` |
| `RQ-WTP-008` | A WTP is evidence and a structural input only; it must never act as claim, lease, assignment, Acceptance, verdict, or execution authority. | Negative authority tests and review inspection. | `0046-02`, `0046-04`, `0046-07` |

## 3. IP requirements

| ID | Requirement | Verification | Downstream |
|---|---|---|---|
| `RQ-IP-001` | An IP must be Integrator-owned and bind one exact WTP REF+digest and all identity/version/status inputs from `RQ-WTP-001`. | Schema/interface completeness and mismatch refusals. | `0046-03`, `0046-04`, `0046-07` |
| `RQ-IP-002` | Each step must bind exact source/target tips, target-before state, ordered predecessor absorption, merge mode, checkpoint/test profile, reconciliation choice, hygiene, recovery, evidence, and authority boundary. | Initial-plan schema example and full-step semantic checks. | `0046-03`, `0046-04`, `0046-06`, `0046-07` |
| `RQ-IP-003` | The final-`main` operation may appear only as the final planned step and must name candidate/target pins, root preflight, hygiene, actor authority, merge mode, verification, and recovery; a plan must not execute or authorize it. | Missing-field and unauthorized/non-final action refusals. | `0046-03`, `0046-04`, `0046-07` |
| `RQ-IP-004` | Acceptance closure must be an immutable normalized member manifest and digest covering prerequisite edges/boundaries, candidate and contract identities, dispositions/claims, decisions/evidence, reviewer authority, and invalidation state. | Closure reconstruction, digest mismatch, invalidation and candidate-binding fixtures. | `0046-03`, `0046-04`, `0046-07` |
| `RQ-IP-005` | Before every consequential step, the IP consumer must revalidate WTP status, supersession, digest, compatibility, closure, and exact runtime premises. | Step-boundary stale/withdrawn/mismatch tests. | `0046-03`, `0046-04`, `0046-06`, `0046-07` |
| `RQ-IP-006` | Append-only refresh is allowed only for an already-bounded operational alternative with unchanged structure, meaning, scope, checkpoint reach, authority, validation, and recovery. | Refresh-pass versus revision-required matrix. | `0046-03`, `0046-04`, `0046-06` |
| `RQ-IP-007` | A refresh event must bind old/new pins, reason, stale class, recomputed ancestry/overlap/closure/hygiene results, identity, and evidence digest; missing/stale/invalid Acceptance remains blocking. | Refresh-event schema and blocking-Acceptance fixtures. | `0046-03`, `0046-04`, `0046-06`, `0046-07` |
| `RQ-IP-008` | Bad plans and execution history must be superseded or withdrawn append-only, never edited in place. | Revision-chain and recovery inspection. | `0046-03`, `0046-06`, `0046-07` |

## 4. Migration and activation requirements

| ID | Requirement | Verification | Downstream |
|---|---|---|---|
| `RQ-MIG-001` | The migration population is exactly the 32 Features in [`feature-population.tsv`](../campaign-evidence/0046-measurement-baseline/feature-population.tsv), derived from `TODO.md` at the pinned baseline; `DONE.md` Features are excluded from active migration. | Exact set equality and population digest. | `0046-05`, `0046-06`, `0046-07` |
| `RQ-MIG-002` | Before an operative migration decision, every population member is safely treated as non-governed by WTP/IP. The baseline planning disposition is `deferred`; existing rules remain controlling. | All rows have the explicit baseline state, owner, trigger, and no activation claim. | `0046-05`, `0046-07` |
| `RQ-MIG-003` | The operative manifest must assign exactly one of `migrated`, `compatible-with-bounds`, or `deferred`, with Feature/branch baseline, gates, evidence, omissions, risks, owner, trigger, recovery, and validator result. | Manifest set/cardinality/completeness checks. | `0046-05`, `0046-07` |
| `RQ-MIG-004` | `migrated` requires complete conforming WTP/IP evidence; compatibility must state bounds and must not imply hidden compliance; material unknowns must remain `deferred`. | Disposition-specific required-field and evidence checks. | `0046-05`, `0046-07` |
| `RQ-MIG-005` | Migration must not rewrite foreign claims, contracts, Acceptance, verdicts, merge evidence, or snapshots. | Exact changed-path and history-preservation checks. | `0046-05`, `0046-07` |
| `RQ-MIG-006` | Activation must progress only through the state machine below, with no direct `dormant`→`active` transition and no inference from green tooling alone. | Lifecycle transition and authority tests. | `0046-04`, `0046-05`, `0046-06`, `0046-07` |
| `RQ-MIG-007` | Rollback must stop affected gates, retain last valid plans and evidence, restore prior behavior only through separate authorization, and preserve append-only history. | Fail-closed recovery drill and review. | `0046-05`, `0046-06`, `0046-07` |

## 5. Operational and measurement requirements

| ID | Requirement | Verification | Downstream |
|---|---|---|---|
| `RQ-OPS-001` | Every validation or drill must retain exact command/procedure, baseline, environment controls, exit status, population/counts, and content digests. | Evidence-manifest inspection and replay. | `0046-02`, `0046-03`, `0046-04`, `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-002` | Pre/post comparison must use the five frozen measures and definitions in `measurement-baseline.json`; denominator, window, exclusions, and data-quality flags must remain identical or be reported as non-comparable. | Measurement schema and comparison audit. | `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-003` | Discovery reads are the pinned-claim line-count proxy defined in the baseline, not an estimate of unrecorded human/tool activity. | Re-run exact command and compare digest/count. | `0046-06`, `0046-07` |
| `RQ-OPS-004` | Stale handoffs and blocked preflights count only explicit retained textual events matching the frozen expressions; zero means “no explicit retained match,” not proof of absence. | Re-run expressions and preserve limitations. | `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-005` | Integration rework counts matching commits in the frozen time/ref boundary; later comparison must report exposure time and commit population. | Re-run command and inspect matching subjects. | `0046-06`, `0046-07` |
| `RQ-OPS-006` | Recovery time is elapsed commit time between a named incident anchor and named terminal recovery pin; trial recovery uses the same start/end event semantics. | Pin reachability and arithmetic replay. | `0046-06`, `0046-07` |
| `RQ-OPS-007` | Tracked evidence is internal and must exclude raw mailbox bodies, secrets, credentials, raw home-directory paths, and claim bodies not already authoritative. Raw inventories are ephemeral; only minimized rows, counts, commands, and SHA-256 digests are committed. | Privacy review and changed-path inspection. | `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-008` | Committed baselines and supersession history are retained with Git history; disposable raw extracts are not promoted. Deletion or expiry must not be invented by this Feature. | Artifact classification and history inspection. | `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-009` | Every open decision must name owner, current safe default, decision trigger, deadline/event boundary, affected requirements, and the behavior while unresolved. No placeholder may silently permit work. | Open-decision table completeness. | `0046-03`, `0046-05`, `0046-06`, `0046-07` |
| `RQ-OPS-010` | All failures must be actionable and fail closed at the affected step without cleaning or appropriating a foreign worktree. | Negative tests, dirty-worktree canary, and recovery drill. | `0046-02`, `0046-04`, `0046-06`, `0046-07` |

## 6. Activation state machine

| State | Entry | Permitted behavior | Exit / stop |
|---|---|---|---|
| `dormant` | Current baseline. Candidate contracts may exist. | Author, validate, and review isolated artifacts; existing authority alone governs live work. | Enter `trial` only when `0046-01..05` implementation inputs exist for the declared trial, mandatory checkpoint obligations remain visible, and `0046-06` starts a non-operative self-application. Any missing/mismatched input stays dormant. |
| `trial` | Feature `0046` explicitly self-applies WTP/IP as additional evidence in disposable or isolated contexts. | Run normal, stale, overlap, Acceptance, hygiene, and recovery drills. WTP/IP cannot block or authorize live work. | Return to `dormant` on unexpected permit/refusal, identity mismatch, incomplete population, recovery failure, or audit gap. Eligibility for `active` requires completed `0046-07`, current checkpoint/Acceptance closure, independent QA disposition, complete migration manifest, and separate governance authorization. |
| `active` | Only a separately authorized governance integration changes controlling repository behavior after all Feature gates pass. | Apply only to Features whose operative manifest disposition and bounds permit it. Existing Acceptance, checkpoint, hygiene, root-preflight, and final-main authority remain cumulative controls. | Stop affected gates and invoke `RQ-MIG-007` on invalid/withdrawn plans, unsafe drift, false permit/refusal, incomplete migration, or authority mismatch. |

There is no direct `dormant`→`active` transition. This document leaves the system `dormant`.

## 7. Pinned population and baseline dispositions

The exact population is retained in [`feature-population.tsv`](../campaign-evidence/0046-measurement-baseline/feature-population.tsv). All 32 rows have the non-operative planning disposition `deferred` because no row yet has complete, independently reviewed WTP/IP evidence. This is the safe pre-migration default, not the operative manifest owned by `0046-05`.

- **Owner:** Task `0046-05` implementer with independent QA participation.
- **Revisit trigger:** composed gate `0046-04` is implementation-complete and a pinned migration run starts.
- **Risk while deferred:** repeated ad-hoc topology/integration discovery remains; the pre-existing process remains authoritative.
- **Recovery:** withdraw/supersede only the later manifest; never rewrite source Feature history.

## 8. Open decisions

| Decision | Owner | Safe default while open | Trigger / event boundary | Affected requirements |
|---|---|---|---|---|
| `OD-0046-01` — whether the candidate becomes repository-wide active governance | Current user/registered Management authority through a separately authorized governance change | Remain `dormant`; trial evidence has no operative effect. | After `0046-07` records current checkpoint, Acceptance-closure, migration, recovery, and QA results. | `RQ-MIG-006`, `RQ-MIG-007`, `RQ-OPS-009` |
| `OD-0046-02` — each Feature's operative migration disposition | `0046-05` implementer produces evidence; mandatory checkpoint reviewer/Integrator evaluates reach | Keep baseline `deferred`; existing rules govern. | Pinned migration run after `0046-04`, one explicit row per population member. | `RQ-MIG-001..005` |
| `OD-0046-03` — disposition of unexpected trial gaps | Finding owner named by `0046-06`; Integrator handles checkpoint consequences | Stop the affected drill, retain evidence, remain or return `dormant`. | Any false permit/refusal, non-reproducible identity, incomplete recovery, or audit gap. | `RQ-WTP-005..008`, `RQ-IP-005..008`, `RQ-MIG-007`, `RQ-OPS-010` |

No open decision grants provisional authority. There are no unresolved placeholders.

## 9. Reverse handoff map

| Task | Requirements received | Expected evidence |
|---|---|---|
| `0046-02` | `RQ-WTP-001..008`, `RQ-OPS-001`, `RQ-OPS-010` | Canonicalizer/validator, stable refusal codes, fixtures, dirty-worktree canary. |
| `0046-03` | `RQ-IP-001..008`, `RQ-OPS-001`, `RQ-OPS-009` | IP contract/schema/template, trial plan, refresh/revision examples. |
| `0046-04` | `RQ-WTP-001..008`, `RQ-IP-001..007`, `RQ-MIG-006`, `RQ-OPS-001`, `RQ-OPS-010` | Composed validator, closure/stale/overlap/authority matrix, checkpoint evidence. |
| `0046-05` | `RQ-WTP-007`, `RQ-MIG-001..007`, `RQ-OPS-001..002`, `RQ-OPS-004`, `RQ-OPS-007..009` | Exact operative migration manifest, set-equality proof, independent QA audit. |
| `0046-06` | `RQ-WTP-001..007`, `RQ-IP-002`, `RQ-IP-005..008`, `RQ-MIG-001..002`, `RQ-MIG-006..007`, `RQ-OPS-001..010` | Non-operative trial, comparable measurements, refusal and recovery drills. |
| `0046-07` | All requirements except implementation-only fixture details; specifically every `RQ-*-*` remains review input | Integrated evidence manifest, checkpoint/closure review, activation-or-stop recommendation. |

## 10. Recovery and supersession

Corrections create a new baseline version that names this REF, changed requirement IDs, population/evidence impact, and downstream invalidation. Historical measurement rows and source pins remain immutable. A correction cannot silently activate policy or amend Architect/Integrator ownership.
