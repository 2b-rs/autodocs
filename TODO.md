# TODO — Open Point List

HOW TO USE:

- *Features* are represented as 2nd level Headings.
- New *Features* shall normally be added to the top of list
- Features consist of *Tasks*.
- a *Feature* is considered complete once all of its *Tasks* are complete.
- Complete *Features* shall be moved to DONE.md and marked with a completion date + time. TODO.md and DONE.md must be committed after each completed feature.

- *Tasks* are dashed items whose first line carries a completion marker and task ID. Supporting acceptance-criteria, Definition-of-Done, decision, and history bullets may follow.
  [ ] - open. No work has been done w/r to this item
  [u] - unclear. No agentic work can currently be performed on this item because user/manager discussion, authorization, or clarification is required before proceeding.
  [p] - partially implemented. The agent has started work on this item, but it is not yet complete; use this while work is in progress, including across conversations, so agents can determine the next best unfinished item.
  [?] - unknown - we simply don't know. Next step is to look into the repository and decide whether to amend TODO or promote to `[x]`.
  [x] - executed - task has been completed. If a task is completed, the results shall be checked in and `REF: xxxxxx` (git hash) shall be added.
- A task's imperative sentence and any **Acceptance criteria** bullets are normative. The sentence must identify an observable deliverable or result; add explicit acceptance criteria and a **Definition of Done** whenever completion, failure behavior, evidence, or review authority would otherwise be ambiguous.
- Unless a task states a stricter gate, `[x]` requires the committed deliverable, the specified validation or authorized review evidence, resolution or explicit disposition of material findings, and the commit `REF`.
- *Tasks* shall have a granularity so that they can be implemented in one go. If preparation or implementation is agentic but the final approval/rating/acceptance requires a named human authority, split the work or keep it `[p]`; set `[u]` only when that human decision is the next unresolved action. Do not copy `[u]` transitively to every dependent task: its explicit prerequisite already records the block.
- A task/subtask prerequisite is a **start gate** for that item. A Feature prerequisite is a **Feature-closure gate**: individual tasks may proceed when their own start gates permit, but the dependent Feature cannot move to `DONE.md` first. Conditional or alternative lifecycle dependencies must be materialized after the governing scope decision as explicit task prerequisites or as machine-enforced selected-profile edges; prose-only dependencies are not sufficient.
- Agents shall keep these markers up to date while working and in conversation hand-offs: set `[p]` once implementation/investigation has started, set `[u]` only as defined above, and avoid leaving active work as plain `[ ]` when a better state is known.

## ID scheme

- *Feature names* are kept consistent in English (translate on introduction if needed).

- Every *Feature* gets a unique **feature ID**: a 4-digit number with leading zeroes, e.g. `0001`. Feature headings are written as `## Feature: XXXX — <name>`.

- Every *Task* within a feature gets a **task ID** `XXXX-YY`, where `XXXX` is the feature ID and `YY` is a 2-digit task number, unique within that feature (e.g. `0001-01`, `0001-02`). Task IDs are rendered in bold right after the checkbox marker, e.g. `- [ ] **0001-01** ...`.

- A *Task* may be split into **subtasks**, identified as `XXXX-YY.ZZ`, where `ZZ` is a 2-digit subtask number unique within that task (e.g. `0001-01.01`, `0001-01.02`).

- *Tasks* and *Features* may declare **prerequisites** — other tasks/features that must be done first. One prerequisite relation is written as:

  `XXXX[-YY[.ZZ]]:AAAA[-BB[.CC]]`

  - `XXXX` — feature ID of the dependent item
  - `-YY` / `.ZZ` — optional dependent task/subtask; omitted means the whole feature depends on the prerequisite
  - `AAAA` — feature ID of the prerequisite
  - `-BB` / `.CC` — optional prerequisite task/subtask; omitted means the dependency is on the whole feature
  - Multiple prerequisites are a comma-separated list of complete relations; the dependent ID is repeated in each relation.

  Examples:
  - `0002:0001` — Feature `0002` as a whole depends on Feature `0001` as a whole.
  - `0002-09:0001` — Task `0002-09` depends on Feature `0001` as a whole.
  - `0002-09:0001-08` — Task `0002-09` depends specifically on Task `0001-08`.
  - `0006-04.02:0006-04.01` — Subtask `0006-04.02` depends on sibling Subtask `0006-04.01`.
  - `0014-13:0015-06, 0014-13:0016-01` — Task `0014-13` has two prerequisites.

  Prerequisites are noted inline in the task/feature text after `PREREQ:`.

## Feature: 0021 — Website-Initiated Specification Review Flags

**PREREQ:** 0021:0005, 0021:0006

**Goal:** Let a website user request a traceable re-review of any published specification record—including an element currently curated as valid—without directly changing that record’s status or factual content. The website must produce an authenticated or self-declared review/curation request package that can be ingested into the existing queue/lifecycle, reviewed by the responsible roles, and linked back to the originating record and its published history; the GitHub path submits the package, while the JSON path exports it for later transfer and ingestion.

**Scope and safety boundary:** “Flag for review” is a request for re-curation, not an in-place edit, publication withdrawal, approval, or rejection. The request must carry the exact record/version/text context and a user-provided rationale; it must use the existing browser-to-GitHub-submission or JSON-export boundary and the existing `curation_ingest.py` queue creation path. No browser user, agent, or client-side code may transition a record to `valid/*`, rewrite a record, or close a curation item.

**Feature Definition of Done:**
- Every eligible published record page exposes an accessible “Flag for review” action with no loss of history/provenance context.
- The action produces a schema-valid, target-integrity-checked curation request package that identifies the record, canonical/version ID, current content/text hash, current status, requesting actor and authoritative trust context, concern category, rationale, and optional evidence/field references.
- Ingested requests enter `_src/spec/curation-queue/open/` only through the existing ingestion boundary, normalize into the unified workflow lifecycle, and remain linked to the originating record in user-facing reports; exported or merely submitted packages are not presented as queued.
- Invalid, stale, duplicate, unattributed, attribution-policy-violating, and malformed packages receive clear user feedback and cannot silently create record changes; policy-accepted self-declared packages retain their lower trust level.
- Automated tests cover the browser flow, generated package, ingestion/queue mapping, authorization boundaries, record-page rendering, and end-to-end traceability; relevant pipeline documentation is authoritative and current.

### Campaign A — Contract and Process Definition

- [ ] **0021-01** Define the authoritative website “Flag for review” process, role boundaries, lifecycle semantics, and non-bypass rules in `docs/pipeline/`.
  - **Acceptance criteria:** The docs define which published records are eligible and every exclusion; define who may submit, claim, propose, accept/reject, apply, and close a web-originated request; distinguish review versus curation routing; specify the `valid/*` re-review rule; define stale/duplicate/abuse handling; and state that the website never mutates records directly.
  - **Definition of Done:** `docs/pipeline/` documents are internally consistent with `workflow-lifecycle.md`, `roles.md`, `actions.md`, `status-model.md`, and `curation-item-schema.md`; a validation/testable set of normative requirements is committed.

- [ ] **0021-02** PREREQ: 0021-02:0021-01 Specify the versioned browser request-package schema and deterministic request identity for a re-curation flag.
  - **Acceptance criteria:** Schema includes request ID/version, target canonical and version ID, content/text hash, source URL/locator, status snapshot, actor claim, authoritative transport-derived identity/trust metadata, category, rationale, optional field/evidence references, timestamps, and client/schema version; downloaded JSON is always self-declared until a trusted ingestion envelope proves otherwise; duplicate identity, canonical serialization, stale-hash, sensitive-field, and retention rules are unambiguous.
  - **Definition of Done:** JSON Schema or equivalent validator, valid/invalid examples, and deterministic-ID fixtures are committed; the same semantic package supports GitHub-Issue submission and JSON export/later transfer without conflating their lifecycle states.

- [ ] **0021-03** PREREQ: 0021-03:0021-02 Extend the ingestion boundary to recognize, validate, de-duplicate, and route website re-curation submissions.
  - **Acceptance criteria:** `curation_ingest.py` or a clearly delegated adapter accepts only schema-valid packages, verifies target record/version/hash, derives authoritative identity/trust only from the trusted transport envelope, rejects spoofed trust claims, preserves a lossless mapping of submission identity/context into the queue item, creates an `open` curation-queue item with record linkage, and rejects malformed/stale/duplicate inputs with actionable diagnostics; no rejected input creates history and no accepted input directly writes factual record fields.
  - **Definition of Done:** Automated tests cover happy path, unknown record, obsolete version/hash, malformed schema, duplicate submission, unsupported category, insufficient attribution, spoofed trust metadata, and lossless submission-to-queue mapping; output conforms to `curation-item@v1` (or a deliberately versioned successor) and unified lifecycle validation.

### Campaign B — Website Experience and Generated Views

- [ ] **0021-04** PREREQ: 0021-04:0021-01, 0021-04:0021-02 Design the record-page interaction, confirmation, and accessibility behavior for requesting re-review.
  - **Acceptance criteria:** The UX defines the action placement for valid and non-valid records, required rationale/category fields, optional evidence references, current record/version/status disclosure, consent/trust disclosure, confirmation behavior, success/error/stale states, keyboard operation, focus management, mobile layout, and the no-JavaScript fallback transport/confirmation/failure behavior; terminology makes clear that a request does not alter the record immediately.
  - **Definition of Done:** Approved UI contract is recorded in authoritative pipeline/UI documentation; testable acceptance scenarios cover standard, valid-curated, stale, duplicate, and submission-failure paths.

- [ ] **0021-05** PREREQ: 0021-05:0021-03, 0021-05:0021-04 Implement the browser-side “Flag for review” flow on generated record pages.
  - **Acceptance criteria:** Generated pages expose an accessible action and dialog/form; the form binds the rendered record’s canonical/version ID, current hash, status, and source URL without user re-entry; it validates required inputs locally, produces the specified request package, and uses GitHub submission or JSON export without browser-side record mutation. The UI distinguishes `exported`, `submitted`, and `ingested/queued`; a JSON download is never presented as submitted or queued, a submitted GitHub issue shows only its transport receipt until ingestion, and queue identity/linkage appears only after trusted ingestion returns or publishes it.
  - **Definition of Done:** Desktop/mobile/browser tests verify keyboard accessibility, visible focus, accessible labels/errors, request serialization, cancellation, transport failure, and no-JavaScript fallback behavior; generated HTML remains deterministic.

