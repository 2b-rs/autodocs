# Automotive SPICE Capability Level 2 requirements for ECU development

## 1. Capability-level rule

Automotive SPICE PAM 4.0 defines six capability levels. Level 2 is the **Managed process** level: a process that already achieves its purpose is planned, monitored, and adjusted, while the work products it produces are established, controlled, and maintained.

For **each assessed process**, CL2 requires:

| Attribute | Required rating |
|---|---|
| `PA 1.1 Process performance` | **Fully achieved (F)** |
| `PA 2.1 Process performance management` | **Largely achieved (L) or Fully achieved (F)** |
| `PA 2.2 Work product management` | **Largely achieved (L) or Fully achieved (F)** |

A strong result in one attribute cannot compensate for a weak result in another. Ratings also cannot be averaged across different processes.

## 2. Rating scale

| Rating | Achievement band | Interpretation |
|---|---:|---|
| `N — Not achieved` | 0%–15% | Little or no evidence of the attribute |
| `P — Partially achieved` | >15%–50% | Some approach and achievement, but relevant aspects remain absent or unpredictable |
| `L — Largely achieved` | >50%–85% | Systematic approach and significant achievement, with weaknesses remaining |
| `F — Fully achieved` | >85%–100% | Complete, systematic achievement with no significant weakness |

PAM 4.0 optionally refines `P` and `L` into `P-`, `P+`, `L-`, and `L+`. The bands support professional judgment; they are not a formula such as “eight of ten checklist entries.” Evidence must be validated and interpreted in the assessment context.

## 3. PA 1.1 — Process performance

### Required achievement

The process achieves its defined outcomes.

### Assessment meaning

For the selected process:

- the intent of its process-specific base practices is achieved;
- expected results exist;
- produced work products or other evidence demonstrate the outcomes; and
- no significant outcome weakness remains if `F` is claimed.

CL2 therefore cannot be obtained merely by adding project-management templates around an incompletely performed process. Every selected process must first demonstrate all material Level-1 outcomes. The detailed Level-1 rule, complete PAM 4.0 applicability inventory, ECU profiles, and process-performance survey are in [`02-level-1-requirements.md`](02-level-1-requirements.md).

## 4. PA 2.1 — Process performance management

PA 2.1 asks whether the performance of the particular process is managed. PAM 4.0 defines eight achievements and six generic practices.

### Achievements

The evidence must demonstrate that:

1. a process-performance strategy is defined from identified objectives;
2. process performance is planned;
3. performance is monitored and adjusted against the plan;
4. human-resource needs, responsibilities, and authorities are determined;
5. physical/material resource needs are determined;
6. people are prepared to execute their responsibilities;
7. required physical/material resources are identified, available, allocated, and used; and
8. interfaces among involved parties are managed for effective communication and responsibility assignment.

### Generic practices

For each generic practice below, **PAM intent** paraphrases PAM 4.0. **Project readiness implementation** identifies stronger controls selected for this repository; those controls are not presented as universally mandated artifact fields or documents.

#### GP 2.1.1 — Identify objectives and define the performance strategy

**PAM intent:** determine the activity/work-product-management scope, expected results, process-performance objectives and criteria, assumptions and constraints, and the performance approach/method. A common project handbook may cover several processes.

#### GP 2.1.2 — Plan process performance

**PAM intent:** establish planning consistent with the strategy/objectives; define activities and work packages, estimates, schedule, and milestones.

**Project readiness implementation:** also record dependencies, planned outputs, and explicit completion/entry/exit criteria so the repository can validate its plans mechanically.

#### GP 2.1.3 — Determine resource needs

**PAM intent:** determine the required amount of human resources and their experience, knowledge, and skills; determine physical/material needs; and determine responsibilities and authorities for the process and its work products.

**Project readiness implementation:** make tool, license, infrastructure, service, data, and facility needs explicit where they are relevant to the process instance.

#### GP 2.1.4 — Identify and make resources available

**PAM intent:** identify and allocate the people who perform/manage the process according to need, qualify them to execute their responsibilities, and identify/make available/allocate/use the other required resources.

**Project readiness interpretation:** a generic role description is not accepted as sufficient evidence of named allocation, availability, authority, or competence for a process instance.

#### GP 2.1.5 — Monitor and adjust process performance

**PAM intent:** monitor performance to identify deviations from planning, take appropriate action, and adjust planning as necessary.

