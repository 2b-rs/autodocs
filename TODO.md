# TODO — Open Point List

HOW TO USE:

- *Features* are represented as 2nd level Headings.
- New *Features* shall normally be added to the top of list
- Features consist of *Tasks*.
- a *Feature* is considered complete once all of its *Tasks* are complete.
- Complete *Features* shall be moved to DONE.md and marked with a completion date + time. TODO.md and DONE.md must be committed after each completed feature.

- *Tasks* are dashed items, one line per task, with a completion marker. Examples see below
  [ ] - open. No work has been done w/r to this item
  [u] - unclear. No agentic work can currently be performed on this item because user/manager discussion or clarification is required before proceeding.
  [p] - partially implemented. The agent has started work on this item, but it is not yet complete; use this while work is in progress, including across conversations, so agents can determine the next best unfinished item.
  [?] - unknown - we simply don't know. Next step is to look into the repository and decide whether to amend TODO: or promote do [x]
  [x] - executed - task has been completed. If a task is completed, the results shall be checked in and REF: xxxxxx (git hash) shall be added 
- *Tasks* shall have a granularity so that they can be implemented in one go, i.e. without further user interaction. 
- Agents shall keep these markers up to date while working and in conversation hand-offs: set `[p]` once implementation/investigation has started, set `[u]` only when further progress is blocked on user discussion/decision, and avoid leaving active work as plain `[ ]` when a better state is known.

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

## Feature: 0020 — Automotive ECU Level 1 Scope, Responsibility, and Evidence Boundary

**Goal:** Establish the concrete ECU product and organizational boundary for a PAM 4.0 Level-1 target, select the named processes by actual responsibility, and prevent documentation-pipeline evidence from being misrepresented as ECU process-instance evidence. The current repository is an enabling process/tool foundation; capability must be demonstrated on approved ECU process instances.

- [u] **0020-01** Approve the first assessed ECU product/variant and supplied-product boundary, organizational unit, customer/intended use, lifecycle stage, project/release or increment, assessment purpose/timing, target profile, and permitted claim wording; identify whether the unit owns a complete ECU system lifecycle or receives allocated software requirements. The automotive ECU domain is confirmed, but these concrete scope decisions still require sponsor/manager and competent-assessor agreement.
- [ ] **0020-02** PREREQ: 0020-02:0020-01 Define and enforce the evidence boundary among canonical origins `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, and `controlled-scenario`; require `product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, revision, owner, origin, validity, retention, and confidentiality metadata and prohibit cross-product evidence substitution or opportunistic aggregation.
- [ ] **0020-03** PREREQ: 0020-03:0020-01 Define the ECU responsibility/authority matrix across customer, system, software, hardware, ML, cybersecurity, functional safety, calibration, manufacturing/service, integration, validation, release, operations, and suppliers; record who performs, reviews, approves, accepts, monitors, communicates, and retains evidence at every lifecycle interface.
- [ ] **0020-04** PREREQ: 0020-04:0020-03 Complete and approve an applicability matrix for all 32 PAM 4.0 processes, starting with the 14-process ECU software-delivery nucleus and adding each of `SYS.1`–`SYS.5` and `VAL.1` only for its actual owned responsibility; use the 20-process profile only when the complete system lifecycle and intended-use validation are owned, and justify every included, shared, external, or excluded process from supplied-product and responsibility evidence.
- [ ] **0020-05** PREREQ: 0020-05:0020-03, 0020-05:0020-04 Decide `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` applicability; create dependency-linked execution Features/tasks for every included process, and for every shared/external process define controlled inputs, outputs, acceptance, monitoring, escalation, configuration, risk, and evidence interfaces rather than treating it as absent.
- [ ] **0020-06** PREREQ: 0020-06:0020-03, 0020-06:0020-04 Decide applicable Automotive SPICE for Cybersecurity model/version and ISO/SAE 21434 responsibilities, plus ISO 26262 functional-safety responsibilities; create separate dependency-linked Features for applicable cybersecurity or safety lifecycles, register their completion gates in the selected profile, and do not present generic PAM 4.0 evidence as proof of either framework.
- [ ] **0020-07** PREREQ: 0020-07:0020-02, 0020-07:0020-04 Tailor and approve the Level-1 assessment input and official-outcome worksheets: process instances, evidence/interview validation, sampling/aggregation, assessor competence/independence, outcome and PA 1.1 rationale, report format, confidentiality, and rule that CL1 requires `PA 1.1 = L` or `F` per named process.
- [ ] **0020-08** PREREQ: 0020-08:0020-02, 0020-08:0020-03, 0020-08:0020-04, 0020-08:0020-05, 0020-08:0020-06, 0020-08:0020-07 Instantiate the controlled process/work-product/evidence catalogue for the selected ECU profile, assigning ECU-specific work products, owners, repositories, review/approval criteria, lifecycle interfaces, baseline/retention controls, and evidence obligations; baseline initial gaps without assigning a capability rating.
- [ ] **0020-09** PREREQ: 0020-09:0020-05, 0020-09:0020-06, 0020-09:0020-08 Create and validate the selected-profile execution register: for every included base, cybersecurity, safety, or other lifecycle process, identify the exact execution Feature/task and completion gate; for every shared/external process, identify the approved interface-evidence gate; reject a profile with an included process that has no executable path to assessment evidence.