- [ ] **0021-06** PREREQ: 0021-06:0021-05 Render review-request state and traceability in record history and curation/report views.
  - **Acceptance criteria:** An ingested/queued request is discoverable from the target record’s history/details and from curation reports; views show request identity, lifecycle state, status snapshot, target version, actor/trust presentation consistent with privacy rules, and a durable link to the queue item and available transport receipt; exported packages and submitted-but-not-ingested GitHub issues are not represented as queue/history state, and the record remains visibly valid until a later governed decision changes it.
  - **Definition of Done:** Generated-page and report assertions cover a valid curator-decided record with an open re-review request plus accepted and rejected lifecycle outcomes; browser/ingestion tests separately prove that stale or otherwise rejected pre-ingest submissions create no queue/history entry; link and DOM validation pass.

### Campaign C — Assurance and Release

- [ ] **0021-07** PREREQ: 0021-07:0021-03, 0021-07:0021-05, 0021-07:0021-06 Verify end-to-end lifecycle, authorization, and anti-bypass behavior.
  - **Acceptance criteria:** An end-to-end fixture demonstrates published record → browser request → validated ingestion → queued item → claim/proposal → human accept/reject → governed application/closure; negative tests cover altered target identity/hash, spoofed actor/trust metadata, stale/duplicate requests, and prove that UI, AI, and ingestion cannot silently approve, reject, close, or edit a record outside their permitted roles.
  - **Definition of Done:** Automated test suite and validation reports pass; findings are recorded and resolved or explicitly queued; traceability from rendered control through submission and queue item to the record is reproducible.

- [ ] **0021-08** PREREQ: 0021-08:0021-07 Publish the feature, update operating guidance, and close the implementation campaign.
  - **Acceptance criteria:** Operator and user guidance explains how to submit, triage, decide, and follow a website-originated re-review request; reports identify web-originated requests without overstating their authority; release notes identify security/privacy and process limitations.
  - **Definition of Done:** Full generation, validation, and regression checks pass; the feature Definition of Done is evidenced by committed documentation, tests, and generated output; campaign closure records the release decision and any residual follow-up items.

## Feature: 0020 — Automotive ECU Level 1 Scope, Responsibility, and Evidence Boundary

**Goal:** Establish the concrete ECU product and organizational boundary for a PAM 4.0 Level-1 target, select the named processes by actual responsibility, and prevent documentation-pipeline evidence from being misrepresented as ECU process-instance evidence. The current repository is an enabling process/tool foundation; capability must be demonstrated on approved ECU process instances.

**ASPICE task acceptance envelope (applies to Features `0020`, `0022`–`0032`, and `0011`–`0018` below):** Unless a task explicitly produces only a definition or readiness mechanism, completion requires evidence from the approved ECU product/project/process instance and baseline. Every deliverable must carry controlled identity/version/origin, owner and required authority, applicable lifecycle trace and consistency results, findings/contrary evidence and disposition, validation or review evidence, retention/access classification, and an unambiguous pass/fail or decision gate. A template, tool, documentation campaign, synthetic scenario, or external party's evidence cannot substitute for the assessed unit's own execution. Assessment disposition (`included/rated` or `out of scope/not rated`) is recorded separately from execution responsibility (`internal`, `shared`, or `external`); a shared in-scope process requires evidence for the assessed unit's portion as well as controlled external interfaces.

- [u] **0020-01** Approve the first assessed ECU product/variant and supplied-product boundary, organizational unit, customer/intended use, lifecycle stage, project/release or increment, assessment purpose/timing, target profile, and permitted claim wording; identify whether the unit owns a complete ECU system lifecycle or receives allocated software requirements. The automotive ECU domain is confirmed, but these concrete scope decisions still require sponsor/manager and competent-assessor agreement.
- [ ] **0020-02** PREREQ: 0020-02:0020-01 Define and enforce the evidence boundary among canonical origins `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, and `controlled-scenario`; require `product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, revision, owner, origin, validity, retention, and confidentiality metadata and prohibit cross-product evidence substitution or opportunistic aggregation.
- [ ] **0020-03** PREREQ: 0020-03:0020-01 Define the ECU responsibility/authority matrix across customer, system, software, hardware, ML, cybersecurity, functional safety, calibration, manufacturing/service, integration, validation, release, operations, and suppliers; record who performs, reviews, approves, accepts, monitors, communicates, and retains evidence at every lifecycle interface.
- [ ] **0020-04** PREREQ: 0020-04:0020-03 Complete and approve an applicability matrix for all 32 PAM 4.0 processes, starting with the 14-process ECU software-delivery nucleus and adding each of `SYS.1`–`SYS.5` and `VAL.1` only for its actual owned responsibility; use the 20-process profile only when the complete system lifecycle and intended-use validation are owned. Record assessment disposition (`included/rated` or `out of scope/not rated`) separately from execution responsibility (`internal`, `shared`, or `external`); for every shared process identify the assessed unit's outcomes/activities and internal execution gate plus the external activities and interface/acceptance gate, all justified from supplied-product and responsibility evidence.
- [ ] **0020-05** PREREQ: 0020-05:0020-03, 0020-05:0020-04 Decide `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` applicability; create dependency-linked execution Features/tasks for every included process. For every shared process register both the assessed unit's execution gate and the external interface gate; for every fully external process define controlled inputs, outputs, acceptance, monitoring, escalation, configuration, risk, and evidence interfaces rather than treating it as absent.
- [ ] **0020-06** PREREQ: 0020-06:0020-03, 0020-06:0020-04 Decide applicable Automotive SPICE for Cybersecurity model/version and ISO/SAE 21434 responsibilities, plus ISO 26262 functional-safety responsibilities; create separate dependency-linked Features for applicable cybersecurity or safety lifecycles, register their completion gates in the selected profile, and do not present generic PAM 4.0 evidence as proof of either framework.
- [ ] **0020-07** PREREQ: 0020-07:0020-02, 0020-07:0020-04 Tailor and approve the Level-1 assessment input and official-outcome worksheets: process instances, evidence/interview validation, sampling/aggregation, assessor competence/independence, outcome and PA 1.1 rationale, report format, confidentiality, and rule that CL1 requires `PA 1.1 = L` or `F` per named process.
- [ ] **0020-08** PREREQ: 0020-08:0020-02, 0020-08:0020-03, 0020-08:0020-04, 0020-08:0020-05, 0020-08:0020-06, 0020-08:0020-07 Instantiate the controlled process/work-product/evidence catalogue for the selected ECU profile, assigning ECU-specific work products, owners, repositories, review/approval criteria, lifecycle interfaces, baseline/retention controls, and evidence obligations; baseline initial gaps without assigning a capability rating.
- [ ] **0020-09** PREREQ: 0020-09:0020-05, 0020-09:0020-06, 0020-09:0020-08 Create and validate the selected-profile execution register: for every included base, cybersecurity, safety, or other lifecycle process, identify the exact execution Feature/task and completion gate; for every shared process, record whether it is rated, the assessed unit's exact outcomes/activities and execution gate, and the external input/output/acceptance/feedback gate; for every fully external process, identify the approved interface-evidence gate and prohibit an internal rating. Materialize every conditional predecessor, release, and assessment relationship as a concrete TODO prerequisite or machine-enforced selected-profile edge; reject a profile, release, evidence freeze, or assessment when an included process or selected edge has no executable, satisfied path to valid evidence, or when interface evidence is substituted for the assessed unit's own performance.

## Feature: 0027 — ECU Management and Supporting Process Performance

**PREREQ:** 0027:0020

**Goal:** Perform `MAN.3`, `MAN.5`, `MAN.6`, `SUP.1`, `SUP.8`, `SUP.9`, and `SUP.10` on real ECU process instances. Reuse suitable mechanisms from Features `0011`–`0017`, but do not duplicate records or credit documentation-product execution as ECU evidence.

- [ ] **0027-01** PREREQ: 0027-01:0020-08 Establish and approve the ECU `MAN.3` project plan covering goals/motivation, boundaries, lifecycle, releases, feasibility, work packages, dependencies, estimates, schedule/milestones, deliverables, commitments, entry/exit criteria, named qualified assignments, competencies, tools/infrastructure/material resources, interfaces, communication, and escalation.
- [ ] **0027-02** PREREQ: 0027-02:0027-01 Operate recurring `MAN.3` actual-versus-plan monitoring throughout the ECU lifecycle; retain status, deviations, causes, impacts, decisions, corrective actions, owners/dates, replanning, escalation, effectiveness, closure, and affected-party communication.
- [ ] **0027-03** PREREQ: 0027-03:0020-08, 0027-03:0027-01 Establish and operate ECU `MAN.5` risk management with defined criteria and a maintained register covering technical, schedule, resource, supplier, integration, verification/validation, release, tool, safety-interface, cybersecurity-interface, and external-dependency risks; retain exposure, treatment, residual acceptance, monitoring, effectiveness, escalation, and closure evidence.
- [ ] **0027-04** PREREQ: 0027-04:0020-08, 0027-04:0027-01 Establish and operate ECU `MAN.6` measurement from approved information needs through metric definition, validated collection, analysis, trend/limitation communication, and documented decisions. Retain each value's unit, source, timestamp, process-instance/baseline context, data-quality result, analysis, limitations, communication, and linked management decision; keep missing, invalid, or incomparable data visibly distinct from successful results.
- [ ] **0027-05** PREREQ: 0027-05:0020-08 Establish and operate ECU `SUP.8` configuration management for requirements, architecture/design, source/generated code, binaries/firmware, toolchain/configuration, calibration/variant data, test assets/environments, supplier items, records/evidence, and releases; perform controlled change/versioning, baselines, status accounting, audits, backup/restore, access, retention, and availability controls.
- [ ] **0027-06** PREREQ: 0027-06:0020-08, 0027-06:0027-01, 0027-06:0027-05 Establish and operate appropriately independent ECU `SUP.1` quality assurance across selected processes and work products; identify the approved provisions checked and retain the named QA authority, independence/conflict assessment, conformance/nonconformance results, communication, escalation, management resolution, corrective-action verification, recurrence prevention, status reporting, and closure.
- [ ] **0027-07** PREREQ: 0027-07:0020-08, 0027-07:0027-01, 0027-07:0027-05 Establish and approve one ECU `SUP.9` problem lifecycle covering reproducible intake, classification/severity/priority, cause and impact analysis, high-impact alert criteria/recipients, urgent-action authorization, durable resolution, verification, communication, closure, status/trends, and links to controlled changes; distinguish problems from work packages, desired changes, and rehearsals, and validate the mechanism with positive/negative fixtures.
- [ ] **0027-08** PREREQ: 0027-08:0020-08, 0027-08:0027-01, 0027-08:0027-05 Establish and approve one ECU `SUP.10` change-request lifecycle covering intake/status, affected-baseline and dependency/resource/schedule/risk impact, priority, approve/reject/withdraw authority, implementation trace for approved changes, proof of non-implementation for rejected/withdrawn requests, verification/consistency, communication, closure, trends, and links to problems; validate every decision branch with positive/negative fixtures.
- [ ] **0027-09** PREREQ: 0027-09:0027-07 Operate `SUP.9` on representative real ECU problems through verified closure and status/trend reporting. A scenario may qualify the mechanism but cannot satisfy ECU execution; if no representative problem exists in the approved observation period, keep the execution gate open and obtain an assessor-approved sampling/observation extension.
- [ ] **0027-10** PREREQ: 0027-10:0027-08 Operate `SUP.10` on the representative real ECU change requests in the approved sample, including implemented, rejected, or withdrawn paths where present, and retain authorization, impact, implementation/non-implementation, verification, communication, closure, and status/trend evidence. A scenario may qualify the mechanism but cannot satisfy ECU execution; absent decision branches require documented sampling rationale or an assessor-approved extension, not invented records.

