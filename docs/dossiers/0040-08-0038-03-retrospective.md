# Task `0040-08` — retrospective pilot of `0038-03`

**Pilot scope:** Apply the process amended by Task `0040-05` retrospectively to
the historical intake and implementation of Task `0038-03`.

**Status:** Retrospective implementation evidence only. This document is not a
`decision-record@v1`, Task acceptance, an integration review, an integration
verdict, or `Acceptance: ✓`.

**Historical-state boundary:** Task `0038-03` remains closed exactly as recorded
in [`TODO.md`](../../TODO.md). This pilot does not reopen it, change it, replace
its historical reasoning, or claim authority over its implementation. Every
counterfactual statement below is labelled as such.

## 1. Evidence baseline and method

The pilot uses these current and historical sources:

- the Task `0038-03` entry and closure history in
  [`TODO.md`](../../TODO.md), including the 99-file green result;
- the chronological check-in provenance and handoff history in
  [`0038-03-20260816T224129Z.txt`](../../logs/check-in-provenance/0038-03-20260816T224129Z.txt);
- observations `T1`–`T8` and requirements `RQ-DEC-01` … `RQ-PROC-04` in the
  [requirements dossier](re-intake-evidence-traceability-and-roles.md);
- the current [`decision-record@v1`](../pipeline/decision-record.md), especially
  its closed trigger list and required record shape;
- the binding [cross-item gate-scope review exception](../../AGENTS.md) and the
  [process-role model](../pipeline/process-roles.md), including its four-case
  decision table; and
- [`DEC-0040-005`](0040-05-cross-item-scope-review.md), which selected the narrow
  pre-mutation rule used by this pilot.

The method is a chronological counterfactual: retain only facts evidenced by the
historical sources, apply the current rule at each point where it would have
been applicable, and do not backfill an identity, authority, decision,
alternative disposition, or review result that was not recorded at the time.

## 2. Chronological walk-through

### Step 1 — autonomous intake selected `0038-03`

After Task `0033-01` closed, the mandatory backlog scan selected `0038-03`; its
prerequisite `0038-01` was terminal. The historical claim described the intended
outcome as an automation-safety validator plus remediation of high-risk tracked
scripts. Selection of the Task alone would not yet have fired the narrow
`cross-item-blast-radius` trigger: difficulty, novelty, shared paths, and the
mere word “validator” are not sufficient.

**Amended-process state:** `[p]`. Ordinary intake, inventory, and bounded design
work may proceed.

### Step 2 — the proposed gate behavior became explicit before mutation

The first retained handoff says both that no `0038-03` substantive source
mutation had occurred and that the planned behavior was already known:

1. discover the live scan scope from Git-tracked automation paths;
2. scan the repository's tracked scripts rather than only Task-local files; and
3. integrate the checker into `_src/validate.py`.

This is the **exact trigger point** under the amended process. Once those three
properties were declared together, the proposed gate could block validation
and therefore closure of work units other than `0038-03`. That is actual
declared cross-item gate behavior, not a hypothetical effect of an ordinary
bug. It matches the positive `0038-03` row in the four-case table and triggers
`cross-item-blast-radius` before the first mutation implementing the scanner or
its `_src/validate.py` integration.

The trigger does not depend on knowing in advance that `_src/run-loop.sh` would
later fail. It depends on the declared reach of the gate. The same facts also
make `material-architecture-or-repository-behavior` a likely additional trigger
because repository-wide validation behavior was being established, but only
`cross-item-blast-radius` is needed for the mandatory pre-mutation scope review.

**Amended-process state:** remain `[p]`; qualifying mutation is now blocked until
both the decision record and distinct Architect review exist.

### Step 3 — bounded preparation remains allowed under `[p]`

The Implementer could continue all preparation that does not implement,
activate, widen, narrow, affirmatively retain, or remove the qualifying gate
scope. In this case that includes:

- inventorying candidate script paths and execution boundaries;
- identifying `_src/validate.py` as the affected validation gate;
- identifying `repository:autodocs`, `task:0038-03`, and relevant path-level
  subjects such as `path:_src/run-loop.sh` as affected scope;
- identifying the contemporaneous Tasks whose validation or closure would be
  affected, without using a vague “all Tasks” substitute where exact Task IDs
  were available;
- drafting, but not falsely labelling as conforming, the required decision
  record;
- collecting evidence about sandbox-internal automation versus the privileged
  host bootstrapper; and
- obtaining the assigned Architect's scope review.

Tests, parser experiments, or candidate analysis that do not mutate the
qualifying repository gate may also proceed if otherwise authorized. The
process therefore does not force an immediate user interruption merely because
the trigger was found.

### Step 4 — a pre-mutation decision record was required

A real record created at that time would have needed every field required by
`decision-record@v1`. The following is a **record-shape assessment, not a
historical decision record**:

| Required field or block | What was knowable at the pre-mutation point | What this retrospective must not invent |
|---|---|---|
| Stable `DEC-NNNN-NNN` ID and `Record format` | A repository-unique ID and `decision-record@v1` would have been required. | No retrospective ID is assigned. |
| `Recorded at` | It had to be a real ISO-8601 timestamp with timezone before qualifying mutation. | The historical sources do not supply the missing decision time. |
| `Deciding identity`, `Role`, and `Authority reference` | An immutable deciding identity, an allowed process role, and a real assignment or authority reference were required. | The Implementer's identity, capability class, or Git author is not silently promoted into decision authority. |
| `Subject` | Scope of the automation-safety gate over tracked scripts and its blocking integration into `_src/validate.py`. | No broader product or policy mandate is inferred. |
| `Decision` | The authorized scope and enforcement mode had to be selected before mutation. | The later implemented outcome proves what code did, not that an authorized pre-implementation selection was recorded. |
| `Technical justification` | The record had to explain why the selected paths, execution boundaries, rule profile, blocking severity, and project-validator coupling were appropriate. | A later green scan is not substituted for scope justification. |
| `Triggers` | At least `cross-item-blast-radius`; likely also `material-architecture-or-repository-behavior`. | No additional security, waiver, risk, or release trigger is asserted without evidence. |
| `Considered alternatives` | At least two alternatives, exactly one eventually selected, each with a reason. | No historical alternative disposition is reconstructed. |
| `Consequences` | Cross-Task blocking, policy maintenance, ownership, recovery, false-positive cost, and the effect of future script changes had to be stated. | Later consequences are not represented as foreknown facts. |
| `Affected work units` | At minimum `task:0038-03` and `repository:autodocs`, plus exact contemporaneous affected units and relevant path references. | Unverified historical Task lists are not fabricated. |
| `Affected gates` | At minimum `validation:_src/validate.py`; any closure gate claimed as directly affected had to be named precisely. | A generic “everything” gate is not used. |
| `Review participation` | The distinct Architect's identity, role, participation, position, and note had to be recorded. | No support verdict is attributed retrospectively. |
| `Waiver` | `none` unless a bounded exception was actually authorized with conflict, reason, scope, duration, and controls. | No waiver or management exception is inferred. |

The likely alternatives that a competent scope review should have made explicit
are listed below only as **counterfactual candidates**. They are not claims
about what the historical Implementer considered:

- **Candidate A — uniform repository-wide blocking gate:** scan all tracked
  automation with one rule/policy model and hard-wire the result into
  `_src/validate.py`. This is the behavior later implemented, but its historical
  implementation is not evidence of a valid recorded selection.
- **Candidate B — execution-boundary profiles:** keep tracked coverage but use
  separately justified profiles for sandbox-internal automation and the
  privileged host bootstrapper. This candidate is made plausible by `T3`; it is
  not asserted to have been considered historically.