## Feature: 0027 — ECU Management and Supporting Process Performance

**PREREQ:** 0027:0020

**Goal:** Perform `MAN.3`, `MAN.5`, `MAN.6`, `SUP.1`, `SUP.8`, `SUP.9`, and `SUP.10` on real ECU process instances. Reuse suitable mechanisms from Features `0011`–`0017`, but do not duplicate records or credit documentation-product execution as ECU evidence.

- [ ] **0027-01** PREREQ: 0027-01:0020-08 Establish and approve the ECU `MAN.3` project plan covering goals/motivation, boundaries, lifecycle, releases, feasibility, work packages, dependencies, estimates, schedule/milestones, deliverables, commitments, entry/exit criteria, named qualified assignments, competencies, tools/infrastructure/material resources, interfaces, communication, and escalation.
- [ ] **0027-02** PREREQ: 0027-02:0027-01 Operate recurring `MAN.3` actual-versus-plan monitoring throughout the ECU lifecycle; retain status, deviations, causes, impacts, decisions, corrective actions, owners/dates, replanning, escalation, effectiveness, closure, and affected-party communication.
- [ ] **0027-03** PREREQ: 0027-03:0020-08, 0027-03:0027-01 Establish and operate ECU `MAN.5` risk management with defined criteria and a maintained register covering technical, schedule, resource, supplier, integration, verification/validation, release, tool, safety-interface, cybersecurity-interface, and external-dependency risks; retain exposure, treatment, residual acceptance, monitoring, effectiveness, escalation, and closure evidence.
- [ ] **0027-04** PREREQ: 0027-04:0020-08, 0027-04:0027-01 Establish and operate ECU `MAN.6` measurement from approved information needs through metric definition, validated collection, analysis, trend/limitation communication, and documented decisions; keep missing, invalid, or incomparable data visibly distinct from successful results.
- [ ] **0027-05** PREREQ: 0027-05:0020-08 Establish and operate ECU `SUP.8` configuration management for requirements, architecture/design, source/generated code, binaries/firmware, toolchain/configuration, calibration/variant data, test assets/environments, supplier items, records/evidence, and releases; perform controlled change/versioning, baselines, status accounting, audits, backup/restore, access, retention, and availability controls.
- [ ] **0027-06** PREREQ: 0027-06:0020-08, 0027-06:0027-01, 0027-06:0027-05 Establish and operate appropriately independent ECU `SUP.1` quality assurance across selected processes and work products; retain conformance/nonconformance results, communication, escalation, management resolution, corrective-action verification, recurrence prevention, status reporting, and closure.
- [ ] **0027-07** PREREQ: 0027-07:0020-08, 0027-07:0027-05 Operate `SUP.9` on real ECU problems from reproducible recording/classification through cause and impact analysis, urgent-action authorization where needed, durable resolution, verification, communication, closure, and status/trend reporting; distinguish real problems from work packages, desired changes, and controlled rehearsals.
- [ ] **0027-08** PREREQ: 0027-08:0020-08, 0027-08:0027-05 Operate `SUP.10` on real ECU change requests from intake through dependency/resource/schedule/risk and affected-baseline impact analysis, priority/authorization, implementation trace, verification/consistency confirmation, communication, closure, and status/trend reporting; link related problems without conflating lifecycles.

## Feature: 0022 — ECU System Process Interface and Trace Foundation

**PREREQ:** 0022:0020, 0022:0027-05

**Goal:** Define the common responsibility, interface, configuration, and lifecycle-trace controls used by individually selected `SYS.1`–`SYS.5` processes. This Feature does not claim that any system process was performed.

- [ ] **0022-01** PREREQ: 0022-01:0020-09 Define the per-process system interface plan without waiting for future outputs: for each `SYS.1`–`SYS.5` process, record included/shared/external/excluded status, performer/authority, required input and output types, internal predecessor task or external acceptance gate, configuration/change/problem/risk feedback, and exact completion/evidence gate.
- [ ] **0022-02** PREREQ: 0022-02:0022-01 Extend the shared lifecycle model and validators for stakeholder requirement ↔ system requirement ↔ system architecture/element ↔ allocated software/hardware/ML requirement ↔ implementation ↔ verification/validation ↔ problem/change/release traces, including variants, baselines, status, rationale, responsibility origin, and consistency checks.

## Feature: 0028 — Conditional ECU Requirements Elicitation Process Performance (SYS.1)

**PREREQ:** 0028:0020, 0028:0022, 0028:0027-01

