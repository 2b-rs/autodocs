# Task `0040-09` — Feature `0040` integration and management review package

**Status:** Candidate integration package. No aggregate `Acceptance: ✓` is
claimed by this document. The current user must decide the management-only
questions in section 11 against the pinned candidate presented after Task
implementation is committed.

- **Task:** `0040-09`
- **Feature:** `0040`
- **Integrator/facilitator:** `agent:zed:0040-09:20260818T180401Z-760531d011eb`
- **Feature input tip:** `86e285435e305a1e5c98fbb7aa1634bb3d9d8563`
- **Task start/claim commit:** `5d5388a53`
- **Independent aggregate audit:** session `dba7a212-14b4-4ffc-a0fe-c52f416d6b4a`
- **Audit result before remediation:** FAIL for aggregate acceptance readiness;
  PASS to continue bounded remediation and package preparation.

## 1. Review scope and limits

This package reviews Feature `0040` as one process change. It checks:

1. every stable requirement from the intake baseline;
2. every Task state, REF, prerequisite, and integration checkpoint;
3. authority and separation, including the incomplete waiver and the invalid
   agent-as-Management entry;
4. whether any new blocking gate lacks a decision record;
5. the accepted `0040-05` baseline for material drift;
6. all residuals from the retrospective pilot;
7. downstream ownership for work deliberately not implemented here;
8. claim reconciliation and validation.

It does **not** claim that downstream Feature `0037` traceability or reserved
Task `0039-01` effectiveness work is already implemented. It does not assess
Automotive SPICE capability. References to Automotive SPICE describe process
support only and remain separate from the ECU assessment in Features
`0011`–`0032`.

## 2. Integrated Task and checkpoint inventory

| Task | State | Substantive REF / disposition REF | Checkpoint | Aggregate result |
|---|---:|---|---|---|
| `0040-10` | `[x]` | `1164a971762e51673917458fa1342ce4507dd632` | no | Automation-safety blocker repaired; 71 findings, 35 disposed critical, zero unresolved critical, zero policy errors. `DEC-0040-10-001` remains structurally legacy and semantically incomplete at role and decision-scope review; additive map added in this Task. |
| `0040-01` | `[x]` | `7437905a6a6c0b7987ab6870f19cc5fc45ff774b` | no | Restrictive two-class mapping, three roles, two functions, Management outside agent roles, and five personas implemented. Historical Task prose reconciled to the already approved trilateral result. |
| `0040-02` | `[w]` | `7437905a6a6c0b7987ab6870f19cc5fc45ff774b` | no | Superseded by the five personas in `process-roles.md`; no five extra authority documents. |
| `0040-03` | `[x]` | `7bca09caeea83b8e26e2d69dd4f837eaa2317f39` | no | `decision-record@v1`, correction format, and legacy-map format implemented. |
| `0040-04` | `[w]` | `7437905a6a6c0b7987ab6870f19cc5fc45ff774b` | no | Rejected as duplicate of Feature `0037`; reciprocal bindings were added under current-user decision `DEC-0040-006` after distinct Architect review. |
| `0040-05` | `[x]` + `✓` | `f06867e06529469e26452e9cf20d362eb0d9648e`; review `063a85998f90197b698b9672e816ffaba7e5fb15` | **mandatory** | Current user approved all five questions and the pinned baseline. Material-drift analysis is in section 6. |
| `0040-06` | `[w]` | `7437905a6a6c0b7987ab6870f19cc5fc45ff774b` | no | Unbounded reference campaign rejected; the durable terminology and no-capability-claim rule are retained where they carry weight. |
| `0040-07` | `[w]` | `7437905a6a6c0b7987ab6870f19cc5fc45ff774b` | no | Effectiveness proof explicitly deferred by customer; `DEC-0040-006` binds the deterministic 20-Task measurement/evidence contract to still-reserved `0039-01`. |
| `0040-08` | `[x]` | `7d0c78f35522739e0b1550efd3ed5eb13fc431a1` | no | Pilot disposition `effective-for-declared-0038-03-scope-with-recorded-residuals`; six residuals retained. |
| `0040-09` | `[p]` | assigned after substantive commit | **mandatory** | This package; current user review pending. |

All listed commit objects were resolved in Git. The completed Task REFs are
ancestors of the integrated Feature input tip through the branch sequence.

