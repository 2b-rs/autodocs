# Stakeholder analysis — virtualized automotive ECU software (`0013-01`)

**Item:** Task `0013-01` of Feature `0013`
**Product:** `virtualized-automotive-ecu`
**Project:** `autodocs-ecu-software`
**Increment:** `software-without-kernel`
**Status:** analysis candidate; not a stakeholder-requirements baseline, agreement, or approval
**Confidentiality:** `internal`

This dossier identifies who may supply, constrain, use, agree, assess, or be
affected by the assessed software increment. It preserves what current evidence
does **not** establish. Task `0013-02`, not this Task, owns creation and approval
of the stakeholder-requirements baseline.

## 1. Request and provenance

### 1.1 Requester wording

Task `0013-01` requests:

> Identify stakeholder groups, sources, intended-use scenarios, operating
> environments, needs, constraints, communication channels, and agreement
> authorities for the assessed product.

The Management product-boundary statement is preserved verbatim from
`DEC-0020-001`:

> Wir entwickeln ausschließlich System- und Applikationssoftware für ein
> virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in
> Entwicklung und wird später hinzugefügt.

For orientation only, this means that the assessed unit develops system and
application software for a virtualized automotive ECU, while the kernel is
still in development and will be added later. The German record above remains
the authoritative wording.

### 1.2 Evidence hierarchy

| Source ID | Source and provenance | What it establishes | Authority and limitation |
|---|---|---|---|
| `SRC-0013-01-01` | Current `TODO.md`, Task `0013-01` | Required analysis dimensions | Task contract; does not supply product facts |
| `SRC-0013-01-02` | `docs/pipeline/aspice-cl2-assessment-input.md`, Task `0011-01` REF `a22b8344267adc05d4ff47dca5056fa473a244bb` | Controlled assessed-product identifiers, increment boundary, 14 named process instances, evidence and assessment constraints | Binding prerequisite input for this analysis; contains open Management parameters and no named customer or intended-use actor |
| `SRC-0013-01-03` | `docs/dossiers/dec-0020-01-ecu-scope.md`, `DEC-0020-001` | Management’s product/supplied-product boundary and permitted claim wording | Authoritative for that bounded decision; explicitly rejects inventing customer, release train, kernel inclusion, and complete-ECU ownership |
| `SRC-0013-01-04` | `docs/dossiers/req-0020-03-responsibility-authority-matrix.md`, REF `ab2d1d81ddf56e8cf1b7219715bfc0ecf02da6b4` | Current implementation record of internal software responsibility and open lifecycle parties | Supporting current evidence; implementation-complete but carries no `Acceptance: ✓` |
| `SRC-0013-01-05` | `docs/dossiers/req-0020-04-applicability-matrix.md`, REF `51331b71b6ec48fdcc0c517bfd8541009480437f` | Current selected 14-process nucleus; SYS/VAL/HWE exclusions | Supporting current evidence; implementation-complete but carries no `Acceptance: ✓` |
| `SRC-0013-01-06` | `docs/dossiers/req-0020-06-cybersecurity-safety-applicability.md`, REF `c11c2a0b94c6d2198086a855f1b295074659db92` | No owned cybersecurity or functional-safety lifecycle in this increment; no ASIL or compliance claim | Supporting current evidence; does not mean security/safety-related product constraints are absent |

Source status terms in this dossier are:

- **confirmed** — stated by `SRC-0013-01-02` or its authoritative Management
  source;
- **derived** — the smallest implication of two or more cited current sources,
  without adding a product fact;
- **open** — the stakeholder class or information category is relevant, but no
  current source names the party or supplies the content;
- **excluded this increment** — outside the current supplied-product or owned
  lifecycle boundary; this is not evidence that no external interface exists.

## 2. Atomic analysis requirements

### `REQ-0013-01-01` — Preserve the assessed-product boundary

- **Description:** The stakeholder-analysis record SHALL identify the assessed
  product only as `virtualized-automotive-ecu`, project
  `autodocs-ecu-software`, increment `software-without-kernel`, and SHALL keep
  kernel, OS, hardware, manufacturing, complete-ECU lifecycle, and complete-ECU
  release outside the current owned boundary.