- [ ] **0028-01** PREREQ: 0028-01:0020-08 Establish and agree the `SYS.1` ECU stakeholder-requirements baseline from identified customer, user, regulatory, operational, manufacturing/service, safety, cybersecurity, supplier, and internal sources; retain intended-use scenarios, environments, priorities, acceptance, changes/impacts/risks, status, disposition, and communication.

## Feature: 0029 — Conditional ECU System Requirements Analysis Process Performance (SYS.2)

**PREREQ:** 0029:0020, 0029:0022, 0029:0027-05

- [ ] **0029-01** PREREQ: 0029-01:0020-09, 0029-01:0022-01 Accept and baseline the stakeholder-requirement input for internal `SYS.2`: use Feature `0028` output when `SYS.1` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.1` performance.
- [ ] **0029-02** PREREQ: 0029-02:0029-01 Analyze, derive, structure, prioritize, agree, and baseline `SYS.2` ECU system requirements, including behavior, modes/states, interfaces, diagnostics, timing/performance/resources, environment, safety/cybersecurity constraints, correctness, feasibility, dependencies, verification criteria, rationale, status, communication, and bidirectional stakeholder trace.

## Feature: 0030 — Conditional ECU System Architectural Design Process Performance (SYS.3)

**PREREQ:** 0030:0020, 0030:0022, 0030:0027-05

- [ ] **0030-01** PREREQ: 0030-01:0020-09, 0030-01:0022-01 Accept and baseline the system-requirement input for internal `SYS.3`: use `0029-02` when `SYS.2` is internal, or validate the external/shared responsible party, baseline, assumptions, acceptance, configuration identity, status, and feedback interface without claiming internal `SYS.2` performance.
- [ ] **0030-02** PREREQ: 0030-02:0030-01 Define, evaluate, agree, and baseline the `SYS.3` ECU system architecture, including system elements, HW/SW/ML/external allocations, static/dynamic interfaces, modes/states, resource budgets, failure behavior, variants, alternatives, quality evaluation, rationale, communication, and bidirectional system-requirement trace.

## Feature: 0031 — Conditional ECU System Integration and Integration Verification Process Performance (SYS.4)

**PREREQ:** 0031:0020, 0031:0022, 0031:0023-08, 0031:0027-05

- [ ] **0031-01** PREREQ: 0031-01:0020-09, 0031-01:0022-01 Accept and baseline the system architecture and all system-element inputs for internal `SYS.4`: use `0030-02` and applicable internal element outputs when those processes are internal, or validate each external/shared owner, baseline, interface, configuration, acceptance, open finding, and feedback path without claiming its process performance.
- [ ] **0031-02** PREREQ: 0031-02:0031-01, 0031-02:0022-02 Define and approve the `SYS.4` integration and integration-verification sequence, preconditions, builds, architecture/interface/interaction measures, selection/coverage and regression rationale, environments/data, entry/exit and pass/fail criteria, result retention, and architecture-to-measure trace.
- [ ] **0031-03** PREREQ: 0031-03:0031-02 Integrate controlled ECU system elements according to the approved sequence; execute selected `SYS.4` measures, retain pass/fail and coverage results, trace architecture/interfaces to measures/results, resolve or disposition findings, and communicate the integration summary.

## Feature: 0032 — Conditional ECU System Verification Process Performance (SYS.5)

**PREREQ:** 0032:0020, 0032:0022, 0032:0027-05

- [ ] **0032-01** PREREQ: 0032-01:0020-09, 0032-01:0022-01 Accept the controlled system-requirement and integrated-system inputs for internal `SYS.5`: use `0029-02` and `0031-03` when those processes are internal, or validate each external/shared owner, baseline, exact ECU element/configuration/environment identity, status, acceptance, open findings, and feedback path without claiming external process performance.
- [ ] **0032-02** PREREQ: 0032-02:0032-01, 0032-02:0022-02 Define and approve `SYS.5` integrated-system verification against ECU system requirements, including selection/coverage and regression rationale, target or representative environments, data, entry/exit, pass/fail, retention, and system-requirement-to-measure trace.
- [ ] **0032-03** PREREQ: 0032-03:0032-02 Execute `SYS.5` on the controlled integrated ECU baseline; retain pass/fail and coverage results, trace results to system requirements, resolve or disposition findings, communicate the summary, and preserve exact ECU hardware/software/calibration/configuration/tool/environment identity.

## Feature: 0023 — ECU Software Engineering Process Performance (SWE.1–SWE.6)

**PREREQ:** 0023:0020, 0023:0027-01, 0023:0027-05

**Goal:** Develop and verify actual ECU software through `SWE.1`–`SWE.6`. Documentation generators, imported public requirements, and pipeline validators may be reused as tools or patterns but are not the ECU requirements, implementation, or verification results.

- [ ] **0023-11** PREREQ: 0023-11:0020-09, 0023-11:0027-05 Accept and baseline the allocated software-development inputs required by the approved profile: when `SYS.2`/`SYS.3` are internal, use the controlled outputs of `0029-02`/`0030-02`; when they are shared/external, validate the responsible party, allocated requirements, architecture/interface constraints, assumptions, acceptance criteria, configuration identity, change/problem/risk feedback, and bidirectional interface evidence without claiming internal `SYS` performance.
- [ ] **0023-01** PREREQ: 0023-01:0023-11 Analyze, derive, structure, prioritize, agree, and baseline `SWE.1` ECU software requirements from accepted allocated system/stakeholder requirements and architecture/interface constraints, covering behavior, interfaces, timing/resources, diagnostics, modes/states, applicable safety/cybersecurity constraints, environment effects, correctness, feasibility, dependencies, estimates, verification criteria, rationale, status, communication, and bidirectional trace.
- [ ] **0023-02** PREREQ: 0023-02:0023-01 Define, evaluate, agree, and baseline the `SWE.2` ECU software architecture, including components, interfaces, static/dynamic behavior, scheduling/concurrency/resources, hardware/external interfaces, failure behavior, variants, alternatives, technical-quality evaluation, rationale, communication, and bidirectional trace.
- [ ] **0023-03** PREREQ: 0023-03:0023-02 Define and agree `SWE.3` ECU software detailed designs and unit/interface contracts, including static/dynamic behavior, data/control flow, algorithms, resource/concurrency constraints, coding principles, model/generated-code boundaries where applicable, and trace to software architecture and requirements.
- [ ] **0023-04** PREREQ: 0023-04:0023-03 Construct or generate each in-scope ECU software unit against its detailed design and coding principles; retain source/model/tool identity, construction and code-review findings, corrections, approvals, communication, and bidirectional design-to-unit/source trace.
- [ ] **0023-05** PREREQ: 0023-05:0023-03, 0023-05:0023-04 Define and approve `SWE.4` unit-verification specifications, methods, selection, applicable static-analysis/structural and other coverage objectives, regression rationale, controlled toolchain/environment/data, expected results and criteria, and detailed-design/unit-to-measure trace.
- [ ] **0023-06** PREREQ: 0023-06:0023-05 Execute `SWE.4` on the controlled ECU unit baseline; retain pass/fail data and coverage, trace detailed design/units to measures/results, resolve or disposition findings, and communicate the summary.
- [ ] **0023-07** PREREQ: 0023-07:0023-02, 0023-07:0023-03, 0023-07:0023-06 Define and approve the `SWE.5` component-verification and software-integration sequence, preconditions, builds, architecture/design/interface measures, selection/coverage and regression rationale, environments/data, criteria, and trace.
- [ ] **0023-08** PREREQ: 0023-08:0023-07 Integrate controlled ECU software components according to the approved sequence; execute `SWE.5` component/integration measures, retain pass/fail and coverage results, trace results, resolve or disposition findings, and communicate the summary.
- [ ] **0023-09** PREREQ: 0023-09:0023-01, 0023-09:0023-02, 0023-09:0023-08 Define and approve `SWE.6` integrated-software verification against software requirements, including release/regression selection, coverage, controlled target or representative environments, entry/exit, pass/fail, retention, and software-requirement-to-measure trace.
- [ ] **0023-10** PREREQ: 0023-10:0023-09 Execute `SWE.6` on the controlled integrated ECU software baseline; retain pass/fail and coverage results, trace results to software requirements, resolve or disposition findings, communicate the summary, and preserve exact source/executable/configuration/toolchain/target/environment identity.

## Feature: 0024 — ECU Product Release Process Performance (SPL.2)

**PREREQ:** 0024:0020, 0024:0027, 0024:0023

**Goal:** Perform `SPL.2` for the identified supplied ECU software/product without forcing ownership of `VAL.1`. The selected-profile gate must require Feature `0026` before release/assessment when intended-use validation is included and must otherwise require the approved external/shared validation and acceptance interface.

- [ ] **0024-01** PREREQ: 0024-01:0020-08, 0024-01:0027-05, 0024-01:0023-10 Define `SPL.2` ECU release content, identity, eligibility/approval criteria, compatible hardware/vehicle and variant scope, firmware/executable, calibration/configuration and flashing/delivery artifacts as applicable, release notes, known limitations, licenses/notices, support and update/rollback information, recipients/delivery controls, and release-record requirements.
- [ ] **0024-02** PREREQ: 0024-02:0024-01, 0024-02:0027-02, 0024-02:0027-03, 0024-02:0027-04, 0024-02:0027-06, 0024-02:0027-07, 0024-02:0027-08 Verify every release prerequisite activated by the selected profile, then assemble, audit, approve, deliver, and verify receipt or deployment of one complete controlled ECU release package; retain baseline identity, release authority, quality/risk/validation status, accepted deviations, notes, support/rollback information, delivery result, and links to included problems and changes.

## Feature: 0025 — Automotive ECU Level 1 Pilot Assessment and Closure

**PREREQ:** 0025:0020, 0025:0027, 0025:0023, 0025:0024

**Goal:** Assess PA 1.1 only after every process activated in the selected ECU profile has been performed or its approved shared/external interface evidence is ready, correct material outcome gaps, and publish a bounded process capability profile. CL1 requires `PA 1.1 = L` or `F` for each named target process; no repository-wide or product-certification claim is permitted.

- [ ] **0025-01** PREREQ: 0025-01:0020-07, 0025-01:0020-09 Select and approve the ECU pilot process instances, release/baselines, assessment schedule, interview roles, documentary evidence population, sampling/aggregation, confidentiality, assessor competence/independence, and all active system, validation, supplier, hardware, ML, cybersecurity, safety, reuse, or improvement execution Features; do not impose a fixed sample count unless the assessment input justifies it.
- [ ] **0025-02** PREREQ: 0025-02:0025-01, 0025-02:0024-02 Execute the selected-profile readiness gate: verify that every included process’s registered Feature/task is complete with ECU execution evidence, every shared/external process has approved interface and acceptance evidence, every exclusion remains justified, and no activated conditional lifecycle is missing; block evidence freeze on any mismatch.
- [ ] **0025-03** PREREQ: 0025-03:0025-02 Validate and freeze the ECU evidence index with artifact IDs/revisions, product/project/process/process-instance/baseline metadata, official outcome/indicator mapping, owners, authenticity, completeness, validity, confidentiality, contrary evidence, and unresolved limitations; exclude documentation-pipeline and synthetic execution evidence from ECU outcome claims.
- [ ] **0025-04** PREREQ: 0025-04:0025-03 Conduct and version interviews/observations, validate evidence, characterize every official Level-1 outcome for each selected process, and derive a reasoned `PA 1.1` rating without checklist arithmetic or averaging across different processes.
- [ ] **0025-05** PREREQ: 0025-05:0025-04 Issue a versioned internal Level-1 assessment report containing scope, process instances, method, evidence baseline, outcome judgments, per-process PA 1.1 ratings/capability levels, strengths, weaknesses, risks, exclusions/shared responsibilities, and findings; assign no rating to out-of-scope processes.
- [ ] **0025-06** PREREQ: 0025-06:0025-05 Triage every material outcome weakness/finding with root cause, impact, owner, due date, approved correction or accepted-residual decision, links to controlled problems/changes, affected lifecycle evidence, and required re-verification.
- [ ] **0025-07** PREREQ: 0025-07:0025-06 Execute bounded correction, re-verification, effectiveness, evidence-baseline revision, and reassessment cycles; exit only when each declared Level-1 target process has `PA 1.1 = L` or `F`, or management records that the target is unmet and approves a next-cycle plan without a CL1 claim.
- [ ] **0025-08** PREREQ: 0025-08:0025-07 Obtain an independent readiness review of scope, process selection, responsibility allocations, assessor competence, evidence validity, outcome/rating rationale, unresolved risks, and claim wording; record accepted limitations and the recommendation for a formal/external assessment.
- [ ] **0025-09** PREREQ: 0025-09:0025-08 Record the management decision and publish only the supported ECU process capability profile with organizational/product scope, release/process instances, PAM version, assessment method/date, evidence baseline, per-process ratings, exclusions/shared responsibilities, limitations, and validity period; hand the validated Level-1 baseline to Feature `0018` for the CL2 pilot.

## Feature: 0026 — Conditional ECU Intended-Use Validation Process Performance (VAL.1)

**PREREQ:** 0026:0020, 0026:0027-05, 0026:0023-10

**Goal:** Perform `VAL.1` only when Feature `0020` assigns intended-use validation to the assessed unit. If responsibility is external/shared, do not execute or rate this Feature internally; register the responsible party, controlled integrated-product input, validation result/acceptance output, change/problem feedback, and assessment interface under `0020-09`.

- [ ] **0026-01** PREREQ: 0026-01:0020-09 Accept the controlled stakeholder expectations/intended-use and integrated-product input baselines from the responsible internal or external lifecycle processes, then define and approve the ECU `VAL.1` strategy/specifications including operational scenarios, representative target environments, variants/configurations, measures, sequence, selection/regression rationale, infrastructure, entry/exit and pass/fail criteria, stakeholder trace, acceptance authority, and result retention.
- [ ] **0026-02** PREREQ: 0026-02:0026-01 Execute `VAL.1` on the approved integrated ECU baseline in selected representative operational environments; evaluate and trace results to stakeholder requirements/intended-use scenarios, resolve or disposition findings, communicate outcomes, and retain the authorized acceptance decision.

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
- [ ] **0012-04** PREREQ: 0012-04:0011-04, 0012-04:0012-03 Assign named qualified people and physical/material resources to process-instance work packages, communicate responsibilities/authority, make them available, record their actual use according to need, and retain availability, training/mentoring, allocation, and use evidence.
- [ ] **0012-05** PREREQ: 0012-05:0011-04, 0012-05:0012-02 Define and operate an interface/communication matrix covering internal/external parties, responsibilities, commitments, channels, cadence, response/escalation expectations, and required communication records.
- [ ] **0012-06** PREREQ: 0012-06:0012-02 Implement recurring actual-versus-plan status reviews with deviations, cause, impact, owner, due date, corrective action, replanning, decision, closure, and effectiveness evidence.
- [ ] **0012-07** PREREQ: 0012-07:0012-02, 0012-07:0012-03, 0012-07:0012-04, 0012-07:0012-05, 0012-07:0012-06, 0012-07:0012-08 Extend campaign/project-plan schemas, validators, reports, and templates so PA 2.1 evidence is generated and retained through normal work rather than reconstructed retrospectively.
- [ ] **0012-08** PREREQ: 0012-08:0011-05, 0012-08:0012-01 Define a performance strategy and measurable/assessable objectives, criteria, assumptions, constraints, and methods for every scoped process.

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
- [ ] **0014-04** PREREQ: 0014-04:0014-01, 0014-04:0015-06 Correct validation/reporting gate weaknesses, including real review/curation queue discovery, mandatory client-render coverage or approved exception, shared run identity, complete required subreports, and failure on missing/inconsistent stage evidence; add regression tests.
- [ ] **0014-05** PREREQ: 0014-05:0007-01, 0014-05:0007-02, 0014-05:0014-03 Complete independent review and freeze of the 200-record extraction benchmark, define its applicability/coverage limits, and retain approval plus benchmark-version evidence.
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
- [ ] **0015-08** PREREQ: 0015-08:0015-03, 0015-08:0015-06 Perform and retain configuration audits plus backup/restore tests for a representative source, campaign, evidence bundle, and published release baseline.
- [ ] **0015-09** PREREQ: 0015-09:0015-05 Wire evidence snippets, dependency edges, supersession triggers, invalidation/revisit results, and their reports into real writers and controlled stores.

## Feature: 0016 — Problem Resolution, Change Request, and Product Release Control

**PREREQ:** 0016:0011, 0016:0015

- [ ] **0016-01** PREREQ: 0016-01:0011-05 Define one SUP.9 problem-record model and lifecycle covering unique identity, reproducibility, classification, severity/priority, cause/common cause, impact, recorded authorization before urgent action, high-impact alert criteria/recipients, owner, durable resolution, verification, communication, closure, and trend data.
- [ ] **0016-02** PREREQ: 0016-02:0011-05 Define one SUP.10 change-request model and lifecycle covering identity/status, initiator, rationale, affected baselines, dependencies, resource/schedule/risk impact, priority, approval authority, implementation trace, verification, communication, and closure.
- [ ] **0016-03** PREREQ: 0016-03:0016-01, 0016-03:0016-02 Define classification/linking rules that keep MAN.3 work packages and improvement work in the managed plan, create SUP.9 records only for problems, create SUP.10 records only for requested changes, and link related records without conflating their lifecycles.
- [ ] **0016-04** PREREQ: 0016-04:0013-08, 0016-04:0016-02 Enforce change impact analysis, prioritization, authorization, and traceability to requirements, architecture/design/code, tests, risks, plans, configuration items, and intended release before implementation.
- [ ] **0016-05** PREREQ: 0016-05:0014-13, 0016-05:0016-01, 0016-05:0016-02 Enforce implementation confirmation, independent verification where required, affected-work-product consistency, requester/affected-party communication, accepted closure, and trend/common-cause reporting.
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

**PREREQ:** 0018:0011, 0018:0012, 0018:0015-07, 0018:0015-08, 0018:0025

- [ ] **0018-01** PREREQ: 0018-01:0011-02, 0018-01:0025-09 Select and approve representative ECU pilot process instances/releases, assessment schedule, planned interview roles, ECU evidence baseline, sampling/aggregation, and independence safeguards; documentation campaigns such as Feature `0019` may contribute reusable definitions/mechanisms only and cannot enter as ECU execution evidence or imported ratings.
- [ ] **0018-02** PREREQ: 0018-02:0018-01 Execute a first end-to-end managed ECU pilot using all planning, requirements, traceability, verification/validation/QA, configuration, problem/change/release, risk, measurement, and review controls; retain one atomic ECU evidence set.
- [ ] **0018-03** PREREQ: 0018-03:0018-02 Execute a second representative ECU process instance or assessor-approved equivalent sample, applying lessons through controlled process adjustment and demonstrating repeatability rather than one-off compliance construction.
- [ ] **0018-04** PREREQ: 0018-04:0018-02, 0018-04:0018-03 Validate and freeze the pre-assessment ECU evidence index, including artifact IDs/revisions, product/project/process/process-instance/baseline and origin metadata, process/outcome/attribute mapping, owners, authenticity, completeness, confidentiality, and unresolved limitations; interview records are added/versioned during assessment.
- [ ] **0018-05** PREREQ: 0018-05:0018-04 Perform the internal R1-style assessment, conduct and version interviews, validate evidence, characterize every Level-1 outcome and PA 2.1/PA 2.2 achievement for every scoped process, derive the capability profile, and issue a versioned assessment report with strengths, weaknesses, risks, and findings.
- [ ] **0018-06** PREREQ: 0018-06:0018-05 Triage every assessment finding, record root cause/impact/owner/due date and an approved correction or accepted-residual disposition, and create bounded child remediation tasks linked to controlled changes and required re-verification.
- [ ] **0018-07** PREREQ: 0018-07:0018-06 Execute versioned correction/re-verification/effectiveness cycles, publish a new evidence-baseline revision and reassessment after each cycle, and exit only when no CL2-blocking finding remains or the sponsor records that CL2 cannot be claimed and opens a next-cycle plan.
- [ ] **0018-08** PREREQ: 0018-08:0018-07 Obtain an independent readiness review of applicability, scope, assessor competence, evidence validity, ratings, open risks, and claim wording; record accepted residual limitations and recommendation on formal external assessment.
- [ ] **0018-09** PREREQ: 0018-09:0018-08 Record the management decision and publish the final ECU profile with organizational/supplied-product scope, process instances, PAM version, assessment method/date, ECU evidence baseline, per-process ratings, shared/excluded responsibilities, limitations, and validity period. Make no blanket CL2 claim unless every declared target process meets the gate, and do not imply safety, cybersecurity, regulatory, or product certification.

## Feature: 0019 — Eclipse S-Core Database Import

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
  - **Acceptance criteria:** Each manifest source resolves to the declared SHA; a deterministic archive or checkout inventory with SHA-256 hashes is stored/referenced; every source artifact selected for extraction has repository, ref, commit, path, and locator evidence; absent/unavailable artifacts are reported rather than omitted silently.
  - **Definition of Done:** A clean-environment verification reconstructs the same source inventory and hashes (or reports a documented upstream-unavailability exception); inventory report is committed/persisted and linked from the campaign manifest.

- [ ] **0019-03** PREREQ: 0019-03:0019-01 Define and test the S-Core import profile: source selectors, supported artifact classes, field mapping, status defaults, and explicit non-goals.
  - **Acceptance criteria:** A versioned import-profile document/config maps each supported source class to `module`, `component`, `design-doc`, or `process-doc`; it identifies mandatory fields, source locators, status/traceability defaults, duplicate/conflict behavior, and conditions that must create a review/curation item; sample artifacts from every in-scope repository demonstrate the mapping.
  - **Definition of Done:** Profile is reviewed against `score-identity-scheme.md`, `data-model.md`, `status-model.md`, and `processes.md`; automated fixtures cover every supported class and every defined rejection/queue condition.

### Campaign B — Extraction and Normalization

- [ ] **0019-04** PREREQ: 0019-04:0019-02, 0019-04:0019-03 Implement the v0.6.0 manifest-driven S-Core extraction adapter.
  - **Acceptance criteria:** The adapter accepts only a manifest-pinned source set, extracts the profile’s supported artifacts, and emits deterministic raw extraction output; it does not fall back to moving refs such as `main`; failures identify repo/ref/path/locator and leave no partial canonical corpus presented as complete.
  - **Definition of Done:** Unit and integration tests cover successful extraction, missing source, invalid ref/hash, malformed Sphinx-needs item, duplicate identity, and unsupported artifact; repeated extraction from the same snapshot produces identical normalized raw output.

- [ ] **0019-05** PREREQ: 0019-05:0019-04 Normalize raw S-Core extraction output into canonical versioned records.
  - **Acceptance criteria:** Every emitted record conforms to `ECLIPSE/S-CORE/<kind>/<id>@rel:<release>#<content-hash8>`, carries all non-canonical provenance required by `score-identity-scheme.md`, contains source-backed traceability, has an initial status/reason and history entry, and records content hashes deterministically; identity collisions and source contradictions are routed to review/curation rather than overwritten.
  - **Definition of Done:** Schema, canonical-ID, version-ID, provenance, and deterministic-content-hash tests pass; a fixture corpus demonstrates each of the four supported kinds plus collision and contradiction handling.