## Feature: 0022 — ECU System Process Interface and Trace Foundation

**PREREQ:** 0022:0020, 0022:0027-05

**Goal:** Define the common responsibility, interface, configuration, and lifecycle-trace controls used by individually selected `SYS.1`–`SYS.5` processes. This Feature does not claim that any system process was performed.

- [ ] **0022-01** PREREQ: 0022-01:0020-09 Define the per-process system interface plan without waiting for future outputs: for each `SYS.1`–`SYS.5` process, record assessment disposition separately from internal/shared/external execution responsibility, including the assessed unit's exact outcome/activity boundary for every shared process, performer/authority, required input and output types, internal predecessor task or external acceptance gate, configuration/change/problem/risk feedback, and exact completion/evidence gate.
- [ ] **0022-02** PREREQ: 0022-02:0022-01 Extend the shared lifecycle model and validators for stakeholder requirement ↔ system requirement ↔ system architecture/element ↔ allocated software/hardware/ML requirement ↔ implementation ↔ verification/validation ↔ problem/change/release traces, including variants, baselines, status, rationale, responsibility origin, and consistency checks. Represent verification/validation specification or measure and result as distinct trace nodes with the correct `SWE.4`, `SWE.5`, `SWE.6`, `SYS.4`, `SYS.5`, or `VAL.1` basis; reject wrong-basis, stale-baseline, cross-variant, and orphan traces.

## Feature: 0028 — Conditional ECU Requirements Elicitation Process Performance (SYS.1)

**PREREQ:** 0028:0020, 0028:0022, 0028:0027-01

- [ ] **0028-01** PREREQ: 0028-01:0020-08 Establish and agree the `SYS.1` ECU stakeholder-requirements baseline from identified customer, user, regulatory, operational, manufacturing/service, safety, cybersecurity, supplier, and internal sources; retain stakeholder-identification and elicitation records, intended-use scenarios, environments, priorities, analyzed conflicts and their resolution/disposition, acceptance, changes/impacts/risks, status, communication, and the authority/evidence for stakeholder agreement.

## Feature: 0029 — Conditional ECU System Requirements Analysis Process Performance (SYS.2)

**PREREQ:** 0029:0020, 0029:0022, 0029:0027-01, 0029:0027-05

- [ ] **0029-01** PREREQ: 0029-01:0020-09, 0029-01:0022-01, 0029-01:0027-01 Accept and baseline the stakeholder-requirement input for internal `SYS.2`: use Feature `0028` output when `SYS.1` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.1` performance.
- [ ] **0029-02** PREREQ: 0029-02:0029-01 Analyze, derive, structure, prioritize, agree, and baseline `SYS.2` ECU system requirements, including behavior, modes/states, interfaces, diagnostics, timing/performance/resources, environment, safety/cybersecurity constraints, correctness, feasibility, dependencies, verification criteria, rationale, status, communication, and bidirectional stakeholder trace. Maintain the baseline through controlled changes with impact/risk and operating-environment analysis, bidirectional consistency checks, supersession/status evidence, and affected-party communication.

## Feature: 0030 — Conditional ECU System Architectural Design Process Performance (SYS.3)

**PREREQ:** 0030:0020, 0030:0022, 0030:0027-01, 0030:0027-05

- [ ] **0030-01** PREREQ: 0030-01:0020-09, 0030-01:0022-01, 0030-01:0027-01 Accept and baseline the system-requirement input for internal `SYS.3`: use `0029-02` when `SYS.2` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.2` performance.
- [ ] **0030-02** PREREQ: 0030-02:0030-01 Define, evaluate, agree, and baseline the `SYS.3` ECU system architecture, including system elements, HW/SW/ML/external allocations, static/dynamic interfaces, modes/states, resource budgets, failure behavior, variants, alternatives, quality evaluation, rationale, communication, and bidirectional system-requirement trace. Allocate or explicitly disposition every applicable system requirement and maintain requirement–architecture allocation completeness, consistency, and change-impact evidence after baselining.

## Feature: 0031 — Conditional ECU System Integration and Integration Verification Process Performance (SYS.4)

**PREREQ:** 0031:0020, 0031:0022, 0031:0027-01, 0031:0027-05

- [ ] **0031-01** PREREQ: 0031-01:0020-09, 0031-01:0022-01, 0031-01:0027-01 Accept and baseline the system architecture and all system-element inputs for internal `SYS.4`: use `0030-02` and applicable internal element outputs when those processes are internal, or validate each external/shared owner, baseline, interface, configuration, acceptance, open finding, and feedback path without claiming its process performance. The selected-profile register must materialize the applicable internal predecessor tasks and external/shared acceptance gates; no hard-coded software-only predecessor may stand in for that selected system-element set.
- [ ] **0031-02** PREREQ: 0031-02:0031-01, 0031-02:0022-02 Define and approve the `SYS.4` integration and integration-verification sequence, preconditions, builds, architecture/interface/interaction measures, selection/coverage and regression rationale, environments/data, entry/exit and pass/fail criteria, result retention, and architecture-to-measure trace.
- [ ] **0031-03** PREREQ: 0031-03:0031-02 Integrate controlled ECU system elements according to the approved sequence; execute selected `SYS.4` measures, retain pass/fail and coverage results, trace architecture/interfaces to measures/results, resolve or disposition findings, and communicate the integration summary. Retain exact integration-build, system-element, hardware/software/ML/calibration/variant, tool, data, and environment identity.

## Feature: 0032 — Conditional ECU System Verification Process Performance (SYS.5)

**PREREQ:** 0032:0020, 0032:0022, 0032:0027-01, 0032:0027-05

- [ ] **0032-01** PREREQ: 0032-01:0020-09, 0032-01:0022-01, 0032-01:0027-01 Accept the controlled system-requirement and integrated-system inputs for internal `SYS.5`: use `0029-02` and `0031-03` when those processes are internal, or validate each external/shared owner, baseline, exact ECU element/configuration/environment identity, status, acceptance, open findings, and feedback path without claiming external process performance.
- [ ] **0032-02** PREREQ: 0032-02:0032-01, 0032-02:0022-02 Define and approve `SYS.5` integrated-system verification against ECU system requirements, including selection/coverage and regression rationale, target or representative environments, data, versioned expected results, entry/exit, pass/fail, retention, and system-requirement-to-measure trace tied to the controlled requirement and environment/configuration baseline.
- [ ] **0032-03** PREREQ: 0032-03:0032-02 Execute `SYS.5` on the controlled integrated ECU baseline; retain pass/fail and coverage results, trace results to system requirements, resolve or disposition findings, communicate the summary, and preserve exact ECU hardware/software/calibration/configuration/tool/environment identity.

## Feature: 0023 — ECU Software Engineering Process Performance (SWE.1–SWE.6)

**PREREQ:** 0023:0020, 0023:0027-01, 0023:0027-05

**Goal:** Develop and verify actual ECU software through `SWE.1`–`SWE.6`. Documentation generators, imported public requirements, and pipeline validators may be reused as tools or patterns but are not the ECU requirements, implementation, or verification results.

