# Assessment basis and proposed ECU scope

## 1. Status and limitations

This is a **PAM 4.0-informed readiness survey and gap analysis**, not a formal Automotive SPICE assessment and not a process capability rating.

The program intends to develop software for automotive ECUs. This is within the embedded-automotive domain for which Automotive SPICE is intended. The current repository, however, is a public-specification documentation/data-pipeline and publication product. It is an enabling first step, not yet the concrete ECU product or process instance to be assessed.

The following assessment-input decisions remain open under Feature `0020`:

- the first ECU, variant, and supplied-product boundary;
- organizational unit and customer/supplier relationship;
- intended use, lifecycle stage, project, release/increment, and assessment purpose;
- system/software/hardware/ML, supplier, cybersecurity, safety, validation, and release responsibilities;
- named PAM processes and process instances;
- exclusions, shared/external responsibilities, sampling, aggregation, and permitted claims; and
- assessment timing, assessor competence/independence, confidentiality, and evidence baseline.

The survey was based on:

- Automotive SPICE PAM 4.0;
- repository documentation, source code, tests, data, reports, and backlog state inspected during the 2026-08-14/15 review;
- a sampled repository-state capture produced by the project runner; and
- no ECU project artifacts, organizational records, customer/supplier agreements, interviews, target executions, external issue/CI systems, or assessor-validated ECU evidence.

“Not demonstrated” in this dossier means that sufficient validated evidence was not found in the inspected scope. It does not prove that an activity never occurs outside the repository. For the future ECU product, no `N/P/L/F` rating is assigned because no approved ECU process instance was assessed.

## 2. Normative and informative basis

### Primary source

VDA QMC, *Automotive SPICE® Process Reference Model / Process Assessment Model, Version 4.0*, released 2023-11-29:

<https://vda-qmc.de/wp-content/uploads/2023/12/Automotive-SPICE-PAM-v40.pdf>

Relevant sections include:

- §3.2: measurement framework;
- §3.2.2: process-attribute rating;
- §3.2.4: capability-level model;
- §4: process purposes, outcomes, base practices, and output information items;
- §5.2–5.3: `PA 1.1`, `PA 2.1`, and `PA 2.2`; and
- Annex B: information-item characteristics.

The PAM incorporates elements from ISO/IEC 33020:2019 and ISO/IEC 15504-5:2006. This survey does not claim independent conformance to those standards.

Cybersecurity-specific processes require the applicable Automotive SPICE for Cybersecurity model and ISO/SAE 21434 responsibility mapping. Functional-safety work requires a separate ISO 26262 lifecycle. Neither is silently treated as part of the 32-process PAM 4.0 inventory.

### Local sources

The main repository sources inspected were:

- `README.md`, `AGENTS.md`, `TODO.md`, `DONE.md`, and `BACKLOG.md`;
- `_src/ARCHITEKTUR.md`, `_src/WARTUNG.md`, `_src/KONVENTIONEN.md`, and `_src/SPEC_BUILD_PROCESS.md`;
- `docs/pipeline/*.md`;
- `_src/generate.py`, `_src/validate.py`, and relevant `_src/tools/*.py`;
- `_src/tests/`, `_src/tools/test_*.py`, and fixtures; and
- campaign, record, review/curation, report, and generated publication artifacts.

No local copy of the official PAM is redistributed. Before an assessment baseline is approved, the outcome worksheets must be checked against the official VDA QMC publication and record its version/date.

## 3. Critical terminology

### Capability belongs to a process

Automotive SPICE has a process dimension and a capability dimension. Capability levels are derived **for a named process** from that process’s attribute ratings. There is no single context-free rating called “the repository’s ASPICE level” or “the ECU’s ASPICE certification.”

| Process | PA 1.1 | PA 2.1 | PA 2.2 | Capability |
|---|---:|---:|---:|---:|
| `SWE.1` | L | — | — | CL1 |
| `SWE.2` | F | L | L | CL2 |
| `VAL.1` | P | — | — | CL0 |

This example is illustrative, not a current result. A process outside scope has no rating, not an assumed `N` or CL0.

### Capability Level 1

CL1 requires `PA 1.1 Process performance = L or F` for the named process. The process achieves significant or complete performance of its defined outcomes. Base practices and output information items are indicators, not a one-file-per-item checklist or a points formula.

See [`02-level-1-requirements.md`](02-level-1-requirements.md) for the complete Level-1 survey.

### Capability Level 2

CL2 requires, for each named process:

- `PA 1.1 = F`;
- `PA 2.1 = L or F`; and
- `PA 2.2 = L or F`.

See [`02-level-2-requirements.md`](02-level-2-requirements.md).

### Process instance

A process instance is a concrete execution in a product/project and organizational context. Future ECU examples could be:

- `SWE.1` for ECU product X, software release R1;
- `SWE.4` for the controlled unit baseline of that release;
- `SYS.4` for ECU integration build B17 on a named hardware/calibration baseline;
- `SUP.9` for problems handled by that ECU project during a defined period; or
- `SPL.2` for the supplied firmware/release package delivered to a named recipient.