- [ ] **0019-06** PREREQ: 0019-06:0019-05 Implement S-Core-specific validation and campaign evidence reporting.
  - **Acceptance criteria:** Validation checks record schema, kind/ID registry conformance, source-ref/SHA integrity, required provenance, traceability, module/component containment, dangling references, malformed Sphinx-needs identities, duplicate versions, and status consistency; a persisted report provides pass/fail, totals by kind/status, queued exceptions, tool/version metadata, and actionable findings.
  - **Definition of Done:** Negative fixtures prove every validation class fails correctly; the validation report is machine-readable and human-readable, retained with the campaign, and meets the validation-evidence conditions in `aspice-level1-score-import.md`.

### Campaign C — Curation, Publication, and Acceptance

- [ ] **0019-07** PREREQ: 0019-07:0019-05 Integrate imported S-Core exceptions with the unified review and curation lifecycle.
  - **Acceptance criteria:** Unsupported, ambiguous, conflicting, missing-provenance, and non-auto-verifiable S-Core records create canonical `curation-item@v1` or review items with source/version evidence; queue states and allowed actors follow `workflow-lifecycle.md` and `roles.md`; user-facing reports link from each queue item to its record/version/source locator.
  - **Definition of Done:** End-to-end tests demonstrate discovered → queued → claimed → proposed → accepted/rejected → applied/published behavior for an S-Core sample; no tool or AI path can silently perform an `accepted`/`rejected` content decision.