- **Acceptance intent:** The identifiers and exclusions match
  `SRC-0013-01-02` and `SRC-0013-01-03`; no broader capability is stated.
- **Assumptions / exclusions:** Assumes those sources remain current; excludes
  any later increment or unstated complete-product responsibility.

### `REQ-0013-01-02` — Identify groups without inventing identities

- **Description:** The record SHALL give every relevant stakeholder class a
  stable group ID and status, and SHALL use `open` when the evidence does not
  name a person or organization.
- **Acceptance intent:** Every group in §3 has an ID, evidence, interest, and
  agreement role; no named customer, OEM, assessor, supplier, or kernel owner is
  invented.
- **Assumptions / exclusions:** A stakeholder class may be recorded before its
  representative is known; class identification is not assignment or agreement.

### `REQ-0013-01-03` — Bind each claimed fact to a source

- **Description:** The record SHALL distinguish authoritative Management
  decisions, the controlled `0011-01` input, supporting implementation records,
  and missing stakeholder-originated sources.
- **Acceptance intent:** Each confirmed or derived entry in §§3–8 cites at least
  one `SRC-*`; missing sources are listed explicitly in §4.
- **Assumptions / exclusions:** Supporting implementation records inform current
  consistency but do not gain Acceptance or Management authority here.

### `REQ-0013-01-04` — Separate product use from process and assessment use

- **Description:** The record SHALL NOT represent software development,
  verification, release, or assessment activity as an end-user intended-use
  scenario for the ECU product.
- **Acceptance intent:** §5 labels lifecycle/assessment scenarios separately and
  leaves vehicle mission, users, and complete-product validation open.
- **Assumptions / exclusions:** Product end use is unknown; no `VAL.1` ownership
  or representative-user coverage is claimed.

### `REQ-0013-01-05` — Bound operating-environment claims

- **Description:** The record SHALL state the known virtualized-ECU and
  above-kernel boundary and SHALL leave unstated platform, resource, interface,
  vehicle, geographic, regulatory, and field conditions open.
- **Acceptance intent:** §6 contains no hypervisor, CPU, bus, timing, memory,
  vehicle, jurisdiction, or deployment assertion without a source.
- **Assumptions / exclusions:** “Virtualized automotive ECU” is a context label,
  not authorization to select platform architecture or environmental limits.

### `REQ-0013-01-06` — Classify needs and constraints

- **Description:** Each stakeholder need or constraint SHALL be marked
  `confirmed`, `derived`, `open`, or `excluded this increment`, with its source
  and affected group.
- **Acceptance intent:** §7 has no unlabeled product requirement and makes no
  safety, cybersecurity, or capability claim.
- **Assumptions / exclusions:** Candidate needs remain analysis inputs; approval,
  priority, feasibility commitment, and baseline status belong downstream.

### `REQ-0013-01-07` — Identify recordable communication channels

- **Description:** The analysis SHALL identify the communication record needed
  for each interface while leaving tool, cadence, address, and named participant
  open unless current evidence fixes them.
- **Acceptance intent:** §8 states purpose, participants, retained evidence, and
  current readiness for every channel class.
- **Assumptions / exclusions:** The need for a recordable interaction does not
  select a repository tool, protocol, meeting, cadence, or notification address.

### `REQ-0013-01-08` — Fail closed on agreement authority

- **Description:** A missing agreement authority SHALL be recorded as `open` and
  SHALL NOT be inferred from authorship, Requirements Engineer role, internal
  responsibility, mailbox traffic, or repository access.
- **Acceptance intent:** §9 names only authorities established by the sources and
  blocks agreement where the deciding role is not assigned.
- **Assumptions / exclusions:** Internal responsibility may establish a function
  without naming its authorized holder; no agent role is promoted by this record.

### `REQ-0013-01-09` — Route genuine product decisions

- **Description:** Unresolved choices that materially alter product use,
  environment, interface, stakeholder baseline, or authority SHALL be retained
  as `PD-0013-01-*` items for Project Lead routing to the named deciding role.