- [ ] **0023-11** PREREQ: 0023-11:0020-09, 0023-11:0027-05 Accept and baseline the allocated software-development inputs required by the approved profile: when `SYS.2`/`SYS.3` are internal, use the controlled outputs of `0029-02`/`0030-02`; when they are shared/external, validate the responsible party, allocated requirements, architecture/interface constraints, assumptions, acceptance criteria, configuration identity, change/problem/risk feedback, and bidirectional interface evidence without claiming internal `SYS` performance. The selected-profile register must materialize the actual internal predecessor or external/shared acceptance-gate edges.
- [ ] **0023-01** PREREQ: 0023-01:0023-11 Analyze, derive, structure, prioritize, agree, and baseline `SWE.1` ECU software requirements from accepted allocated system/stakeholder requirements and architecture/interface constraints, covering behavior, interfaces, timing/resources, diagnostics, modes/states, applicable safety/cybersecurity constraints, environment effects, correctness, feasibility, dependencies, estimates, verification criteria, rationale, status, communication, and bidirectional trace. Maintain input–software-requirement consistency and trace through controlled changes, including impact/risk analysis, supersession/status, and affected-party communication.
- [ ] **0023-02** PREREQ: 0023-02:0023-01 Define, evaluate, agree, and baseline the `SWE.2` ECU software architecture, including components, interfaces, static/dynamic behavior, scheduling/concurrency/resources, hardware/external interfaces, failure behavior, variants, alternatives, technical-quality evaluation, rationale, communication, and bidirectional trace. Allocate or explicitly disposition every applicable software requirement to components/interfaces and retain allocation completeness and consistency results.
- [ ] **0023-03** PREREQ: 0023-03:0023-02 Define and agree `SWE.3` ECU software detailed designs and unit/interface contracts, including static/dynamic behavior, data/control flow, algorithms, resource/concurrency constraints, coding principles, model/generated-code boundaries where applicable, and trace to software architecture and requirements.
- [ ] **0023-04** PREREQ: 0023-04:0023-03 Construct or generate each in-scope ECU software unit against its detailed design and coding principles; retain source/model/tool identity, construction and code-review findings, corrections, approvals, communication, and bidirectional design-to-unit/source trace.
- [ ] **0023-05** PREREQ: 0023-05:0023-03, 0023-05:0023-04 Define and approve `SWE.4` unit-verification specifications, methods, selection, applicable static-analysis/structural and other coverage objectives, regression rationale, controlled toolchain/environment/data, expected results and criteria, and detailed-design/unit-to-measure trace.
- [ ] **0023-06** PREREQ: 0023-06:0023-05 Execute `SWE.4` on the controlled ECU unit baseline; retain pass/fail data and coverage, trace detailed design/units to measures/results, resolve or disposition findings, communicate the summary, and retain exact unit/source or model, build/toolchain, configuration, data, and environment identity.
- [ ] **0023-07** PREREQ: 0023-07:0023-02, 0023-07:0023-03, 0023-07:0023-06 Define and approve the `SWE.5` component-verification and software-integration sequence, preconditions, builds, architecture/design/interface measures, selection/coverage and regression rationale, environments/data, criteria, and trace.
- [ ] **0023-08** PREREQ: 0023-08:0023-07 Integrate controlled ECU software components according to the approved sequence; execute `SWE.5` component/integration measures, retain pass/fail and coverage results, trace results, resolve or disposition findings, communicate the summary, and retain exact component/integration build, source/binary, configuration, toolchain, target, data, and environment identity.
- [ ] **0023-09** PREREQ: 0023-09:0023-01, 0023-09:0023-02, 0023-09:0023-08 Define and approve `SWE.6` integrated-software verification against software requirements, including release/regression selection, coverage, controlled target or representative environments, entry/exit, pass/fail, retention, and software-requirement-to-measure trace.
- [ ] **0023-10** PREREQ: 0023-10:0023-09 Execute `SWE.6` on the controlled integrated ECU software baseline; retain pass/fail and coverage results, trace results to software requirements, resolve or disposition findings, communicate the summary, and preserve exact source/executable/configuration/toolchain/target/environment identity.

## Feature: 0024 — ECU Product Release Process Performance (SPL.2)

**PREREQ:** 0024:0020, 0024:0023

**Goal:** Perform `SPL.2` for the identified supplied ECU software/product without forcing ownership of `VAL.1`. The selected-profile gate must require Feature `0026` before release/assessment when intended-use validation is included and must otherwise require the approved external/shared validation and acceptance interface.

- [ ] **0024-01** PREREQ: 0024-01:0020-08, 0024-01:0027-05, 0024-01:0023-10 Define `SPL.2` ECU release content, identity, eligibility/approval criteria, compatible hardware/vehicle and variant scope, firmware/executable, calibration/configuration and flashing/delivery artifacts as applicable, release notes, known limitations, licenses/notices, support and update/rollback information, recipients/delivery controls, and release-record requirements.
- [ ] **0024-02** PREREQ: 0024-02:0020-09, 0024-02:0024-01, 0024-02:0027-02, 0024-02:0027-03, 0024-02:0027-04, 0024-02:0027-06, 0024-02:0027-07, 0024-02:0027-08 Verify every release prerequisite activated by the selected-profile register—including internal validation execution or the approved external/shared acceptance gate—and verify the disposition/closure or authorized carry-over of every actual applicable problem/change; then assemble, audit, approve, deliver, and verify receipt or deployment of one complete controlled ECU release package. Retain baseline identity, release authority, quality/risk/validation status, accepted deviations, notes, support/rollback information, delivery result, and links to included problems and changes. The release gate fails when any selected-profile edge is absent, stale, inconsistent, or unsatisfied, but does not require inventing a problem or rejected change solely for release.

## Feature: 0025 — Automotive ECU Level 1 Pilot Assessment and Closure

**PREREQ:** 0025:0020, 0025:0027, 0025:0023, 0025:0024

**Goal:** Assess PA 1.1 only after every process activated in the selected ECU profile has been performed or its approved shared/external interface evidence is ready, correct material outcome gaps, and publish a bounded process capability profile. CL1 requires `PA 1.1 = L` or `F` for each named target process; no repository-wide or product-certification claim is permitted.

- [ ] **0025-01** PREREQ: 0025-01:0020-07, 0025-01:0020-09 Select and approve the ECU pilot process instances, release/baselines, assessment schedule, interview roles, documentary evidence population, sampling/aggregation, confidentiality, assessor competence/independence, and all active system, validation, supplier, hardware, ML, cybersecurity, safety, reuse, or improvement execution Features; do not impose a fixed sample count unless the assessment input justifies it.
- [ ] **0025-02** PREREQ: 0025-02:0025-01, 0025-02:0024-02 Execute the machine-enforced selected-profile readiness gate: verify that every included process's registered Feature/task and conditional predecessor edge is complete with valid ECU execution evidence; every shared in-scope process has ECU execution evidence for the assessed unit's portion plus approved external interface/acceptance evidence; every relevant fully external process has approved interface/acceptance evidence and no internal rating; every out-of-scope process has approved exclusion rationale, no internal rating, and interface evidence only where an actual lifecycle interface exists; every exclusion remains justified; and no activated conditional lifecycle is missing. Block evidence freeze on any absent, stale, inconsistent, wrong-origin, or unsatisfied gate.
- [ ] **0025-03** PREREQ: 0025-03:0025-02 Validate and freeze the ECU evidence index with artifact IDs/revisions, product/project/process/process-instance/baseline metadata, official outcome/indicator mapping, owners, authenticity, completeness, validity, confidentiality, contrary evidence, and unresolved limitations; exclude documentation-pipeline and synthetic execution evidence from ECU outcome claims.
- [ ] **0025-04** PREREQ: 0025-04:0025-03 Conduct and version interviews/observations, validate evidence, characterize every official Level-1 outcome for each selected process, and derive a reasoned `PA 1.1` rating without checklist arithmetic or averaging across different processes.
- [ ] **0025-05** PREREQ: 0025-05:0025-04 Issue a versioned internal Level-1 assessment report containing scope, process instances, method, evidence baseline, outcome judgments, per-process PA 1.1 ratings/capability levels, strengths, weaknesses, risks, assessment disposition, execution responsibility, and findings. A shared in-scope process is rated on the approved process-instance boundary; a fully external or out-of-scope process receives no internal rating.
- [ ] **0025-06** PREREQ: 0025-06:0025-05 Triage every material outcome weakness/finding with root cause, impact, owner, due date, approved correction or accepted-residual decision, links to controlled problems/changes, affected lifecycle evidence, and required re-verification.
- [ ] **0025-07** PREREQ: 0025-07:0025-06 Execute bounded correction, re-verification, effectiveness, evidence-baseline revision, and reassessment cycles; exit only when each declared Level-1 target process has `PA 1.1 = L` or `F`, or management records that the target is unmet and approves a next-cycle plan without a CL1 claim.
- [ ] **0025-08** PREREQ: 0025-08:0025-07 Obtain an independent readiness review of scope, process selection, responsibility allocations, assessor competence, evidence validity, outcome/rating rationale, unresolved risks, and claim wording; record accepted limitations and the recommendation for a formal/external assessment.
- [ ] **0025-09** PREREQ: 0025-09:0025-08 Record the management decision and publish the supported assessment-result profile—with no Level-1 success or CL2-entry claim—with organizational/product scope, release/process instances, PAM version, assessment method/date, evidence baseline, per-process ratings, separate assessment-disposition and execution-responsibility statements, limitations, validity period, and any next-cycle plan.
- [ ] **0025-10** PREREQ: 0025-10:0025-09 Confirm, authorize, and publish the bounded ECU Level-1 success and CL2-handoff statement only when every process in the approved CL2-entry profile has validated `PA 1.1 = L` or `F`, the selected-profile execution register and all conditional edges are satisfied, and the approved evidence baseline and limitations are identified. Closing or publishing an unsuccessful pilot does not satisfy this task.
  - **Acceptance criteria:** The gate evaluates each named process separately, rejects missing/invalid/wrong-origin evidence and any `N`/`P` target rating, and links to the authorized assessment and management decisions.
  - **Definition of Done:** A versioned, independently reviewed and management-authorized pass result plus the exact bounded success/handoff statement are committed; this is the only Level-1 dependency accepted by Feature `0018`.

## Feature: 0026 — Conditional ECU Intended-Use Validation Process Performance (VAL.1)

**PREREQ:** 0026:0020, 0026:0027-05, 0026:0023-10

**Goal:** Perform `VAL.1` only when Feature `0020` assigns intended-use validation to the assessed unit. If responsibility is external/shared, do not execute or rate this Feature internally; register the responsible party, controlled integrated-product input, validation result/acceptance output, change/problem feedback, and assessment interface under `0020-09`.

- [ ] **0026-01** PREREQ: 0026-01:0020-09 Accept the controlled stakeholder expectations/intended-use and integrated-product input baselines from the responsible internal or external lifecycle processes, then define and approve the ECU `VAL.1` strategy/specifications including operational scenarios, representative users/actors and their coverage rationale, representative target environments, variants/configurations and their coverage rationale, measures, sequence, selection/regression rationale, infrastructure, entry/exit and pass/fail criteria, stakeholder trace, acceptance authority, and result retention.
- [ ] **0026-02** PREREQ: 0026-02:0026-01 Execute `VAL.1` on the approved integrated ECU baseline in selected representative operational environments; evaluate and trace results/coverage to stakeholder requirements/intended-use scenarios, resolve or disposition findings, communicate outcomes, retain the authorized acceptance decision, and retain exact integrated-product, hardware/software/calibration/variant, tool, data, user/actor, and environment identity.

