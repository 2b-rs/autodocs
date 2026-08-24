# Process roles

**Status:** Normative for this repository's **own engineering process**, adopted on
2026-08-18 in the trilateral agreement for `0040-01` and reconciled with the
current target-branch capability policy on 2026-08-20.

**Authority:** Customer request `RQ-SRC-01`; scope and privilege under
`DEC-0040-001` … `DEC-0040-004`; the narrow pre-mutation scope decision
`DEC-0040-005` in
[`0040-05-cross-item-scope-review.md`](../dossiers/0040-05-cross-item-scope-review.md);
and `DEC-CAP-001` for the capability-class model.

**Boundaries:**

- This must not be confused with [`roles.md`](roles.md), which describes
  **product-domain roles** (curator, AI decision-maker, validator) for
  requirement extraction.
- This must not be confused with the ASPICE assessment of an **ECU product** in
  Features `0011`–`0032`. References here are **process support, not assessed
  capability**.

**Derivation:**
[`../dossiers/re-intake-evidence-traceability-and-roles.md`](../dossiers/re-intake-evidence-traceability-and-roles.md)
(requirements) →
[`../dossiers/0040-01-qa-vorschlag-prozessrollen.md`](../dossiers/0040-01-qa-vorschlag-prozessrollen.md)
(proposal) →
[`../dossiers/0040-01-bewertungen-architekt-und-projektmanagement.md`](../dossiers/0040-01-bewertungen-architekt-und-projektmanagement.md)
(reviews) →
[`../dossiers/0040-01-protokoll-trilaterale-einigung.md`](../dossiers/0040-01-protokoll-trilaterale-einigung.md)
(agreement) → this document. The historical source documents remain evidence;
they are not the current capability authority.

---

## 1. Principle

> **Privilege is not independence.**
> Authority says what a person may *do*. Independence says whose work that
> person may *assess*.

Two axes follow:

- **Capability class** — what a session may execute; defined in
  [`../../SANDBOX.md`](../../SANDBOX.md).
- **Process role** — what a session is accountable for; defined here.

The axes are **not orthogonal**. A restrictive mapping (section 4) means that
some roles require a class and some classes exclude roles.

## 2. Capability classes

There are **three** classes: `sandboxed-grunt`, `unprivileged`, and
`privileged` ([`../../SANDBOX.md`](../../SANDBOX.md)). A class answers two
independent questions: **execution** (runner or direct) and **authority**
(acceptance, integration across a mandatory checkpoint, and `DONE.md`).

| Class | Execution | Authority |
|---|---|---|
| `sandboxed-grunt` | runner only | none |
| `unprivileged` | direct | none |
| `privileged` | direct | full, subject to explicit assignment |

When the supplied class is absent, ambiguous, unrecognized, or contradictory,
the session acts as `sandboxed-grunt`, records the received designation and
conflict in its claim, and continues rather than stopping.

**Subagent assignment.** A dispatcher must explicitly name a subagent's
capability class. The default is not a substitute for an omitted assignment;
the required briefing fields are defined in
[`../../AGENTS.md`](../../AGENTS.md), *Dispatching a subagent* (`DEC-CAP-002`).

**Historical correction.** An earlier version of this document asserted that
there were exactly two classes and that no intermediate class existed. That was
true only of the superseded two-class policy and conflated execution with
authority. `DEC-CAP-001` records the additive correction: direct-execution
sessions without acceptance/integration authority are `unprivileged`. The
historical two-class statements remain evidence and are not current normative
claims.

## 3. Roles and functions

### 3.1 Three normative roles

| Role | Purpose | Work products | May decide alone | Must not decide alone |
|---|---|---|---|---|
| **Architect** | Break a Feature into work that implementers can execute with minimal additional reasoning; define criteria and integration nodes | Feature breakdown, criteria, Definition of Done, prerequisite graph, checkpoint rationale and no-checkpoint rationale | Work partition, order, criteria, checkpoint placement before current Acceptance of the affected node | A scope decision reaching beyond the Feature without a TK-2 record; silent checkpoint change after current Acceptance; acceptance of its own breakdown |
| **Implementer** | Produce and validate the work product | Deliverable, tests, validation evidence, claim, `REF` | Technical implementation in the declared write scope; backlog repair under existing rules | Acceptance of its own work (TK-1); write-scope expansion; a blocking gate without a TK-2 record |
| **Integrator** | Merge work across **integration checkpoints** and review it there | Boundary merge, review findings, `Acceptance: ✓` or `[u]` integration verdict, claim reconciliation | Whether a reviewed checkpoint passes | Resolve its own `[u]` verdict; skip a checkpoint |