- **Acceptance intent:** §10 states the decision, required decider, evidence
  needed, and downstream effect for each item.
- **Assumptions / exclusions:** The Project Lead routes decisions but does not
  decide customer, Management, assessor, or external-authority questions.

### `REQ-0013-01-10` — Provide a non-approving handoff

- **Description:** This record SHALL give `0013-02` a bounded elicitation input
  without approving stakeholder needs or choosing software architecture.
- **Acceptance intent:** §11 lists entry conditions and refuse-at-use conditions;
  this dossier contains no `Acceptance: ✓` and no approved product requirement.
- **Assumptions / exclusions:** `0013-02` may use this work as input; it must not
  treat completion of `0013-01` as stakeholder agreement or architecture choice.

## 3. Stakeholder-group register

| Group ID | Stakeholder group | Status | Evidence | Interest / contribution | Agreement role at this point |
|---|---|---|---|---|---|
| `STK-0013-01-MGT` | Management sponsor / product-boundary authority | confirmed role; identity for the next decision not recorded here | `SRC-0013-01-02`, `03` | Assessment purpose, bounded product claim, scope changes, target date, sponsor signature | May decide product/supplied-product boundary and later lifecycle inclusion; existing decision is limited to `DEC-0020-001` |
| `STK-0013-01-CUS` | Customer or requesting organization | open | `SRC-0013-01-03`, `04` explicitly do not name one | Business need, acceptance context, priority, contractual and vehicle-level constraints | Open; no customer agreement can be claimed |
| `STK-0013-01-IUA` | Intended-use actors, operators, maintainers, or representative users | open | `SRC-0013-01-04`, `05` leave `VAL.1` external/not selected | Operational missions, normal/abnormal use, usability, service and field expectations | Open; no representative or acceptance authority is named |
| `STK-0013-01-SYS` | Complete-ECU system / allocation authority | external to current owned scope; unnamed | `SRC-0013-01-03`–`05` | Controlled allocated software requirements, system context, interface and acceptance constraints | Open; assessed unit does not own complete-system agreement this increment |
| `STK-0013-01-KRN` | Kernel/OS provider and kernel-interface authority | excluded from supplied product this increment; party open | `SRC-0013-01-02`–`04` | Kernel-interface contract, platform services, versions, resource and integration constraints | Open; later kernel inclusion requires new Management decision |
| `STK-0013-01-SWE` | Assessed software organization: performers and process owners for software above the kernel | confirmed internal group; named roles open | `SRC-0013-01-02`, `04`, `05` | Feasible, unambiguous allocated needs; controlled requirements, implementation, integration, verification, change and evidence | Internal responsibility is established, but no named stakeholder-baseline approver is established |
| `STK-0013-01-QVR` | Software reviewers, verifiers, and quality representatives | derived internal functions; identities and independence open | `SRC-0013-01-02`, `04`, `05` | Verifiable criteria, review independence where required, defects and traceable closure | May review owned software work when assigned; does not thereby accept stakeholder needs |
| `STK-0013-01-REL` | Owned-software package release/acceptance authority | confirmed internal function; identity open | `SRC-0013-01-04`, `05` | Exact software baseline, release criteria, limitations, trace and retained decision | Authority for owned package is internal but is not assigned to a named role/person here; no complete-ECU release authority |
| `STK-0013-01-OPS` | Operations, service, support, and field-feedback parties | open | `SRC-0013-01-04` | Deployment, diagnostics, update, incident, maintenance and field constraints | Open; no operational party or feedback authority is named |
| `STK-0013-01-SUP` | Suppliers and external platform/tool/calibration providers | open | `SRC-0013-01-04`, `05` | Controlled external inputs, versions, support limits, acceptance and change notification | Open; no shared process or supplier acceptance gate exists |
| `STK-0013-01-CSF` | Cybersecurity / functional-safety constraint authorities | no owned CS/FS lifecycle this increment; external constraint source remains open | `SRC-0013-01-02`, `06` | Any applicable product constraints and allocation; prevention of unsupported 21434/26262 claims | Later owned-lifecycle inclusion requires new Management decision; no current ASIL, TARA/HARA owner, or compliance approver |
| `STK-0013-01-ASM` | Independent competent assessor / assessment team | confirmed required role; not named | `SRC-0013-01-02` | Competent, independent access to controlled evidence and report rationale | Assessment conclusions require the named competent assessor; Management waiver does not fill the missing name or independence evidence |