## Feature: 0011 — Automotive SPICE CL2 Assessment Method and Governance Foundation

**Goal:** Establish the reusable assessment method, governance, roles, process/work-product catalogue, and claim controls needed to raise the approved ECU profile from Level 1 to Level 2. The automotive ECU domain is confirmed; Feature `0020` owns the concrete ECU product, organizational, responsibility, process-instance, and evidence boundary.

- [u] **0011-01** PREREQ: 0011-01:0020-01 Align the CL2 assessment purpose, organizational/product boundary, PAM version, process profile/instances, exclusions, target dates, and claim wording with the sponsor/manager and competent-assessor decisions for the concrete ECU scope; record the CL2 extension in a versioned assessment input. This remains blocked until `0020-01` identifies the ECU instance.
- [ ] **0011-02** PREREQ: 0011-02:0011-01, 0011-02:0020-07 Extend the single approved Level-1 assessment method and worksheets with PA 2.1/PA 2.2 achievements, CL2 aggregation/rating rationale, assessor competence/independence, evidence validation, and report content; do not create a parallel assessment method or duplicate Level-1 outcome worksheets.
- [ ] **0011-03** PREREQ: 0011-03:0011-01 Reconcile `docs/pipeline/aspice-level1-score-import.md`, Feature 0019 acceptance wording, and all other ASPICE claims with the approved named-process outcomes; preserve the `0010`→`0019` alias note and prohibit capability wording unsupported by an assessment.
- [ ] **0011-04** PREREQ: 0011-04:0011-01 Define and assign the process-owner, performer, reviewer, approver, curator, release-authority, QA, assessor, and escalation roles, including authorities, independence requirements, deputies, and required competencies.
- [ ] **0011-05** PREREQ: 0011-05:0011-01, 0011-05:0011-04, 0011-05:0020-08 Extend the single ECU process/work-product/evidence catalogue with PA 2.1/PA 2.2 requirements, quality/control criteria, repositories, owners, review/approval rules, and retained attribute evidence; do not create a separate CL2 catalogue.
- [ ] **0011-06** PREREQ: 0011-06:0011-02, 0011-06:0011-03, 0011-06:0011-04, 0011-06:0011-05 Baseline process-by-process evidence coverage for the approved ECU profile without assigning unsupported capability levels; record product/process-instance/origin, evidence revisions/validity and contrary evidence, keep documentation execution separate, and open traceable findings for every unsupported outcome or attribute achievement.

## Feature: 0012 — Managed Process Performance (PA 2.1 and MAN.3)

**PREREQ:** 0012:0011

- [ ] **0012-01** PREREQ: 0012-01:0011-01 Define and approve MAN.3 project goals/motivation, boundaries, lifecycle, release scope, feasibility evaluation, and consistency rules for plans, estimates, resources, commitments, and schedule.
- [ ] **0012-02** PREREQ: 0012-02:0012-01, 0012-02:0012-08 Establish an integrated project/process plan with work packages, dependencies, estimates, schedule, milestones, deliverables, entry/exit criteria, and commitments for each release or campaign.
- [ ] **0012-03** PREREQ: 0012-03:0012-02 Determine and record human-resource quantities/availability, role authority, competency needs, qualification actions, tools, licenses, infrastructure, services, data, and other material-resource needs.
- [ ] **0012-04** PREREQ: 0012-04:0011-04, 0012-04:0012-03 Assign named qualified people and physical/material resources to process-instance work packages, communicate responsibilities/authority, confirm competence and availability, and define how allocation and actual use will be retained during managed execution. This is a readiness task; actual resource use must be operated and evidenced in `0018-02`.
- [ ] **0012-05** PREREQ: 0012-05:0011-04, 0012-05:0012-02 Define and operate an interface/communication matrix covering internal/external parties, responsibilities, commitments, channels, cadence, response/escalation expectations, and required communication records.
- [ ] **0012-06** PREREQ: 0012-06:0012-02 Define and implement the recurring actual-versus-plan review mechanism, cadence, authority, escalation, and evidence contract for deviations, cause, impact, owner, due date, corrective action, replanning, decision, closure, and effectiveness. This is a readiness task; recurring reviews and adjustments must be operated in `0018-02`.
- [ ] **0012-07** PREREQ: 0012-07:0012-02, 0012-07:0012-03, 0012-07:0012-04, 0012-07:0012-05, 0012-07:0012-06, 0012-07:0012-08 Extend campaign/project-plan schemas, validators, reports, templates, and controlled retention paths before managed execution so PA 2.1 evidence is generated and correlated through normal work rather than reconstructed retrospectively; add negative checks for missing, stale, cross-process-instance, or retrospectively fabricated stage evidence.
- [ ] **0012-08** PREREQ: 0012-08:0011-05, 0012-08:0012-01 Define a performance strategy and measurable/assessable objectives, criteria, assumptions, constraints, and methods for every scoped process.
- [ ] **0012-09** PREREQ: 0012-09:0012-07 Confirm pre-execution PA 2.1 readiness for every scoped ECU process: approved strategy/objectives, integrated plan, resource needs and named assignments, competence/availability, interfaces/communications, monitoring/adjustment method, and controlled evidence capture are available before the managed pilot. This gate makes no claim that PA 2.1 has been operationally achieved.
  - **Acceptance criteria:** The review is process-specific and fails on an unassigned authority, unavailable resource, missing interface, unapproved plan, or missing evidence-capture path.
  - **Definition of Done:** A versioned readiness report identifies the approved ECU scope/baseline, every pass/fail result, reviewer/authority, findings, and closure or blocking status.

## Feature: 0013 — Stakeholder and Software Requirements with Lifecycle Traceability

**PREREQ:** 0013:0011

- [ ] **0013-01** PREREQ: 0013-01:0011-01 Identify stakeholder groups, sources, intended-use scenarios, operating environments, needs, constraints, communication channels, and agreement authorities for the assessed product.
- [ ] **0013-02** PREREQ: 0013-02:0013-01 Create and approve a versioned stakeholder-requirements baseline with stable IDs, source, rationale, priority, acceptance criteria, status, change history, and validation method.
- [ ] **0013-03** PREREQ: 0013-03:0013-02 Derive, structure, prioritize, analyze, agree, and communicate a versioned software-requirements baseline covering functional/non-functional behavior, data/provenance integrity, determinism, performance, security/privacy, accessibility, i18n, reporting, deployment, and support; record correctness, feasibility, interdependency, effort/schedule, operating-environment impact, rationale, status, and verification method.
- [ ] **0013-04** PREREQ: 0013-04:0013-03 Update, technically analyze, agree, approve, and communicate the software architecture against requirements/quality criteria, including static components/interfaces, dynamic behavior/interactions, external interfaces, failure modes, deployment, estimates, alternatives, and rationale.
- [ ] **0013-05** PREREQ: 0013-05:0013-04 Create, agree, and communicate static/dynamic detailed designs and interface/data/behavior contracts for defined software units; define coding principles, design records, and code-review criteria and map units to architecture elements.
- [ ] **0013-06** PREREQ: 0013-06:0013-03, 0013-06:0013-04, 0013-06:0013-05 Define the lifecycle trace schema and implement automated consistency checks for stakeholder requirements, software requirements, architecture, detailed design/units, and source code; Features 0014 and 0016 extend the same schema to verification/validation and change/release evidence.
- [ ] **0013-07** PREREQ: 0013-07:0013-02, 0013-07:0013-03 Inventory and classify requirement candidates scattered across TODOs, conventions, maintenance/process documents, schemas, and tests; identify duplicates, conflicts, design statements, process rules, and imported domain content without migrating them yet.
- [ ] **0013-08** PREREQ: 0013-08:0013-02, 0013-08:0013-03 Define and operate requirement agreement, status communication, change-impact analysis, consistency review, and baseline supersession procedures with retained decisions.
- [ ] **0013-09** PREREQ: 0013-09:0013-05 Construct or confirm every in-scope unit against its detailed design and coding principles, record code-review/construction findings, correct inconsistencies, and communicate the agreed design/units.
- [ ] **0013-10** PREREQ: 0013-10:0013-07, 0013-10:0013-08 Migrate approved requirement candidates into the controlled hierarchy in reviewable batches while retaining source links and supersession history.
- [ ] **0013-11** PREREQ: 0013-11:0013-06, 0013-11:0013-09, 0013-11:0013-10 Populate and review bidirectional stakeholder-requirement ↔ software-requirement ↔ architecture ↔ detailed-design/unit ↔ source-code traces and close unexplained gaps.

## Feature: 0014 — Lifecycle-Level Verification, Intended-Use Validation, and Quality Assurance

**PREREQ:** 0014:0012, 0014:0013

