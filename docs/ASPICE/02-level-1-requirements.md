# Automotive SPICE Capability Level 1 requirements for ECU development

## 1. Purpose and status

This document surveys the process requirements relevant to reaching Automotive SPICE Capability Level 1 (CL1) while developing software for automotive electronic control units (ECUs). It is based on Automotive SPICE PAM 4.0 and uses paraphrases rather than reproducing the model text.

The program context is now clear: the long-term product is automotive ECU software, and the current public-specification documentation, extraction, curation, generation, and validation repository is an enabling first step. That clarification establishes an Automotive SPICE-relevant development domain. It does **not** yet establish an assessable ECU product, organizational unit, process profile, or process instance, and it does not turn documentation-pipeline evidence into ECU-development evidence.

This is a readiness survey, not an assessment result. The official process purposes, outcomes, base practices, output-information indicators, and rating rules in the cited PAM remain authoritative.

## 2. What Capability Level 1 means

### 2.1 Capability is assigned to a named process

Automotive SPICE has:

- a **process dimension**, containing process purposes, outcomes, base practices, and output-information indicators; and
- a **capability dimension**, used to rate how well each selected process is performed.

There is no context-free rating called “the repository’s ASPICE level.” The assessment result is a profile such as `SWE.1 = CL1`, `SWE.2 = CL1`, and `SUP.8 = CL0` for identified process instances in an identified organizational and product scope.

A process outside the approved assessment scope is **not rated**. It must not be reported as `N`, `CL0`, or passed merely because it was excluded.

### 2.2 CL1 rating rule

Capability Level 1 is the **Performed process** level. For each assessed process:

| Process attribute | CL1 requirement |
|---|---|
| `PA 1.1 Process performance` | **Largely achieved (`L`) or Fully achieved (`F`)** |

If `PA 1.1` is `N` or `P`, that process remains at Capability Level 0.

| Rating | Achievement band | Meaning for PA 1.1 |
|---|---:|---|
| `N — Not achieved` | 0%–15% | Little or no achievement of the process attribute is evident. |
| `P — Partially achieved` | >15%–50% | Some achievement is evident, but important aspects are absent or unpredictable. |
| `L — Largely achieved` | >50%–85% | A systematic approach and significant achievement are evident, with weaknesses remaining. |
| `F — Fully achieved` | >85%–100% | Complete, systematic achievement is evident and no significant weakness remains. |

The bands guide professional judgment. They are not a formula based on the percentage of checked base practices, present documents, passed tests, or completed TODO items.

CL1 differs from the CL2 target documented in [`02-level-2-requirements.md`](02-level-2-requirements.md). CL2 requires `PA 1.1 = F` and both `PA 2.1` and `PA 2.2` at `L` or `F`. CL1 does not require PA 2.1 or PA 2.2, although selected management and support processes such as `MAN.3` and `SUP.8` can themselves be assessed at CL1.

### 2.3 What PA 1.1 requires

For a selected process, PA 1.1 asks whether its defined outcomes are achieved. Evidence normally has to show that:

1. the process is actually performed in the selected process instance;
2. its material outcomes are achieved;
3. its base-practice intent is represented by the implemented activities or an effective alternative;
4. resulting work products or other objective evidence exist and are internally consistent;
5. responsible people can corroborate how the process was performed; and
6. weaknesses are reflected honestly in the outcome and attribute judgment.

Base practices and output information items are assessment indicators, not a mandatory document checklist. One artifact may support several outcomes, and one outcome may require several artifacts. A template, schema, tool, policy, or generated file does not by itself prove that an ECU process outcome occurred.

## 3. What Level 1 does and does not impose

PAM 4.0 does **not** impose one universal set of processes on every organization. Scope depends on the supplied product, contractual responsibility, organizational unit, lifecycle, assessment purpose, customer expectations, and actual process instances.

For this program, the following staged starting profiles are defensible hypotheses:

