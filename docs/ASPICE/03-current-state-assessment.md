# Current-state assessment: documentation foundation and ECU capability readiness

## 1. Executive finding

**The repository does not currently contain evidence sufficient to demonstrate Capability Level 1 or Level 2 for an automotive ECU process.** The program’s ECU-development domain is clear, but no concrete ECU product, organizational unit, responsibility profile, project/release, or process instance has been approved or executed in the inspected scope.

The repository contains meaningful evidence for a different product: a documentation/data-pipeline and publication capability. Architecture, deterministic generation, extraction traceability, configuration conventions, structured validation, tests, and evidence schemas can become reusable ECU process assets or mechanisms after review and tailoring. Documentation execution evidence cannot be substituted for ECU execution evidence.

Two conclusions must therefore remain separate:

- **ECU Level 1:** not assessable from the current evidence population; no ECU `PA 1.1` rating or capability level is assigned.
- **Documentation-pipeline CL2 readiness:** substantial technical foundations exist, but the inspected evidence does not support `PA 1.1 = F`, `PA 2.1 ≥ L`, and `PA 2.2 ≥ L` for any of the previously mapped candidate processes.

A valid ECU result requires Feature `0020` scope approval, real ECU process instances, official-outcome worksheets, validated evidence/interviews, defined aggregation, and assessment under Feature `0025` (CL1) or Feature `0018` (CL2).

## 2. Method and confidence

The assessment used repository artifacts only. It classified evidence as:

- **defined** — documented policy/process/criteria;
- **implemented** — code/schema/test exists;
- **operated** — a retained real execution artifact exists for a named product/process instance;
- **reviewed/approved** — a competent, authorized review and disposition is retained.

