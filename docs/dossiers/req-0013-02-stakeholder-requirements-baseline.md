# Stakeholder-requirements baseline candidate (`0013-02`)

## 1. Baseline identity and approval state

| Field | Value |
|---|---|
| Baseline ID | `SRB-0013-02-virtualized-automotive-ecu-software-without-kernel` |
| Candidate version | `0.1.0-candidate` |
| Product | `virtualized-automotive-ecu` |
| Project | `autodocs-ecu-software` |
| Increment | `software-without-kernel` |
| Source snapshot | exact prerequisite branch tip `0013-01@ec4d20cd1875a1b6bcdfd32f6738da0c12c8b072` |
| Baseline status | `candidate-unapproved` |
| Operative / agreed | `no` |
| Approval authority | `not-assigned`; open decision `PD-0013-01-04` |
| Customer / intended-use authority | `not-assigned`; open decisions `PD-0013-01-01`, `02` |
| Classification | `internal` |
| Change record | `CHG-0013-02-001` |

This is a controlled, review-ready **baseline candidate**. It is not an
approved stakeholder baseline and supplies no customer agreement, product
functional behavior, architecture, release authorization, assessment rating,
or `Acceptance: ✓`. Neither authorship, Task completion, mailbox delivery,
Project Lead routing, nor repository access can change that status.

The current Task contract asks for a versioned baseline while its awarded
execution contract prohibits invented approval. This candidate satisfies the
bounded preparation that is possible now and records the exact missing approval
boundary. It does not add or alter any `TODO.md` prerequisite or downstream
start gate; every consumer must preserve the `candidate-unapproved` state when
using it as input.

## 2. Request and source provenance

Task `0013-02` requests:

> Create and approve a versioned stakeholder-requirements baseline with stable
> IDs, source, rationale, priority, acceptance criteria, status, change history,
> and validation method.

The awarded execution constraint further requires explicit disposition of
`PD-0013-01-01` through `PD-0013-01-08` and prohibits inventing approval.

| Source ID | Repository source | Provenance / authority | Use in this candidate |
|---|---|---|---|
| `SRC-0013-02-01` | `docs/dossiers/req-0013-01-stakeholder-analysis.md` at `0013-01@ec4d20cd1875a1b6bcdfd32f6738da0c12c8b072` | Exact terminal prerequisite analysis; implementation record, not approval | Stakeholder groups, source gaps, scenarios, environments, needs, constraints, channels, authorities, and `PD-*` items |
| `SRC-0013-02-02` | `docs/pipeline/aspice-cl2-assessment-input.md`, Task `0011-01` REF `a22b8344267adc05d4ff47dca5056fa473a244bb` | Controlled assessment input | Product/project/increment IDs, 14 process instances, confidentiality, evidence and assessor constraints |
| `SRC-0013-02-03` | `docs/dossiers/dec-0020-01-ecu-scope.md`, `DEC-0020-001` | Management decision for the bounded supplied-product claim | Software-above-kernel boundary; kernel later; no complete-system/hardware/manufacturing claim |
| `SRC-0013-02-04` | `docs/dossiers/req-0020-03-responsibility-authority-matrix.md`, REF `ab2d1d81ddf56e8cf1b7219715bfc0ecf02da6b4` | Supporting implementation record; no `Acceptance: ✓` | Internal owned-software functions and explicitly unnamed lifecycle parties |
| `SRC-0013-02-05` | `docs/dossiers/req-0020-04-applicability-matrix.md`, REF `51331b71b6ec48fdcc0c517bfd8541009480437f` | Supporting implementation record; no `Acceptance: ✓` | Selected 14-process nucleus and current SYS/VAL/HWE exclusions |
| `SRC-0013-02-06` | `docs/dossiers/req-0020-06-cybersecurity-safety-applicability.md`, REF `c11c2a0b94c6d2198086a855f1b295074659db92` | Supporting implementation record; no `Acceptance: ✓` | No owned CS/FS lifecycle, ASIL, or compliance claim this increment |
| `SRC-0013-02-07` | Current Task `0013-02` wording and atomic award `1787972152778-9b8f67b6` | Task contract and coordination record; mailbox is not product authority | Required work-product fields and non-approval boundary |