The register identifies stakeholder **classes**, not an agreed RACI. Named
assignments, deputies, competence, availability, and recurring interface cadence
belong to later role and managed-process work (`0011-04`, `0012-04`, `0012-05`).

### 3.1 Affected lifecycle interfaces

For compactness in interface and channel tables, suffixes such as `CUS`, `SWE`
and `ASM` refer to the corresponding full `STK-0013-01-*` IDs above.

| Interface ID | From → to | Information / decision crossing the interface | Present boundary |
|---|---|---|---|
| `IF-0013-01-CUS` | `CUS` / `IUA` → `SWE` / stakeholder-baseline authority | Business need, intended use, priority, acceptance outcomes, changes | Parties, source and accepting authority open |
| `IF-0013-01-SYS` | `SYS` → `SWE` | Allocated system requirements, external behavior, vehicle/system constraints and acceptance criteria | Complete-system work is external; controlled allocation missing |
| `IF-0013-01-KRN` | `KRN` ↔ `SWE` | Kernel/platform services, compatibility, resources, errors, version and integration constraints | Kernel excluded this increment; interface authority and baseline missing |
| `IF-0013-01-VR` | `SWE` ↔ `QVR` | Requirement quality, feasibility, verification criteria, findings and closure | Internal functions supported; named roles and agreement remit open |
| `IF-0013-01-REL` | `SWE` / `QVR` → `REL` → receiving authority | Exact owned-software package, trace, verification results, limitations and release decision | Owned-package release internal; receiver and named authority open |
| `IF-0013-01-OPS` | `REL` / `SWE` ↔ `OPS` / `IUA` | Deployment/service constraints and field feedback | Parties and operational context open; no data collection implied |
| `IF-0013-01-ASM` | `MGT` / assessed groups ↔ `ASM` | Assessment scope, objective evidence, interviews, findings, responses and signed report | Assessment structure known; assessor, date and sample open |
| `IF-0013-01-CSF` | external `CSF` authority → `SWE` / `MGT` | Any allocated product constraint and decision whether an owned lifecycle is later included | No owned CS/FS lifecycle now; external constraint source open |

## 4. Stakeholder-originated source register

Current repository sources establish the assessment and supplied-product
boundary, but they do not contain an approved customer or system stakeholder
baseline. These are the source classes `0013-02` must acquire or explicitly
disposition.

| Source-candidate ID | Expected source owner | Required content | Current state | Refuse-at-use condition |
|---|---|---|---|---|
| `SOU-0013-01-BIZ` | `STK-0013-01-CUS` or authorized Management product authority | Business objective, requested capability, rationale, priority, contractual limits | missing | Do not derive product functions solely from TODO prose or assessment scope |
| `SOU-0013-01-USE` | `STK-0013-01-IUA` and customer/product authority | Actors, vehicle mission, normal/abnormal scenarios, acceptance outcomes, usage frequency and criticality | missing | Do not call development, test, or assessment activity “product intended use” |
| `SOU-0013-01-SYS` | `STK-0013-01-SYS` | Controlled allocated system requirements, system boundary, vehicle interfaces and system acceptance criteria | missing | Do not claim internal `SYS.1`–`SYS.5` or complete-system authority |
| `SOU-0013-01-KRN` | `STK-0013-01-KRN` | Kernel/OS interface contract, supported services, versions, resources, failure and compatibility constraints | missing | Do not infer interface behavior from “kernel later” |
| `SOU-0013-01-ENV` | Customer/system/platform authorities | Target virtualized and deployment environments, variants, hardware dependencies, networks, I/O, timing, memory, diagnostics, geography and regulations | missing | Do not select or claim a target environment beyond the current boundary |
| `SOU-0013-01-OPS` | `STK-0013-01-OPS` | Deployment, update, service, support, incident, telemetry/privacy and field-feedback expectations | missing | Do not invent operational responsibility or data collection |
| `SOU-0013-01-CSF` | Authorized customer/system CS/FS authority | Applicable security/safety constraints and allocation, if any | missing; owned lifecycle excluded | Do not equate PAM evidence with ISO/SAE 21434 or ISO 26262 proof |
| `SOU-0013-01-ORG` | Authorized internal software/process owners | Feasibility, resource, quality, release, evidence and support constraints for the owned package | partially represented by `SRC-0013-01-02`, `04`, `05`; named owners absent | Do not treat a generic internal token as a named commitment |

