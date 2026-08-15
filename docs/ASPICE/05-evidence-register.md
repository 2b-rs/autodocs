# ASPICE evidence register and ECU validity trace matrix

## 1. Evidence classification

This survey distinguishes four evidence classes:

| Code | Class | Meaning |
|---|---|---|
| `I` | Defined intent | Policy, process description, convention, acceptance criterion, or planned rule |
| `M` | Implemented mechanism | Source code, schema, validator, test, or workflow capable of performing a control |
| `O` | Objective execution evidence | A retained result from an actual process instance: approved baseline, completed review, report, log, decision, release, measurement, or closed issue |
| `S` | Self-reported completion | Backlog/DONE claim or prose assertion not independently corroborated by the inspected evidence |

`I/M/O/S` is a **project-specific evidence-readiness classification**, not a PAM-prescribed evidence taxonomy or rating rule. This project requires intent, implemented mechanisms where automation is expected, and objective execution evidence as a local safeguard. Code and documentation alone do not prove routine process execution.

Class and origin are separate. Every evidence item used for assessment must also identify one origin:

| Origin | Meaning |
|---|---|
| `process-definition` | Reusable policy, method, template, criterion, or process description |
| `implemented-mechanism` | Reusable tool, schema, validator, workflow, or repository control |
| `documentation-execution` | Result from a documentation/extraction/curation/publication process instance |
| `ecu-execution` | Result from the approved ECU product/process instance |
| `controlled-scenario` | Fixture, rehearsal, or synthetic case that is explicitly not represented as a real product event |

An `O` artifact is objective only for the product/process instance it actually records. A documentation campaign can be `O/documentation-execution`; it is not `O/ecu-execution`. Reusable definitions and mechanisms may support an ECU process after tailoring and use, but their existence is not outcome evidence.

## 2. Documentation-foundation PA 2.1 trace

| Generic practice | Existing evidence | Class | Sufficiency | Main gap |
|---|---|---:|---|---|
| `GP 2.1.1` Objectives and strategy | `TODO.md` feature goals/acceptance criteria; `AGENTS.md` runner goal hierarchy; `_src/SPEC_BUILD_PROCESS.md`; `docs/pipeline/processes.md` | I | Partial | No approved process-specific performance objectives, criteria, assumptions, constraints, and strategy for every scoped process. |
| `GP 2.1.2` Plan performance | TODO IDs, prerequisites, campaign phases/manifests | I/M | Partial | No maintained estimates, schedule, milestones, commitments, planned review points, or integrated release/process plan. |
| `GP 2.1.3` Determine resource needs | Tool prerequisites in `_src/WARTUNG.md`; generic roles in `docs/pipeline/roles.md` | I | Weak | No quantity/availability, competency matrix, authority, license/tool capacity, infrastructure, or budget needs per process instance. |
| `GP 2.1.4` Make resources available | Runner allocates workers; tools exist | M | Weak | No named assignment, availability, qualification/training/mentoring, delegated authority, or resource-allocation record. |
| `GP 2.1.5` Monitor and adjust | Extraction/build counts, TODO states, performance claims, report deltas | M/O/S | Partial | No actual-versus-plan baseline, thresholds, recurring status review, deviation owner/due date, replanning, or effectiveness closure. |
| `GP 2.1.6` Manage interfaces | Human/AI/tool boundaries in `docs/pipeline/roles.md`; workflow lifecycle; ingest interfaces | I/M | Partial | No approved communication/interface matrix, commitments, response expectations, supplier/user interfaces, or retained communication evidence. |

## 3. Documentation-foundation PA 2.2 trace