The missing stakeholder-originated source classes retain the stable IDs from
`SRC-0013-02-01`: `SOU-0013-01-BIZ`, `USE`, `SYS`, `KRN`, `ENV`, `OPS`, `CSF`,
and `ORG`. A missing source is never replaced by a repository author’s guess.

## 3. Status, priority, and validation vocabulary

### 3.1 Requirement status

| Status | Meaning |
|---|---|
| `candidate-confirmed` | Requirement content is directly supported by an authoritative current source, but this baseline revision is still unapproved |
| `candidate-derived` | Smallest traceable implication of current sources; requires review and approval before becoming operative |
| `blocked-source` | Required stakeholder content or authority is absent; the entry records a completeness condition, not product behavior that may be implemented |
| `conditional-open` | Applies only if a later authorized scope/responsibility decision activates the interface |
| `approved` | Reserved for a future exact revision with an append-only approval record satisfying §7; not used in this candidate |
| `rejected` / `superseded` | Reserved for an append-only disposition retaining the prior text and rationale; not used in this initial candidate |

### 3.2 Priority

| Priority | Meaning |
|---|---|
| `P0-must` | Boundary, authority, safety-of-claim, source, or approval condition; omission makes the candidate unusable as an agreed baseline |
| `P1-high` | Required for credible downstream derivation or operation once the applicable interface is assigned |
| `P2-medium` | Important completeness item whose applicability remains conditional |

### 3.3 Validation methods

- **Source comparison:** compare the candidate statement with the exact cited
  source revision.
- **Trace audit:** resolve every requirement-to-source and requirement-to-
  stakeholder/interface reference without an orphan.
- **Authority-record inspection:** verify deciding identity, role, remit, exact
  baseline version, disposition, date, and retained record.
- **Document inspection:** verify an exact required field/value is present and no
  prohibited claim occurs.
- **Scenario review:** authorized stakeholder representatives review normal,
  abnormal, out-of-use, and acceptance outcomes against their source.
- **Environment review:** authorized system/platform/software representatives
  review exact variants, interfaces, resources, and compatibility constraints.

## 4. Stakeholder-requirement records

Each record is atomic at this level. “The baseline SHALL” means this controlled
stakeholder-requirements work product, not an architectural implementation.

### `REQ-0013-02-01` — Preserve the supplied-product boundary

- **Statement:** The baseline SHALL identify the product as
  `virtualized-automotive-ecu`, project `autodocs-ecu-software`, increment
  `software-without-kernel`, and SHALL limit the supplied product to system and
  application software above the kernel interface.
- **Source:** `SRC-0013-02-02`, `SRC-0013-02-03`;
  `NEED-0013-01-01`, `CON-0013-01-01`.
- **Rationale:** Management authorized this exact bounded claim; widening it
  would misstate the assessed product.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only if all three identifiers and the
  software-above-kernel boundary are present verbatim in meaning and no kernel,
  hardware, manufacturing, or complete-ECU ownership is asserted.
- **Status:** `candidate-confirmed`.
- **Validation method:** source comparison and prohibited-claim document scan.
- **Affected stakeholders/interfaces:** `STK-0013-01-MGT`, `SWE`, `KRN`, `REL`,
  `ASM`; `IF-0013-01-KRN`, `REL`, `ASM`.
- **Assumptions / exclusions:** Assumes `DEC-0020-001` remains current; excludes
  later increments and any unstated system, hardware, or vehicle responsibility.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-02` — Control every stakeholder source

- **Statement:** Every requirement eligible for approval SHALL identify its
  stable source ID, exact revision/baseline, originator, source authority,
  recorded date, confidentiality, applicability, and change-history reference.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-02`;
  `NEED-0013-01-05`, `SOU-0013-01-ORG`.