Each item must additionally use the canonical origin `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, or `controlled-scenario`. An artifact can be objective evidence for one process instance while being irrelevant to another.

A mechanism was not credited as fully operational merely because tests exist. A statement in `DONE.md` was treated as self-reported unless corroborated. Evidence in ignored/transient output was treated as weakly controlled.

Earlier dossier drafts used `N/P/L/F` letters as informal evidence-coverage shorthand. That notation is removed here because the same letters are formal process-attribute ratings. This survey now uses plain-language coverage descriptions only. No official-outcome worksheets, approved ECU process instances, evidence-validation interviews, or aggregation were available, and no arithmetic scoring was used.

## 3. Documentation-foundation mapping against cross-cutting attributes

This section assesses only how the current documentation product may inform future process design. It is not an ECU attribute assessment.

### PA 1.1 — Process performance

**Documentation-foundation coverage: partial across the previously mapped profile; not rated and not transferable to an ECU instance.**

Strengths:

- real software and publication outputs exist;
- the layered architecture is explicit in `_src/ARCHITEKTUR.md`;
- generation, validation, extraction, curation, and reporting tools are implemented;
- many records and generated pages demonstrate actual operation;
- tests and negative fixtures exist;
- traceability/status/history concepts are substantial.

Weaknesses:

- project/product stakeholder requirements are not controlled;
- architecture and verification are not traced to a software-requirement baseline;
- intended-use validation evidence is missing;
- product release approval/package/support evidence is incomplete;
- quality, problem, change, risk, and measurement process outcomes are only partially performed;
- campaigns and curation items often lack closure/decision/publication evidence;
- several advanced data-governance mechanisms remain unwired in normal operation.

### PA 2.1 — Process performance management

**Documentation-foundation coverage: partial across the previously mapped profile; no formal rating or ECU claim is supported.**

Existing foundations:

- TODO task IDs, states, prerequisites, acceptance criteria, and definitions of done;
- campaign lifecycle descriptions;
- generic human/AI/tool roles;
- runner purpose/goal/estimate conventions;
- counts, durations, statuses, and report summaries;
- examples of reactive corrections and performance optimization.

Missing systematic evidence:

- approved strategy/objectives and quality/time/throughput criteria per process;
- integrated work packages, estimates, schedule, milestones, and commitments;
- resource quantity/availability, competency requirements, named assignments, and qualification;
- interface/communication agreements;
- recurring actual-versus-plan review;
- deviation cause, corrective action, owner, due date, replanning, and effectiveness closure.

`docs/pipeline/aspice-level1-score-import.md` now correctly labels itself a local campaign-evidence contract and excludes managed planning/monitoring/responsibility evidence from Feature 0019. That exclusion is an important current-state limitation. The document also now clarifies that CL2 monitoring may be qualitative and/or quantitative, while statistical quantitative analysis/control is associated with CL4.

### PA 2.2 — Work-product management

**Documentation-foundation coverage: partial across the previously mapped profile; not rated and not transferable to an ECU instance.**

Strengths:

- source/generated separation and source-of-truth rules;
- many schemas, ID conventions, status models, and append-only design principles;
- Git-based source control and package lock for Node dependencies;
- curation/review queues and content-hash checks;
- build-report schema, campaign manifests, version/evidence/dependency APIs;
- validators and tests.

Weaknesses:

- no complete controlled work-product/configuration-item catalogue;
- review/approval criteria and evidence are uneven;
- `output/`, logs, runner archives, and `run.sh` are ignored without a clearly controlled alternative evidence repository;
- sampled run archive/build report storage was empty or incomplete;
- combined reports can select independently latest subreports and tolerate missing stages, so “success” need not mean one atomic run;
- Python/system tool dependencies are not comprehensively pinned;
- campaign manifest/version/evidence tooling is not fully wired to production writers;
- real curation closure is sparse relative to open queues;
- generated artifacts and release packages lack a consistently identified approval baseline.

## 4. Process-by-process readiness summary

The first coverage column describes reusable definitions/mechanisms or documentation execution only. The second asks whether objective execution evidence exists for an approved ECU process instance. “None” is an evidence finding, not a formal `N` rating.

| Process | Documentation foundation coverage | ECU execution evidence | Capability assigned? |
|---|---|---|---|
| `SYS.1` | Weak/partial audience and intake concepts | None | No |
| `SYS.2` | Public domain records and schemas are not ECU system requirements | None | No |
| `SYS.3` | Pipeline architecture is not an ECU system architecture | None | No |
| `SYS.4` | Pipeline integration checks are not ECU system integration evidence | None | No |
| `SYS.5` | Pipeline validation is not ECU system verification evidence | None | No |
| `SWE.1` | Partial pipeline requirements/conventions | None | No |
| `SWE.2` | Relatively strong pipeline architecture mechanism | None | No |
| `SWE.3` | Partial pipeline design/code/test mechanism | None | No |
| `SWE.4` | Partial reusable unit-test mechanism | None | No |
| `SWE.5` | Partial reusable integration-validation mechanism | None | No |
| `SWE.6` | Partial reusable integrated-validation mechanism | None | No |
| `VAL.1` | Little intended-use validation even for the documentation product | None | No |
| `SPL.2` | Partial documentation publication mechanism | None | No |
| `SUP.1` | Partial validation/review mechanism | None | No |
| `SUP.8` | Substantial configuration concepts; incomplete operation | None | No |
| `SUP.9` | Partial queues/finding mechanism | None | No |
| `SUP.10` | Partial intake/change mechanism | None | No |
| `MAN.3` | Partial backlog/campaign planning concepts | None | No |
| `MAN.5` | Little maintained process evidence | None | No |
| `MAN.6` | Partial counts/reporting mechanism | None | No |

Conditional `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` are not rated. Feature `0020` must decide their applicability from ECU responsibility, not from repository artifact availability.

## 5. Documentation-foundation engineering findings

The detailed findings below concern the documentation/data-pipeline product. They identify reusable strengths and limitations but do not characterize the performance of future ECU processes.

### SYS.1 — Requirements Elicitation

Evidence:

- `README.md` identifies the product and publication location;
- `_src/sources/pages/process.json` and process documentation identify audiences and pipeline activities;
- browser review intake provides one stakeholder-feedback channel;
- TODO feature narratives capture internal needs.

Insufficiency:

- no stakeholder map or communication commitments;
- no elicitation record or agreed stakeholder-requirement baseline;
- no stable expectation IDs, priority, source, acceptance status, or change/impact history;
- no systematic status/disposition communication;
- volunteer/end-user testing remains backlog work.

Documentation-foundation coverage: informal and partial for that product; no ECU `SYS.1` result or rating.

### SYS.2–SYS.5 — ECU system lifecycle

No ECU system-requirement baseline, system architecture/allocation, system integration baseline, architecture/interface-based integration-verification results, or system-requirements-based verification results exist in the inspected scope. Public specification records, the pipeline architecture, pipeline orchestration, and `validate.py` do not substitute for these process outcomes.

Assessment: no ECU execution evidence; no rating assigned. Feature `0022` defines the shared system interface/trace foundation, and conditional Features `0028`–`0032` add independently selectable `SYS.1`–`SYS.5` execution paths.

### SWE.1 — Software Requirements Analysis

Evidence:

- `_src/WARTUNG.md`, `_src/KONVENTIONEN.md`, architecture invariants, schemas, and TODO acceptance criteria define many expected behaviors and constraints;
- Feature 0019 has unusually detailed acceptance and evidence criteria.

Insufficiency:

- requirements are scattered and mix process rules, design decisions, operational instructions, and product requirements;
- no approved software-requirement baseline with stable IDs, attributes, priority, rationale, verification method, and status;
- no systematic feasibility/impact analysis or bidirectional trace to architecture, code, and tests;
- imported `SWS_*`/S-Core records describe source-domain content, not requirements for this pipeline software.

Documentation-foundation coverage: partial; no ECU `SWE.1` result or rating.

### SWE.2 — Software Architectural Design

Evidence:

- `_src/ARCHITEKTUR.md` defines a five-layer architecture, dependencies, tools, invariants, and extension recipes;
- `docs/pipeline/data-model.md`, `workflow-lifecycle.md`, and related schema documents define important static and dynamic structures;
- source separation and project-neutral design are explicit.

Insufficiency:

- no trace from architecture elements to approved software requirements;
- dynamic behavior, external interfaces, failure behavior, security/privacy, and deployment architecture are unevenly specified;
- technical-quality evaluation, alternatives, rationale, and approval are not systematically recorded;
- documentation contains implemented, partially implemented, and conceptual behavior in the same corpus.

Documentation-foundation coverage: comparatively strong but partial; no formal attribute hypothesis and no ECU `SWE.2` result or rating.

### SWE.3 — Detailed Design and Unit Construction

Evidence:

- substantial Python and JavaScript implementation;
- module docstrings and tool documentation;
- localized design descriptions and schemas;
- tests exercise many units.

Insufficiency:

- no controlled detailed-design set or defined unit catalogue;
- no coding standard and systematic code-review evidence;
- no complete trace from requirements/architecture through detailed design to code;
- no retained construction/code-review approval baseline.

Documentation-foundation coverage: partial; no ECU `SWE.3` result or rating.

### SWE.4 — Software Unit Verification

Evidence:

- unit tests and negative fixtures under `_src/tests/`;
- tool-specific tests such as `_src/tools/test_build_report.py`;
- parser, identity, campaign, lifecycle, versioning, and rendering checks.

Insufficiency:

- no approved unit-verification strategy;
- no release-specific selection, coverage objectives, structural/static-analysis strategy, or regression rationale;
- no detailed-design/unit-to-verification-measure/result trace;
- no controlled CI/test execution report tied to release baselines;
- the 200-record benchmark remains a draft with unresolved curation/shape issues in Feature 0007.

Documentation-foundation coverage: partial; no ECU `SWE.4` result or rating.

### SWE.5 — Component and Integration Verification

Evidence:

- documented pipeline sequence;
- `validate.py` checks cross-file/tree/link/language/lifecycle consistency;
- build-report combination and end-to-end generation mechanisms;
- multilingual and browser checks.

Insufficiency:

- no controlled integration sequence, preconditions, component/interface verification specifications, or coverage selection;
- no architecture/detailed-design-to-component/integration-measure/result trace;
- combined reports are not guaranteed to represent all stages from one run;
- absent stage data may be represented as empty instead of failing the release evidence bundle.

Documentation-foundation coverage: partial; no ECU `SWE.5` result or rating.

### SWE.6 — Software Verification

Evidence:

- broad integrated validation orchestrated by `_src/validate.py`;
- generated report pages and structured findings;
- reproducibility, links, languages, namespaces, records, and lifecycle checks.

Insufficiency:

- checks verify internal invariants, not a controlled software-requirement baseline;
- no requirements-to-measures/results trace;
- no approved release/regression selection and pass/fail specification;
- sampled workflow validation code was reported to inspect queue paths different from the actual `_src/spec/review-queue` and `_src/spec/curation-queue` locations;
- no retained, controlled release-specific test result set.

Documentation-foundation coverage: partial; no ECU `SWE.6` result or rating.

### VAL.1 — Validation

Evidence:

- public deployment and direct browser use;
- browser/client-rendered checks;
- browser review widget and language checks.

Insufficiency:

- existing browser checks are product verification, not intended-use validation;
- no identified user groups and stakeholder expectations tied to validation;
- no representative user scenarios, operational environment matrix, selection criteria, validation sessions, satisfaction/usability/accessibility findings, or acceptance decision;
- no trace to stakeholder requirements.

Documentation-foundation coverage: little intended-use validation evidence; no formal `N` rating and no ECU `VAL.1` result.

### SPL.2 — Product Release

Evidence:

- generated multilingual publication exists;
- `_src/publish.sh` packages and pushes files;
- site/release metadata and build reports exist.

Insufficiency:

- no consistent unique release/package identifier tied to inputs and reports;
- no explicit release-content baseline, approval record, release notes, known limitations, support type/service level/duration, rollback, or delivery confirmation;
- publication script does not itself prove a successful complete generation/validation/approval gate;
- package completeness relative to configured languages/reports is not systematically demonstrated.

Documentation-foundation coverage: partial; no ECU `SPL.2` result or rating.

## 6. Documentation-foundation supporting process findings

### SUP.1 — Quality Assurance

Evidence:

- extensive validation and quality reports;
- roles distinguish curator, validator, tools, and AI;
- escalation to human judgment exists;
- quality criteria are embedded in schemas/conventions.

Insufficiency:

- verification/testing is not equivalent to independent QA;
- no QA plan, independence criteria, conformance-audit schedule, objective process audit, nonconformance owner/due date, escalation record, management resolution, or recurrence-prevention evidence;
- some checks can be skipped or inspect incomplete paths;
- open queues do not demonstrate issue resolution.

Documentation-foundation coverage: partial; no ECU `SUP.1` result or rating.

### SUP.8 — Configuration Management

Evidence:

- Git-based source control;
- clear source/generated classification;
- IDs, status/history, schemas, manifests, package locks, append-only version APIs;
- reproducibility objective and checks.

Insufficiency:

- no complete configuration-management plan or configuration-item catalogue;
- evidence/report/run outputs are ignored or transient;
- not all dependencies and external inputs are pinned/content-hashed;
- baseline, status accounting, configuration audit, backup/recovery, and release identity are incomplete;
- production wiring of version stores and campaign manifests is incomplete.

Documentation-foundation coverage: substantial mechanisms but incomplete operation; no formal attribute hypothesis and no ECU `SUP.8` result or rating.

### SUP.9 — Problem Resolution Management

Evidence:

- review/curation queues, extraction residuals, validation findings, and TODO defects;
- workflow states and claim mechanics;
- evidence/rationale fields.

Insufficiency:

- no unified problem record with reproducibility, classification, cause/common-cause, impact, urgent action, owner, long-term resolution, verification, closure, and trend reporting;
- problem and change semantics are mixed across TODO, review queues, curation queues, reports, and commits;
- review completion semantics may delete evidence;
- sampled curation report showed many open items and no closure flow evidence.

Documentation-foundation coverage: partial; no ECU `SUP.9` result or rating.

### SUP.10 — Change Request Management

Evidence:

- TODO/change backlog, Git history, review/curation ingest, content hashes, decision classes, and controlled human authority boundaries;
- stale-text/conflict checks before applying review packages.

Insufficiency:

- no consistent change-request identity/status across all intake paths;
- impact on work products, resources, schedule, risk, requirements, tests, and release is not systematically analyzed;
- approval/authorization, implementation confirmation, trace to affected baselines, verification, communication, and closure are incomplete;
- coded decision hooks are not fully wired.

Documentation-foundation coverage: partial; no ECU `SUP.10` result or rating.

## 7. Documentation-foundation management process findings

### MAN.3 — Project Management

Evidence:

- feature goals, task IDs, dependencies, acceptance criteria, definitions of done, and campaign phases;
- generic roles and tool prerequisites;
- some status and run estimates.

Insufficiency:

- no approved project goals/boundaries/lifecycle/release plan as a controlled management baseline;
- no estimates, integrated schedule/milestones, named owners, resource/competency allocation, commitments, interface agreements, or recurring status review;
- no systematic actual-versus-plan analysis and corrective replanning;
- `BACKLOG.md` forms a second informal work list outside the TODO governance model.

Documentation-foundation coverage: partial; no ECU `MAN.3` result or rating.

### MAN.5 — Risk Management

Evidence:

- incidental risk language and technical cautions;
- some escalation and fail-safe behavior.

Insufficiency:

- no risk-management strategy;
- no maintained risk register;
- no probability/severity/exposure criteria, owners, treatments, due dates, residual risk, review cadence, effectiveness checks, or closure evidence.

Documentation-foundation coverage: little maintained risk-process evidence; no formal `N` rating and no ECU `MAN.5` result.

### MAN.6 — Measurement

Evidence:

- build durations, counts, findings, fallback/reject counts, queue status, extraction deltas, and performance comparisons;
- structured report schemas.

Insufficiency:

- no approved management information needs;
- no operational metric definitions, owner, source, collection method, data-quality rule, target, threshold, cadence, analysis method, or retention baseline;
- reports can be incomplete or combine unrelated runs;
- little evidence that trends drive documented management decisions and corrective actions.

Documentation-foundation coverage: partial; no ECU `MAN.6` result or rating.

## 8. Additional enabling-process observations

### PIM.3 — Process Improvement

The repository demonstrates improvement activity through performance optimization, incident corrections, new validators, and TODO/DONE evolution. However, a process-improvement opportunity is not the same as a product fix. A rated `PIM.3` process would need explicit sponsorship, current-state analysis, prioritized improvement goals, deployment/training, monitoring of effects, and communicated lessons. The roadmap can provide this loop, but `PIM.3` is not automatically required to rate other selected processes at CL1 or CL2.

### REU.2 — Management of Products for Reuse

The architecture describes project-neutral reuse and copy recipes. It does not yet demonstrate managed reuse candidates, target-context analysis, limitations, qualification, provision, and provider feedback. Keep REU.2 conditional unless reusable pipeline packages become a deliberate assessed product.

## 9. Data-quality and credibility concerns

The following issues should be resolved because they weaken confidence in evidence even when the underlying mechanisms are promising:

- documentation intentionally mixes implemented, partial, and conceptual behavior;
- some DONE entries are self-reported or use non-hash references;
- the active S-Core import was renumbered from conflicting `0010` to `0019`; historical `0010` remains Performance Package 2, and the alias must be preserved when migrating evidence references;
- campaign manifests and version stores include evidence that appears retrospective or synthetic;
- build reports may omit a producer or runner reference while still publishing success;
- output evidence is ignored and sampled archives were empty;
- hundreds of review/curation items remain open;
- record statuses can be mechanically backfilled without equivalent field-level review evidence;
- `BACKLOG.md` contains active work outside the canonical TODO state model.

These are not all direct PAM violations, but they reduce evidence integrity and must be addressed by configuration, change, and QA controls.

## 10. Overall sufficiency judgment

The current evidence is **not sufficient to assign Automotive SPICE Capability Level 1 or Level 2 to any ECU process**. The ECU development domain is applicable, but the assessable product/organization/process instances and responsibility profile remain unapproved, and no ECU execution evidence was found. No capability ratings are assigned.

The repository is a strong technical foundation for process assets and evidence tooling, not a demonstrated ECU process system. The shortest credible path is not to create decorative compliance documents or relabel documentation evidence. It is to:

1. approve a precise ECU product, organizational, responsibility, process, and evidence boundary;
2. operate the selected `SYS`, `SWE`, `VAL`, `SPL`, support, and management processes on a real controlled ECU instance;
3. preserve lifecycle-correct traceability and product-specific objective evidence;
4. assess every official process outcome and obtain `PA 1.1 = L or F` per Level-1 target process;
5. correct outcome weaknesses and publish only the supported process profile; and
6. then add/validate PA 2.1 and PA 2.2 controls and reach `PA 1.1 = F` for the CL2 target.

Features `0020` and `0022`–`0032` implement the ECU Level-1 core, independently selectable system/validation paths, and assessment stage. Features `0011`–`0018` remain the reusable CL2/process-system foundation.