| Generic practice | Existing evidence | Class | Sufficiency | Main gap |
|---|---|---:|---|---|
| `GP 2.2.1` Define work-product requirements | JSON schemas, `docs/pipeline/*-schema.md`, `_src/KONVENTIONEN.md`, source/generated rules, status models | I/M | Relatively strong | Incomplete catalogue; inconsistent quality/review/approval criteria across all process work products. |
| `GP 2.2.2` Define storage/control requirements | Git conventions, directory model, ID/status/version docs, report retention prose | I | Partial | Access, backup/recovery, complete retention/disposal, approval, and baseline rules are not consistently defined; some documented rules conflict with actual ignored/transient storage. |
| `GP 2.2.3` Identify/store/control | Git-tracked source, records, campaign reports, append-only APIs, package locks | M/O | Partial | Runtime reports/logs are ignored or absent; campaign/version mechanisms are not fully production-wired; Python/tool versions and release baselines are incomplete. |
| `GP 2.2.4` Review/adjust | `validate.py`, tests, review/curation queues, curator role, ingest checks | M/O | Partial | Independent review, authenticated approval, issue resolution, and closure are not routinely retained; hundreds of open items remain and some validators do not inspect the real queue paths. |

## 4. Documentation repository evidence inventory

All artifacts in this section belong to the current documentation/data-pipeline product unless a future controlled register explicitly identifies an ECU product and process instance. Their relevance column describes potential reuse or documentation-process relevance, not ECU process performance.

### Architecture, sources, and reproducibility

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `_src/ARCHITEKTUR.md` | Five-layer model, invariants, source-of-truth locations, generated-artifact policy | I | `SWE.2`, `SUP.8`, PA 2.2 | No trace to approved software requirements or architecture review/decision record. |
| `_src/WARTUNG.md` | Operational generation/i18n/validation/publication procedures and prerequisites | I | Engineering, release, PA 2.1/2.2 | Procedure text does not prove use, schedule, approval, or retained result. |
| `_src/generate.py` | Deterministic generation and build-report producer | M | `SWE.3`, `SWE.5`, `SWE.6`, `SPL.2` | Report page counts/changed targets have known incompleteness; no requirement trace. |
| Generated language trees | Actual delivered artifacts | O | `SPL.2`, product evidence | Release identity, approval, package completeness, and delivery baseline are weak. |

### Requirements, architecture, and design

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `TODO.md` | Stable task IDs, prerequisites, acceptance criteria, and status assertions | I/S | `MAN.3`, `SUP.10`, partial requirements | Task definitions/criteria are intent (`I`); uncorroborated status/completion assertions are self-report (`S`), not objective execution evidence. The backlog is not an agreed stakeholder/software requirement baseline. |
| `_src/KONVENTIONEN.md` | Product/content conventions | I | `SWE.1`, `SWE.3`, PA 2.2 | No stable requirement IDs, priorities, approval status, or trace. |
| `_src/SPEC_BUILD_PROCESS.md` | Campaign lifecycle, roles, statuses, evidence-first rules | I | Multiple processes | Mixes target model and implemented state; not a per-instance plan. |
| `docs/pipeline/aspice-level1-score-import.md` | Local Feature-0019 campaign-evidence contract | I | Documentation campaign only | Defines project-local controls, not generic Level-1 base practices; any execution is `documentation-execution`, cannot support ECU outcomes, and still requires a valid named-process assessment for capability wording. |

### Verification and quality

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `_src/validate.py` | Structural, link, language, record, namespace, status, and workflow checks; structured report | M | `SWE.5`, `SWE.6`, `SUP.1` | Mostly invariant-based; no requirement baseline/trace. Real `_src/spec/*-queue` discovery and malformed-payload continuation are regression-tested as of 2026-08-15, but client-render checks may still be skipped and release-specific results are not retained. |
| `_src/tests/` and `_src/tools/test_*.py` | Unit/integration-oriented checks and negative fixtures | M | `SWE.4`, `SWE.5` | No controlled verification strategy, selection/coverage rationale, CI result, or release-specific retained execution evidence. |
| `_src/tests/fixtures/spec_extraction/benchmark-draft.json` | 200-record benchmark draft | O/I | Verification test data | Not frozen/approved; `TODO.md` Feature 0007 records unresolved review metadata and definition-shape questions. |
| `docs/pipeline/client-rendered-validation.md` | Browser/client-render validation approach | I | `SWE.6` | Browser verification is not end-user intended-use validation (`VAL.1`). |