- **Rationale:** Traceable source identity prevents anonymous, stale,
  cross-product, or retrospectively fabricated requirements.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only if every non-rejected requirement resolves
  to a controlled source with all nine named fields; any missing or ambiguous
  authority fails approval eligibility.
- **Status:** `candidate-derived`.
- **Validation method:** trace audit plus authority-record inspection.
- **Affected stakeholders/interfaces:** all `STK-0013-01-*` groups and all
  `IF-0013-01-*` interfaces.
- **Assumptions / exclusions:** Current repository sources may establish scope
  constraints; they do not substitute for missing customer/system sources.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-03` — Acquire business need and product intended use

- **Statement:** Before this candidate can be approved as a product stakeholder
  baseline, it SHALL contain an authority-verified business/request source and
  an intended-use source that name the customer or product authority, actors,
  vehicle/product mission, normal and abnormal scenarios, out-of-use cases,
  acceptance outcomes, rationale, and priority.
- **Source:** `SRC-0013-02-01`; `SOU-0013-01-BIZ`, `SOU-0013-01-USE`;
  `NEED-0013-01-02`; `PD-0013-01-01`, `02`.
- **Rationale:** Development, verification, release, and assessment activities
  are not product intended use, and current evidence contains no product
  functional mission.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only if authenticated sources name the authorized
  customer/product representative and define every listed intended-use field;
  `not-decided`, silence, TODO prose alone, or an internal guess fails.
- **Status:** `blocked-source`.
- **Validation method:** authority-record inspection and scenario review.
- **Affected stakeholders/interfaces:** `STK-0013-01-CUS`, `IUA`, `MGT`, `SWE`,
  `OPS`; `IF-0013-01-CUS`, `OPS`.
- **Assumptions / exclusions:** Records a missing-source condition only; no
  vehicle function or user behavior is invented here.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-04` — Acquire controlled system allocation

- **Statement:** Every software requirement derived from system behavior SHALL
  trace to a controlled allocation from an authorized system authority that
  identifies the system boundary, allocated behavior, vehicle/external
  interfaces, constraints, acceptance criteria, revision, and change authority.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-03`, `SRC-0013-02-04`;
  `SOU-0013-01-SYS`, `NEED-0013-01-03`, `PD-0013-01-03`.
- **Rationale:** The assessed unit owns software above the kernel but does not
  own the complete ECU system lifecycle this increment.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass per derived requirement only when its system
  source and authority resolve to an exact revision; absent allocation or an
  internally invented `SYS.1`–`SYS.5` source fails.
- **Status:** `blocked-source`.
- **Validation method:** trace audit and authority-record inspection.
- **Affected stakeholders/interfaces:** `STK-0013-01-SYS`, `SWE`, `QVR`;
  `IF-0013-01-SYS`.
- **Assumptions / exclusions:** Does not claim internal complete-system authority
  or choose the form of the system specification.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-05` — Acquire the kernel/platform interface baseline

- **Statement:** Software behavior that depends on kernel or platform services
  SHALL trace to an authority-controlled interface baseline naming the provider,
  revision, supported services, compatibility, resources, timing/error behavior,
  failure handling, and change notification.
- **Source:** `SRC-0013-02-01`–`04`; `SOU-0013-01-KRN`;
  `NEED-0013-01-03`; `PD-0013-01-03`.
- **Rationale:** “Kernel later” defines exclusion, not an interface contract.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass per dependent requirement only if the named
  provider and receiving software authority agree the exact interface revision
  and every listed field is present; assumption from product label alone fails.
- **Status:** `blocked-source`.
- **Validation method:** source comparison, trace audit, and environment review.
- **Affected stakeholders/interfaces:** `STK-0013-01-KRN`, `SYS`, `SWE`, `QVR`;
  `IF-0013-01-KRN`.