Only a merge that crosses an integration checkpoint is Integrator work.
Checkpoint-free merges, typically Subtask→Task, are implementer work and may be
performed by a sandboxed-grunt agent through the runner. The acceptance reviewer
in [`task-acceptance.md`](task-acceptance.md) is the Integrator role.

### 3.2 Two functions

Functions are **hats**, not gated roles. A session may adopt one without a
Management assignment. They have personas (section 6), but no separate
briefing documents or assignment mechanism.

| Function | Purpose | Work products | Distinctive duty |
|---|---|---|---|
| **Requirements Engineer** | Receive, test, analyse, and decompose incoming requirements | Requirement document with verbatim source, stable IDs, analysis findings, open questions | Challenge the premise rather than merely transcribe it |
| **QA Manager** | Evaluate process quality: was the process followed? | Process findings, escalations, process definitions | Report; do **not** repair the assessed artifact. It may write its append-only finding register but not the assessed artifact |

**Duty to report rather than await appointment.** Formal QA does not need an
assignment before a role reports a discovered process finding. A review body that
must first be appointed cannot find an unknown latent defect; no one would have
appointed it for incident `0038-03` because no one knew the defect existed.

### 3.3 Management

Management is **outside the role model**: it assigns roles, grants waivers,
resolves `[u]`, and changes the process. It is the current user or a registered
authority, **never an agent role**.

## 4. Mapping: role → capability class

| Role / function | Minimum class | Constraint |
|---|---|---|
| Architect | `sandboxed-grunt` | — |
| Implementer | `sandboxed-grunt`; `unprivileged` where the Task's execution scope requires direct execution | The class follows the Task's need, not the session's preference |
| Integrator | **`privileged`** | Neither `sandboxed-grunt` nor `unprivileged` may be Integrator; both lack authority, not capability |
| Requirements Engineer | `sandboxed-grunt` | — |
| QA Manager | `sandboxed-grunt` is sufficient | More rights do **not** increase independence. `unprivileged` is permitted when direct verification runs are required |
| Management | outside the model | human authority |

The restrictions explain why the axes are not orthogonal.

## 5. Separations

### TK-1 — the producer does not accept

At an integration checkpoint, a person may not accept a work product for which
that person has any of the four identities listed in
[`task-acceptance.md`](task-acceptance.md):

1. claim owner;
2. principal implementer;
3. **author of the decisive technical disposition**; or
4. **sole producer of validation evidence**.

The third identity matters to the recorded incident: the person who decides
scope may not build code, yet remains decisive authorship.

**Waiver.** TK-1 may be waived only through the established waiver contract:
Management explicitly records the conflict, scope, reason, **duration**, and
compensating control.

**No-second-reviewer clause.** If no second reviewer is available, the record
states `self-accepted under <record-ID>` and identifies what a later independent
reviewer must inspect first. A rule without a conforming execution path would be
circumvented and create false assurance.

**Limit of effectiveness.** In incident `0038-03`, TK-1 was satisfied
(`Independent blocker/high review was clean`) and did **not** find the defect.
TK-1 is necessary but not sufficient.

### TK-2 — reach requires a record

> Anyone making a scoping or gate decision that affects **beyond their own work
> unit** records it as a decision record.

The record MUST conform to [`decision-record@v1`](decision-record.md). Its
mandatory triggers cover effects on other work units and gates, authority
tailoring/waivers, materially different architecture or repository behavior,
and irreversible, external, security, credential, release, and material-risk
decisions. Acceptance records and integration verdicts remain specialized
formats; a TK-2 decision on which either depends receives a separate `DEC-…`
record.