### Reviews, curation, and authority

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `docs/pipeline/roles.md` | Human/AI/tool responsibilities and authority boundaries | I | PA 2.1, `SUP.1`, `SUP.9`, `SUP.10` | Generic roles; no named process-instance assignment, competence, independence, or communicated acceptance. |
| `docs/pipeline/workflow-lifecycle.md` | Shared curation lifecycle and transitions | I | `SUP.9`, `SUP.10`, PA 2.2 | Some tools use shortcuts or distinct persistence semantics. |
| `_src/tools/review_flags.py`, `_src/tools/curation_flags.py` | Queue claiming/completion mechanisms | M | `SUP.9`, `SUP.10` | Review completion may delete queue evidence; operational closure is not demonstrated consistently. |
| `_src/spec/*-queue/` and curation report | Real open review/curation items | O | Problem/change/review evidence | Sampled report showed 383 open and no claimed/completed items; existence of a queue does not demonstrate resolution. |
| `_src/tools/review_ingest.py`, `curation_ingest.py` | Authenticity/hash/conflict checks and controlled apply/queue paths | M | `SUP.10`, PA 2.2 | No complete representative accepted/rejected/applied/published evidence set was found. |

### Configuration, versions, campaigns, and evidence

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| Git repository and `.gitignore` | Source configuration control; explicit exclusions | M/O | `SUP.8`, PA 2.2 | `output/`, logs, runner archives, and `run.sh` are ignored; no alternative controlled evidence repository is identified. |
| `_src/tools/campaign_manifest.py` and campaign manifests | Scope/tool/queue snapshots and campaign identity | M/O | `MAN.3`, `SUP.8` | Normal writer integration and robust content-based corpus identity are incomplete; sample manifests lack decisions/reports. |
| `_src/tools/version_store.py` | Append-only requirement-version API | M | `SUP.8` | Documentation says normal scraper writers are not fully wired; sampled materialized entries appear synthetic. |
| `_src/tools/evidence_snippet.py`, `dependency_graph.py`, `supersession_trigger.py` | Version-pinned evidence/dependency/invalidation mechanisms | M | Traceability, change/problem control | Documentation explicitly describes missing operational wiring; little/no production evidence. |
| `package-lock.json` | Node dependency resolution | O/M | `SUP.8` | Python/lxml/Graphviz and runner-installed dependencies are not equivalently pinned; runner may bypass lockfile discipline. |

### Build, reports, and release

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `docs/pipeline/build-report-schema.md` | Canonical report schema and producer counts | I | PA 2.2, `MAN.6`, release evidence | Schema alone does not guarantee complete/correlated reports. |
| `_src/tools/build_report.py` | Combined report aggregation | M | `SWE.5/6`, `SPL.2`, `MAN.6` | Selects latest reports independently and may tolerate absent stages, so a “success” need not represent one complete run. |
| Published `build-reports.html` / page model | One human-readable report | O | Release/measurement evidence | Sample showed missing i18n stage/runner reference; source timestamps may span different runs. |
| `_src/run-loop.sh`, `output/run-current.*` | Script/log pairing and execution trace mechanism | M/O | PA 2.1/2.2, reproducibility | Run archive was sampled empty and output is ignored; evidence is not a controlled release baseline. |
| `_src/publish.sh` | Publication packaging/push mechanism | M | `SPL.2` | Does not itself establish complete generation/validation/approval gate, release notes, support/rollback, or all configured-language completeness. |

### Management, risk, and measurement

| Artifact | Evidence | Class | Relevance | Limitation |
|---|---|---:|---|---|
| `TODO.md`/`DONE.md` | Work definitions, dependencies, status, self-reported completions and references | I/S | `MAN.3`, `SUP.10`, PIM | Definitions are intent; completion/status assertions remain self-report unless separately corroborated by retained objective execution records. Estimates, owners, schedule and actual-vs-plan control are incomplete. |
| Build/extraction/curation counts | Durations, finding counts, fallback/reject/status quantities | O | `MAN.6`, monitoring | Metrics are not derived from approved information needs; no definitions, targets, thresholds, trend review, or decision linkage. |
| Performance entries in `DONE.md` | Before/after runtime claims | S | `PIM.3`, measurement | Useful improvement narrative but not a controlled measurement/approval record. |
| Risk artifacts | None found as a maintained process record | — | `MAN.5` | No strategy, register, owner, exposure, treatment, review, residual risk, or closure evidence. |
| Resource/competency artifacts | Generic prerequisites/roles only | I | PA 2.1, `MAN.3` | No staffing/availability, competence criteria, training, qualification, tool/license capacity, or named allocation. |