**Project readiness implementation:** retain actual-versus-plan status, deviation/cause, decision, corrective action, owner, due date, replanning, and closure/effectiveness information so adjustment is auditable rather than inferred.

#### GP 2.1.6 — Manage interfaces among involved parties

**PAM intent:** determine internal and required external involved parties, assign responsibilities, determine communication mechanisms, and establish/maintain effective communication.

**Project readiness implementation:** document commitments and include contributors, approvers, resource providers, recipients, suppliers, operators, and affected stakeholders as applicable.

### Typical PA 2.1 information

PAM 4.0 maps PA 2.1 to information such as:

- process-performance strategy and objectives;
- work packages and schedule;
- progress status;
- resource needs and allocations;
- communication matrix; and
- communication evidence.

These may be implemented in a combined project/process plan, issue system, campaign manifest, dashboards, decision records, and retained communications; separate documents are not mandatory.

## 5. PA 2.2 — Work product management

PA 2.2 asks whether the work products produced by the process are appropriately managed.

### Achievements

The evidence must demonstrate that:

1. requirements for process work products are defined;
2. storage and control requirements are defined;
3. work products are identified, stored, and controlled accordingly; and
4. work products are reviewed and adjusted to satisfy their requirements.

### Generic practices

As above, **PAM intent** states the model requirement and **Project readiness implementation** records this repository’s stronger chosen controls.

#### GP 2.2.1 — Define work-product requirements

**PAM intent:** define required content and structure, quality criteria, and applicable review/approval criteria. Some work-product types may legitimately require neither review nor approval.

**Project readiness implementation:** also define identity/metadata and ownership, and make any no-review/no-approval classification explicit.

#### GP 2.2.2 — Define storage and control requirements

**PAM intent:** define storage and control requirements, including identification and distribution; use a defined status model where a work-product status is needed.

**Project readiness implementation:** define repository/location, naming, access/authorization, availability, versioning/baselining, retention/archive/disposal, and sensitivity/license controls. Backup/recovery is added because it is relevant to this project’s SUP.8 configuration-management target; it is not asserted as a separate generic PA 2.2 mandate for every process.

#### GP 2.2.3 — Identify, store, and control work products

**PAM intent:** identify controlled work products; store/control them according to requirements; establish change control; perform required versioning/baselining; and make revision status available through appropriate mechanisms.

**Project readiness interpretation:** code for an append-only store is not accepted as operational evidence if real process writers do not use it, and a retention policy is not accepted as demonstrated when actual evidence remains only in an ignored local directory.

#### GP 2.2.4 — Review and adjust work products

**PAM intent:** review work products against defined requirements/criteria and ensure resolution of issues arising from reviews.

**Project readiness implementation:** record findings, decisions, adjustments, and closure. Automated validation can contribute to review evidence but does not replace human review/approval where judgment or independence is required.

### Typical PA 2.2 information

PAM 4.0 maps PA 2.2 to information such as:

- requirements for work products;
- review and approval criteria;
- quality criteria;
- review evidence;
- baselines; and
- controlled repositories.

## 6. Level-1 outcomes for the recommended profile

PA 1.1 is process-specific. The following table summarizes the outcome themes that must be **fully** demonstrated for every selected CL2 process. The full ECU starting profile is shown; Feature `0020` may approve a smaller allocated-software profile or add conditional processes based on actual responsibility. The authoritative detail remains Chapter 4 of PAM 4.0.