Documentation examples include one AUTOSAR extraction/curation campaign, the Eclipse S-Core v0.6.0 import, or one documentation publication release. Those are different products and process instances.

Evidence from unrelated instances must not be combined opportunistically. The assessment input must state which instances are sampled and how ratings are aggregated.

### Indicators are not a mandatory document checklist

Base practices, generic practices, and information items help an assessor judge outcomes and attributes. One artifact can contain several required kinds of information, and several artifacts can collectively supply one information item. Alternative implementations are acceptable when validated evidence demonstrates the required result.

Renaming a TODO entry “project plan,” a test “SWE.6,” or a Git commit “approval” does not make it adequate when the relevant process outcome is absent.

## 4. Product and evidence boundaries

### 4.1 Target assessed product: automotive ECU development

Feature `0020-01` must identify one concrete supplied product. Depending on responsibility, this may be:

1. a complete ECU/system product including hardware/software integration;
2. an ECU software product running on allocated hardware; or
3. a software component integrated by a customer or higher-tier supplier.

The scope must include the product context, variants/configurations, operating environment, customer and external interfaces, release/increment, organizational unit, and lifecycle responsibilities. “We develop ECU code” establishes the domain but is not by itself a sufficient assessment input.

### 4.2 Enabling product: documentation and process tooling

The current repository contains:

- imported public specification records and provenance;
- page models, templates, diagrams, translations, and curated content;
- extraction, normalization, generation, validation, indexing, diagram, and i18n software;
- review/curation/version/dependency/evidence schemas and tools; and
- generated multilingual publication artifacts.

These can contribute reusable process intent (`I`) or implemented mechanisms (`M`). Real documentation campaigns can provide objective evidence (`O`) for their own named instances. They do not become objective ECU execution evidence merely because the source material or future use is automotive.

The imported AUTOSAR and S-Core requirements are **domain content**. They are not a substitute for stakeholder, system, software, hardware, ML, safety, or cybersecurity requirements governing a particular ECU product.

### 4.3 Required origin and validity metadata

Each assessment artifact should identify at least:

- product and project;
- named process and process instance;
- baseline and artifact revision;
- owner and evidence origin;
- validity/applicability and relationships to other evidence;
- review/approval where required; and
- retention, access, confidentiality, and integrity controls.