- **Candidate C — staged enforcement:** begin with Task-local or advisory
  reporting, establish ownership and dispositions, and expand to a blocking
  repository gate only after scope review. This candidate would trade immediate
  enforcement for lower cross-item coupling.

A conforming record could only be completed after an authorized deciding
identity selected one alternative and stated the reasons and consequences. A
retrospective author cannot fill those authority-owned facts with `unknown`,
`TBD`, or hindsight.

### Step 5 — the distinct Architect makes the scope-review call

The management-instantiated Architect must have been a different identity from
the Implementer. The Architect's call was specifically to `supports` or
`opposes` the proposed reach after examining affected units, gates, execution
boundaries, and authority. It was not a code review, test review, Task
acceptance, integration review, or `Acceptance: ✓`.

The current evidence does not prove which verdict that Architect would have
returned. It does show what the review had to challenge: why a privileged host
bootstrapper with no Task or claim (`T3`/`T4`) was governed by the same blocking
profile as sandbox-internal automation, and what future edits would do to exact
dispositions and every consumer of `_src/validate.py`.

The Architect's participation does not by itself supply final decision
authority. The deciding identity and authority reference still had to be valid
in the record. If the Architect opposed the proposal, qualifying mutation would
remain blocked until Management or another registered authority resolved the
dissent or issued a conforming bounded exception. The Implementer could not
self-resolve the disagreement.

### Step 6 — `[u]` is conditional, not immediate

The Task would remain `[p]` while the affected-unit analysis, draft record, or an
already assigned Architect review could still progress. It would become `[u]`
only when Architect assignment, the authority decision, dissent resolution, or
a Management exception was the sole remaining action. This is the amended
cross-item exception to the historical autonomy rule represented by `T8`.

Consequently, the historical instruction that an ordinary drafting defect is
not a reason for `[u]` would no longer suppress this case. The reason is not that
this was a difficult drafting defect; it is that the declared gate behavior met
the canonical cross-item predicate. No qualifying mutation is permitted while
the pre-mutation gate remains unmet.

### Step 7 — implementation and green validation come only after scope authority

Historically, implementation proceeded through parser hardening, exact
hash-bound dispositions, tests, a live scan, and independent blocker/high code
review. The closed Task records a successful 99-file scan with 54 findings, 28
disposed critical findings, 26 advisories, zero unresolved or policy errors,
and a passing full `_src/validate.py`.

Under the amended process, those results are valuable implementation-verification
evidence, but they occur **after** the scope decision and Architect review. They
cannot retroactively satisfy either precondition.

The green result was insufficient for four independent reasons:

1. It proved consistency only against the then-current 99 files and policy
   bytes; it did not prove that the chosen population was the right population.
2. Exact evidence-bound dispositions can become stale after an in-scope file
   changes, which is what `T5` later demonstrated.
3. Zero unresolved findings says nothing about whether sandbox-internal and
   privileged-host automation should share one blocking profile (`T3`).
4. The independent blocker/high review examined implementation quality and was
   clean, yet the scope decision remained undocumented and unchallenged. That
   is direct evidence that implementation independence alone is not the
   distinct Architect scope review required by the amended process.

### Step 8 — the latent coupling became operational

Later on 2026-08-17, `_src/run-loop.sh` changed. The requirements dossier records
three stale policy entries and ten unresolved critical findings, blocking the
closure path of other Tasks (`T5`). It also records that the Architect role was
introduced only after the `0038-03` implementation (`T7`).

The amended process would not need to predict those exact later findings. It
would surface the defect earlier—at Step 2—because the blocking reach was
already declared. The pre-mutation record and distinct scope review would then
make the host boundary, ownership gap, future-change consequence, and chosen
enforcement alternative visible before the gate became repository behavior.

## 3. T1–T8 disposition under the amended process

