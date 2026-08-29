# Automotive SPICE Capability Level 1 and Level 2 survey

**Survey baseline:** 2026-08-15

**Reference model:** Automotive SPICE® Process Assessment Model (PAM), version 4.0, released 2023-11-29

**Assessment type:** internal repository and readiness gap analysis; not a formal process assessment and not a capability rating

## Current-authority overlay

This survey remains a dated observation of the `2026-08-15` baseline. Later
authority does not rewrite what was known then. Current readers must also use
`DEC-0020-001`, the approved 14-process applicability matrix from `0020-04`,
the `0020-07` assessment method, and `DEC-0011-001` for the
documentation-evidence association boundary.

Feature `0019` evidence is `documentation-execution` and may be traced only as
candidate evidence with exact instance, origin, baseline, limitations,
validity, and contrary evidence. Neither that association nor this survey
assigns outcome achievement, `N`/`P`/`L`/`F`, CL1, or CL2. The historical
`0010` to active `0019` renumbering remains provenance, while completed
historical `0010` remains Performance Package 2.

## Program context

The program intends to develop software for automotive electronic control units (ECUs). The present repository documents publicly available specification elements and implements extraction, curation, generation, validation, and publication tooling. That work is an enabling first step, not the final assessed ECU product.

This clarification resolves the earlier domain question: ECU software development is within Automotive SPICE’s intended embedded-automotive domain. Important scope questions remain unresolved, however. No concrete ECU/product variant, supplied-product boundary, organizational unit, project/release, lifecycle responsibility allocation, process profile, or process instance has yet been approved for assessment.

The documentation pipeline may supply reusable process definitions, trace/evidence schemas, validators, reports, and configuration mechanisms. Its execution evidence belongs to documentation-pipeline process instances and cannot be used as objective ECU execution evidence merely because both concern automotive specifications.

## Purpose

This dossier answers four questions:

1. What does Automotive SPICE Capability Level 1 require for each named process?
2. Which PAM 4.0 processes are a defensible starting profile for ECU software or complete ECU development?
3. How far do the current repository processes and evidence support that future ECU goal?
4. What additional management and work-product controls are needed to progress from CL1 to CL2?

The short answer is:

> The repository provides useful process/tooling foundations, but there is currently no approved ECU process instance and therefore no evidence basis for assigning CL1 or CL2 to any ECU process. The next milestone is to scope and operate a real ECU Level-1 process profile; CL2 then adds managed performance and work-product management to processes whose outcomes are fully achieved.

Automotive SPICE does not assign one capability level to a repository or ECU in the abstract. Capability is rated **per named process** in an approved assessment scope.

| Milestone | Per-process gate |
|---|---|
| Capability Level 1 | `PA 1.1 = L or F` |
| Capability Level 2 | `PA 1.1 = F`, `PA 2.1 = L or F`, and `PA 2.2 = L or F` |

A strong result in one process cannot compensate for a weak result in another, and a process outside scope receives no rating.

## Documents

| Document | Purpose |
|---|---|
| [`01-assessment-basis-and-scope.md`](01-assessment-basis-and-scope.md) | Source, terminology, two-product evidence boundary, candidate ECU process profiles, exclusions, and assessment method |
| [`02-level-1-requirements.md`](02-level-1-requirements.md) | Comprehensive CL1 rule, all-32-process applicability survey, ECU process-performance requirements, and evidence method |
| [`02-level-2-requirements.md`](02-level-2-requirements.md) | CL2 rating rule and PA 2.1/PA 2.2 management requirements layered onto performed processes |
| [`03-current-state-assessment.md`](03-current-state-assessment.md) | Assessment of the current documentation foundation and its insufficiency as ECU execution evidence; no formal ratings |
| [`04-gap-roadmap.md`](04-gap-roadmap.md) | Staged ECU CL1 and CL2 roadmap, dependencies, and exit criteria |
| [`05-evidence-register.md`](05-evidence-register.md) | Trace from indicators to repository evidence, origin/product validity, and limitations |

The executable backlog decomposition is in `TODO.md`:

- Features **0011–0018**: reusable assessment, process-management, work-product, engineering, support, and CL2 foundation;
- Feature **0019**: a documentation-domain Eclipse S-Core import campaign that makes no capability claim; and
- Features **0020 and 0022–0032**: ECU-specific CL1 scope, core/conditional process operation, assessment, correction, and closure.

## Candidate ECU process profiles

Feature `0020` must approve the supplied-product boundary and responsibility allocation. Until then, use these as starting hypotheses rather than declared assessment scopes.

### ECU software-delivery nucleus — 14 processes

For an organization receiving allocated software requirements/architecture constraints and delivering ECU software:

- `SWE.1`–`SWE.6`;
- `SPL.2`;
- `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`; and
- `MAN.3`, `MAN.5`, `MAN.6`.

### Full ECU system-and-software profile — 20 processes

Where the organization owns the complete system lifecycle **and** intended-use validation, add:

- `SYS.1`–`SYS.5`; and
- `VAL.1`.

Where responsibilities are split, include only the processes actually performed by the assessed unit and control the interfaces/evidence for each shared or external process.

### Conditional scope

- `ACQ.4` when the assessed unit monitors a development supplier;
- `HWE.1`–`HWE.4` when ECU electronics development/verification is owned;
- `MLE.1`–`MLE.4` and `SUP.11` when the automotive product has an in-scope ML model/data lifecycle;
- `PIM.3` when organizational process improvement itself is assessed; and
- `REU.2` when components/platforms are deliberately managed as reuse products.