- **Assumptions / exclusions:** Does not include the kernel in the supplied
  product or select an API, OS, hypervisor, or architecture.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-06` — Define operating environments and variants

- **Statement:** Before environment-dependent product behavior is approved, the
  baseline SHALL identify the authorized virtualized and deployment environment
  revisions, supported variants/configurations, compute/resource constraints,
  external interfaces, operational conditions, compatibility limits, and the
  rationale for included and excluded environments.
- **Source:** `SRC-0013-02-01`; `SOU-0013-01-ENV`;
  `PD-0013-01-03`.
- **Rationale:** “Virtualized automotive ECU” is a context label and does not
  specify hypervisor, CPU, memory, timing, I/O, network, vehicle, jurisdiction,
  or field conditions.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only when each listed dimension has a controlled
  value/range or an authority-approved explicit non-applicability disposition,
  with exact variant and source revisions.
- **Status:** `blocked-source`.
- **Validation method:** environment review and trace audit.
- **Affected stakeholders/interfaces:** `STK-0013-01-CUS`, `IUA`, `SYS`, `KRN`,
  `SWE`, `SUP`, `OPS`; `IF-0013-01-CUS`, `SYS`, `KRN`, `OPS`.
- **Assumptions / exclusions:** Does not choose any environment or translate an
  unknown value into an implementation default.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-07` — Make requirements atomic, verifiable, and traceable

- **Statement:** Every requirement eligible for agreement SHALL contain one
  stable ID, one unambiguous obligation, source, rationale, priority, binary
  acceptance criteria, status, validation method, affected stakeholders and
  interfaces, assumptions/exclusions, and append-only change history.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-07`;
  `NEED-0013-01-04`, `05`.
- **Rationale:** Downstream analysis cannot establish correctness, coverage, or
  change impact from compound, anonymous, or unverifiable prose.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only if every required field is present, the
  statement contains one testable obligation, and every source and affected
  interface resolves; otherwise fail the individual record.
- **Status:** `candidate-derived`.
- **Validation method:** document inspection and trace audit.
- **Affected stakeholders/interfaces:** all requirement source, review, and
  receiving groups; particularly `CUS`, `SYS`, `KRN`, `SWE`, `QVR`, `REL`.
- **Assumptions / exclusions:** This schema does not approve content or choose
  downstream architecture, design, code, or verification technique.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-08` — Preserve the owned-software release boundary

- **Statement:** Stakeholder requirements for integration, acceptance, and
  release SHALL distinguish the owned software package from kernel, hardware,
  manufacturing, vehicle, and complete-ECU integration/release and SHALL name
  the authorized receiving and internal release/acceptance roles before an
  operative commitment is recorded.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-03`–`05`;
  `NEED-0013-01-04`, `CON-0013-01-01`; `PD-0013-01-05`.
- **Rationale:** Current responsibility is internal only for the assessed unit’s
  software package; identities and remits remain unassigned.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass only if the exact package baseline and both
  authorities are named and no complete-product acceptance is attributed to the
  assessed unit; `internal` without a bounded authority fails operative use.
- **Status:** `candidate-derived`.
- **Validation method:** boundary source comparison and authority-record
  inspection.
- **Affected stakeholders/interfaces:** `STK-0013-01-SWE`, `QVR`, `REL`, `SYS`,
  `KRN`; `IF-0013-01-REL`.
- **Assumptions / exclusions:** Does not perform or authorize release and does
  not include kernel/hardware/vehicle scope.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-09` — Retain agreement and change communication

- **Statement:** Every proposed agreement, rejection, conflict disposition,
  change, and supersession SHALL communicate the exact requirement/baseline
  revision to all affected source and receiving authorities and retain sender,
  recipients, authority, date, comments, decision, rationale, impact, and
  closure state.
- **Source:** `SRC-0013-02-01`; `NEED-0013-01-06`;
  `CH-0013-01-AGREE`, `CH-0013-01-IMPACT`; `PD-0013-01-06`.
- **Rationale:** Authorship, attendance, delivery, or silence cannot demonstrate
  agreement or controlled change.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass per event only when every named field is present,
  affected parties are trace-derived, and each required authority records an
  explicit disposition; silence or unversioned communication fails.