| Observation | Retrospective result | Process disposition |
|---|---|---|
| `T1` repo-wide blocking scope | Detected at Step 2 before first qualifying mutation. | Fixed by `0040-05`'s canonical trigger and pre-mutation gate. |
| `T2` green result hid latent scope defect | Green remains implementation evidence only. | Fixed normatively by `0040-05`; scope authority precedes validation. |
| `T3` host and sandbox automation shared one yardstick | Not automatically rejected, but made an explicit scope-review question. | Decision and distinct Architect review required; actual host disposition was addressed by Task `0040-10`. |
| `T4` host file had no Task/claim owner | Exposed when affected paths and units are enumerated. | The concrete host gap was addressed by `0040-10`; persistent-infrastructure ownership remains an acknowledged role-model gap. |
| `T5` later edits blocked all closures | Recorded as a foreseeable consequence category, though exact future findings cannot be predicted. | Concrete damage addressed by `0040-10`; future qualifying changes remain subject to the pre-mutation rule. |
| `T6` no decision circumstances | A conforming record is mandatory before mutation. | Fixed by `0040-03` plus the operative gate in `0040-05`. |
| `T7` Architect introduced too late | A distinct, management-instantiated Architect must review before mutation. | Fixed by `0040-01`/`0040-05`; review quality remains a measured residual below. |
| `T8` autonomy rule suppressed escalation | The cross-item exception keeps preparation `[p]` and permits `[u]` at the exact authority-only boundary. | Fixed by the binding `AGENTS.md` exception introduced by `0040-05`. |

## 4. Residual escape paths

The amended process would have intercepted the declared `0038-03` design, but
it is not escape-proof. The following residuals are intentionally recorded
rather than argued away.

| ID | Residual escape or limitation | Effect | Existing owner or explicit follow-up |
|---|---|---|---|
| `RES-01` | **Undeclared or misclassified reach.** The trigger is applied to actual declared behavior. An Implementer who omits the repository-wide effect or incorrectly calls it Task-local may never request the Architect review. | A qualifying mutation can still begin without the process gate if the reach is hidden from every pre-mutation check. | Task `0040-09` must check that Feature `0040` introduced no blocking gate without an `RQ-DEC-05` record. Downstream Task `0039-01` owns machine-checkable structural rules, independent pilot review, and outcome-to-Task coverage for the standard breakdown process. Its pilots should measure missed-trigger findings, not only produced records. |
| `RES-02` | **No current automatic enforcement of `decision-record@v1`.** The Markdown contract is machine-checkable in principle, but this pilot found no implemented validator that prevents a malformed or missing pre-mutation record. | Compliance presently depends on agents and reviewers applying the rule correctly. | `0040-09` provides a manual aggregate check for this Feature. Downstream `0039-01` explicitly requires machine-checkable structural rules; future issue-store decision operations and validation are assigned to `0037-10.03`/`0037-10.04`. Until one of those paths enforces the contract, this remains open. |
| `RES-03` | **Passive inheritance is deliberately excluded.** An existing contested gate is not reviewed merely because unrelated work inherits it. | A latent legacy scope can remain in force until a Task affirmatively retains, changes, or removes it. | The concrete `0038-03` damage and host scope were addressed by `0040-10`. Downstream `0039-01` must disposition legacy-gate discovery in its migration/change-control design; the exclusion should remain visible rather than being reported as complete prevention. |
| `RES-04` | **A distinct Architect can still make a poor call.** Separation creates a challenge point but does not guarantee technical insight or a correct verdict. | A documented, independently reviewed scope may still be wrong. | `0040-09` re-examines the process coherently. Downstream `0039-01` requires independent review of two pilots. The 20-completed-Task measurement in `process-roles.md` should be supplemented in that review with scope-review findings and later reversals, because counting records/escalations alone measures use, not quality. |
| `RES-05` | **Authority assignment can stall.** When Architect assignment or dissent resolution is the sole remaining action, `[u]` correctly blocks mutation but does not guarantee a timely human response. | The defect cannot silently ship, but throughput can stop indefinitely. | This is not a safety escape; it is an operational limitation. Downstream `0039-01` owns metrics, exceptions, and improvement feedback. Measure `[u]` age and resolution outcome alongside the existing 20-Task record/escalation count. |
| `RES-06` | **Path ownership remains incomplete.** Naming `path:_src/run-loop.sh` exposes the absence of a Task/claim but does not by itself create durable ownership for infrastructure outside Task flow. | Future changes can again lack an accountable work-unit contract even when a gate record names the path. | `0040-10` fixed and dispositioned the concrete host-bootstrapper findings. `process-roles.md` still records persistent infrastructure ownership as an uncovered responsibility; downstream `0039-01` must address ownership in its migration, role/action, and change-control design. |