Every acquired source needs a stable source identity, revision/baseline,
originator, authority, date, confidentiality, applicability, and change history.
That requirement is an elicitation input to `0013-02`; this Task does not choose
the storage mechanism.

## 5. Intended-use and lifecycle-scenario analysis

### 5.1 What current evidence supports

| Scenario ID | Scenario | Classification | Evidence and boundary |
|---|---|---|---|
| `SCN-0013-01-LC1` | Develop and maintain system and application software above the kernel interface for the `software-without-kernel` increment | confirmed lifecycle scenario, not end-user intended use | `SRC-0013-01-02`, `03`; says what the assessed unit supplies, not what a driver/operator does |
| `SCN-0013-01-LC2` | Integrate, verify, and release the assessed unit’s owned software package | derived lifecycle scenario, not complete-ECU use | `SRC-0013-01-02`, `04`, `05`; excludes kernel/hardware/complete-ECU integration and release |
| `SCN-0013-01-AS1` | Assess the 14 named software-delivery process instances using controlled evidence | confirmed assessment-use scenario, not product use | `SRC-0013-01-02`; no rating or Capability Level result is asserted |

### 5.2 Product intended use remains open

The phrase “virtualized automotive ECU” establishes a product context, not a
complete intended-use definition. No current source establishes:

- the vehicle or ECU function served by the software;
- the customer, operator, maintainer, diagnostic actor, or affected person;
- normal, abnormal, degraded, startup, shutdown, update, recovery, or misuse
  scenarios;
- operational inputs, outputs, decisions, side effects, hazards, assets, or
  acceptance outcomes;
- whether intended-use validation is performed by a customer, system owner,
  another external party, or a later internal increment.

Until `SOU-0013-01-USE` and its agreement authority exist, these are elicitation
gaps, not implied requirements. `VAL.1` remains outside the selected profile.

## 6. Operating-environment analysis

| Environment dimension | Current statement | Status / source | Required next evidence |
|---|---|---|---|
| Product context | Virtualized automotive ECU | confirmed; `SRC-0013-01-02`, `03` | Exact virtualization and deployment baseline |
| Supplied software layer | System and application software above the kernel interface | confirmed; `SRC-0013-01-02`, `03` | Controlled allocation and kernel-interface baseline |
| Kernel / OS | Kernel still in development and added later; kernel and OS outside this increment | confirmed exclusion; `SRC-0013-01-02`, `03` | Owner, version, interface, compatibility and inclusion decision |
| Hardware / manufacturing | Outside current owned increment | confirmed exclusion; `SRC-0013-01-02`, `03`, `05` | External hardware constraints if the software depends on them |
| Virtualization platform | Not identified | open | Hypervisor/runtime identity, configuration, services and failure behavior |
| Compute and resources | CPU architecture, memory/storage, timing, scheduling and performance limits not identified | open | Quantified platform/resource constraints |
| Vehicle / external interfaces | Networks, buses, sensors, actuators, diagnostics, data formats and external systems not identified | open | Controlled system/interface specifications |
| Variants / configurations | No target variant set beyond the increment ID | open | Supported variants, compatibility and selection rationale |
| Development / verification environment | No toolchain, simulator, test target, data, or equivalence criteria identified by this input | open | Controlled environment and representativeness evidence |
| Operational / field environment | Vehicle class, environmental conditions, service/deployment model and jurisdiction not identified | open | Customer/system/operations source baseline |
| Security / safety context | No owned 21434/26262 lifecycle or ASIL this increment | confirmed lifecycle exclusion; `SRC-0013-01-06` | Any externally allocated product constraints; later Management decision for owned inclusion |