- **Status:** `candidate-derived`.
- **Validation method:** authority-record inspection and trace audit.
- **Affected stakeholders/interfaces:** all affected groups/interfaces;
  especially `IF-0013-01-CUS`, `SYS`, `KRN`, `VR`, `REL`, `OPS`.
- **Assumptions / exclusions:** Does not select communication tooling, cadence,
  address, or escalation timing; those remain `PD-0013-01-06` / `0012-05` work.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-10` — Control operations and field-feedback scope

- **Statement:** If operations, deployment, service, update, incident,
  diagnostics, telemetry/privacy, or field-feedback responsibility is assigned,
  the baseline SHALL identify the authorized party, applicable environments,
  data and privacy boundary, expected outcomes, response/closure authority, and
  controlled source; until then it SHALL assert none of those behaviors.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-04`;
  `SOU-0013-01-OPS`, `NEED-0013-01-08`; `PD-0013-01-08`.
- **Rationale:** Operations parties and responsibility are currently unnamed;
  omission must not silently become internal product behavior or data use.
- **Priority:** `P2-medium` while responsibility is unassigned; reassess on
  activation.
- **Acceptance criteria:** While unassigned, pass only if no operational or data
  behavior is claimed. After assignment, pass only if every listed field and
  authority is controlled and traced.
- **Status:** `conditional-open`.
- **Validation method:** source/authority inspection and scenario review.
- **Affected stakeholders/interfaces:** `STK-0013-01-OPS`, `CUS`, `IUA`, `SWE`,
  `REL`; `IF-0013-01-OPS`.
- **Assumptions / exclusions:** Does not authorize telemetry, personal-data
  processing, deployment, service, update, or external effects.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-11` — Preserve evidence identity and confidentiality

- **Statement:** Requirement agreement and validation evidence SHALL retain the
  applicable product, project, process/interface, baseline, revision, owner,
  origin, validity, retention, and confidentiality metadata and SHALL remain
  `internal` unless an authorized distribution decision says otherwise.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-02`;
  `NEED-0013-01-05`, `07`; `CON-0013-01-02`, `03`, `05`.
- **Rationale:** Wrong-origin, cross-baseline, uncontrolled, or publicly exposed
  evidence cannot support this product baseline or assessment.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass per retained record only if all ten metadata
  fields are present and valid for this product/increment; wrong-origin,
  uncontrolled interview-only, or unauthorized distribution fails.
- **Status:** `candidate-confirmed`.
- **Validation method:** metadata trace audit and source comparison.
- **Affected stakeholders/interfaces:** all groups; especially
  `STK-0013-01-ASM`, `MGT`, `SWE`, `QVR` and `IF-0013-01-ASM`.
- **Assumptions / exclusions:** Interviews may contextualize evidence but do not
  substitute for controlled artifacts; this requirement does not claim a rating.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-12` — Keep cybersecurity and functional-safety claims bounded

- **Statement:** This baseline SHALL NOT claim an owned Automotive SPICE for
  Cybersecurity, ISO/SAE 21434, ISO 26262, ASIL, TARA/HARA, cybersecurity case,
  or safety case lifecycle this increment; any externally allocated product
  constraint SHALL identify its authorized source and exact allocation.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-02`, `SRC-0013-02-06`;
  `SOU-0013-01-CSF`, `CON-0013-01-04`; `PD-0013-01-08`.
- **Rationale:** Generic PAM evidence is not cybersecurity or functional-safety
  proof, while external constraints must not be lost merely because the owned
  lifecycles are excluded.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Pass if prohibited owned-lifecycle/compliance claims
  are absent and every included CS/FS-related product constraint has an
  authorized external source; any unsupported ASIL or compliance statement
  fails.
- **Status:** `candidate-confirmed` for exclusion; `conditional-open` for future
  external constraints.