## 5. Process evidence summary

The current evidence below is a documentation-product foundation. The decisive ECU gap is objective execution on a concrete ECU baseline; “none” is not a formal `N` rating.

| Process | Reusable/documentation foundation | Decisive ECU evidence gap |
|---|---|---|
| `SYS.1` | Product audience/intent in README/process pages; browser review intake | No ECU stakeholders, elicitation/agreement/change/status records or baseline |
| `SYS.2` | Imported public requirements and schemas | No analyzed ECU system-requirement baseline or stakeholder trace |
| `SYS.3` | Pipeline architecture patterns | No ECU system architecture, allocations, evaluation, rationale or trace |
| `SYS.4` | Pipeline orchestration and integration checks | No controlled ECU element integration or architecture/interface-based measures/results |
| `SYS.5` | Broad pipeline validation patterns | No integrated-ECU verification against system requirements |
| `SWE.1` | Maintenance rules, conventions, TODO acceptance criteria | No ECU software-requirement baseline, allocation, agreement or trace |
| `SWE.2` | `_src/ARCHITEKTUR.md`, process/data-model documentation | No ECU software architecture, requirement allocation, evaluation or approval |
| `SWE.3` | Implemented Python/JavaScript and docstrings | No ECU detailed design, coding/construction, source baseline, review or trace |
| `SWE.4` | Unit tests and negative fixtures | No ECU unit strategy, design/unit trace, controlled run or results |
| `SWE.5` | Pipeline checks and component orchestration | No ECU component/integration sequence, architecture/design trace or results |
| `SWE.6` | Broad `validate.py` checks | No ECU software-requirement-based verification or release-specific results |
| `VAL.1` | Browser/client-render checks | No ECU intended-use scenarios, representative environment, stakeholder trace, results or acceptance |
| `SPL.2` | Generated site and publication script | No identified approved ECU firmware/product package, notes, compatibility, support, delivery or rollback evidence |
| `SUP.1` | Validators, reviews, authority boundaries | No independent ECU QA plan, conformance audits, escalation or closure |
| `SUP.8` | Git, schemas, IDs, version APIs | No ECU configuration-item catalogue, baselines, status, audits, restore or retained evidence |
| `SUP.9` | Review/curation queues and lifecycle | No real ECU problem records with cause, resolution, verification, closure and trends |
| `SUP.10` | Ingest/change mechanisms and TODO | No real ECU change impact/authorization/implementation/verification/closure trace |
| `MAN.3` | Feature scopes and campaign concepts | No approved ECU integrated plan, assignments, resources, schedule, commitments or control history |
| `MAN.5` | Incidental technical risk language | No ECU risk strategy/register, treatments, monitoring, residual decisions or closure |
| `MAN.6` | Counts, durations, reports | No ECU information needs, metric definitions, values, analysis, communication or decisions |

Conditional `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` require a Feature `0020` applicability decision. No current artifact is treated as ECU execution evidence for them.

## 6. ECU evidence-retention requirements going forward

As a local readiness control, every new ASPICE-related artifact should identify:

- `product_id` and `project_id`;
- named process and `process_instance_id`;
- official process outcome or attribute achievement supported;
- artifact ID, controlled location, origin class, and validity/applicability;
- owner, reviewer, approver, authority, and status;
- `baseline_id`, artifact revision, timestamps, and integrity information;
- input/source and lifecycle trace;
- review criteria, findings, contrary evidence, and disposition;
- problem/change and resolution/closure evidence;
- confidentiality, retention, access, archival, and disposal rules; and
- whether the item is real execution evidence or a controlled scenario/fixture.

Feature `0020-02` must make cross-product substitution mechanically visible or invalid. Feature `0025-02` verifies selected-profile execution readiness, and Feature `0025-03` freezes only valid ECU evidence for Level-1 assessment. Feature `0018` may extend the same evidence population with PA 2.1/PA 2.2 evidence, but it cannot import documentation ratings.

This register should eventually be generated from controlled metadata rather than maintained as a manually synchronized narrative.