### 3.1 ECU software-delivery nucleus — 14 processes

Use this as the minimum starting hypothesis when the organization receives allocated software requirements and architecture constraints and develops/releases ECU software without owning the complete ECU system lifecycle:

- `SWE.1`–`SWE.6`;
- `SPL.2`;
- `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`; and
- `MAN.3`, `MAN.5`, `MAN.6`.

Excluding system processes requires evidence that system responsibilities are external or shared, plus controlled interfaces for incoming requirements/architecture, integration feedback, verification results, changes, risks, and acceptance.

### 3.2 Full ECU system-and-software starting profile — 20 processes

Use the complete 20-process profile when the assessed organization owns the full ECU/item system lifecycle **and** intended-use validation. Add to the 14-process nucleus:

- `SYS.1`–`SYS.5`; and
- `VAL.1`.

Where responsibility is split, include only each process actually performed by the assessed unit and control the inputs, outputs, acceptance, feedback, configuration, change/problem, and assessment interfaces for shared/external processes. Feature `0020` must approve, share, or exclude every process based on real responsibility rather than on which artifacts happen to exist in this repository.

## 4. Complete PAM 4.0 process inventory and applicability survey

The table accounts for all 32 PAM 4.0 processes. “Starting treatment” is a survey recommendation, not an assessment decision.