## 3. Requirement disposition matrix

The intake prose says “17” requirements, but its stable tables contain **20**:
4 traceability + 5 decision + 4 process + 4 role + 2 standard + 1
effectiveness requirement. No ID is silently discarded.

| Requirement | Disposition | Evidence / owner |
|---|---|---|
| `RQ-TRACE-01` | **Deferred with durable reciprocal owner; not yet implemented.** | `DEC-0040-006` binds baseline retention/index regeneration evidence to `0037-17.02` without making it a second source writer. |
| `RQ-TRACE-02` | **Deferred with partitioned reciprocal owners; not yet implemented.** | Structural mappings: `0037-17.02`; read-only query semantics: `0037-17.03`; CLI exposure: `0037-10.04`. |
| `RQ-TRACE-03` | **Deferred with durable reciprocal owners; not yet implemented.** | `0037-17.03` and `0037-10.04` now require evidence/requirement↔file/commit in both directions and exclude line/symbol completion/freshness gates under `DEC-0040-004/006`. |
| `RQ-TRACE-04` | **Deferred with partitioned reciprocal owners; not yet implemented.** | The three `0037` contracts require explicit missing/dangling/unresolvable/redacted behavior and library/CLI tests. |
| `RQ-DEC-01` | **Implemented.** | `docs/pipeline/decision-record.md`: ISO-8601 timestamp with timezone. |
| `RQ-DEC-02` | **Implemented, with two disclosed historical defects.** | Exact identity grammar in `decision-record@v1`; `DEC-0040-005` agent-as-Management needs current-user ratification/correction; `DEC-0040-10-001` is truthfully mapped as incomplete. |
| `RQ-DEC-03` | **Implemented.** | Required technical justification in `decision-record@v1`; examples and Feature records. |
| `RQ-DEC-04` | **Implemented.** | Append-only correction events with exact effective-block digest bytes. |
| `RQ-DEC-05` | **Implemented and exercised.** | Closed trigger set in `decision-record@v1`; canonical `cross-item-blast-radius`; accepted `0040-05` rule; retrospective `0040-08`. |
| `RQ-PROC-01` | **Implemented with residuals.** | Accepted `0040-05` process plus `0040-08` pilot; disposition is effective for declared reach, not escape-proof. |
| `RQ-PROC-02` | **Implemented.** | Qualifying gate scope requires a named conforming decision before mutation. |
| `RQ-PROC-03` | **Implemented.** | Distinct management-instantiated Architect support required before qualifying mutation. |
| `RQ-PROC-04` | **Implemented.** | `AGENTS.md` permits bounded `[p]` preparation and `[u]` only at the remaining authority-only boundary. |
| `RQ-ROLE-01` | **Implemented after premise correction.** | Repository has two capability classes, not three; `process-roles.md` separates capabilities and responsibilities with a restrictive mapping. |
| `RQ-ROLE-02` | **Implemented with deliberate tailoring.** | Three assigned roles, two ungated functions, Management outside the agent role model; uncovered responsibilities are explicit. |
| `RQ-ROLE-03` | **Implemented through personas.** | Five actionable personas in section 6 of `process-roles.md`; separate briefing files were rejected as duplicate authority surface. |
| `RQ-ROLE-04` | **Implemented.** | TK-1, TK-2, mapping, incompatibilities, and “privilege is not independence.” |
| `RQ-STD-01` | **Partially implemented and deliberately tailored.** | The intake retains the detailed provisional ASPICE mapping; `process-roles.md` carries focused SUP.8 and SWE.4/SWE.6/SYS.5 references plus the terminology boundary. The unbounded campaign to add references throughout all process documents was rejected, and `decision-record.md` itself carries no ASPICE citation. No broader implementation is claimed. |
| `RQ-STD-02` | **Implemented.** | Explicit “process support, not assessed capability” boundary and separation from ECU Features `0011`–`0032`. |
| `RQ-EFF-01` | **Deliberately deferred by customer; still open with durable reciprocal owner.** | `DEC-0040-006` binds the deterministic population, activation reference, counts, quality/latency context, conclusion rule, and `docs/dossiers/0039-01-effectiveness-measurement.md` to `0039-01`; its `[u]` reservation remains unchanged. |

