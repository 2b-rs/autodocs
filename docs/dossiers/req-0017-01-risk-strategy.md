# Requirements — MAN.5 risk strategy (`0017-01`)

**Status:** Review-ready candidate; **not approved and not operative**.

**Item:** Task `0017-01` of Feature `0017`

**Process instance:** `MAN.5-sw-nokernel-1`

**Product:** `product_id=virtualized-automotive-ecu`

**Project:** `project_id=autodocs-ecu-software`

**Increment:** `increment=software-without-kernel`

**Evidence origin:** `process-definition`

**Confidentiality:** `internal`

This dossier defines a candidate MAN.5 strategy. It does not approve itself,
accept residual risk, operate a risk register, prove ECU execution, create an
Automotive SPICE rating, authorize release, or establish cybersecurity or
functional-safety compliance. Activation requires the Management decision and
distinct Architect gate-scope review in [section 13](#13-approval-and-activation-boundary).

## 1. Authority and source baseline

The candidate is bounded by:

- the Management-approved ECU supplied-product boundary in
  [`DEC-0020-001`](dec-0020-01-ecu-scope.md): system and application software
  for a virtualized automotive ECU, above the kernel interface; the kernel is
  added later;
- the approved 14-process profile in
  [`REQ-0020-04`](req-0020-04-applicability-matrix.md), where `MAN.5` is
  `included/rated` and performed internally for this increment;
- the explicit exclusion of owned cybersecurity and functional-safety
  lifecycles in [`REQ-0020-06`](req-0020-06-cybersecurity-safety-applicability.md);
- the process instance, evidence-origin, validity, confidentiality and
  non-substitution rules in the
  [CL2 assessment input](../pipeline/aspice-cl2-assessment-input.md);
- the MAN.5 outcome in the
  [Level-1 requirements](../ASPICE/02-level-1-requirements.md) and the managed
  process/work-product expectations in the
  [Level-2 requirements](../ASPICE/02-level-2-requirements.md); and
- the current gap recorded in the
  [evidence register](../ASPICE/05-evidence-register.md): no maintained ECU
  strategy, register, treatment, monitoring, residual decision, or closure
  evidence yet exists.

No current record names the human MAN.5 Process Owner, Risk Manager,
Management Sponsor, or residual-risk acceptance authority. Repository Project
Lead, Security Engineer, Integrator, and Task-Acceptance roles do not acquire
those authorities by implication.

## 2. Objective and applicability

### `REQ-0017-01-01` — Bounded MAN.5 purpose

The strategy SHALL control project and product uncertainty that can affect the
objectives, supplied software, schedule, resources, interfaces, evidence,
verification, release or external dependencies of `software-without-kernel`.
It SHALL be instantiated by the ECU work under Feature `0027`; this reusable
definition is not `ecu-execution` evidence by itself.

The strategy SHALL NOT claim responsibility for the kernel, OS, hardware,
manufacturing, complete ECU system lifecycle, `SYS.1`–`SYS.5`, `VAL.1`, an
Automotive SPICE for Cybersecurity lifecycle, ISO/SAE 21434, ISO 26262, an
ASIL, TARA, HARA, safety case, or cybersecurity case. A signal that one of
those responsibilities may apply follows the interface escalation in
[section 8](#8-authority-and-escalation).

## 3. Operating principles

1. **Identify early and repeatedly.** Absence of a registered risk is not
   evidence of absence.
2. **Separate fact, estimate and decision.** Each score records its evidence,
   uncertainty, assessor, time and baseline. An accepted residual risk is a
   human decision, not a score calculation.
3. **Use the worst credible impact.** Impact dimensions are not averaged; the
   maximum supported dimension determines the score.
4. **Fail closed on ambiguity.** Unknown owner, authority, scope, baseline,
   likelihood or impact prevents acceptance and closure. Uncertain scoring
   uses the more severe credible band until evidence narrows it.
5. **Treat before accepting.** Acceptance is considered only after feasible
   preventive, detective, containment and recovery controls are evaluated and
   treatment effectiveness is evidenced.
6. **Preserve history.** Reassessment, acceptance, rejection, closure and
   reopening are additive. No prior score or decision is overwritten.
7. **Keep authorities separate.** Task Acceptance, integration, release,
   security/privacy advice, safety/cybersecurity approval and residual-risk
   acceptance are distinct decisions.

## 4. Risk lifecycle and record contract

### `REQ-0017-01-02` — Complete, traceable records

Task `0017-02` SHALL instantiate a maintained register. Each risk record SHALL
contain at least:

- stable risk ID, title and lifecycle state;
- product, project, increment, process and process-instance identity;
- affected requirements, work products, baselines, milestones, parties and
  decisions;
- category, source/trigger, event, cause and consequence stated separately;
- evidence references, assumptions, confidence and contrary evidence;
- initial probability, impact by dimension, exposure and scoring time;
- named human risk owner and named treatment owner;
- selected response (`avoid`, `reduce`, `transfer/share`, or `accept`) and
  treatment actions with owners, due dates and verification criteria;
- contingency/recovery trigger, action and authority;
- current action status, residual probability, residual impact, residual
  exposure and effectiveness evidence;
- escalation, acceptance/rejection, closure and reopening decisions with exact
  human authority references and timestamps;
- links to related plans, problems, changes, verification, release and
  communication records; and
- revision, validity, confidentiality, retention location and canonical
  evidence origin.

Lifecycle states are `identified`, `analyzed`, `treatment-required`,
`treatment-in-progress`, `monitoring`, `escalated`, `residual-decision-pending`,
`accepted`, `closed`, and `reopened`. Only a recorded authorized human decision
may enter `accepted`. `closed` additionally requires completed treatment,
verified effectiveness, no overdue actions and an authorized disposition.
Material new evidence or baseline change reopens the record.

## 5. Categories and identification sources

### `REQ-0017-01-03` — Required coverage

Every identification review SHALL consider all categories below and record
either identified risks or a reasoned `none-found` result for the reviewed
baseline. A category is not evidence of a real risk; it is a search obligation.

| Category | Required sources and examples |
|---|---|
| Technical/product | requirements ambiguity, architecture/interface mismatch, implementation defects, performance/capacity, compatibility, recovery and rollback |
| Scope and normative interpretation | source drift, wrong PAM/model/version, misinterpretation, unsupported claim, hidden exclusion or responsibility expansion |
| Provenance and configuration | provenance loss, stale or mixed baselines, wrong variant, missing trace, uncontrolled tool/configuration/calibration, non-reproducibility |
| Data and nondeterminism | incomplete/corrupt data, biased sampling, unstable generation, flaky results, non-repeatable AI/tool output, false pass from missing observations |
| Verification and validation | inadequate independence, missing coverage, invalid environment, unrepresentative input, unresolved finding, unverifiable acceptance criterion |
| Schedule, effort and resources | unrealistic estimate, critical-path delay, unavailable infrastructure, budget/compute limits, capacity conflict |
| Competence and organization | missing competence, unclear responsibility, unavailable approver, single-person dependency, ineffective interface or communication |
| Supplier and external dependency | unnamed or failing supplier/party, API/service/model change, license or availability constraint, unverified supplied baseline |
| Integration and release | incompatible inputs, incomplete bundle, migration/rollback failure, delivery error, unauthorized or premature release |
| Security, privacy and licensing | authorization bypass, credential/secret exposure, personal-data disclosure, dependency vulnerability, unsafe external effect, license incompatibility |
| Safety/cybersecurity interface | evidence that ISO 26262 or ISO/SAE 21434 responsibility may apply despite the current exclusion; potential safety or cybersecurity consequence requiring a separate lifecycle decision |
| Process and evidence integrity | ineffective control, missing audit trail, evidence substitution, reconstruction after the fact, retention/access failure, misleading capability claim |

Identification inputs include planning and status data, requirements and design
reviews, verification/validation and QA findings, configuration audits,
problem/change records, supplier/interface status, tool/service changes,
security/privacy/license review, release-readiness evidence, lessons learned and
management-review decisions.

## 6. Probability, impact and exposure

### `REQ-0017-01-04` — Reproducible scoring

Probability and impact are scored from 1 to 5. The assessment horizon SHALL be
the affected increment or the next governed milestone/release, whichever ends
first. The record SHALL state the horizon and evidence. Percentages are ranges,
not invented precision.

| Score | Probability criterion |
|---:|---|
| 1 — Rare | Credible but exceptional; estimated chance `<=5%`; no occurrence in comparable controlled baselines |
| 2 — Unlikely | Plausible under identifiable conditions; `>5%` to `20%`; isolated precursor or weak trend |
| 3 — Possible | Could occur in ordinary execution; `>20%` to `50%`; relevant occurrence or multiple precursors |
| 4 — Likely | Expected unless controls improve; `>50%` to `80%`; recurring precursor or ineffective control |
| 5 — Almost certain/current | `>80%`, already occurring, or trigger condition presently true |

Impact is assessed independently across product/technical correctness,
verification and evidence integrity, schedule/cost/resources, external
commitment/release, security/privacy/license, and safety/cybersecurity
interface. The highest credible dimension is the impact score.

| Score | Impact criterion |
|---:|---|
| 1 — Negligible | Local rework within an owned activity; no baseline, milestone, external commitment, sensitive-data or authority effect |
| 2 — Minor | Bounded work-package rework; objective and controlled baseline remain achievable without external or release effect |
| 3 — Moderate | Milestone, baseline, verification conclusion or multiple work packages require approved correction/replanning; no irreversible effect |
| 4 — Major | Release/acceptance readiness, contractual commitment, material security/privacy/license exposure, or a critical process outcome can fail; recovery is costly or cross-party |
| 5 — Severe | Irreversible/external effect, unauthorized disclosure/control, inability to recover, or credible safety/cybersecurity lifecycle consequence; Management and specialist decision required |

Exposure is `probability × impact`, an integer from 1 to 25. Initial and
residual exposure use the same rule and are stored separately. Score reduction
requires changed evidence, not merely a planned action.

## 7. Thresholds and required response

### `REQ-0017-01-05` — Fail-closed treatment gates

These thresholds are a proposed cross-item gate and remain non-operative until
section 13 is satisfied.

| Exposure | Class | Minimum response |
|---:|---|---|
| `1–4` | Low | Named owner; monitor at the regular cadence; record rationale for treatment or proposed acceptance |
| `5–9` | Medium | Treatment plan, due date and effectiveness criterion required; escalate if overdue, rising, or authority/scope is uncertain |
| `10–15` | High | Escalate within one working day; treatment and contingency required; affected baseline, commitment or release remains blocked until exposure is reduced or an authorized residual decision is recorded |
| `16–25` | Critical | Immediate containment/stop of the affected action; notify Management and relevant specialist authority without delay; no release or irreversible/external action while unresolved |

The following overrides apply regardless of arithmetic score:

- an active credential/secret compromise, unauthorized disclosure or
  uncontrolled external effect is `Critical`;
- a plausible safety/cybersecurity lifecycle responsibility or consequence is
  at least `High` and remains blocked pending the separate Management decision
  required by `REQ-0020-06-07`;
- absent owner, acceptance authority, baseline, recovery path or material
  evidence makes residual acceptance invalid;
- overdue treatment raises the class one band for escalation purposes; and
- a release-affecting risk cannot be accepted by the release performer or Task
  reviewer merely because validation is green.

## 8. Authority and escalation

### `REQ-0017-01-06` — Named human decisions

| Responsibility | Permitted action | Explicit limit |
|---|---|---|
| Management | Approve/replace this strategy; appoint MAN.5 roles; define bounded residual-risk delegations; decide lifecycle/scope expansion | Must use a durable authority record; approval is not Task Acceptance or release authorization |
| MAN.5 Process Owner | Maintain the approved strategy and process; ensure resources, cadence, reporting and interfaces | Role is not yet named; cannot self-grant residual-risk authority |
| Risk Manager | Facilitate identification/scoring, check record completeness, monitor exposure/actions, escalate breaches and report status | May challenge or raise a score; cannot accept material residual risk unless separately delegated as a human risk owner |
| Named human risk owner | Own one risk, select/propose treatment, keep evidence current and request residual decision | May accept only classes explicitly delegated by Management; delegation must name scope and limit |
| Treatment owner | Execute actions and produce effectiveness evidence | Cannot approve own effectiveness or accept the residual risk solely by performing treatment |
| Relevant registered specialist | Assess security, privacy, safety, cybersecurity, legal/license or other specialist consequence | Advises/approves only within registered specialist authority; does not gain generic Management, release or Task-Acceptance authority |
| QA / independent verifier | Verify process adherence, evidence and treatment effectiveness | Does not accept residual risk or approve release |
| Release authority | Decide release under the separate release contract after risk prerequisites are satisfied | Cannot manufacture missing risk acceptance or specialist approval |
| Repository Project Lead / Dispatcher | Coordinate assignments and route decisions | Project coordination grants no residual-risk acceptance |
| Task-Acceptance reviewer / Integrator | Review exact repository work products under assigned authority | Task Acceptance and integration do not accept product, security/privacy, safety/cybersecurity or release risk |

No residual-risk delegation exists at this candidate baseline. Therefore the
operative fallback is: **no residual-risk acceptance; unresolved material risk
remains blocking**. The Management activation decision may adopt the following
bounded model or replace it:

- Low: named human risk owner within an explicit Management delegation;
- Medium: Management-appointed risk authority independent of the treatment
  owner for that decision;
- High: Management plus every applicable registered specialist and separate
  release authority where release is affected; and
- Critical: no standing delegation; case-specific Management decision with
  specialist participation, compensating controls, expiry/review date and
  recovery evidence.

Escalation recipients and service times must be activated by name. Until then,
High/Critical notifications route through the assigned Project Lead to
Management, without treating delivery of a mailbox message as the decision.

## 9. Review cadence and triggers

### `REQ-0017-01-07` — Timely reassessment

- Active risks: at least weekly.
- High risks: every working day until reduced or decided.
- Critical risks: continuous owner attention with a recorded daily Management
  disposition while the affected action remains stopped.
- All open risks: at planning/replanning, baseline creation, milestone exit,
  release readiness and management review.
- Triggered review: material requirement/scope/baseline/architecture change;
  new or changed supplier/external service/tool/model; failed or inconclusive
  verification; QA/problem/security/privacy/license finding; schedule/resource
  deviation; incident; control failure; source/norm change; or evidence that
  the safety/cybersecurity applicability decision may be stale.
- Accepted or closed risks: at the recorded review/expiry date and whenever a
  trigger or materially changed baseline invalidates the decision.

Missed cadence is itself a process risk and prevents a stale record from being
presented as current.

## 10. Reporting and communication

### `REQ-0017-01-08` — Decision-useful reporting

The Risk Manager SHALL publish a versioned report at the regular review cadence
and for every High/Critical escalation. It SHALL contain:

- baseline/time, scope and responsible roles;
- counts and exposure distribution by state/category;
- new, changed, reopened, accepted, closed and overdue risks;
- top exposures with trend, treatment status, due date and effectiveness;
- High/Critical blockers and the exact decision/authority still required;
- interface risks to safety, cybersecurity, privacy, licensing, suppliers,
  verification, release, problems and changes;
- missing/invalid data, scoring uncertainty and stale decisions;
- decisions made, owners, deadlines and linked records; and
- comparison with the prior report without deleting history.

Recipients SHALL include the appointed MAN.5 Process Owner, relevant project
management, affected work-product/baseline owners, QA, release authority for
release-affecting risks, and applicable registered specialists. High/Critical
reports also go to the named Management Sponsor. Recipient identities remain an
activation parameter; the candidate does not invent them.

## 11. Retention, integrity and access

### `REQ-0017-01-09` — Durable evidence

- Strategy versions, register records, source evidence, scoring history,
  treatments, effectiveness checks, reports, communications, decisions,
  approvals, rejections, closures and reopenings SHALL be versioned and linked.
- Records SHALL retain the metadata required by the CL2 assessment input,
  including baseline/revision, owner, origin, validity, confidentiality,
  access and retention location.
- `process-definition` and `implemented-mechanism` evidence SHALL NOT substitute
  for actual `ecu-execution`; controlled scenarios remain labeled as such.
- Supersession is additive. Destructive rewrite, deletion of contrary evidence,
  or back-dated reconstruction is prohibited.
- Retain all records through final closure of the increment **and** completion
  of the next independent assessment that consumes them. After that event,
  deletion requires a recorded Management decision plus confirmation that no
  contractual, legal, safety, cybersecurity, privacy, audit, litigation-hold
  or open-risk obligation requires longer retention. If that check is absent,
  retain rather than delete.
- Confidentiality defaults to `internal`. Secrets, credentials and unnecessary
  personal data SHALL NOT be stored in the register; restricted evidence is
  referenced through its controlled location and access record.
- Restore/readability SHALL be tested at least annually and before an
  assessment or release that relies on the evidence.

## 12. Interfaces and recovery

### `REQ-0017-01-10` — No orphaned consequence

- Treatment-causing product/process changes link to `SUP.10`; discovered
  defects/problems link to `SUP.9`; controlled items/baselines link to `SUP.8`;
  verification and QA evidence link to their authoritative records.
- Release-affecting risk status is an input to release readiness, never release
  authorization itself.
- Safety/cybersecurity applicability signals reopen `REQ-0020-06` through a new
  Management decision; ordinary MAN.5 treatment cannot waive that boundary.
- Failed treatment, missed cadence, invalid evidence, authority loss, expired
  acceptance, or baseline drift moves the risk back to `treatment-required`,
  `escalated`, or `residual-decision-pending` as applicable.
- Recovery evidence identifies the last valid baseline, containment state,
  restoration/rollback steps, verification, responsible owner and authority to
  resume. Absence of a verified recovery path blocks irreversible/external
  action.

## 13. Approval and activation boundary

### `REQ-0017-01-11` — Required decisions before operation

This candidate defines thresholds that can block other Tasks, release and ECU
execution. Under the canonical
[`cross-item-blast-radius`](../pipeline/decision-record.md#2-when-a-record-is-mandatory)
rule, activation requires both:

1. a conforming Management `decision-record@v1` that approves or replaces the
   strategy, names the MAN.5 Process Owner, Risk Manager, Management Sponsor,
   residual-risk authorities and their bounded classes, recipients/service
   times, retention owner, affected work units and gates; and
2. a supporting scope review by a Management-instantiated Architect distinct
   from this implementer, testing the proposed threshold reach, authority
   separation, safety/cybersecurity boundary, release interface and recovery
   behavior.

The decision should explicitly resolve:

- whether the proposed 1–5 scales and `1–4`/`5–9`/`10–15`/`16–25` bands are
  adopted;
- which named human roles may accept Low, Medium, High or Critical residual
  risk, if any;
- which risks block baselines, commitments, verification, release or external
  action;
- escalation recipients, response times and working-time calendar;
- retention ownership and any longer contractual/legal period; and
- the exact downstream gates, including `0017-02`, `0017-03`, `0017-07`, ECU
  instantiation under `0027-03`, and affected release-readiness work.

Until both records are committed on the authoritative baseline, this document
is preparation only. It must not be cited as an operative gate, an approved
strategy, a residual-risk decision or completion of Task `0017-01`.

## 14. Verification checklist

A reviewer can accept this candidate for decision routing only if all answers
are `yes`:

1. Does it retain the exact `software-without-kernel` ECU boundary and the
   14-process profile?
2. Does it cover all Task-required categories/sources, scoring, thresholds,
   authority, cadence, reporting and retention controls?
3. Are probability, impact and exposure reproducible and fail closed under
   uncertainty?
4. Are initial exposure, treatment, residual exposure, effectiveness,
   acceptance and closure separate?
5. Are Task Acceptance, release, residual-risk, specialist and Management
   authorities kept distinct?
6. Are security/privacy/license and safety/cybersecurity interface risks
   escalated without claiming 21434/26262 performance?
7. Does the evidence-origin rule prevent process definitions or fixtures from
   impersonating ECU execution?
8. Are history, access, retention and recovery auditable?
9. Is the candidate visibly non-operative until the required Management
   decision and Architect review exist?