- [ ] **0019-08** PREREQ: 0019-08:0019-06, 0019-08:0019-07 Generate and validate the S-Core v0.6.0 published views.
  - **Acceptance criteria:** Valid records are rendered into the HTML tree with record history, canonical/version identity, provenance/traceability, and review indicators; invalid/hypothesized/unresolved records remain excluded from factual publication while visible in the curation/review reports; all language-tree, DOM, link, and client-rendered validation checks pass.
  - **Definition of Done:** A clean generation is repeatable with zero semantic differences; published report counts reconcile exactly with the campaign validation report and queue counts; screenshots/DOM assertions cover at least one record of every kind and one unresolved case.

- [ ] **0019-09** PREREQ: 0019-09:0019-08 Perform the v0.6.0 import campaign review, curator release decision, and local campaign-evidence closure under `docs/pipeline/aspice-level1-score-import.md` without waiting for ECU scope; classify its canonical origin as `documentation-execution`, describe it as documentation-campaign evidence, make no capability claim, and leave any later named documentation-process mapping to `0011-03`.
  - **Acceptance criteria:** The campaign report demonstrates every criterion in `aspice-level1-score-import.md`: committed manifest, traced/versioned records, persisted validation outcome, human-readable outcome summary, and explicit campaign closure; unresolved items and exclusions are quantified and linked to queues; curator records an accept/reject/conditional-publication decision.
  - **Definition of Done:** Campaign is closed according to Phase 6 of `processes.md`, closure report and decision are committed, no open validation blocker is mislabeled as valid, and all Feature 0019 Definition-of-Done bullets are independently evidenced by committed artifacts and test reports.