| Group | Processes | Starting treatment for an ECU-code program |
|---|---|---|
| Acquisition | `ACQ.4 Supplier Monitoring` | Conditional: include where the assessed unit monitors an ECU hardware, software, calibration, test, ML, cybersecurity, or other development supplier against an agreement. |
| Supply | `SPL.2 Product Release` | Core for the party releasing ECU software or an ECU product. |
| System engineering | `SYS.1`–`SYS.5` | Core for full ECU/system responsibility; otherwise external/shared with explicit lifecycle interfaces. |
| Software engineering | `SWE.1`–`SWE.6` | Core for ECU software development. |
| Hardware engineering | `HWE.1`–`HWE.4` | Conditional on responsibility for ECU electronics requirements, design, or verification. |
| Machine-learning engineering | `MLE.1`–`MLE.4` | Conditional on responsibility for an ML-enabled automotive product/model lifecycle. |
| Supporting | `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `SUP.11` | `SUP.1`/`SUP.8`/`SUP.9`/`SUP.10` are core for the recommended ECU delivery profile; `SUP.11 Machine Learning Data Management` is conditional on ML-data lifecycle responsibility. |
| Management | `MAN.3`, `MAN.5`, `MAN.6` | Core for a defensible ECU delivery profile. |
| Process improvement | `PIM.3 Process Improvement` | Enabling/conditional; not automatically required to rate other processes at CL1. |
| Reuse | `REU.2 Management of Products for Reuse` | Conditional when software/platform components are deliberately managed as reuse products. |
| Validation | `VAL.1 Validation` | Core where the unit owns intended-use validation or product acceptance; otherwise external/shared with controlled interfaces. |

The numeric gaps in identifiers such as `SUP.2`–`SUP.7` are intentional. Process identifiers are inherited from the broader reference-model structure.

## 5. Core system and software process requirements

The following tables summarize the performance result that must be demonstrated and the main activity/evidence themes an assessor would expect to sample. They are not substitutes for the official PAM outcome and indicator tables.

### 5.1 System engineering and validation

| Process | Required performed-process result | Principal activity and evidence themes |
|---|---|---|
| `SYS.1 Requirements Elicitation` | Stakeholder needs and expectations for the ECU are identified, agreed, maintained, and communicated. | Identify stakeholder groups and authoritative sources; elicit needs, constraints, intended use, and operating contexts; analyze and resolve conflicts; agree requirements; analyze changes, impacts, and risks; maintain status and communication. Evidence may include a stakeholder map, elicitation records, agreed stakeholder requirements, change/disposition history, and communication records. |
| `SYS.2 System Requirements Analysis` | Stakeholder requirements are transformed into an analyzed and agreed system-requirement baseline suitable for architecture and verification. | Specify functional and non-functional requirements, interfaces, modes/states, timing/resources, diagnostics, environmental and regulatory constraints; structure and prioritize; analyze correctness, feasibility, dependencies, impact, and verifiability; define verification criteria; maintain bidirectional trace and consistency; communicate agreement. |
| `SYS.3 System Architectural Design` | A suitable system architecture allocates requirements to system elements and defines their static/dynamic relationships and interfaces. | Define elements, external/internal interfaces, behavior, modes/states, HW/SW/ML allocations, resource budgets and failure behavior; evaluate alternatives and quality characteristics; record rationale; maintain requirement trace and consistency; agree and communicate the architecture. |
| `SYS.4 System Integration and Integration Verification` | System elements are integrated in a controlled sequence, and components, interfaces, and interactions are verified against the system architecture. | Define integration sequence and preconditions; specify/select architecture-based verification measures, coverage, regression, environments and criteria; integrate controlled baselines; execute and evaluate measures; trace architecture/interface → measure → result; resolve findings and communicate status. |
| `SYS.5 System Verification` | The integrated ECU/system is verified against system requirements. | Specify/select requirements-based verification measures and release/regression coverage; control target or representative environments, data, expected results and criteria; execute/evaluate; trace system requirement → measure → result; resolve findings and communicate the verification summary. |
| `VAL.1 Validation` | The ECU/system is shown to be suitable for intended use and stakeholder expectations in representative operational conditions. | Define intended-use scenarios, representative users/actors, variants and operational environments; specify/select validation measures and coverage; execute/evaluate; trace stakeholder expectation → validation measure → result; resolve findings; communicate and retain acceptance decisions. Verification against requirements is not automatically intended-use validation. |

### 5.2 Software engineering

| Process | Required performed-process result | Principal activity and evidence themes |
|---|---|---|
| `SWE.1 Software Requirements Analysis` | Allocated system or stakeholder inputs are transformed into analyzed, verifiable, agreed software requirements. | Specify functional/non-functional behavior, interfaces, timing/resources, diagnostics, modes/states and applicable safety/cybersecurity constraints; structure/prioritize; analyze correctness, feasibility, dependencies, estimates and operating-environment effects; define verification criteria; trace, agree and communicate. |
| `SWE.2 Software Architectural Design` | A suitable software architecture allocates software requirements and defines software components, interfaces, and behavior. | Define static structure, interfaces and dynamic behavior; address scheduling, concurrency, resources, hardware/external interfaces and failure behavior; evaluate quality characteristics and alternatives; record rationale; maintain requirements trace/consistency; agree and communicate. |
| `SWE.3 Software Detailed Design and Unit Construction` | Detailed designs define software units sufficiently for construction, and units are constructed consistently with requirements, architecture, designs, and coding principles. | Define unit structure, interfaces, data/control flow, algorithms and behavior; establish coding/design principles; construct or generate units; review design and code; maintain requirement ↔ architecture ↔ detailed design/unit ↔ source trace; correct inconsistencies and communicate agreed outputs. |
| `SWE.4 Software Unit Verification` | Software units are verified against detailed design and applicable unit criteria. | Define/select static and dynamic measures, coverage and regression rationale; control tools, environment, fixtures, data and expected results; execute and evaluate; trace detailed design/unit → measure → result; resolve findings and communicate a summary. |
| `SWE.5 Software Component Verification and Integration Verification` | Software components and progressively integrated software are verified against architecture and detailed design. | Define component and integration verification measures, sequence/preconditions, coverage and regression; verify components; integrate controlled elements; verify interfaces/interactions; trace architecture/design → measure → result; resolve findings and communicate. |
| `SWE.6 Software Verification` | Integrated ECU software is verified against its software-requirement baseline. | Specify/select requirements-based release/regression measures and coverage; control target or representative environments, software/configuration, data and criteria; execute/evaluate; trace software requirement → measure → result; resolve findings and communicate the summary. |

The verification bases must not be conflated:

- `SWE.4`: detailed design and software unit;
- `SWE.5`: software architecture/detailed design, components, interfaces, and integration;
- `SWE.6`: software requirements and integrated software;
- `SYS.4`: system architecture, system elements, interfaces, and system integration;
- `SYS.5`: system requirements and the integrated system; and
- `VAL.1`: stakeholder expectations and intended use in representative operation.

## 6. Core release, support, and management process requirements

| Process | Required performed-process result | Principal activity and evidence themes |
|---|---|---|
| `SPL.2 Product Release` | An identified, approved, complete ECU software/product package is delivered to intended recipients. | Define release content and eligibility; assemble controlled executable/firmware, configuration/calibration, compatibility, flashing/delivery and support items as applicable; check completeness and consistency; identify/version and approve; provide release notes, known limitations and support/rollback information; deliver and retain the result. |
| `SUP.1 Quality Assurance` | Products and processes are objectively evaluated against defined provisions, with nonconformances communicated, resolved, and escalated when necessary. | Define QA strategy, criteria, responsibilities and independence; perform product/process conformance checks; record and communicate findings; track resolution; escalate unresolved deviations; verify corrective action and report quality status. Testing by the developer is not automatically independent QA. |
| `SUP.8 Configuration Management` | Configuration integrity and availability are established and maintained. | Define the CM approach; identify configuration items and attributes; control changes, versions and access; establish baselines; perform status accounting and configuration audits; preserve availability and recovery. Typical ECU items include requirements, models/designs, source/generated code, toolchain/configuration, calibration/variant data, tests/environments, supplier items, evidence and releases. |
| `SUP.9 Problem Resolution Management` | Problems are recorded, analyzed, controlled, resolved, verified, closed, and reported. | Create unique reproducible records; classify/severity/priority; analyze cause and impact; authorize urgent actions; initiate durable correction; trace related changes/items; verify resolution; communicate/close; report status and trends. A work package or desired enhancement is not automatically a problem. |
| `SUP.10 Change Request Management` | Change requests are analyzed, authorized, implemented under control, verified, closed, and communicated. | Record/status requests; analyze dependencies, affected baselines, resources, schedule, risk and product impact; prioritize and approve/reject; trace implementation and related problems; confirm verification/consistency; close and communicate. Problem and change lifecycles must remain distinct but linked. |
| `MAN.3 Project Management` | The ECU project is planned and controlled so agreed objectives and commitments can be achieved. | Define goals, motivation, boundaries, lifecycle and releases; assess feasibility; estimate and schedule work; allocate resources and competencies; manage interfaces and commitments; monitor actuals/deviations; correct and replan; communicate status. This is process-specific Level 1 performance, not a substitute for PA 2.1 on every other process. |
| `MAN.5 Risk Management` | Project/product risks are identified, analyzed, prioritized, treated, monitored, and communicated. | Define criteria; identify risks repeatedly; assess probability/impact and exposure; assign owners/treatments; monitor action progress, residual exposure and effectiveness; escalate/accept/close with authority. Safety and cybersecurity risk processes may impose additional requirements outside base PAM 4.0. |
| `MAN.6 Measurement` | Measurement information is defined, collected, analyzed, communicated, and used to support management decisions. | Derive information needs; define product/process metrics, units, sources, collection and analysis; validate/store values with context; interpret trends and limitations; communicate results; record decisions. Use **metric** for indicators and reserve **measure** for verification/validation activities. |

## 7. Conditional PAM 4.0 process requirements

These processes must be included when the assessed organization performs the corresponding responsibility. They must not be excluded solely because the current repository has no evidence for them.

| Process | Inclusion trigger | Level-1 performance themes |
|---|---|---|
| `ACQ.4 Supplier Monitoring` | The assessed unit acquires and monitors an external ECU development product/service. | Agree joint activities, deliverables, technical milestones, information exchange, responsibilities and acceptance/escalation criteria; monitor progress/performance and technical results; communicate deviations; track corrective actions and accepted supplied baselines. Being monitored by an OEM does not make `ACQ.4` the supplier’s process; acquiring a sub-supplier can. |
| `HWE.1 Hardware Requirements Analysis` | The unit owns ECU electronics requirements. | Analyze, agree, baseline, communicate and trace allocated hardware requirements, interfaces, constraints, feasibility and verification criteria. |
| `HWE.2 Hardware Design` | The unit designs ECU electronics. | Define/evaluate hardware elements, interfaces and implementation data; maintain requirements trace, rationale, consistency, agreement and communication. |
| `HWE.3 Verification against Hardware Design` | The unit verifies hardware implementation against design. | Specify/select and execute design-based verification on controlled samples/baselines; retain selection, environment, pass/fail, trace, findings and summary. |
| `HWE.4 Verification against Hardware Requirements` | The unit verifies hardware against hardware requirements. | Specify/select and execute requirements-based verification; retain requirement → measure → result trace, coverage, findings and exact hardware/environment identity. |
| `MLE.1 Machine Learning Requirements Analysis` | The automotive product includes an ML model and the unit owns ML requirements. | Analyze, agree and trace ML requirements, operating-domain assumptions, data needs, quality/performance criteria, constraints and test criteria. |
| `MLE.2 Machine Learning Architecture` | The unit owns ML architecture. | Define/evaluate model components, interfaces, data/pre/post-processing, deployment relationships, rationale and trace. |
| `MLE.3 Machine Learning Training` | The unit trains the model. | Train with controlled data, code, parameters, tools and environments; identify intermediate/final models and retain reproducibility and result evidence. |
| `MLE.4 Machine Learning Model Testing` | The unit owns model testing. | Define/select and execute controlled model tests on appropriately separated data; trace results to ML requirements; evaluate, resolve findings and communicate. |
| `SUP.11 Machine Learning Data Management` | The unit manages ML data. | Define data requirements; control provenance, acquisition, labeling, quality, preprocessing, partitioning, versions, access, representativeness, limitations and model/data trace. |
| `PIM.3 Process Improvement` | Organizational process improvement is itself assessed. | Identify and prioritize improvement opportunities; plan/deploy improvements; provide resources/competence; monitor effects and communicate results. It is not a prerequisite imposed on all other CL1 processes. |
| `REU.2 Management of Products for Reuse` | Components/platforms are deliberately offered and managed as reuse products. | Identify and evaluate reuse products; define supported contexts, qualification, limitations and provision; maintain versions/status; collect use and feedback. Incidental code reuse is insufficient. |

Use of generative AI to assist documentation or coding does not by itself create an `MLE.1`–`MLE.4` process instance. Applicability depends on the automotive product’s ML model and data lifecycle.

## 8. Related but separate responsibility decisions

### 8.1 Cybersecurity

Cybersecurity-specific process IDs are not part of the 32-process base PAM 4.0 inventory. If the ECU/item is cybersecurity-relevant, Feature `0020` must select the applicable Automotive SPICE for Cybersecurity model/version and allocate responsibilities for the extension processes commonly identified as `ACQ.2`, `MAN.7`, and `SEC.1`–`SEC.4`, together with ISO/SAE 21434 interfaces.

Generic `MAN.5` risk management, security requirements in `SYS.2`/`SWE.1`, secure coding, or penetration tests do not by themselves demonstrate those cybersecurity processes.

### 8.2 Functional safety

Automotive SPICE capability does not demonstrate ISO 26262 compliance, functional-safety achievement, ASIL suitability, or product approval. The ECU scope decision must identify safety responsibilities and create a separate safety lifecycle backlog where applicable, while maintaining controlled interfaces to Automotive SPICE requirements, architecture, implementation, verification, configuration, problems, changes, risks, and release.

### 8.3 Product compliance

An Automotive SPICE assessment rates process capability. It does not certify the ECU’s safety, cybersecurity, regulatory conformity, functional correctness, or fitness for every use.

## 9. Evidence and assessment method for Level 1

For every selected process and sampled process instance, the assessment input should require an outcome worksheet containing:

1. process ID, purpose, organizational responsibility, and process-instance boundary;
2. each official PAM outcome and its relevant base-practice/output indicators;
3. validated objective evidence, artifact revision/baseline, source, owner and access location;
4. interview or observation corroboration;
5. outcome achievement, strengths, weaknesses and contrary evidence;
6. sampling and aggregation rationale across process instances;
7. PA 1.1 rating rationale; and
8. resulting process capability level and limitations.

Repository evidence should also carry:

- `product_id` and `project_id`;
- `process_id` and `process_instance_id`;
- `baseline_id` and artifact revision;
- evidence owner, reviewer/approver where applicable, and validity period;
- canonical origin (`process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, or `controlled-scenario`), separate from the `I/M/O/S` evidence class; and
- confidentiality, retention, and access rules.