| Process | Required Level-1 outcome themes |
|---|---|
| `SYS.1` | Identify stakeholder sources and expectations; agree stakeholder requirements; maintain communication; analyze changes, impacts, and risks; communicate status and disposition. |
| `SYS.2` | Derive, specify, structure, prioritize, analyze, agree, communicate, trace, and maintain verifiable system requirements, including feasibility, dependencies and operating-environment effects. |
| `SYS.3` | Define/evaluate system elements, allocations, static/dynamic interfaces and behavior; record rationale; maintain requirement trace/consistency; agree and communicate the architecture. |
| `SYS.4` | Define system integration sequence and architecture/interface-based verification; integrate controlled elements; execute, trace, evaluate, summarize, communicate, and resolve findings. |
| `SYS.5` | Specify/select system-requirement-based verification; execute in controlled environments; trace requirements, measures and results; evaluate, summarize, communicate, and resolve findings. |
| `SWE.1` | Derive and specify functional/non-functional software requirements; structure and prioritize; analyze correctness, feasibility, dependencies, estimates, and operating-environment effects; maintain consistency/traceability; agree and communicate. |
| `SWE.2` | Define static components/interfaces and dynamic behavior; analyze quality characteristics and suitability; record rationale; maintain traceability and consistency to requirements; agree and communicate architecture. |
| `SWE.3` | Define detailed static/dynamic unit design and interfaces; construct units using defined principles; maintain consistency and traceability among requirements, architecture, design, and code; communicate agreed outputs. |
| `SWE.4` | Specify/select unit-verification measures, criteria, environment, coverage, and regression needs; execute and record; trace measures and results; summarize and communicate. |
| `SWE.5` | Specify component and integration verification; define sequence/preconditions; integrate elements; verify components and interactions; record, trace, summarize, and communicate. |
| `SWE.6` | Specify requirements-based integrated-software verification; select release/regression coverage; execute with pass/fail evidence; trace requirements, measures, and results; summarize and communicate. |
| `VAL.1` | Define intended-use validation measures in representative operational environments; select coverage; execute/evaluate; trace to stakeholder expectations; communicate results. |
| `SPL.2` | Determine release content and criteria; identify and assemble a controlled package; approve it; provide release notes/support information; deliver to intended recipients. |
| `SUP.1` | Define product/process quality criteria; independently and objectively evaluate conformance; report and resolve nonconformances; prevent recurrence; escalate unresolved issues. |
| `SUP.8` | Identify configuration items and attributes; establish change control; control modifications; establish baselines; report status; audit completeness/consistency; support backup/recovery. |
| `SUP.9` | Record/classify reproducible problems; analyze causes and impact; authorize urgent actions; initiate and track durable resolution; verify and close; report status/trends. |
| `SUP.10` | Record/status change requests; analyze dependencies, impacts, resources, schedule, and risk; prioritize and approve; trace to affected items/problems; confirm implementation; close and communicate. |
| `MAN.3` | Define project goals, boundaries, lifecycle, and release scope; assess feasibility; plan/monitor work, estimates, resources, competencies, interfaces, commitments, escalation, and schedule; correct deviations. |
| `MAN.5` | Identify risks regularly; assess probability/severity and priority; choose treatment; assign and execute actions; monitor exposure and effectiveness; correct deviations. |
| `MAN.6` | Identify management information needs; derive suitable process/product metrics; define collection/analysis; collect and store values with context; interpret; communicate; use results for decisions. |

## 7. Project-specific readiness evidence

The following is this program’s chosen ECU-readiness implementation, not a PAM-prescribed list of mandatory files. A convincing evidence set for an approved ECU process instance should include:

- approved stakeholder, system, and software requirements with stable IDs and status, plus applicable hardware/ML requirements;
- system/software architecture, detailed-design/unit, code/model, and allocation traceability;
- process plans with objectives, work packages, estimates, schedule, owners, resources, competencies, interfaces, and criteria;
- actual-versus-plan status, deviations, corrective actions, and replanning;
- work-product catalogue with schemas/quality/review/control/retention rules;
- controlled configuration and release baselines;
- `SWE.4` unit verification against detailed design, `SWE.5` component/integration verification against software architecture and detailed design, `SWE.6` integrated-software verification against software requirements, `SYS.4` integration verification against system architecture/interfaces, `SYS.5` verification against system requirements, and intended-use validation strategies/results;
- independent QA findings and closure;
- separate, traceable problem and change records;
- risk register and treatment monitoring;
- metric definitions, values/trends, interpretation, and decisions;
- an atomic build/test/release evidence package tied to one baseline and one run;
- release approval, release notes, delivery evidence, and known limitations.

## 8. What CL2 does not automatically require

CL2 does not by itself require:

- one prescribed lifecycle methodology;
- one file per information item;
- a particular issue tracker or commercial tool;
- organizational standard-process and tailoring infrastructure associated with CL3;
- every process in the PAM to be assessed; or
- zero defects.

It does require that every selected process be fully performed and managed with appropriately controlled work products. CL2 monitoring may be qualitative and/or quantitative; statistical/quantitative process analysis and control are PA 4.1/PA 4.2 concerns and are not hidden CL2 conditions. Tooling can automate much of the evidence collection, but an implemented function without routine, retained, reviewed evidence is not enough.