## 7. Needs and constraints

These are analyzed needs and constraint candidates, not approved stakeholder
requirements.

| ID | Need or constraint | Groups | Status | Source / rationale |
|---|---|---|---|---|
| `NEED-0013-01-01` | Keep all claims, requirements and evidence within the exact software-above-kernel supplied-product boundary | `MGT`, `SWE`, `REL`, `ASM` | confirmed | `SRC-0013-01-02`, `03` |
| `NEED-0013-01-02` | Obtain an authoritative business need and product intended-use statement before approving product behavior | `CUS`, `IUA`, `MGT`, `SWE` | open | No current customer or intended-use source exists |
| `NEED-0013-01-03` | Receive controlled allocated requirements and kernel/platform interface constraints before deriving software requirements | `SYS`, `KRN`, `SWE`, `QVR` | open | Above-kernel responsibility implies an interface, but current sources do not define it |
| `NEED-0013-01-04` | Make owned-software requirements verifiable and package acceptance traceable to the agreed stakeholder source and exact baseline | `SWE`, `QVR`, `REL`, `CUS` | derived | Internal SWE.1–SWE.6 and SPL.2 scope in `SRC-0013-01-02`, `04`, `05`; acceptance authority remains open |
| `NEED-0013-01-05` | Preserve source, revision, origin, validity, confidentiality, contrary evidence, and change history | all groups; especially `ASM` | confirmed for assessment evidence; derived for stakeholder sources | `SRC-0013-01-02`; prevents retrospective or cross-product substitution |
| `NEED-0013-01-06` | Communicate proposed needs, conflicts, decisions, changes, limitations, and unresolved gaps to every affected authority and retain the response | all interface groups | derived; channel details open | Agreement cannot be demonstrated from authorship or silence |
| `NEED-0013-01-07` | Provide a competent, independent assessor with objective evidence; interviews may contextualize but not replace artifacts | `ASM`, `MGT`, `SWE`, `QVR` | confirmed | `SRC-0013-01-02` |
| `NEED-0013-01-08` | Capture operations, service, update, incident, privacy, and field-feedback needs if the product boundary later includes them | `OPS`, `CUS`, `IUA`, `SWE` | open | Relevant stakeholder class is unnamed; no behavior is inferred |
| `CON-0013-01-01` | Kernel, OS, hardware, manufacturing, complete-ECU system lifecycle, complete-ECU release, and vehicle-level validation are not claimed this increment | all | confirmed constraint | `SRC-0013-01-02`–`05` |
| `CON-0013-01-02` | The selected assessment profile is the 14 named internal process instances; no cross-process or cross-baseline aggregation | `ASM`, `SWE`, `MGT` | confirmed constraint | `SRC-0013-01-02`, `05` |
| `CON-0013-01-03` | `documentation-execution`, controlled scenarios, foreign products, and interviews cannot substitute for authentic ECU execution evidence | `ASM`, `SWE`, `QVR` | confirmed constraint | `SRC-0013-01-02` |
| `CON-0013-01-04` | No owned cybersecurity or functional-safety lifecycle, ASIL, 21434, or 26262 compliance claim is permitted this increment | `CSF`, `MGT`, `SWE`, `REL`, `ASM` | confirmed constraint | `SRC-0013-01-02`, `06` |
| `CON-0013-01-05` | Assessment material is `internal`; public distribution is not authorized | `MGT`, `ASM`, all recipients | confirmed for current input | `SRC-0013-01-02`; a later distribution decision may narrow or widen only with authority |
| `CON-0013-01-06` | Lead/co-assessor names, target date, customer, product actor, platform and stakeholder-baseline approver remain unset | all | confirmed gap | Source placeholders and explicit `not-decided` records |