## Feature: 0007 — Database Quality Assurance

### Campaign A — Baseline

- [u] **0007-01** PREREQ: 0007-01:0006 — Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null` on many)
  - 2026-08-12: the 12 headingless-but-populated blockers (all `RS_LT_*`) are resolved. `spec_scrape.py`'s new numbered-subsection heading fallback (commit `fdba7e28`) recovers their real headings from the source PDF; `benchmark-draft.json`'s expected values were updated to match and verified against the source (recount confirms 0 headingless-but-populated entries remain). The remaining freeze blockers are exclusively `review.status`/`complete_start` metadata, not extraction-shape gaps.
  - 2026-08-12: manually truthed the two previously called-out "empty-fields" blockers in `_src/tests/fixtures/spec_extraction/benchmark-draft.json`:
    - `RS_SAF_21101` is intentionally an inline citation in prose on pages 9-10 of `AUTOSAR_AP_RS_PlatformHealthManagement.pdf`, not a formal requirement block; `heading = null`, `fields = {}`, and `complete_start = null` are correct ground truth. Added an explanatory review note.
    - `RS_DIAG_04005` on page 15 of `AUTOSAR_FO_RS_Diagnostics.pdf` is a real formal requirement block (`[RS_Diag_04005] Manage Security Access level handling`); replaced the incorrect empty expected values with the actual heading/fields and `complete_start = true`, with a review note explaining the mixed-case source ID.
  - Recount after this truthing: exactly 12 headingless-but-populated benchmark entries remain, all in `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`). This cleanly overlaps with the separate TODO item to model dense definition lists as an explicit record shape.

### Definition-precision follow-ups

- [u] **0007-02** Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
  - 2026-08-12: implemented and shipped the `AUTOSAR_FO_RS_LogAndTrace` variant of this shape (numbered subsection line immediately above a bare `[RS_LT_xxxxx]` marker, e.g. `4.2.1.1.8 The LT shall ...` followed by `[RS_LT_00001] ⌈`) as `spec_scrape.py`'s new `_subsection_heading_before` fallback, commit `fdba7e28`. All 12 affected benchmark entries now have correct headings and the recount confirms 0 headingless-but-populated entries remain.
  - NOT yet verified: the originally cited `RS_PHM_00001..00003` example does not appear in `benchmark-draft.json` at all (no matching IDs found), so it's unconfirmed whether AUTOSAR_AP_RS_PlatformHealthManagement uses the exact same shape or a different one. This item stays open until that case (or another concrete instance beyond RS_LT) is located and confirmed handled.