**Aggregate requirement verdict:** Every ID has a truthful disposition.
Four traceability requirements and the effectiveness requirement remain open,
but their reciprocal downstream assignment is now authorized and recorded by
`DEC-0040-006`; none is misreported as implemented.
`RQ-STD-01` is only partially implemented after deliberate tailoring.
`RQ-DEC-02` has two visible historical authority defects. This is complete
disposition, not complete downstream implementation.

## 4. Decision and authority analysis

### 4.1 `DEC-0040-001` — incomplete waiver

The provisional waiver authorizes this Feature owner to combine normally
separated work, but it has no duration. `PRIVILEGED.md` and
`decision-record@v1` require a start and an end/event. Only the granting current
user may provide the missing duration, replace the waiver, or revoke it.

The incomplete waiver was **not used for self-acceptance**:

- `0040-05` was accepted by
  `authority:current-user:0040-05-review:20260818T174212Z`, not by the agent;
- `0040-09` has no Acceptance yet;
- all other Feature Tasks are not checkpoints and carry no Acceptance.

The aggregate review still needs a management decision on duration/revocation
because the Feature contract and final integration mention this waiver.

### 4.2 `DEC-0040-005` — invalid agent-as-Management identity

The record is structurally `decision-record@v1`, but it says:

- deciding identity: `agent:zed:0040-05:...`;
- role: `Management`.

`process-roles.md` says Management is the current user or a registered authority,
never an agent. The current user later approved the five substantive questions
and the exact `0040-05` baseline, so the rule has explicit user support. That
later acceptance does not silently repair the earlier decision record. The user
must explicitly ratify the underlying scope decision as Management or reject it.
A ratification will be append-only and will not rewrite the false historical
role entry.

### 4.3 `DEC-0040-10-001` — truthful legacy incompleteness

This scope decision predates `decision-record@v1`. Task `0040-09` adds
`DEC-0040-10-001-LM001` in its existing dossier. The map is:

- structurally `legacy-structurally-nonconforming`;
- semantically `incomplete` at `Role` and `Review.Participation`;
- explicit that implementation peer review was not decision-scope review;
- not a correction, authority grant, or v1 upgrade.

The concrete safety repair remains objectively green. The map prevents the
aggregate review from presenting the historical scope authority as complete.

### 4.4 Cross-item contract mutation caught and rolled back

The first aggregate remediation attempted to add reciprocal requirements to
`0037-17.02`, `0037-17.03`, `0037-10.04`, and reserved `0039-01`. Independent
review session `69cc599c-eaf8-4856-a42a-0ec4c39ee4c2` correctly found that this
changes foreign acceptance/closure contracts. The accepted rule covers both
blocking gates **and contract changes**; absence of executable code does not make
the mutation local.

The attempted edits were uncommitted and were rolled back to the Feature-input
bytes. The current user then explicitly selected Variant A and rejected B/C. A
distinct non-privileged Architect reviewed the exact partition and returned
`supports` with the scope conditions below. `DEC-0040-006` was recorded in full
before the contract mutation, and only then were the four Task contracts changed.

Alternatives presented for that decision were:

- **A — selected recommendation:** bind all four traceability requirements to
  the three existing `0037` Tasks and bind the 20-Task effectiveness measurement
  to `0039-01`, with the exact partition, tests, evidence path, and maturity
  conditions now recorded in `DEC-0040-006` and the four `TODO.md` contracts.
- **B — retain one-way deferral only:** leave foreign contracts unchanged. This
  avoids cross-item mutation but leaves Feature `0040` without durable reciprocal
  ownership and was the original aggregate audit finding.
- **C — create new downstream Tasks:** avoids modifying existing contracts but
  duplicates already planned `0037` capabilities and adds backlog surface.

Other gate findings remain as before: `0040-05` has a decision and Architect
review but needs Management ratification; `0040-10` has a truthful incomplete
legacy map; `0040-03` wires no validator; no traceability tool was added to
`_src/validate.py`. No other undisclosed Feature `0040` gate or contract mutation
was found.