A completed documentation import is objective evidence for that import process instance. A reusable schema or validator can be an implemented mechanism. Neither is objective execution evidence for `SYS.4`, `SWE.6`, `VAL.1`, or any other ECU process unless it was actually used in that ECU instance and the resulting evidence is valid for the assessed outcome.

## 10. Current sufficiency conclusion

For the future ECU product, the current repository is **not yet sufficient to demonstrate CL1 for any process**, because:

- no concrete ECU product, organizational unit, release, responsibility allocation, or process instance has been approved;
- no ECU stakeholder/system/software requirements, architectures, detailed designs, source baseline, target build, verification/validation results, or release package exist in the inspected scope;
- no ECU-specific management, quality, configuration, problem, change, risk, measurement, supplier, or assessment records were found; and
- existing evidence belongs to the documentation/data-pipeline product and cannot be aggregated into an ECU capability rating.

This is an evidence-boundary conclusion, not a formal `N` or CL0 rating. A process not assessed receives no rating.

The repository is nevertheless a useful foundation. Stable identities, provenance, versioning concepts, trace schemas, curation workflows, validators, reports, deterministic generation, tests, and authority boundaries can become reusable process assets or tools after they are adapted, controlled, and operated on real ECU process instances.

The dependency-linked remediation plan is documented in [`04-gap-roadmap.md`](04-gap-roadmap.md) and Features `0020` and `0022`–`0032` in `TODO.md`. Features `0011`–`0018` remain reusable CL2/process-system work; they do not substitute for the ECU-specific execution evidence required by the new features.

## 11. Claim discipline

Before a validated assessment, use wording such as:

> “The project is preparing an Automotive SPICE PAM 4.0 Level-1 process profile for a future automotive ECU development instance. Current documentation-pipeline artifacts are enabling process assets, not ECU capability evidence.”

After assessment, state the organizational unit, supplied product, release/process instances, process profile, PAM/version, assessment method/date, evidence baseline, per-process PA 1.1 ratings, exclusions/shared responsibilities, and limitations.

Do not say “the repository is ASPICE Level 1,” “the ECU is ASPICE certified,” or “all processes are Level 1” unless the expanded statement is supported by a valid named-process assessment result.

## 12. Authoritative source

- VDA QMC, *Automotive SPICE® Process Reference Model / Process Assessment Model, Version 4.0*, released 2023-11-29: <https://vda-qmc.de/wp-content/uploads/2023/12/Automotive-SPICE-PAM-v40.pdf>
- VDA QMC Automotive SPICE publications page: <https://vda-qmc.de/en/automotive-spice/automotive-spice-veroeffentlichungen/>

The official PAM’s distribution notice directs recipients to obtain it from VDA QMC. This repository links to the source and does not redistribute the PDF.