- [ ] **0014-01** PREREQ: 0014-01:0013-03, 0014-01:0013-05 Define reviewed strategies for SWE.4 unit verification, SWE.5 component/integration verification, and SWE.6 integrated-software verification, including methods, selection, coverage, regression, environments, entry/exit, pass/fail, and result-retention criteria.
- [ ] **0014-02** PREREQ: 0014-02:0014-01, 0014-02:0013-11 Create versioned verification specifications and traces with the correct basis at each level: SWE.4 detailed-design/unit ↔ measure ↔ result, SWE.5 architecture/detailed-design ↔ component/integration measure ↔ result, and SWE.6 software requirement ↔ integrated-software measure ↔ result.
- [ ] **0014-03** PREREQ: 0014-03:0014-01, 0014-03:0015-03, 0014-03:0015-04 Control verification environments, tools, dependencies, fixtures, test data, expected results, coverage metrics, and regression-selection rationale as configuration items.
- [p] **0014-04** PREREQ: 0014-04:0014-01, 0014-04:0015-06 Correct validation/reporting gate weaknesses, including real review/curation queue discovery, mandatory client-render coverage or approved exception, shared run identity, complete required subreports, and failure on missing/inconsistent stage evidence; add regression tests. Queue discovery under `_src/spec/*-queue`, curation-item conformance, malformed-JSON continuation, and regression tests were fixed on 2026-08-15; client-render enforcement, run correlation, complete subreports, and missing-stage failure remain open.
- [ ] **0014-05** PREREQ: 0014-05:0007-04, 0014-05:0014-03 Qualify the independently approved and frozen 200-record extraction benchmark for the verification strategy: define its applicability, shape/document coverage and limits, regression-selection use, controlled environment, and retained benchmark-version/hash evidence without treating it as ECU verification evidence.
- [ ] **0014-06** PREREQ: 0014-06:0013-02 Define and review a VAL.1 specification/strategy with representative users and operational target environments, validation measures, sequence, infrastructure, entry/exit and pass/fail criteria, release/regression selection, stakeholder trace, result evaluation, communication, and acceptance authority.
- [ ] **0014-07** PREREQ: 0014-07:0011-04, 0014-07:0011-05 Establish an objective SUP.1 quality-assurance plan with independence safeguards, process/work-product conformance checks, audit schedule, nonconformance records, escalation, management resolution, recurrence prevention, and closure criteria.
- [ ] **0014-08** PREREQ: 0014-08:0014-02, 0014-08:0014-03 Execute selected SWE.4 unit-verification measures, record pass/fail data and coverage, trace results to measures/units, resolve findings, and communicate the summary.
- [ ] **0014-09** PREREQ: 0014-09:0014-02, 0014-09:0014-03 Define integration sequence/preconditions, integrate components to complete software, execute selected SWE.5 component/integration measures, record/trace results, resolve findings, and communicate the summary.
- [ ] **0014-10** PREREQ: 0014-10:0014-02, 0014-10:0014-03 Execute selected SWE.6 integrated-software measures against software requirements, record pass/fail data and coverage, trace results, resolve findings, and communicate the summary.
- [ ] **0014-11** PREREQ: 0014-11:0014-03, 0014-11:0014-06 Execute VAL.1 in selected operational environments, evaluate and trace results to measures/stakeholder expectations, resolve or disposition findings, communicate outcomes, and retain the acceptance decision.
- [ ] **0014-12** PREREQ: 0014-12:0014-07 Execute independent product/process QA checks, report conformances/nonconformances, issue regular quality-status/trend summaries to all affected parties, escalate unresolved issues, obtain management resolution, verify corrective action, and retain communication, closure, and recurrence-prevention evidence.
- [ ] **0014-13** PREREQ: 0014-13:0014-04, 0014-13:0014-08, 0014-13:0014-09, 0014-13:0014-10, 0014-13:0014-11, 0014-13:0014-12, 0014-13:0015-06, 0014-13:0015-07, 0014-13:0016-01, 0014-13:0016-02 Retain release-specific verification, validation, and QA summaries with exact baseline/tool/environment identity, findings, waivers, approvals, issue links, communication, and closure evidence.

## Feature: 0015 — Work-Product and Configuration Management (PA 2.2 and SUP.8)

**PREREQ:** 0015:0011

- [ ] **0015-01** PREREQ: 0015-01:0011-05 Complete the controlled work-product/configuration-item catalogue for requirements, plans, records, source, generated artifacts, schemas, tests, reports, decisions, problems/changes, dependencies, releases, and assessment evidence.
- [ ] **0015-02** PREREQ: 0015-02:0015-01 Define per-type content/metadata/quality requirements and review/approval, identification, status, access, storage, distribution, versioning, baselining, backup/recovery, retention, archival, disposal, license, and sensitivity controls.
- [ ] **0015-03** PREREQ: 0015-03:0015-02 Implement configuration identification, controlled change, baseline creation, configuration-status accounting, completeness/consistency audits, and uniquely reproducible release/campaign baseline IDs.
- [ ] **0015-04** PREREQ: 0015-04:0015-02 Pin and record Python/Node/system-tool dependencies and external input/source identities with content hashes; verify deterministic clean-checkout restoration without moving references or undeclared environment state.
- [ ] **0015-05** PREREQ: 0015-05:0015-03 Wire campaign manifests, append-only requirement versions, and lifecycle validation into real extraction/ingest/publication writers; segregate synthetic fixtures from production stores.
- [ ] **0015-06** PREREQ: 0015-06:0015-03, 0015-06:0015-04 Establish a controlled immutable evidence repository for runner scripts/logs, all correlated subreports, test/QA results, decisions, approvals, and release records; replace reliance on ignored transient `output/` evidence.
- [ ] **0015-07** PREREQ: 0015-07:0015-02 Define and enforce review/approval criteria and evidence schemas for each controlled work-product type, including authenticated actor, role/authority, version reviewed, criteria, findings, decision, timestamp, and issue closure.
- [ ] **0015-08** PREREQ: 0015-08:0015-03, 0015-08:0015-06 Perform and retain configuration audits plus backup/restore tests for a representative source, campaign, evidence bundle, and published release baseline; record the mechanism's limits. Documentation source/campaign evidence qualifies only that mechanism and cannot satisfy ECU PA 2.2 or ECU `SUP.8` without application to the approved ECU product/process instance and baseline.
- [ ] **0015-09** PREREQ: 0015-09:0015-05 Wire evidence snippets, dependency edges, supersession triggers, invalidation/revisit results, and their reports into real writers and controlled stores.
- [ ] **0015-10** PREREQ: 0015-10:0015-07, 0015-10:0018-03 Verify that PA 2.2 work-product review and adjustment was operated throughout all scoped ECU pilot process instances: retain and check the exact version reviewed, applicable content/quality/review criteria, reviewer authority, findings, decisions, resulting revisions, consistency checks, and issue closure; explicitly justify any work-product type requiring no review or approval.
  - **Acceptance criteria:** Every selected process's produced work-product types are covered; missing criteria, unreviewed required products, unresolved material findings, wrong-product evidence, or an unexplained no-review classification fail the gate.
  - **Definition of Done:** The controlled ECU evidence set contains linked review/adjustment records and an independently checked coverage report for the approved process instances and baseline.

## Feature: 0016 — Problem Resolution, Change Request, and Product Release Control

**PREREQ:** 0016:0011, 0016:0015

- [ ] **0016-01** PREREQ: 0016-01:0011-05 Define one SUP.9 problem-record model and lifecycle covering unique identity, reproducibility, classification, severity/priority, cause/common cause, impact, recorded authorization before urgent action, high-impact alert criteria/recipients, owner, durable resolution, verification, communication, closure, and trend data.
- [ ] **0016-02** PREREQ: 0016-02:0011-05 Define one SUP.10 change-request model and lifecycle covering identity/status, initiator, rationale, affected baselines, dependencies, resource/schedule/risk impact, priority, approval authority, implementation trace, verification, communication, and closure.
- [ ] **0016-03** PREREQ: 0016-03:0016-01, 0016-03:0016-02 Define classification/linking rules that keep MAN.3 work packages and improvement work in the managed plan, create SUP.9 records only for problems, create SUP.10 records only for requested changes, and link related records without conflating their lifecycles.
- [ ] **0016-04** PREREQ: 0016-04:0013-08, 0016-04:0016-02 Enforce change impact analysis, prioritization, authorization, and traceability to requirements, architecture/design/code, tests, risks, plans, configuration items, and intended release before implementation.
- [ ] **0016-05** PREREQ: 0016-05:0014-13, 0016-05:0016-01, 0016-05:0016-02, 0016-05:0016-04 Enforce implementation confirmation, independent verification where required, affected-work-product consistency, requester/affected-party communication, accepted closure, and trend/common-cause reporting.
- [ ] **0016-06** PREREQ: 0016-06:0015-03, 0016-06:0015-07 Define SPL.2 release content, identification, eligibility/approval criteria, package assembly from controlled items, release notes, known limitations, licenses, support type/service level/duration, delivery, rollback, and release-record requirements.
- [ ] **0016-07** PREREQ: 0016-07:0014-13, 0016-07:0015-06, 0016-07:0016-06 Make publication verify one complete atomic evidence bundle and approved baseline before delivery, package every configured artifact/language/report, and retain approval, delivery verification, and rollback evidence.
- [ ] **0016-08** PREREQ: 0016-08:0016-04, 0016-08:0016-05, 0016-08:0016-07 Process one accepted change through authorization, implementation, verification, release, communication, and closure with full trace.
- [ ] **0016-09** PREREQ: 0016-09:0016-03, 0016-09:0016-04 Process one rejected or withdrawn change through impact analysis, authorization decision, communication, and closure without implementation/release.
- [ ] **0016-10** PREREQ: 0016-10:0016-01, 0016-10:0016-03 Exercise a high-impact problem/alert path through recorded urgent-action authorization, immediate action, recipient notification, durable resolution, verification, communication, and closure; label controlled scenarios distinctly if no real event is available.
- [ ] **0016-11** PREREQ: 0016-11:0015-09, 0016-11:0016-05 Demonstrate one supersession/invalidation path with preserved audit history, affected-party communication, revisit work, verification, and closure.
- [ ] **0016-12** PREREQ: 0016-12:0016-08, 0016-12:0016-09, 0016-12:0016-10 Produce and regularly communicate problem/change status and trend reports to relevant stakeholders, initiate related corrective/preventive actions from identified trends, and keep any fixture/scenario evidence explicitly separate.
- [ ] **0016-13** PREREQ: 0016-13:0012-02, 0016-13:0016-03 Classify TODO/BACKLOG entries, retain planning work as managed work packages, migrate only true problems/changes, preserve aliases/history, and retire competing active backlog semantics.
- [ ] **0016-14** PREREQ: 0016-14:0016-03 Integrate GitHub/browser intake with canonical problem/change creation and authenticated communication evidence.
- [ ] **0016-15** PREREQ: 0016-15:0016-03 Integrate validation findings, extraction residuals, review/curation queues, and AI proposals with canonical problem/change links without replacing their domain-specific records.

## Feature: 0017 — Risk Management, Measurement, and Management Review

**PREREQ:** 0017:0012, 0017:0015, 0017:0016