### `DEC-0040-006` — Bind deferred traceability and effectiveness requirements to existing downstream Tasks

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T18:57:57Z`
- **Deciding identity:** `authority:current-user:0040-09-variant-a:20260818T185757Z`
- **Role:** `Management`
- **Authority reference:** `TODO-zed-0040-09-20260818T180401Z-760531d011eb.md#management-decision-on-foreign-task-contracts`
- **Subject:** Reciprocal downstream ownership and completion contracts for deferred Feature `0040` traceability and effectiveness requirements
- **Decision:** Apply Variant A. Bind `RQ-TRACE-01` and the structural mapping/finding portions of `RQ-TRACE-02/04` to `0037-17.02`; bind query realization of `RQ-TRACE-02/03/04` at file and commit level to `0037-17.03`; bind CLI exposure of those query requirements to `0037-10.04`; and bind the deferred 20-Task `RQ-EFF-01` measurement to reserved `0039-01`. Preserve the existing Feature `0037` source/index/query/CLI layering, the `0039-01` reservation, and the absence of line/symbol completion gates or a new blocking validator. Apply the exact scope conditions and contract text supported by the distinct Architect review recorded as `PART-01`.
- **Technical justification:** The requirements otherwise have only one-way deferral from Feature `0040`, so a later implementer can complete the named downstream Tasks without proving the customer-requested file/commit trace or effectiveness measurement. The selected existing Tasks already own immutable provenance indexes, forward/reverse queries, CLI exposure, and standard-process metrics, respectively. Partitioning the requirements across those layers avoids a duplicate legacy trace tool and avoids creating new Tasks, while explicit reservation and read-only boundaries prevent implied process adoption or a new repository-wide gate.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Variant A — add partitioned reciprocal bindings to the existing three Feature `0037` Tasks and deferred measurement ownership to reserved `0039-01`
    - **Disposition:** `selected`
    - **Reason:** The current user explicitly confirmed Variant A; it creates durable ownership without duplicating existing architecture and is supported by the distinct Architect subject to the recorded boundaries.
  - **ALT-02:** Variant B — retain only one-way deferral in Feature `0040`
    - **Disposition:** `rejected`
    - **Reason:** The current user explicitly rejected it; it leaves downstream completion contracts free to omit the deferred customer requirements.
  - **ALT-03:** Variant C — create new downstream Tasks
    - **Disposition:** `rejected`
    - **Reason:** The current user explicitly rejected it; it duplicates capabilities and adds backlog surface where suitable owners already exist.
- **Consequences:**
  - **CON-01:** `0037-17.02`, `0037-17.03`, and `0037-10.04` receive stronger completion contracts and can delay their parents and Feature `0037` closure when the new evidence/index/query/CLI tests do not pass.
  - **CON-02:** Required trace depth is file and commit level; line and symbol identity, movement, freshness, and completion gates are excluded.
  - **CON-03:** No new `_src/validate.py` or repository-wide blocking gate is introduced; any later enforcement widening requires a separate TK-2 decision.
  - **CON-04:** `0039-01` remains `[u]` and reserved; this decision changes only its future contract and does not assign an owner, start work, approve the process, or satisfy `RQ-EFF-01`.
  - **CON-05:** `0040:0039-01` remains a Feature-closure gate unless Management separately replaces it; Variant A alone does not close Feature `0040`.
  - **CON-06:** The 20-Task measurement needs an explicit authority-activation reference. If no such reference exists or fewer than 20 qualifying Tasks exist, it records `not-yet-mature` and cannot claim effectiveness; this prevents a hidden activation/measurement deadlock.
  - **CON-07:** The Feature `0037` architecture/review package must incorporate these contract deltas before any exact downstream approval relies on a stale digest.
- **Affected work units:**
  - `task:0037-17.02`
  - `task:0037-17.03`
  - `task:0037-10.04`
  - `task:0039-01`
  - `feature:0037`
  - `feature:0039`
  - `feature:0040`