## 8. Communication-channel register

“Channel” here means the controlled interaction and retained evidence needed for
agreement. It does not prescribe a tool or architecture.

| Channel ID | Purpose and participants | Required retained record | Current readiness |
|---|---|---|---|
| `CH-0013-01-SCOPE` | Product/scope decision between `MGT` and affected product/interface groups | Verbatim request, deciding identity/role, exact baseline, decision, rationale, affected interfaces and supersession | Available for existing `DEC-0020-001`; channel for future decisions is not assigned |
| `CH-0013-01-ELICIT` | Elicit needs and constraints from `CUS`, `IUA`, `SYS`, `KRN`, `OPS`, `SUP`, `CSF` | Source identity/revision, originator and authority, context, need, rationale, priority, constraints, open questions and date | Required; parties/medium/cadence open |
| `CH-0013-01-AGREE` | Review and agree candidate stakeholder requirements among source owner, affected internal groups, and baseline approver | Exact candidate baseline, reviewers, authority, comments/conflicts, dispositions, decision, date and change history | Required for `0013-02`; approver and medium open |
| `CH-0013-01-IMPACT` | Communicate requirement or source change to every affected interface | Changed source/baseline, impact analysis, affected traces/products, owner, due date, decision and closure | Required; operating mechanism belongs to later change/agreement work |
| `CH-0013-01-SWREL` | Communicate owned-software baseline and limitations among `SWE`, `QVR`, `REL` and receiving authority | Exact package/baseline, requirements and verification trace, known limitations, release/acceptance decision | Internal function identified; named sender/recipient/authority open |
| `CH-0013-01-ASM` | Assessment evidence request, interview, findings and report communication among `ASM`, `MGT` and assessed performers | Request/sample, evidence references and origin, interview role/date, findings, responses, report revision and signatures | Report structure exists; competent assessor, date and sample open; interview is not evidence substitution |
| `CH-0013-01-FEED` | Operational/service/problem feedback from `OPS`, `CUS`, `IUA` to product/change authorities | Context, affected baseline, observed/expected outcome, severity, privacy classification, disposition and closure | Open; parties, route, cadence and retention not decided |

Silence, mailbox delivery, repository authorship, or attendance is not agreement.
Task `0012-05` later owns the operating interface/communication matrix with
responsibilities, cadence, response/escalation expectations, and retained
communication evidence.

## 9. Agreement-authority matrix

| Agreement object | Required authority | Current state | Effect while open |
|---|---|---|---|
| Current supplied-product boundary and permitted claim wording | Management | decided only for `DEC-0020-001` | Exact decision may be used; no broader inference |
| Later kernel, complete-system, CS/FS, or lifecycle inclusion | Management through a new bounded decision | open | Remains outside current owned scope |
| Customer/business need and product intended use | Authorized customer/product representative plus the organization’s designated product approver | identities and remit open | No product intended-use agreement or priority claim |
| Allocated system requirements and vehicle/system interfaces | Authorized system/allocation authority | open; complete-system owner not named | No system allocation may be represented as agreed |
| Kernel/platform interface baseline | Authorized kernel/platform owner and receiving software authority | open | No compatibility or interface agreement may be claimed |
| Stakeholder-requirements baseline (`0013-02`) | Designated stakeholder-baseline approver, with affected source authorities participating | not assigned by current evidence | `0013-02` may prepare a candidate but must fail closed before approval |
| Owned-software package | Internal software-package acceptance/release authority | internal function established; role/person and exact remit open | Internal work may be prepared; no named acceptance decision is inferred |
| Assessment input/report and capability conclusion | Named competent independent assessor; Management sponsor for the report signature/disposition | assessor and target date open | Worksheets remain scaffolding; no rating/capability conclusion |
| Public or external report distribution | Authorized Management/confidentiality owner and any affected source owners | open; current classification `internal` | Internal handling only |

## 10. Open product decisions for Project Lead routing