- [ ] **0017-01** PREREQ: 0017-01:0011-01 Define and approve the MAN.5 risk strategy, categories/sources, probability/impact/exposure criteria, thresholds, acceptance/escalation authority, review cadence, reporting, and retention rules.
- [ ] **0017-02** PREREQ: 0017-02:0017-01 Establish a maintained risk register for source drift, normative misinterpretation, provenance loss, data quality, nondeterminism, security/privacy/license exposure, AI/external services, resource/competency gaps, verification/validation, and publication; assign owners, treatments, dates, residual risk, and links to plans/changes.
- [ ] **0017-03** PREREQ: 0017-03:0017-02 Operate recurring risk identification and treatment reviews, monitor exposure and action effectiveness, escalate threshold breaches, update plans, and retain decisions and accepted closure/residual-risk evidence.
- [ ] **0017-04** PREREQ: 0017-04:0012-08 Define MAN.6 management information needs and trace them to operational process/product metrics for outcome/quality, schedule/effort, resources, defects/changes, review closure, coverage, fallback/reject counts, trace completeness, release health, and user validation.
- [ ] **0017-05** PREREQ: 0017-05:0017-04 Specify each metric’s definition, unit, source, owner, collection/validation method, baseline, target/threshold, cadence, analysis, presentation, retention, and decision use; version the measurement specification.
- [ ] **0017-06** PREREQ: 0017-06:0015-06, 0017-06:0017-05 Implement trustworthy correlated collection and trend reporting, including completeness/data-quality flags so missing stages or incomparable process instances cannot appear as successful measurements.
- [ ] **0017-07** PREREQ: 0017-07:0012-06, 0017-07:0017-03, 0017-07:0017-06 Hold periodic management reviews of objectives, actual-versus-plan performance, resources/competencies, risks, metrics, QA findings, problems/changes, and release readiness; retain decisions, owners, due dates, replanning, escalation, and closure.

## Feature: 0018 — Automotive ECU SPICE CL2 Pilot, Internal Assessment, and Readiness Closure

**PREREQ:** 0018:0011, 0018:0012-09, 0018:0015-07, 0018:0015-08, 0018:0025-10

- [ ] **0018-01** PREREQ: 0018-01:0011-02, 0018-01:0012-09, 0018-01:0025-10 Select and approve representative ECU pilot process instances/releases, assessment schedule, planned interview roles, ECU evidence baseline, sampling/aggregation, and independence safeguards; documentation campaigns such as Feature `0019` may contribute reusable definitions/mechanisms only and cannot enter as ECU execution evidence or imported ratings.
- [ ] **0018-02** PREREQ: 0018-02:0018-01 Execute an end-to-end managed ECU pilot using all selected planning, requirements, traceability, verification/validation/QA, configuration, problem/change/release, risk, measurement, and review controls. For every scoped process, operate and retain resource allocation/use, competence/availability, interface management, actual-versus-plan monitoring, correction, replanning, communication, and closure evidence in one atomic ECU evidence set.
- [ ] **0018-03** PREREQ: 0018-03:0018-02 Execute the additional representative ECU process instance(s) or equivalent sampling approved in `0018-01`, applying lessons through controlled process adjustment and demonstrating repeatability rather than one-off compliance construction; do not impose a fixed sample count beyond the approved assessment input.
- [ ] **0018-04** PREREQ: 0018-04:0015-10, 0018-04:0018-02, 0018-04:0018-03 Validate and freeze the pre-assessment ECU evidence index, including artifact IDs/revisions, product/project/process/process-instance/baseline and origin metadata, process/outcome/attribute mapping, owners, authenticity, completeness, confidentiality, and unresolved limitations; interview records are added/versioned during assessment.
- [ ] **0018-05** PREREQ: 0018-05:0018-04 Perform the internal R1-style assessment, conduct and version interviews, validate evidence, characterize every Level-1 outcome and PA 2.1/PA 2.2 achievement for every scoped process, derive the capability profile, and issue a versioned assessment report with strengths, weaknesses, risks, and findings.
- [ ] **0018-06** PREREQ: 0018-06:0018-05 Triage every assessment finding, record root cause/impact/owner/due date and an approved correction or accepted-residual disposition, and create bounded child remediation tasks linked to controlled changes and required re-verification.
- [ ] **0018-07** PREREQ: 0018-07:0018-06 Execute versioned correction/re-verification/effectiveness cycles, publish a new evidence-baseline revision and reassessment after each cycle, and exit only when no CL2-blocking finding remains or the sponsor records that CL2 cannot be claimed and opens a next-cycle plan. A finding is CL2-blocking whenever it prevents `PA 1.1 = F`, `PA 2.1 = L/F`, or `PA 2.2 = L/F` for any declared target process.
- [ ] **0018-08** PREREQ: 0018-08:0018-07 Obtain an independent readiness review of applicability, scope, assessor competence, evidence validity, ratings, open risks, and claim wording; record accepted residual limitations and recommendation on formal external assessment.
- [ ] **0018-09** PREREQ: 0018-09:0018-08 Record the management decision and publish the final assessment-result profile without a CL2 claim, including organizational/supplied-product scope, process instances, PAM version, assessment method/date, ECU evidence baseline, per-process ratings, separate assessment-disposition and execution-responsibility statements, limitations, validity period, and any next-cycle plan. A shared in-scope process is rated on the approved process-instance boundary; a fully external or out-of-scope process receives no internal rating.
- [ ] **0018-10** PREREQ: 0018-10:0018-09 Confirm the CL2 claim gate separately for every declared target process and authorize/publish the exact bounded claim only when `PA 1.1 = F`, `PA 2.1 = L` or `F`, and `PA 2.2 = L` or `F`, with no averaging across attributes or processes. Closing or publishing an unsuccessful pilot without a CL2 claim does not satisfy this task, and the claim must not imply safety, cybersecurity, regulatory, or product certification.
  - **Acceptance criteria:** The gate uses the approved scope, process instances, evidence baseline, assessment method, and authorized ratings; any missing process/attribute result, unsupported aggregation, invalid evidence, or blocking limitation fails it.
  - **Definition of Done:** A versioned independent-readiness and management-authorization record supports the exact bounded claim, and the authorized claim/profile is published and committed with its evidence references.

## Feature: 0019 — Eclipse S-Core Database Import

**PREREQ:** 0019:0006

**ID note:** Renumbered from the conflicting active ID `0010`; historical `0010` remains the completed Performance Package 2 in `DONE.md`. All active task IDs use the `0019-*` namespace.

**Overall goal:** Establish a reproducible, traceable, and curator-governed import of the Eclipse S-Core **v0.6.0** release into the existing specification database. The finished capability must ingest the release-pinned source set as `ECLIPSE/S-CORE` records, validate and expose the results through the same curation, history, and generated HTML mechanisms as the AUTOSAR corpus, and retain a local documentation-campaign evidence set that can be mapped to named documentation-process outcomes after Feature `0011-03`; Feature `0020-02` classifies it as `documentation-execution`, and it makes no ECU or Automotive SPICE capability claim by itself.

**Scope boundary:** This feature imports canonical, release-pinned S-Core source artifacts only—initially `module`, `component`, `design-doc`, and `process-doc` records. It does not certify S-Core for production use, infer undocumented APIs, or claim an Automotive SPICE capability level. It reuses the canonical identity/version conventions in `docs/pipeline/score-identity-scheme.md`, the campaign lifecycle in `docs/pipeline/processes.md`, and the local campaign-evidence contract in `docs/pipeline/aspice-level1-score-import.md` pending `0011-03` reconciliation.

**Feature Definition of Done:**
- A committed, release-pinned `v0.6.0` snapshot manifest identifies every imported repository, upstream tag/ref, resolved SHA, source URI/path, hash, and extraction-tool revision.
- The importer can reproduce the record corpus from that manifest on a clean checkout without network-dependent ambiguity; repeated runs yield no semantic record differences.
- Imported records use the registered `ECLIPSE/S-CORE` kinds, canonical IDs, version IDs, provenance, status/history, and traceability required by the shared data model.
- Automated structural, schema, provenance, traceability, and generated-HTML validation passes are green; their persisted report gives counts and findings.
- All unresolved or non-automatically verifiable items enter the unified review/curation lifecycle, are visible to users, and no such item is silently published as a fact.
- The campaign has a human-readable close report, explicit curator release decision, and a commit reference; the five acceptance conditions in `docs/pipeline/aspice-level1-score-import.md` are evidenced.

### Campaign A — Source Baseline and Import Contract

- [ ] **0019-01** Establish the v0.6.0 source bill of materials and release-pinning policy.
  - **Acceptance criteria:** A reviewed `_src/spec/campaigns/eclipse-score-v0.6.0.json` exists and lists every in-scope repository/component, upstream release label/ref, resolved immutable commit SHA, source URL, source-tree path(s), content/archive hash, license/source notice, and `score_scrape.py` revision; exclusions and their rationale are recorded; the manifest validates against the campaign schema.
  - **Definition of Done:** Manifest/schema validation and a reproducibility check pass; the manifest is committed; the source set is sufficient to re-fetch or verify every imported artifact without referring to `main`.

- [ ] **0019-02** PREREQ: 0019-02:0019-01 Create an immutable local source snapshot and evidence inventory for the v0.6.0 BOM.
  - **Acceptance criteria:** Each manifest source resolves to the declared SHA; immutable source contents or a deterministic local archive/snapshot plus inventory with SHA-256 hashes are retained for every in-scope source; every source artifact selected for extraction has repository, ref, commit, path, and locator evidence; absent/unavailable artifacts block completion or are explicitly removed from scope with rationale in `0019-01`, never omitted silently.
  - **Definition of Done:** A clean-environment verification reconstructs the same source inventory and hashes without depending on upstream availability; the snapshot/inventory report is committed or retained in an immutable controlled store and linked from the campaign manifest.

- [ ] **0019-03** PREREQ: 0019-03:0019-01 Define and test the S-Core import profile: source selectors, supported artifact classes, field mapping, status defaults, and explicit non-goals.
  - **Acceptance criteria:** A versioned import-profile document/config maps each supported source class to `module`, `component`, `design-doc`, or `process-doc`; it identifies mandatory fields, source locators, status/traceability defaults, duplicate/conflict behavior, and conditions that must create a review/curation item; sample artifacts from every in-scope repository demonstrate the mapping.
  - **Definition of Done:** Profile is reviewed against `score-identity-scheme.md`, `data-model.md`, `status-model.md`, and `processes.md`; automated fixtures cover every supported class and every defined rejection/queue condition.

### Campaign B — Extraction and Normalization