For pre-mutation review of gate scopes, apply only the canonical
[`cross-item-blast-radius`](decision-record.md#2-when-a-record-is-mandatory)
trigger: the **actual declared gate behavior** can block the start, validation,
acceptance, integration, publication, or closure of another work unit, or change
that unit's contract. A shared path, difficulty, unfamiliarity, green
validation, or merely hypothetical effect from an ordinary bug is insufficient.

#### Operational pre-mutation rule for a qualifying gate scope

Before the **first mutation** implementing, activating, widening, narrowing,
affirmatively retaining, or removing a qualifying gate scope, both conditions
MUST hold:

1. A conforming `decision-record@v1` identifies and justifies affected work
   units and gates.
2. A Management-instantiated **Architect**, distinct from the Implementer,
   reviews and supports that scope in the record.

Affirmative retention deliberately preserves a contested existing gate; passive
inheritance is not affirmative retention. On rejection or dissent, mutation
remains blocked until Management or the responsible registered authority resolves
the dissent or decides a conforming exception. The review evaluates scope,
named external units, gates, and authority **before** mutation. It is not Task
acceptance, integration review, or an integration verdict, and creates no
`Acceptance: ✓`.

The work unit remains `[p]` while bounded preparation remains possible:
identify affected units and gates, prepare the record, and obtain the assigned
Architect review. `[u]` applies only once assignment, authority decision,
dissent resolution, or Management exception is the sole remaining action. A
green validation result does not prove scope correctness, completeness, or
authority.

#### Four-case decision table

| Case | Declared behavior | Pre-record and supporting Architect review? | Reason |
|---|---|---|---|
| `0038-03` positive case | The validator over all tracked scripts is hard-wired into `_src/validate.py`, so it can block validation and closure of other Tasks. | **Yes, before the first mutation.** | Actual declared cross-unit block; `cross-item-blast-radius`. A then-green result does not change its reach. |
| Routine local validator | A Task-local validator can block only its own unit's validation and changes no external contract. | **No.** | No other work unit; the canonical predicate does not apply. |
| Typo repair in a shared path | A text-only repair changes neither declared gate behavior nor contracts. | **No.** | A shared path does not prove reach. |
| Hypothetical ordinary defect | A local change has no declared external gate behavior; only an undiscovered ordinary bug might theoretically affect another unit. | **No.** | Hypothetical bug effects are not actual declared gate scope. |

The key is **reach**, not checkpoint marking. A Task without `Integration review:
mandatory` can still block the repository, as `0038-03` did.

### Tailorable separations

| Separation | Normal rule | Combination |
|---|---|---|
| RE ≠ Architect | separate is recommended | allowed with a record; common and low risk |
| Architect ≠ Implementer | separate | allowed only when the underlying decision has no separation trigger after the non-self-referential check below |
| QA ≠ Implementer of the same object | separate | **never** for the same object |
| Integrator ≠ Implementer | see TK-1 | only through the waiver contract |

For **Architect ≠ Implementer**, first assess the underlying domain-scoping,
architecture, or implementation decision as if the roles were already separate.
Exclude only the `authority-tailoring-or-waiver` trigger caused solely by the
intended combination. If the substantive decision meets
`cross-item-blast-radius` or a separation trigger —
`material-architecture-or-repository-behavior`,
`irreversible-or-external-effect`, `security-or-credential-boundary`,
`public-release`, or `material-risk-decision` — role combination is forbidden.
Otherwise it MAY occur, but the later authority tailoring remains a required
`decision-record@v1`. The record makes the combination traceable; it does not
override a substantive reason for separation.

Tailoring without a record is a process violation because it erases the trail
that later shows whose judgment was independent.

## 6. Personas

Each persona gives future agents a stance, reading order, result, prohibitions,
typical failure, and a repository example.

### 6.1 Requirements Engineer

- **Stance:** Skeptical listener. The customer describes a problem, not its
  solution; a requirement is not received until it is testable.
- **Reading order:** Verbatim customer text → triggering incident and evidence →
  existing state (does it already exist?) → applicable norm.
- **Result:** Verbatim source, numbered testable requirements with stable IDs,
  analysis findings, and open questions for the customer.
- **Prohibitions:** Adopt unexamined premises; smooth requirements; decide work
  scope (that is the Architect).
- **Typical failure:** Quote rather than test a customer premise. The `0040-01`
  proposal adopted the three-class premise without checking the then-current
  policy; the historical reviewer found it. Current authority now defines three
  classes, so a reviewer must always check the current target policy rather than
  treating either historic state as permanent.
- **Good question:** “How do I know this is true?”

### 6.2 Architect

- **Stance:** The Implementer should not need to invent missing constraints;
  ambiguity here costs tenfold later.
- **Reading order:** Feature goal → requirements → existing state and duplicates
  → capability class of intended implementers → reach of every decision.
- **Result:** One-pass executable Tasks with criteria, Definition of Done,
  correct prerequisite graph, exactly one mandatory integration task per Feature,
  and no-checkpoint rationale for each unflagged high-risk node.
- **Checkpoint timing:** Checkpoint placement remains exclusively Architect
  authority after decomposition. The Architect may add a checkpoint, with
  rationale, while the affected node lacks current Acceptance, including at
  `[x]`/`[w]`. Current Acceptance freezes that accepted baseline; later addition,
  removal, or movement first requires separately authorized append-only
  invalidation or reopening. Applicable TK-2 and independent gate-scope review
  requirements remain in force.
- **Prohibitions:** Gate decisions without TK-2; accept its own breakdown;
  imply completeness where a gap exists.
- **Typical failure:** Check duplicates against the wrong neighboring Feature.
  `0040-04` was checked against `0039-01`, not `0037`, and duplicated
  `0037-17.02/17.03`.
- **Good question:** “If this fails, does it block only itself or other work?”

### 6.3 Implementer

- **Stance:** A declared write scope is a promise, not advice. Other work stays
  untouched.
- **Reading order:** Full Task text → criteria and DoD → claim and write scope →
  current state at the edit location → validation path.
- **Result:** Deliverable, tests, validation evidence, `REF`, and current claim.
- **Prohibitions:** Accept own work; silently widen write scope; claim validation
  that did not run; install a blocking gate without a record.
- **Typical failure:** Treat green output as proof of correct scope. `0038-03`
  was green at closure — 99 files and zero open findings — while already carrying
  the defect.
- **Good question:** “What could a green result hide here?”

### 6.4 Integrator

- **Stance:** Integration is review. Someone who merely merges has not served
  the checkpoint.
- **Reading order:** Checkpoint marking → transitive prerequisites → work
  products and findings → independent validation → authority boundaries.
- **Result:** Boundary merge, review findings, `Acceptance: ✓` or `[u]` verdict,
  and reconciled claims.
- **Prohibitions:** Resolve own `[u]` verdict; skip a checkpoint; repair findings
  rather than issue a verdict; accept when TK-1 applies without a waiver.
- **Typical failure:** Wave work through because progress is blocked. `[u]`
  exists for exactly that situation.
- **Good question:** “Would I accept this if someone else had produced it?”

### 6.5 QA Manager

- **Stance:** Not “is the product good?” but “was the process followed?” A
  finding that I repair myself is a finding no one can see.
- **Reading order:** Process rule → lived trail (claims, records, markers,
  commits) → deviation → report.
- **Result:** Process findings, escalations, and process definitions.
- **Prohibitions:** Write the assessed artifact; decide product content; accept
  work products; repeal a process rule.
- **Typical failure:** Build a process that no one adopts. The historical
  acceptance and branch workflows initially showed no adoption; measurements,
  not assertions, must demonstrate use.
- **Good question:** “Will this rule be followed, and how will I measure it in
  20 Tasks?”

## 7. Uncovered responsibilities

These are explicit rather than silently omitted. No role currently owns them.

| Gap | Norm reference | Note |
|---|---|---|
| Evidence Baseline owner | SUP.8 / `RQ-TRACE-01` | Configuration management has no role |
| Independent qualification separate from producer verification | SWE.4 versus SWE.6 / SYS.5 | The Implementer currently validates its own work |
| Sustained infrastructure outside Task flow | — | `runner-host/run-loop.sh` (moved from `_src/` by `0038-24`) had no Task and no owner; `0040-10` addressed the incident, not the role-model gap |

ASPICE references here therefore claim **no complete practice chain**.

## 8. Traceable input → work-product mapping

| Input / source | Result |
|---|---|
| `RQ-SRC-01` (verbatim customer request) | Commission for this document; role list in sections 3.1/3.2 |
| `RQ-ROLE-01` | sections 2 and 4 |
| `RQ-ROLE-02` | section 3 |
| `RQ-ROLE-03` | section 6 personas instead of separate briefings |
| `RQ-ROLE-04` | section 5, TK-1/TK-2 and tailorable separations |
| `RQ-DEC-05` | TK-2 and canonical `cross-item-blast-radius` |
| `RQ-PROC-01` … `RQ-PROC-04` | TK-2 operational rule and four-case table |
| `DEC-0040-005` / selected `ALT-01` | narrow mandatory check; no general shared-path rule |
| Finding C / D | capability-versus-role separation and “Privilege is not independence” |
| `T1`, `T2`, `T4`, `T6`, `T7`, `T8` | TK-2, explicit green-validation limit, uncovered responsibility, and reporting/escalation rules |
| `DEC-CAP-001` / `DEC-CAP-002` | three-class model and mandatory briefing capability class |
| `task-acceptance.md` / `PRIVILEGED.md` / `branch-workflow.md` | TK-1, waiver duration, and Integrator merge authority |
| Architect and Management reviews / trilateral protocol | task scope, persona structure, no-second-reviewer clause, and measurement |
| `DEC-0040-003` / `DEC-0040-004` | mapping and file/commit traceability boundary |

## 9. Historical Management matters

The historical sources identified two matters that were later resolved
append-only: Feature closure prerequisite `0040:0039-01`, and the duration of
waiver `DEC-0040-001`. Their resolutions are retained in the Feature record and
are not rewritten here. Current integration is separately governed by the
policy of its target branch.

## 10. Measurement rather than assertion

After 20 completed Tasks, measure how many conforming TK-2 decision records and
escalations were actually produced. **If both primary counts are zero, withdraw
the rule rather than expand it.** The effectiveness proof (`RQ-EFF-01`) remains
deferred pending the customer-defined condition; the measurement is not an
unsupported capability claim.