| Decision ID | Genuine remaining choice | Deciding role(s) needed | Minimum evidence before decision | Affected downstream work |
|---|---|---|---|---|
| `PD-0013-01-01` | Name the customer/requesting organization, authorized representative, and product-approval remit | Management and authorized customer/product authority | Contract/request provenance and authority proof | `0013-02`, `0013-03`, validation and release interfaces |
| `PD-0013-01-02` | Define the product’s intended-use actors, vehicle mission, normal/abnormal scenarios, acceptance outcomes and out-of-use cases | Authorized customer/product authority with affected user/operations representatives | `SOU-0013-01-BIZ`, `SOU-0013-01-USE` | Stakeholder baseline, software requirements, verification/validation scope |
| `PD-0013-01-03` | Establish target operating environments and variants, including virtualization, kernel interface, resources, vehicle interfaces and external dependencies | Product/system allocation authority, kernel/platform authority, receiving software authority | Controlled environment/interface baselines | Feasibility, software requirements, architecture, tests and release compatibility |
| `PD-0013-01-04` | Assign stakeholder-requirements baseline approval and change/supersession authority | Management / organizational authority | Role remit, independence/conflict rules, escalation and retention expectations | `0013-02`, `0013-08`, all downstream traces |
| `PD-0013-01-05` | Assign named internal product/process/review/release roles and external interface owners | Organizational Management and each external source authority | Competence, availability, deputies and bounded authority | `0011-04`, `0012-04`, `0012-05`, `0013-02` |
| `PD-0013-01-06` | Choose operating communication media, cadence, response/escalation times and record retention for each channel | Assigned interface and process authorities | Stakeholder availability, confidentiality, tool and retention constraints | `0012-05`, `0013-08`, assessment readiness |
| `PD-0013-01-07` | Name the competent independent assessor, target date, sample and report-distribution authority | Management sponsor and competent assessor | Competence/independence evidence and assessment plan | Assessment execution and any capability claim |
| `PD-0013-01-08` | Name operations, supplier, calibration, CS/FS-constraint and field-feedback authorities where applicable | Management plus relevant external authorities | Actual responsibility and controlled interface evidence | Product constraints, support, change, risk and later lifecycle inclusion |

The Project Lead may route and record these choices but does not acquire the
deciding authority merely by routing them.

## 11. Handoff to `0013-02`

`0013-02` may use this dossier as an elicitation and completeness checklist. A
candidate stakeholder-requirements baseline should:

1. preserve every `SRC-*` and newly acquired `SOU-*` source with stable identity
   and authority;
2. keep each open stakeholder/source/environment field open until evidence is
   obtained or an authorized disposition is recorded;
3. assign each candidate requirement a stable ID, source, rationale, priority,
   binary acceptance intent, validation method, status and change history;
4. trace every candidate to stakeholder group, scenario, environment, need and
   constraint entries in this dossier;
5. reject approval when the source authority or stakeholder-baseline approver
   is absent, ambiguous, or inferred only from authorship or communication;
6. preserve the distinction between end-user intended use, internal software
   lifecycle activity, and assessment activity; and
7. remain within `software-without-kernel` unless a new authoritative Management
   decision changes the supplied-product boundary.

## 12. Assumptions and exclusions

**Assumptions**

- `DEC-0020-001` and the `0011-01` assessment input remain current.
- Supporting `0020-03`, `0020-04`, and `0020-06` implementation records are used
  only for current consistency checking; their lack of `Acceptance: ✓` is not
  concealed or converted into acceptance here.
- Stakeholder classes may be identified before a named representative exists;
  agreement may not.

**Exclusions**

- Approving or baselining stakeholder requirements (`0013-02`).
- Deriving or approving software requirements (`0013-03`).
- Selecting architecture, platform, hypervisor, kernel, protocols, tools, data
  model, or communication implementation.
- Claiming complete-system responsibility, intended-use validation, kernel,
  hardware, manufacturing, cybersecurity/safety lifecycle, ASIL, assessment
  rating, Capability Level, public release, or external agreement.
- `Acceptance: ✓`, integration/checkpoint crossing, `main` advancement, Feature
  closure, or external communication/effects.