No residual above justifies reopening or changing `0038-03`. They are process
findings against the amended mechanism and its downstream standardization.

## 5. Criterion/evidence matrix

| Criterion | Evidence examined | Result |
|---|---|---|
| Walk the historical intake chronologically | `0038-03` provenance receipt, current Task history, and `T1`–`T8` | **Met.** Steps 1–8 separate intake, declaration, preparation, decision/review, implementation, green validation, and later failure. |
| Identify the exact pre-mutation trigger point | Planned Git-tracked scope plus `_src/validate.py` integration; canonical trigger; four-case table | **Met.** Step 2 identifies the point while the retained history still said no substantive mutation had occurred. |
| State the required record without inventing history | `decision-record@v1` fields and truthfulness rules | **Met.** Step 4 names all required blocks and leaves unavailable identity, authority, time, decision, and dispositions explicitly unassigned. |
| Identify likely alternatives without claiming they were historical | `T1`, `T3`, `T4`, `T5` and the implemented outcome | **Met.** Three counterfactual candidate alternatives are listed with no retrospective selection. |
| Identify the distinct reviewing role and authority boundary | `AGENTS.md`, `process-roles.md`, and `DEC-0040-005` | **Met.** Step 5 assigns the scope-review call to a distinct management-instantiated Architect and reserves final authority/dissent resolution appropriately. |
| Preserve bounded `[p]` preparation and conditional `[u]` | `AGENTS.md` cross-item exception and `DEC-0040-005` | **Met.** Steps 3 and 6 identify allowed preparation and the sole-next-authority-action boundary. |
| Explain why the 99-file green result was insufficient | `0038-03` closure, `T2`, `T3`, `T5`, and clean independent implementation review | **Met.** Step 7 distinguishes implementation verification from population, scope, and authority correctness. |
| Report remaining escape paths honestly | Current rule boundaries and Feature/downstream Task contracts | **Met with residuals.** `RES-01` … `RES-06` are mapped to `0040-09`, `0040-10`, `0039-01`, `0037-10.03`/`0037-10.04`, or an explicit measurement. |
| Do not reopen or alter `0038-03` | This dossier's historical-state boundary | **Met.** The pilot makes no foreign Task, code, policy, authority, or acceptance change. |

## 6. Unambiguous pilot disposition

**Disposition: `effective-for-declared-0038-03-scope-with-recorded-residuals`.**

Applied to the evidence actually retained from `0038-03`, the amended process
would have fired before the first qualifying mutation, while the Task was still
`[p]`. It would have required a conforming decision record and a scope review by
a distinct management-instantiated Architect before repository-wide blocking
behavior could be implemented. It therefore addresses the central `T1`/`T6`/
`T7`/`T8` failure chain and demonstrates pilot evidence toward `RQ-PROC-01`.

This is not an unconditional process success claim. Undeclared reach, absent
automatic enforcement, passive inheritance, review quality, authority latency,
and durable infrastructure ownership remain explicit residuals with the owners
and measurements listed above. The pilot creates no Acceptance claim and does
not alter the historical disposition of Task `0038-03`.