- **Validation method:** prohibited-claim scan and authority/source inspection.
- **Affected stakeholders/interfaces:** `STK-0013-01-CSF`, `MGT`, `SYS`, `SWE`,
  `REL`, `ASM`; `IF-0013-01-CSF`.
- **Assumptions / exclusions:** A later owned-lifecycle inclusion requires new
  Management authority; this candidate does not make that decision.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-13` — Protect assessment independence and claim validity

- **Statement:** Use of this stakeholder baseline in an assessment SHALL retain
  its exact approval status and revision, and any assessment conclusion SHALL
  require a named competent assessor with recorded independence and objective
  evidence; a Management waiver or interview SHALL NOT fill those fields.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-02`;
  `NEED-0013-01-07`, `CON-0013-01-02`, `03`, `06`;
  `PD-0013-01-07`.
- **Rationale:** An unapproved candidate or unnamed assessor cannot support a
  capability conclusion.
- **Priority:** `P0-must` for assessment use.
- **Acceptance criteria:** Pass only if the baseline revision/status is quoted
  exactly and the assessor competence, independence, name, evidence and report
  disposition are present; otherwise no assessment conclusion is permitted.
- **Status:** `candidate-confirmed` for the constraint; assessor assignment is
  `blocked-source`.
- **Validation method:** authority-record inspection and evidence trace audit.
- **Affected stakeholders/interfaces:** `STK-0013-01-ASM`, `MGT`, `SWE`, `QVR`;
  `IF-0013-01-ASM`.
- **Assumptions / exclusions:** Does not assign an assessor, sample, date, rating,
  or Capability Level.
- **Change history:** introduced by `CHG-0013-02-001`.

### `REQ-0013-02-14` — Approve only an exact complete revision

- **Statement:** This baseline SHALL become `approved` only through an
  append-only record naming the designated stakeholder-baseline approver and
  bounded remit, the exact candidate version and immutable repository identity,
  every participating source authority, review findings/dispositions, approval
  date, and the disposition of every `blocked-source` or `conditional-open`
  entry applicable to the approved scope.
- **Source:** `SRC-0013-02-01`, `SRC-0013-02-07`;
  `PD-0013-01-04`, `CH-0013-01-AGREE`.
- **Rationale:** No present source assigns approval authority; approval must bind
  an exact reviewed revision and cannot be inferred.
- **Priority:** `P0-must`.
- **Acceptance criteria:** Current candidate: pass the truthfulness check only
  when status remains `candidate-unapproved`. Future approval: pass only if all
  named record fields and authority proofs exist and no applicable blocking
  entry lacks an explicit authorized disposition.
- **Status:** `blocked-source` for approval authority; candidate preparation is
  complete without asserting approval.
- **Validation method:** authority-record inspection, trace audit, and exact-tree
  identity comparison.
- **Affected stakeholders/interfaces:** `STK-0013-01-MGT`, `CUS`, `IUA`, `SYS`,
  `KRN`, `SWE`, `QVR`, `REL`; `IF-0013-01-CUS`, `SYS`, `KRN`, `VR`, `REL`.
- **Assumptions / exclusions:** Requirements Engineer, Project Lead, implementer,
  reviewer, mailbox sender, or commit author is not the approver unless a
  separate authority record expressly assigns that exact remit.
- **Change history:** introduced by `CHG-0013-02-001`.

## 5. Completeness and trace summary