Cybersecurity-specific processes are not part of the 32-process base PAM 4.0 inventory. An applicable ECU requires a separate Automotive SPICE for Cybersecurity/ISO/SAE 21434 scope decision. Functional-safety responsibility requires a separate ISO 26262 lifecycle decision. Automotive SPICE capability does not certify safety, cybersecurity, or product conformity.

## Current evidence characterization

No ECU PA 1.1 rating or capability level is assigned. There is no approved ECU process instance against which the repository can be rated.

| Evidence population | What exists | What it can support | What it cannot support |
|---|---|---|---|
| Process definitions and conventions | Architecture, maintenance/process documents, roles, schemas, ID/status/history rules | Reusable intent and candidate process assets after review/tailoring | Proof that an ECU process outcome occurred |
| Implemented mechanisms | Extractors, generators, validators, tests, version/evidence/dependency APIs, reports | Reusable tools/mechanisms after qualification/configuration as appropriate | ECU execution evidence merely because code exists |
| Documentation execution | Generated documentation, import/curation campaigns, publication and build reports | Outcomes of the named documentation process instance | `SYS`, `SWE`, `VAL`, ECU `SPL`, or ECU support/management outcomes |
| ECU execution | None found in the inspected scope | Nothing can yet be rated | Any CL1 or CL2 ECU capability claim |

The previous `N/P` tables in this dossier were evidence-coverage hypotheses for the documentation pipeline, not ratings. They must not be carried into the ECU profile. A future assessment must apply the official outcome and attribute rules to approved ECU instances.

## What is already useful

- A clear layered architecture and source/generated separation in `_src/ARCHITEKTUR.md` and `_src/WARTUNG.md`.
- Stable identities, status/history concepts, curation queues, version IDs, dependency graphs, and evidence schemas under `_src/tools/` and `docs/pipeline/`.
- Deterministic generation and broad structural validation through `_src/generate.py` and `_src/validate.py`.
- Unit/integration-oriented tests and negative fixtures under `_src/tests/` and `_src/tools/test_*.py`.
- Build-report, campaign, publication-report, and evidence-retention concepts.
- Explicit human/AI/tool authority boundaries in `docs/pipeline/roles.md`.
- A dependency-linked backlog convention in `TODO.md`/`DONE.md`.

These are foundations only. Before reuse for ECU development, they need product-specific requirements, ownership, configuration, review/approval, operating evidence, and assessment validity.

## Why ECU Level 1 is not yet demonstrated

1. **No approved ECU assessment input.** The concrete ECU, supplied product, organization, lifecycle, project/release, process instances, responsibilities, and process profile are unknown.
2. **No ECU engineering baselines.** The repository contains public specification content and pipeline requirements, not approved ECU stakeholder/system/software requirements, architectures, detailed designs, units, binaries, calibration/configuration, or target baselines.
3. **No ECU verification or validation results.** Pipeline unit tests and `validate.py` checks are not `SYS.4`, `SYS.5`, `SWE.4`–`SWE.6`, or `VAL.1` execution evidence for an ECU.
4. **No ECU support/management operation.** No ECU-specific project plan/status, QA, configuration baseline/audit, problems, changes, risks, metrics, supplier monitoring, or release evidence was found.
5. **No outcome assessment.** No official-outcome worksheets, interviews, validated evidence aggregation, PA 1.1 rationale, or process capability profile exist for an ECU instance.
6. **Conditional responsibilities are undecided.** Hardware, ML, suppliers, cybersecurity, functional safety, reuse, and validation responsibility must be allocated explicitly.

## Why Level 2 requires additional work

Even after CL1 is demonstrated, CL2 requires every scoped process to achieve all material outcomes fully and to be managed with appropriately controlled work products:

- `PA 1.1 = F` for each process;
- systematic objectives, planning, resources/competencies, assignments, interfaces, monitoring and adjustment (`PA 2.1 ≥ L`); and
- defined work-product requirements, storage/control, baselines, review and adjustment (`PA 2.2 ≥ L`).

Features `0011`–`0018` provide the detailed CL2 foundation. Feature `0018` must use the validated ECU Level-1 baseline from Feature `0025`; it must not import capability ratings from documentation campaigns.

## Claim discipline

Until Feature `0025` produces a validated result, use wording such as:

> “The project is preparing an Automotive SPICE PAM 4.0 Capability Level-1 process profile for a future automotive ECU development instance. Current documentation-pipeline artifacts are enabling process assets, not ECU capability evidence.”

Do not state that “the repository is ASPICE Level 1/2,” that “the ECU is ASPICE certified,” or that a documentation import is an Automotive SPICE assessment. A future result must name the organizational unit, supplied product, process/release instances, process scope, model/version, method/date, evidence baseline, per-process ratings, shared/excluded responsibilities, and limitations.

## Historical Word snapshot

[`2026-08-15-autodocs-pre-assessment-LEVEL2.docx`](2026-08-15-autodocs-pre-assessment-LEVEL2.docx) is a dated repository-only CL2 pre-assessment snapshot created before the ECU-product clarification. It remains historical evidence of that survey but must not be used as the current ECU Level-1/Level-2 assessment basis. Regenerate or supersede it only after Feature `0020` approves the ECU scope.

## Authoritative source

- VDA QMC, **Automotive SPICE® Process Assessment Model, Version 4.0**: <https://vda-qmc.de/wp-content/uploads/2023/12/Automotive-SPICE-PAM-v40.pdf>
- VDA QMC Automotive SPICE publications page: <https://vda-qmc.de/en/automotive-spice/automotive-spice-veroeffentlichungen/>

The official PAM’s distribution notice directs recipients to obtain it from VDA QMC. This repository therefore links to it rather than redistributing the PDF.