- [ ] **0019-04** PREREQ: 0019-04:0019-02, 0019-04:0019-03 Implement the v0.6.0 manifest-driven S-Core extraction adapter.
  - **Acceptance criteria:** The adapter accepts only a manifest-pinned source set, extracts the profile’s supported artifacts, and emits deterministic raw extraction output; it does not fall back to moving refs such as `main`; failures identify repo/ref/path/locator and leave no partial canonical corpus presented as complete.
  - **Definition of Done:** Unit and integration tests cover successful extraction, missing source, invalid ref/hash, malformed Sphinx-needs item, duplicate identity, and unsupported artifact; repeated extraction from the same snapshot produces identical normalized raw output.

- [ ] **0019-05** PREREQ: 0019-05:0019-04 Normalize raw S-Core extraction output into canonical versioned records.
  - **Acceptance criteria:** Every emitted record conforms to `ECLIPSE/S-CORE/<kind>/<id>@rel:<release>#<content-hash8>`, carries all non-canonical provenance required by `score-identity-scheme.md`, contains source-backed traceability, has an initial status/reason and history entry, and records content hashes deterministically; identity collisions and source contradictions emit deterministic structured exception candidates for `0019-07` rather than being overwritten or prematurely queued.
  - **Definition of Done:** Schema, canonical-ID, version-ID, provenance, and deterministic-content-hash tests pass; a fixture corpus demonstrates each of the four supported kinds plus collision and contradiction handling.

- [ ] **0019-06** PREREQ: 0019-06:0019-05 Implement S-Core-specific validation and campaign evidence reporting.
  - **Acceptance criteria:** Validation checks record schema, kind/ID registry conformance, source-ref/SHA integrity, required provenance, traceability, module/component containment, dangling references, malformed Sphinx-needs identities, duplicate versions, and status consistency; a persisted report provides pass/fail, totals by kind/status, structured exception-candidate counts, tool/version metadata, and actionable findings without claiming candidates are queued before `0019-07`.
  - **Definition of Done:** Negative fixtures prove every validation class fails correctly; the validation report is machine-readable and human-readable, retained with the campaign, and meets the validation-evidence conditions in `aspice-level1-score-import.md`.

### Campaign C — Curation, Publication, and Acceptance

- [ ] **0019-07** PREREQ: 0019-07:0019-05, 0019-07:0019-06 Integrate validated S-Core exception candidates with the unified review and curation lifecycle.
  - **Acceptance criteria:** Unsupported, ambiguous, conflicting, missing-provenance, and non-auto-verifiable S-Core records create canonical `curation-item@v1` or review items with source/version evidence; queue states and allowed actors follow `workflow-lifecycle.md` and `roles.md`; user-facing reports link from each queue item to its record/version/source locator.
  - **Definition of Done:** End-to-end tests demonstrate both `discovered → queued → claimed → proposed → accepted → applied → published` and `discovered → queued → claimed → proposed → rejected → retained/closed without application or publication` for S-Core samples; no tool or AI path can silently perform an `accepted`/`rejected` content decision.

- [ ] **0019-08** PREREQ: 0019-08:0019-06, 0019-08:0019-07 Perform the Phase-6 validation and curator release-readiness review before generated-tree publication.
  - **Acceptance criteria:** The persisted validation report passes; record/status and exception/queue counts reconcile; unresolved items, exclusions, low-confidence decisions, and hypotheses are quantified and linked; the curator reviews every required class and records accept, reject, or explicitly bounded conditional acceptance for the exact corpus/report versions. A rejection or blocking condition leaves this task open and creates linked remediation/re-run work.
  - **Definition of Done:** An authenticated accepting decision (or defined non-blocking conditional acceptance) identifies the exact source snapshot, record corpus, validation report, queue snapshot, permitted publication scope, limitations, and required post-generation checks; no generated tree is published before this gate.

- [ ] **0019-09** PREREQ: 0019-09:0019-08 Generate and validate the curator-authorized S-Core v0.6.0 views.
  - **Acceptance criteria:** Only records authorized by `0019-08` are rendered into the HTML tree with record history, canonical/version identity, provenance/traceability, and review indicators; invalid/hypothesized/unresolved records remain excluded from factual publication while visible in curation/review reports; all language-tree, DOM, link, and client-rendered validation checks pass.
  - **Definition of Done:** A clean generation is repeatable with zero semantic differences; report counts reconcile exactly with the authorized corpus, campaign validation report, and queue snapshot; screenshots/DOM assertions cover at least one record of every kind and one unresolved case.

- [ ] **0019-10** PREREQ: 0019-10:0019-09 Publish the authorized views and close the v0.6.0 import campaign and local campaign-evidence record under `docs/pipeline/aspice-level1-score-import.md` without waiting for ECU scope; classify its canonical origin as `documentation-execution`, describe it as documentation-campaign evidence, make no capability claim, and leave any later named documentation-process mapping to `0011-03`.
  - **Acceptance criteria:** Post-generation checks satisfy the decision in `0019-08`; the campaign report demonstrates every criterion in `aspice-level1-score-import.md`: committed manifest, traced/versioned records, persisted validation outcome, human-readable outcome summary, explicit curator decision, publication result, and campaign closure; unresolved items and exclusions are quantified and linked to queues.
  - **Definition of Done:** Campaign is closed according to Phase 6 of `processes.md`, the accepting decision/closure report and generated result are committed, no open validation blocker is mislabeled as valid, and all Feature 0019 Definition-of-Done bullets are independently evidenced by committed artifacts and test reports.


## Feature: 0007 — Database Quality Assurance

**PREREQ:** 0007:0006

**Goal:** Establish a source-backed, independently approved, immutable 200-record extraction benchmark and automated regression gate without turning unexplained `null` values or unsupported shape assumptions into ground truth.

**Feature Definition of Done:**
- The candidate contains exactly 200 uniquely identified benchmark entries/cases with the documented 18-document and difficult-shape coverage, and every expected value or non-record disposition is traceable to source pages/locators.
- Every record has completed review metadata and an explicit start/end completeness disposition; legitimate inline citations or non-records use a documented `not-applicable`/exclusion state rather than an unexplained `null`.
- Every parser shape represented by the benchmark has a source-backed definition and positive/negative regression fixture; an unlocated or disproved example is corrected or retired rather than implemented speculatively.
- An independent reviewer approves the exact candidate version, limitations, and coverage; the approved benchmark is frozen with a stable ID/content hash and enforced by an automated comparison that fails on semantic extraction drift.

### Campaign A — Candidate truth set

- [p] **0007-01** PREREQ: 0007-01:0006 Complete source-backed truthing of the 200-record benchmark and produce a reviewable freeze candidate.
  - **Acceptance criteria:** Exactly 200 unique entries cover all 18 source documents and the selection policy's difficult shapes; every entry records source pages/locator, expected heading/fields/pages, explicit completeness disposition, reviewer identity/status/notes, and any exclusion/non-record rationale. No entry remains `needs_review`, and no unexplained `complete_start = null` is accepted as a freeze result.
  - **Definition of Done:** The candidate schema/version, inventory, coverage report, and validation command are committed; automated checks reject duplicate/missing entries, unresolved review state, missing provenance, and invalid completeness dispositions.
  - **History (2026-08-12):** Manually truthed the two previously called-out empty-field cases: `RS_SAF_21101` is an inline citation rather than a formal block, while mixed-case source ID `RS_DIAG_04005` is a real formal block with recovered heading/fields and `complete_start = true`.
  - **History (2026-08-12, pre-fix):** A recount found 12 headingless-but-populated `AUTOSAR_FO_RS_LogAndTrace` entries (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`).
  - **History (2026-08-12, current):** Commit `fdba7e28` added the numbered-subsection heading fallback and updated the expected values; the same recount then found zero headingless-but-populated entries. The remaining candidate blockers are unresolved review/completeness metadata, not those 12 headings.

### Campaign B — Shape precision

- [p] **0007-02** Resolve the claimed dense-definition-list/inline-heading record shape from concrete source evidence and retain the already verified `RS_LT` numbered-subsection variant as a distinct shape.
  - **Acceptance criteria:** Locate and cite at least one real instance matching the exact claimed inline-heading/no-marker shape and add positive/negative fixtures, or document that the cited `RS_PHM_00001..00003` example does not support that shape and correct/retire the unsupported claim. Do not generalize the `RS_LT` fallback to a materially different layout without source evidence.
  - **Definition of Done:** Shape documentation names exact source locators and parser boundaries; focused and benchmark regression tests pass for every retained shape and prove unrelated prose/citations are not promoted to records.
  - **History (2026-08-12):** Commit `fdba7e28` implemented the separate `AUTOSAR_FO_RS_LogAndTrace` pattern—a numbered subsection immediately above a bare `[RS_LT_xxxxx]` marker—and all 12 affected benchmark headings now pass. The originally cited `RS_PHM_00001..00003` example is absent from the benchmark and remains unverified.

### Campaign C — Independent approval and enforcement

- [ ] **0007-03** PREREQ: 0007-03:0007-01, 0007-03:0007-02 Conduct an independent review of the candidate truth set, source evidence, completeness/exclusion dispositions, shape coverage, known limits, and reproducibility, and obtain approval for its use as a regression oracle without allowing the preparer to self-approve.
  - **Acceptance criteria:** The reviewer is identified and sufficiently independent/competent; every material finding is closed with an owner/disposition; the approving decision identifies the exact candidate version/hash and accepted limitations. A rejection or returned finding keeps this task `[p]` and triggers remediation/re-review; it does not unblock `0007-04`.
  - **Definition of Done:** A signed or otherwise authenticated approval record and closed-finding report are committed. Set this task to `[u]` only when the candidate is ready and the independent human decision is the next action.

- [ ] **0007-04** PREREQ: 0007-04:0007-03 Freeze and enforce the independently approved benchmark as the extraction regression oracle.
  - **Acceptance criteria:** The frozen artifact has a stable ID/content hash and cannot be silently regenerated over reviewed expectations; a deterministic clean run compares all 200 benchmark entries/cases and reports semantic field/heading/page/completeness drift; negative tests prove changed, missing, duplicate, or unresolved entries fail.
  - **Definition of Done:** The draft status/path is retired or clearly superseded, the automated benchmark gate and operator documentation are committed, and a retained passing report identifies the exact source/tool/benchmark versions.