- **Affected gates:**
  - `task-start:0037-17.03`
  - `task-start:0037-10.04`
  - `feature-closure:0037`
  - `feature-closure:0039`
  - `feature-closure:0040`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:zed-subagent:architect:0040-09:92c2b6fb-e4f1-40b1-a6d8-3130aa552ea7`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Supports Variant A only with collective rather than duplicated ownership; immutable-source writing stays in `0037-17.01`, index representation in `0037-17.02`, read-only file/commit query semantics in `0037-17.03`, and CLI delegation in `0037-10.04`. Requires explicit missing/dangling/redacted behavior, renamed-file history, no line/symbol gate, no new blocking validator, unchanged markers/prerequisites/checkpoints, preserved `0039-01` reservation, deterministic 20-Task population and activation reference, and visible continued `0040` closure blocking.
- **Waiver:** `none`

The current user supplied the Management selection before mutation:

> Ich bestätige Variante A. Die anderen Varianten habe ich gelesen und verworfen.

The distinct non-privileged Architect review session
`92c2b6fb-e4f1-40b1-a6d8-3130aa552ea7` returned `supports` before mutation. This
review is scope authority only; it is not implementation validation or Acceptance.

## 5. Reconciliation changes made by `0040-09`

Completed deterministic aggregate repairs:

1. Reconciled the stale `0040-01` Task title, context, criteria, and Feature DoD
   to the already approved trilateral model: two capability classes, restrictive
   mapping, three roles, two functions, Management outside.
2. Corrected the Feature baseline count from 17 to 20 without changing any ID.
3. Added the truthful legacy-map disposition for `DEC-0040-10-001`.
4. Recorded current-user decision `DEC-0040-006` and the supporting distinct
   Architect review before foreign contract mutation.
5. Added partitioned reciprocal `RQ-TRACE-01`…`04` bindings to `0037-17.02`,
   `0037-17.03`, and `0037-10.04`, including file/commit depth and no line/symbol
   gate.
6. Bound deferred `RQ-EFF-01` measurement/evidence ownership to reserved
   `0039-01`, including activation/maturity/deadlock handling.
7. Created this requirement, authority, drift, residual, claim, and validation
   package.

No active claim is recorded for those foreign Tasks. Disjoint scope alone was
not treated as authority: the initial attempt was rolled back, and the final
mutation follows `DEC-0040-006`. Feature `0039` remains `[u]` and reserved.

## 6. `0040-05` accepted-baseline drift analysis

### 6.1 Pinned acceptance

The accepted review package binds:

- candidate tip `1f9583ad1d8f1f76e3a6050cb14be510ed125801`;
- substantive REF `f06867e06529469e26452e9cf20d362eb0d9648e`;
- `TODO.md` SHA-256
  `996d776b4aa1c9f4d1e11ce4f8ea4d7cca21313c4f9645370824e7ce077d3b79`;
- `AGENTS.md` SHA-256
  `bb08ff0afecde62293f543823d26ed0526676b3a2dfb865e6bd7868561352b36`;
- `docs/pipeline/process-roles.md` SHA-256
  `13d3c8e67cdca10c5b4f7c8e4f48c06b41627b170c7b38f84ea32960a9670fd1`;
- `docs/dossiers/0040-05-cross-item-scope-review.md` SHA-256
  `9e600cf244c8f31c281fbd69c6501aadd09052340a8cef499adcfc80d2379b20`;
- its claim SHA-256
  `0a2af71964bbcefcb672241134c3c482b664b3f707f3467c62321946ee3271d3`.

### 6.2 Drift before aggregate remediation

At Feature input tip `86e285435e305a1e5c98fbb7aa1634bb3d9d8563`, the
`TODO.md` digest was
`259c1e4c98606c737a5e1ab24f1e9330e675d296b4a9f3f0de4a00ddef6f2aaf`.
At Task `0040-09` start commit `5d5388a53`, it was
`b64f2536f81065d2cd8d94786c8267679825346da8bf38852e9b9b1986b0337d`.
Within the accepted five-file work-product manifest, the exact diff from the
accepted candidate to the Task start changed only `TODO.md`. Repository-wide,
that interval also added the separate acceptance evidence, pilot artifacts, and
aggregate claim; those are outside the five-file manifest and are reviewed in
sections 2, 7, and 8:

- added the user-approved `0040-05` Acceptance block;
- closed and documented downstream pilot `0040-08`;
- opened and claimed aggregate Task `0040-09`.

The four other accepted work-product bytes remained exact. No accepted rule,
trigger, negative boundary, Architect/Implementer separation, or scope-review
record changed.

### 6.3 Aggregate-remediation drift

The current pre-review `TODO.md` digest after completed section 5 repairs,
rollback of the first unauthorized attempt, `DEC-0040-006`, Architect review,
and authorized reapplication is
`49a91ac711ffb8d363b338df85d93f8cafdfc643f6e5ccbed4851b82936c705f`.
The changes reconcile the approved `0040-01` contract, correct the requirement
count, and add the separately authorized downstream contracts. They do not alter
the `0040-05` Task contract or any of its four unchanged rule/evidence files.

**Impact verdict:** non-material to the accepted `0040-05` behavior and review
questions. The digest drift is real and retained; it does not silently extend
that acceptance to unrelated later work. The user is asked to confirm this
impact analysis as part of the aggregate review.

## 7. Retrospective residuals and owners

| Residual | Current disposition and owner |
|---|---|
| `RES-01` undeclared/misclassified reach | The aggregate itself initially misclassified foreign contract edits as non-gating; peer review caught them, they were rolled back, and `DEC-0040-006` plus distinct Architect review preceded the final mutation. `0039-01` now owns future structural/missed-trigger evidence. |
| `RES-02` no automatic `decision-record@v1` enforcement | Still open. `0037-10.03`/`.04` remain future enforcement/CLI owners; this Feature does not pretend Markdown is automatically enforced. |
| `RES-03` passive inheritance excluded | Deliberate limitation retained. `0040-10` repaired the concrete incident; `0039-01` now owns legacy-gate discovery in its migration/change-control design. |
| `RES-04` distinct Architect may still make a poor call | The final aggregate review remains active. `0039-01` now requires quality context—missed triggers and later reversals—alongside adoption counts. |
| `RES-05` authority assignment may stall | Demonstrated and resolved for this mutation. `0039-01` now requires `[u]` authority-wait duration/outcome context. |
| `RES-06` persistent path ownership incomplete | Concrete host findings fixed by `0040-10`; `0039-01` now owns the broader migration/role/action/change-control disposition. |

No residual reopens or changes historical Task `0038-03`.

## 8. Claim reconciliation inventory

Claims carried on the Feature branch:

| Claim | Current recorded state | Reconciliation after accepted aggregate integration |
|---|---:|---|
| `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md` | `[p]` temporary intake coordination | Reconcile the completed intake and review decisions into this package/authoritative Task history, then remove as predecessor coordination provenance. Its immutable token is not rewritten. |
| `TODO-zed-0040-10-20260818T141307Z-894c3cd8b63b.md` | `[x]` | Remove after its progress/evidence/REF and legacy decision disposition are confirmed in authoritative records. |
| `TODO-zed-0040-03-20260818T154851Z-1d9d90dcf61d.md` | `[x]` | Remove after decision-contract evidence and REF are confirmed. |
| `TODO-zed-0040-05-20260818T162728Z-4c98b6072815.md` | `[x]`, stale text says checkpoint pending | Preserve the stale historical statement as provenance until aggregate acceptance; then remove after the separate accepted review is confirmed in `TODO.md` and `docs/pipeline/approvals/0040-05-review.md`. Do not rewrite history to pretend it predicted acceptance. |
| `TODO-zed-0040-08-20260818T174425Z-831efc7727f6.md` | `[x]` | Remove after pilot result, residuals, and REF are confirmed. |
| `TODO-zed-0040-09-20260818T180401Z-760531d011eb.md` | `[p]` | Remains active through user review; reconcile at accepted aggregate integration/Feature handoff according to the final closure path. |

No claim files ever existed for `0040-01`, `0040-02`, `0040-04`, `0040-06`, or
`0040-07`. None will be invented retroactively.

The legacy doctor currently reports four Feature-local errors, exactly the four
terminal predecessor claims (`0040-10`, `0040-03`, `0040-05`, `0040-08`). This
is expected under the branch workflow: the Integrator removes carried claims
only after aggregate acceptance. Removing them before review would erase the
recovery path.

## 9. Validation

Validation against the remediated candidate before the package commit:

| Check | Result |
|---|---|
| Full automation-safety scan | **PASS.** 71 findings: 35 critical, all disposed; 36 high; zero unresolved critical; zero policy errors. First 120-second attempt timed out with an empty output file; bounded retry completed within 300 seconds and is the claimed result. |
| Focused parallel-link test | **PASS.** Direct test execution ran 1 test successfully. An earlier `python -m unittest <path>` invocation failed because the path was parsed as an empty module name; this was an invocation error, not a test failure. |
| Added legacy-map JSON/shape check | **PASS.** Two JSON blocks parse, both have the exact 15 semantic keys, and only `role` and `review_participation` are null as declared. |
| `git diff --check` | **PASS** before package creation; rerun required before commit. |
| Editor diagnostics for `TODO.md` | **PASS:** no errors or warnings. |
| Global legacy doctor | **NON-PASSING:** 383 findings (259 errors, 124 warnings). Four findings mention Feature `0040`; all four are the expected terminal predecessor claims retained until aggregate acceptance. No clean global result is claimed. |
| Full `_src/validate.py` | **NON-PASSING:** completed with exit 1 and reported 12 dead internal links from `curation-report.html` and `open-reviews.html` to missing retained logs under `_src/logs/validate-review-request-ui/20260815-154824/`. Those paths are outside Feature `0040`; no full-project pass is claimed. |
| REF reachability | **PASS:** all Task/review commit objects in section 2 resolve; final ancestry and candidate manifest are rechecked after commit. |

The final pre-commit validation reruns `git diff --check`, focused link/path
checks for this package, automation safety if any scanned bytes changed, and REF
ancestry. Results are appended to the Task claim and authoritative completion
record, not retroactively invented here.

## 10. Feature closure prerequisite

Feature `0040` declares:

```text
PREREQ: 0040:0039-01
```

Task `0039-01` remains `[u]` under an explicit reservation. It is a substantial
standard-process Task with two pilots and independent review. Therefore:

- `0040-09` can be implemented and reviewed;
- its checkpoint can receive `Acceptance: ✓`;
- Feature `0040` still cannot move to `DONE.md` while that prerequisite remains
  unsatisfied.

Management must choose one path:

1. **Keep the prerequisite.** Release and complete `0039-01`; Feature `0040`
   waits for it.
2. **Replace the prerequisite with a downstream relationship.** Record that
   `0040` is the accepted focused process amendment and `0039-01` remains the
   later standardization/effectiveness owner; remove the closure gate by an
   explicit management decision.
3. **Reject or redesign the relationship.** Aggregate review becomes
   inconclusive until the replacement is defined.

No agent may infer this decision merely from the desire to finish the Feature.

## 11. Management review questions

The pre-mutation question is resolved: the current user selected Variant A,
rejected B/C, and the distinct Architect returned `supports`; see
`DEC-0040-006`. The remaining questions apply to the final pinned candidate:

1. **Waiver:** What is the exact end of `DEC-0040-001`, or is it revoked/replaced?
   A valid answer is an ISO-8601 end timestamp or a stable end event such as
   aggregate acceptance of `0040-09`.
2. **Decision authority:** Do you ratify the substantive decision in
   `DEC-0040-005` as your own Management decision, while preserving the original
   false agent-as-Management entry as history? If not, what is corrected or
   rejected?
3. **Drift and residuals:** Do you accept the section 6 non-material drift
   analysis and the disclosed incomplete legacy map/residual ownership?
4. **Aggregate verdict:** Is the pinned `0040-09` baseline `accepted`,
   `rejected`, or `inconclusive`?
5. **Closure path:** Keep `0040:0039-01` and release/complete `0039-01`, or replace
   it with an explicit downstream relationship so Feature `0040` may close?

Until all required answers are explicit, no aggregate Acceptance, claim removal,
upward integration, or Feature move is performed.

## 12. Verbatim user provenance relevant to this integration

> Du agierst jetzt als Projektmanager in meinem Auftrag. Analysiere die Abhängigkeiten innerhalb des Feature 0040 und versuche es zum Abschluss zu bringen. Du darfst dafür nicht-privilegierte Subagenten starten. Zu den Reviews mich dann bitte dazuholen.

> Alles klar. Zu den fünf oben genannten Fragen: alle ja. Die gepinnte Baseline ist von mir freigegeben.

> dann los

> Ich bestätige Variante A. Die anderen Varianten habe ich gelesen und verworfen.

The first prompt assigns project management and review facilitation. The second
is the exact `0040-05` checkpoint decision and does not silently answer the new
aggregate questions in section 11. The third triggers continued execution. The
fourth is the Management selection recorded by `DEC-0040-006`; it rejects the
two alternatives but does not answer the later aggregate Acceptance or closure
questions.