| Requirement | Primary need/constraint | Primary source candidates | Current status |
|---|---|---|---|
| `REQ-0013-02-01` | `NEED-0013-01-01`, `CON-0013-01-01` | authoritative `SRC-0013-02-02`, `03` | `candidate-confirmed` |
| `REQ-0013-02-02` | `NEED-0013-01-05` | every acquired `SOU-*` | `candidate-derived` |
| `REQ-0013-02-03` | `NEED-0013-01-02` | `SOU-0013-01-BIZ`, `USE` | `blocked-source` |
| `REQ-0013-02-04` | `NEED-0013-01-03` | `SOU-0013-01-SYS` | `blocked-source` |
| `REQ-0013-02-05` | `NEED-0013-01-03` | `SOU-0013-01-KRN` | `blocked-source` |
| `REQ-0013-02-06` | environment gaps | `SOU-0013-01-ENV` | `blocked-source` |
| `REQ-0013-02-07` | `NEED-0013-01-04`, `05` | all approved sources | `candidate-derived` |
| `REQ-0013-02-08` | `NEED-0013-01-04`, `CON-0013-01-01` | `SOU-0013-01-ORG` plus receiver authority | `candidate-derived` |
| `REQ-0013-02-09` | `NEED-0013-01-06` | agreement/change records | `candidate-derived` |
| `REQ-0013-02-10` | `NEED-0013-01-08` | `SOU-0013-01-OPS` | `conditional-open` |
| `REQ-0013-02-11` | `NEED-0013-01-05`, `07`; `CON-0013-01-02`, `03`, `05` | controlled evidence records | `candidate-confirmed` |
| `REQ-0013-02-12` | `CON-0013-01-04` | `SOU-0013-01-CSF` if constraints exist | confirmed exclusion / conditional constraints |
| `REQ-0013-02-13` | `NEED-0013-01-07`, `CON-0013-01-06` | assessor authority/evidence | confirmed constraint / `blocked-source` assignment |
| `REQ-0013-02-14` | agreement-authority boundary | approval authority record | `blocked-source` |

No product-functional requirement is present because the necessary customer,
intended-use, system-allocation, kernel-interface, and environment sources are
absent. That absence is a measured finding, not permission to fabricate content.

## 6. Disposition of `PD-0013-01-01` through `08`

| Decision | Disposition in candidate `0.1.0-candidate` | Authority / evidence still needed | Effect and linked requirements |
|---|---|---|---|
| `PD-0013-01-01` — customer/requester and representative | `open`; no customer identity or customer-originated requirement inserted | Management plus authorized customer/product authority; contract/request provenance | Blocks customer agreement and approval of customer-derived content; `REQ-0013-02-02`, `03`, `14` |
| `PD-0013-01-02` — intended-use actors and scenarios | `open`; lifecycle/assessment activity remains separated from product use | Authorized customer/product authority with user/operations evidence | Product-functional and intended-use content remains absent; `REQ-0013-02-03`, `10` |
| `PD-0013-01-03` — target environments and interfaces | `open`; no platform, resource, vehicle, kernel-interface, or variant value selected | Product/system allocation, kernel/platform, and receiving software authorities with controlled baselines | Environment-dependent content remains blocked-source; `REQ-0013-02-04`–`06` |
| `PD-0013-01-04` — stakeholder-baseline approval/change authority | `open-blocking-approval`; current revision stays `candidate-unapproved` | Management/organizational authority record assigning exact remit, deputies/conflicts, and change/supersession authority | No approval claim; `REQ-0013-02-09`, `14` |
| `PD-0013-01-05` — named internal/external roles | `open`; generic internal functions are not converted into names or commitments | Organizational Management and each external source authority; competence/availability/remit evidence | Blocks named operational/release commitments, not candidate preparation; `REQ-0013-02-02`, `08`, `14` |
| `PD-0013-01-06` — communication media/cadence/escalation/retention | `deferred-open`; channel record content is specified, implementation choices are not | Assigned interface/process authorities; confidentiality, availability, tooling and retention constraints | Does not block this candidate; blocks claims that agreement/change communication is operated; `REQ-0013-02-09` |
| `PD-0013-01-07` — assessor/date/sample/distribution | `open-assessment`; no assessor, rating, target date, sample or external distribution inserted | Management sponsor and named competent independent assessor | Does not approve this baseline and blocks assessment conclusions; `REQ-0013-02-11`, `13` |
| `PD-0013-01-08` — operations/supplier/calibration/CSF/feedback authorities | `conditional-open`; no responsibilities, product behaviors, data use, ASIL, or compliance claim inserted | Management plus relevant external authorities and actual responsibility/interface evidence | Candidate remains bounded; later applicable constraints require sources; `REQ-0013-02-10`, `12` |