Evidence origin must use one canonical value: `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, or `controlled-scenario`. Cross-product evidence can be reused only for the aspect it genuinely demonstrates; the separate `I/M/O/S` field records evidence class.

## 5. Candidate process profiles

This profile is a recommendation. Feature `0020` must approve it based on responsibility and the assessment purpose.

### 5.1 ECU software-delivery nucleus

| Process | Applicability rationale |
|---|---|
| `SWE.1`–`SWE.3` | ECU software requirements, architecture, detailed design, and unit construction are direct development responsibilities. |
| `SWE.4`–`SWE.6` | Units, components/integration, and integrated software require verification against the correct lifecycle bases. |
| `SPL.2` | The supplied firmware/software package needs controlled identification, approval, content, information, and delivery. |
| `SUP.1` | Objective process/product quality assurance and nonconformance closure are needed. |
| `SUP.8` | Requirements, models, source, binaries, calibration/configuration, tools, tests, evidence, and releases need configuration integrity. |
| `SUP.9` | ECU defects/problems require reproducibility, cause/impact analysis, durable resolution, verification, closure, and trend status. |
| `SUP.10` | Product/process changes require impact analysis, authorization, implementation trace, verification, closure, and communication. |
| `MAN.3` | Scope, lifecycle, work, estimates, resources, competencies, interfaces, commitments, schedule, progress, and corrective control require management. |
| `MAN.5` | Product, project, supplier, integration, verification, release, and external-dependency risks require managed treatment. |
| `MAN.6` | Management decisions require defined and trustworthy measurement information. |

This 14-process nucleus is not a PAM-mandated universal scope; it is the recommended minimum starting hypothesis for an organization that develops and releases ECU software.

### 5.2 Full ECU system-and-software profile

Add the following where the organization owns the corresponding system/product responsibilities:

| Process | Applicability rationale |
|---|---|
| `SYS.1` | Stakeholder/customer, operational, regulatory, service, safety, cybersecurity, and other expectations must be elicited and agreed. |
| `SYS.2` | Stakeholder requirements must be transformed into analyzed system requirements. |
| `SYS.3` | System elements, allocations, interfaces, behavior, variants, budgets, and rationale require an evaluated architecture. |
| `SYS.4` | Hardware/software/ML/external system elements and interfaces require controlled integration and architecture-based verification. |
| `SYS.5` | The integrated ECU/system must be verified against system requirements. |
| `VAL.1` | Suitability for intended use must be validated against stakeholder expectations in representative operation. |

If these responsibilities are external/shared, the scope must identify the responsible party and controlled incoming/outgoing baselines, acceptance, feedback, change, problem, configuration, risk, and release interfaces. A software-only label is not sufficient rationale by itself.

### 5.3 Conditional PAM 4.0 processes

| Process/process group | Inclusion rule |
|---|---|
| `ACQ.4` | Include when the assessed unit monitors a contracted supplier. Public tools or open-source consumption alone do not establish the process. |
| `HWE.1`–`HWE.4` | Include according to actual ECU electronics requirements/design/verification responsibility. Supplied hardware still needs system/configuration/risk/acceptance interfaces. |
| `MLE.1`–`MLE.4`, `SUP.11` | Include per automotive-product ML model/training/testing/data responsibility, not because generative AI assists documentation or coding. Allocate individual processes when responsibilities are split. |
| `PIM.3` | Include when organizational process improvement itself is to be rated. It is not a prerequisite imposed on the other CL1/CL2 processes. |
| `REU.2` | Include when platforms/components are deliberately managed and provided as reuse products. |

The all-32-process inventory and performance themes are in the Level-1 survey.

## 6. Separate cybersecurity and safety decisions

PAM 4.0’s 32-process catalog does not contain cybersecurity-specific `SEC` processes. Where applicable, Feature `0020-06` must select the relevant Automotive SPICE for Cybersecurity model/version and allocate extension responsibilities such as supplier request/selection, cybersecurity risk management, requirements, implementation, risk-treatment verification, and cybersecurity validation. It must also define interfaces to ISO/SAE 21434.

Functional-safety responsibility requires a separate ISO 26262 lifecycle and evidence plan. Automotive SPICE process capability does not establish ASIL suitability or functional-safety compliance. The safety and cybersecurity backlogs should link to, not duplicate, the base requirements, architecture, implementation, verification, configuration, problem/change, risk, QA, and release evidence.

## 7. Proposed staged assessment method

### Stage A — Level 1

After Feature `0020` approves the ECU scope:

1. Select the process instances and evidence population.
2. For each selected process, expand every official PAM outcome and relevant indicator in a controlled worksheet.
3. Validate objective evidence and corroborate it through interviews/observations.
4. Record strengths, weaknesses, contrary evidence, sampling, and aggregation rationale.
5. Apply the `N/P/L/F` scale to `PA 1.1` conservatively; do not compute a checklist percentage.
6. Derive CL1 separately for each process; `PA 1.1` must be `L` or `F`.
7. Correct material findings through controlled changes and reassess.
8. Publish only the bounded ECU process capability profile.

Feature `0025` implements this stage.

### Stage B — Level 2

Using the validated Level-1 baseline:

1. close all material outcome weaknesses until `PA 1.1 = F` for each target process;
2. validate every `PA 2.1` and `PA 2.2` achievement for each process;
3. retain objectives/plans, resource/competency allocations, interfaces, actual-versus-plan monitoring and adjustment;
4. validate work-product requirements, storage/control, baselines, reviews and adjustment; and
5. derive and report the CL2 profile independently per process.

Features `0011`–`0018` provide this CL2 foundation. Statistical/quantitative analysis and control of process variation are associated with PA 4.1/PA 4.2 and must not be imported as hidden CL1/CL2 requirements.

## 8. Baseline and evidence validity

As project-selected readiness controls, an assessment baseline should be clean, uniquely identified, and include or reference:

- assessment input, scope, responsibility/applicability matrix, and process-instance list;
- source-control revision, ECU/release/build identity, and configuration-item status;
- input, supplier, toolchain, dependency, target, hardware, calibration/configuration, and environment identities;
- approved stakeholder/system/software and applicable hardware/ML requirements;
- architecture, detailed design, source/model, binary, and construction/review evidence;
- lifecycle-correct verification/validation specifications, measures, results, coverage, findings, and summaries;
- project status, QA, configuration, problems, changes, risks, metrics, communications, decisions, and approvals;
- atomic build/test/release evidence; and
- release approval, package, notes, delivery result, support and rollback/update information.

Generated or ignored files can be valid evidence only if a controlled repository, integrity mechanism, access rule, and retention policy are identified. A transient local `output/` directory is not sufficient by itself.

## 9. Existing local “Level-1” campaign document

`docs/pipeline/aspice-level1-score-import.md` is a useful local campaign-evidence contract for Feature `0019`. It is **not** an Automotive SPICE Level-1 assessment definition because PAM outcomes and base practices are process-specific and capability is rated for named process instances. Its legacy filename is retained to avoid breaking existing links; the neutral document title and this explicit scope statement are authoritative.

Feature `0019` may report that committed campaign evidence is mapped to named documentation-process outcomes after review. It must not claim an ECU process outcome, ECU PA 1.1 rating, or Automotive SPICE capability level. Any such claim is reserved for the assessment and evidence population defined by Feature `0025` (CL1) or Feature `0018` (CL2).