These are product/authority decisions, not drafting defects. The Project Lead may
route them but may not decide them by interpretation. Bounded candidate work is
complete without changing `0013-02` to `[u]`; a later approval attempt must stop
if `PD-0013-01-04` and applicable source/authority items remain unresolved.

## 7. Approval boundary and candidate review checklist

### 7.1 Current approval record

| Field | Current value |
|---|---|
| Candidate version | `0.1.0-candidate` |
| Candidate repository identity | substantive Task commit, recorded in `TODO.md` after commit |
| Designated baseline approver | `not-assigned` |
| Source-authority participation | `not-recorded` for missing `SOU-*` classes |
| Review disposition | `review-ready`, not approved |
| Approval disposition | `not-approved` |
| Approval date | `none` |
| Operative date / validity | `none` |

### 7.2 Review checklist

A reviewer can verify the candidate without making the missing product decisions:

1. all 14 `REQ-0013-02-*` IDs are unique and every required field is present;
2. every confirmed claim matches its exact cited source revision;
3. every derived statement is the smallest implication and makes no architecture
   choice;
4. every missing customer/system/platform/environment source stays
   `blocked-source` rather than becoming guessed product behavior;
5. all eight `PD-0013-01-*` items have a disposition and required authority;
6. priority, status, acceptance criteria, validation method, assumptions,
   exclusions, affected interfaces, and change history are explicit;
7. `candidate-unapproved` is preserved and no source, author, or role is treated
   as approval by implication; and
8. no `0013-03` work, Acceptance, integration, release, external effect, or
   capability claim is included.

Approval of a future revision is a separate authority action, not part of this
implementation claim.

## 8. Change history and supersession rules

| Change ID | Version | Date | Authoring role | Change | Source / rationale | Approval impact |
|---|---|---|---|---|---|---|
| `CHG-0013-02-001` | `0.1.0-candidate` | 2026-08-29 | Requirements Engineer, Beverly | Initial candidate: `REQ-0013-02-01` through `14`; source/trace/status vocabulary; dispositions for `PD-0013-01-01` through `08`; explicit non-approval boundary | Task `0013-02`, exact `0013-01` prerequisite tip, `SRC-0013-02-01`–`07` | Initial unapproved candidate; no prior approval to invalidate |

Future changes must add a new version and append a change row identifying the
changed requirement IDs, prior/new text or a stable diff reference, cause,
source, impact, authority, and approval effect. Rejected and superseded records
remain traceable; history is not rewritten. This rule specifies observable
record content and does not choose a storage or implementation architecture.

## 9. Assumptions, exclusions, and downstream handoff

**Assumptions**

- The exact `0013-01` tip and `DEC-0020-001` remain current for this candidate.
- Supporting `0020-03`, `0020-04`, and `0020-06` records are useful consistency
  evidence but gain no Acceptance or Management authority here.
- Candidate preparation may complete while approval and stakeholder-originated
  content remain open, provided the status and refuse-at-use boundary are honest.

**Exclusions**

- Named customer, intended-use actor, vehicle mission, product-functional
  behavior, platform/environment value, kernel/API, operational data use, or
  external constraint not present in an authorized source.
- Approval, agreement, Architecture, design, code, verification execution,
  release, Assessment rating, Capability Level, CS/FS compliance, public
  distribution, or external effect.
- Acceptance, integration/checkpoint crossing, `main`/Feature ref movement,
  `DONE.md`, and Task `0013-03` implementation.

**Downstream handoff**

The candidate may be reviewed and cited at its exact status. It does not add a
new Task prerequisite or prevent bounded downstream analysis that explicitly
preserves source gaps and `candidate-unapproved`. No downstream work may call it
approved, customer-agreed, complete, or operative without the separate authority
record defined by `REQ-0013-02-14`.
