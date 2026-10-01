# Requirements — ECU evidence boundary (`0020-02`)

**Item:** Task `0020-02` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-02-20260826T120900Z.md`
**owner_token:** `agent:hguh:0020-02:20260826T120900Z`
**Recorded at:** `2026-08-26T12:14:00Z`
**Capability class:** `unprivileged`

This document defines observable needs. It does not choose architecture, write an enforcer, accept work, or activate a gate against other work units.

Mailbox assignment `1787745915547-dbe736e8` is coordination, not authority.

---

## 1. Provenance (requester wording, preserved)

### 1.1 Task text (`TODO.md`, Feature `0020`, Task `0020-02`)

> Define and enforce the evidence boundary among canonical origins `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, and `controlled-scenario`; require `product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, revision, owner, origin, validity, retention, and confidentiality metadata and prohibit cross-product evidence substitution or opportunistic aggregation.

### 1.2 Feature goal (same Feature heading)

> Establish the concrete ECU product and organizational boundary for a PAM 4.0 Level-1 target, select the named processes by actual responsibility, and prevent documentation-pipeline evidence from being misrepresented as ECU process-instance evidence. The current repository is an enabling process/tool foundation; capability must be demonstrated on approved ECU process instances.

### 1.3 ASPICE task acceptance envelope (Feature `0020` block)

Preserved in full as the envelope this boundary must serve; it is not restated as a new requirement:

> Unless a task explicitly produces only a definition or readiness mechanism, completion requires evidence from the approved ECU product/project/process instance and baseline. Every deliverable must carry controlled identity/version/origin, owner and required authority, applicable lifecycle trace and consistency results, findings/contrary evidence and disposition, validation or review evidence, retention/access classification, and an unambiguous pass/fail or decision gate. A template, tool, documentation campaign, synthetic scenario, or external party's evidence cannot substitute for the assessed unit's own execution. Assessment disposition (`included/rated` or `out of scope/not rated`) is recorded separately from execution responsibility (`internal`, `shared`, or `external`); a shared in-scope process requires evidence for the assessed unit's portion as well as controlled external interfaces.

### 1.4 Management scope already recorded (`DEC-0020-001`)

Verbatim Management sentence (2026-08-25 18:26 +02):

> Wir entwickeln ausschließlich System- und Applikationssoftware für ein virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in Entwicklung und wird später hinzugefügt.

Working identifiers already recorded for later evidence metadata:

- `product_id=virtualized-automotive-ecu`
- `project_id=autodocs-ecu-software`
- `increment=software-without-kernel`

Kernel, complete-ECU-system, and hardware/manufacturing capability MUST NOT be claimed from this increment.

### 1.5 Neighboring survey wording (not this Task's selected strength)

`docs/ASPICE/05-evidence-register.md` currently says Feature `0020-02` “must make cross-product substitution mechanically visible or invalid.” The Task text says **prohibit** substitution and opportunistic aggregation. This dossier uses the Task text. The survey's “visible or invalid” is neighboring intent, not a weakening of the Task.

`docs/ASPICE/04-gap-roadmap.md` draws documentation-execution as “not substitutable” into a named-process assessment. That diagram is supporting evidence of the same need; it is not the contract.

---

## 2. Problem (not solution)

The repository currently holds a documentation/data-pipeline product and, as of `DEC-0020-001`, a first assessed ECU software increment that excludes the kernel. Existing survey documents already *name* five origin values and a metadata list. They do not yet make an evidence item fail, or refuse to be used as ECU execution evidence, when:

- origin is missing, non-canonical, or mixed;
- required identity/metadata fields are missing;
- a documentation-campaign, template, tool, synthetic, or other-product result is offered as the assessed ECU unit's own execution;
- items from different products, projects, instances, or baselines are aggregated as if they were one instance.

The problem is misrepresentation and silent mixing. The need is a defined boundary that can later be enforced. How enforcement is realized is not chosen here.

---

## 3. Canonical origin vocabulary (preserved)

Class (`I`/`M`/`O`/`S`) and origin are separate. This Task binds **origin**. Meanings are taken from `docs/ASPICE/05-evidence-register.md` and are not redesigned:

| Origin | Meaning (preserved) |
|---|---|
| `process-definition` | Reusable policy, method, template, criterion, or process description |
| `implemented-mechanism` | Reusable tool, schema, validator, workflow, or repository control |
| `documentation-execution` | Result from a documentation/extraction/curation/publication process instance |
| `ecu-execution` | Result from the approved ECU product/process instance |
| `controlled-scenario` | Fixture, rehearsal, or synthetic case that is explicitly not represented as a real product event |

An `O` artifact is objective only for the product/process instance it actually records. A documentation campaign can be `O`/`documentation-execution`; it is not `O`/`ecu-execution`. Reusable definitions and mechanisms may support an ECU process after tailoring and use; their existence is not ECU outcome evidence.

---

## 4. Atomic requirements

### `REQ-0020-01` — Canonical origin set is closed

- **Title:** Closed origin vocabulary
- **Description:** The system SHALL identify every evidence item used for Feature `0020` assessment, catalogue, register, freeze, or process-instance demonstration with exactly one origin from the closed set `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, `controlled-scenario`.
- **Acceptance intent:** Given an evidence item offered for those uses, when origin is inspected, then the recorded origin is exactly one of those five strings, or the item is not usable for those uses. A sixth value, an empty origin, or two origins on one item fails.
- **Assumptions:** Existing `I`/`M`/`O`/`S` class remains a separate field; this requirement does not replace it.
- **Exclusions:** Informal notes that are not offered as assessment/catalogue/register/freeze evidence.

### `REQ-0020-02` — Required metadata on every such evidence item

- **Title:** Required evidence identity and control metadata
- **Description:** The system SHALL require the following metadata on every evidence item in the scope of `REQ-0020-01`: `product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, revision, owner, origin, validity, retention, and confidentiality.
- **Acceptance intent:** Given such an item, when metadata is inspected, then each named field is present and non-empty, or the item is not usable for those uses. Presence of extra fields does not satisfy a missing required field.
- **Assumptions:** For this increment, `product_id` and `project_id` bind to `DEC-0020-001` working identifiers unless a later Management `DEC-0020-*` replaces them. `increment=software-without-kernel` is applicable context, not a substitute for `baseline_id`.
- **Exclusions:** Field encoding, storage schema, and filename convention are not chosen here.

### `REQ-0020-03` — Origin meanings are not interchangeable

- **Title:** Origin values are not aliases
- **Description:** The system SHALL treat each canonical origin as a distinct claim about how the item was produced. The system SHALL NOT treat `documentation-execution` as `ecu-execution`, SHALL NOT treat `controlled-scenario` as `ecu-execution`, and SHALL NOT treat `process-definition` or `implemented-mechanism` as ECU process-instance outcome evidence.
- **Acceptance intent:** Given an item whose origin is `documentation-execution`, `controlled-scenario`, `process-definition`, or `implemented-mechanism`, when it is offered as proof of ECU process-instance execution, then that use is refused. The same item may still be used for the aspect its origin actually demonstrates.
- **Assumptions:** Tailoring and later *use* of a definition or mechanism on an ECU instance can produce a *separate* `ecu-execution` item; it does not re-label the original definition/mechanism.
- **Exclusions:** PAM rating rules themselves; this is a local evidence-boundary rule.

### `REQ-0020-04` — Cross-product substitution is prohibited

- **Title:** No cross-product evidence substitution
- **Description:** The system SHALL prohibit using evidence whose `product_id` is not the approved assessed product as a substitute for that product's own execution evidence. The system SHALL prohibit using another project's, instance's, or baseline's evidence as if it belonged to the item's declared `project_id`, `process_instance_id`, or `baseline_id`.
- **Acceptance intent:** Given two items with different `product_id` (or different `project_id` / `process_instance_id` / `baseline_id`), when one is offered in place of the other for ECU execution of the assessed unit, then that substitution is refused. Same-aspect reuse of a definition or mechanism remains allowed only when origin is `process-definition` or `implemented-mechanism` and the item is not presented as `ecu-execution`.
- **Assumptions:** The approved assessed product for this increment is the virtualized automotive ECU software unit of `DEC-0020-001`.
- **Exclusions:** Comparison, citation, or contrast that names the foreign product/project/instance/baseline as foreign.

### `REQ-0020-05` — Opportunistic aggregation is prohibited

- **Title:** No opportunistic aggregation
- **Description:** The system SHALL prohibit aggregating evidence items that do not share the same `product_id`, `project_id`, `process_id`, `process_instance_id`, and `baseline_id` into a single process-instance demonstration, rating input, or evidence freeze as if they were one instance.
- **Acceptance intent:** Given a set offered as one instance's evidence, when any required identity field differs among members, then the set is not accepted as one instance. A named, remaining-foreign list of excluded items does not count as aggregation.
- **Assumptions:** Shared-process *interface* evidence required by later `0020-03`/`0020-04`/`0020-09` is a separate item with its own origin and identity, not a silent merge into the internal instance.
- **Exclusions:** How a later selected-profile register stores the two sides of a shared process; that is `0020-09`.

### `REQ-0020-06` — Documentation campaign is not ECU execution

- **Title:** Documentation-execution cannot satisfy ECU execution
- **Description:** The system SHALL classify Feature `0019` (and any other documentation/extraction/curation/publication campaign) evidence as `documentation-execution` when used at all, and SHALL NOT present it as `ecu-execution` or as Automotive SPICE capability evidence for the assessed ECU unit.
- **Acceptance intent:** Given a documentation-campaign result, when origin is inspected, then it is `documentation-execution` (or it is not used). When it is offered as `ecu-execution` or as an ECU process capability proof, that use is refused.
- **Assumptions:** Matches Feature `0019` overall-goal text that `0020-02` classifies it as `documentation-execution`.
- **Exclusions:** Whether Feature `0019` itself is in or out of a documentation-process assessment; that is not this Task.

### `REQ-0020-07` — Templates, tools, and scenarios cannot substitute for ECU execution

- **Title:** Non-execution artifacts are not ECU execution
- **Description:** The system SHALL NOT accept a template, tool, documentation campaign, synthetic scenario, or external party's evidence as a substitute for the assessed unit's own execution.
- **Acceptance intent:** Given an item whose origin is `process-definition`, `implemented-mechanism`, `documentation-execution`, or `controlled-scenario`, or whose owner/product is not the assessed unit, when it is offered as the assessed unit's own execution, then that use is refused.
- **Assumptions:** Requester wording is the Feature envelope sentence, preserved.
- **Exclusions:** Using those items as what they are (definition, mechanism, documentation-instance result, named scenario, or named external interface evidence).

### `REQ-0020-08` — Kernel and non-owned product evidence stay out of this increment's ECU execution set

- **Title:** Increment bound from `DEC-0020-001`
- **Description:** The system SHALL NOT accept kernel, hardware, manufacturing, or complete-ECU-system execution evidence as `ecu-execution` for this increment's assessed unit.
- **Acceptance intent:** Given an item that claims kernel/hardware/manufacturing/complete-system execution for this increment, when origin/`product_id`/claim wording is inspected, then it is not usable as this increment's `ecu-execution`.
- **Assumptions:** Adding the kernel requires a new Management `DEC-0020-*`.
- **Exclusions:** Recording that such evidence exists *outside* this increment, labelled as not in the supplied-product boundary.

### `REQ-0020-09` — Definition is observable without yet activating other units' start gates

- **Title:** Contract exists as an inspectable work product
- **Description:** Task `0020-02` SHALL produce an inspectable contract that states `REQ-0020-01` through `REQ-0020-08` with provenance, acceptance intent, assumptions, exclusions, and open decisions. This requirement is satisfied by this dossier. It does not by itself change another work unit's start, validation, acceptance, integration, publication, or closure gate.
- **Acceptance intent:** Given this file on branch `0020-02`, when compared to the Task text, then every named origin, every named metadata field, and both prohibitions (substitution, opportunistic aggregation) are present as SHALLs.
- **Assumptions:** “Define” can be completed as a local contract. “Enforce” is a separate, possibly gated, behavior.
- **Exclusions:** Mechanical enforcement.

---

## 5. Open product decisions (not decided here)

These are genuine remaining choices. They are not assumed.

| ID | Decision | Why it is open | Who can close it |
|---|---|---|---|
| `PD-0020-02-01` | What *enforce* means operationally | **Closed** by `DEC-0020-002`: refuse at use/freeze for named ECU consumers; not at arbitrary Task start; not a default `_src/validate.py` check | Architect `uras` |
| `PD-0020-02-02` | Canonical storage/representation of the metadata (schema, catalogue, per-artifact header, or other) | Required fields are named; encoding is not | Architecture, not Requirements |
| `PD-0020-02-03` | Closed value sets for `validity`, `retention`, and `confidentiality` | Fields are required; allowed tokens/periods are not in the Task text | Product/process decision; escalate if more than one valid set remains after evidence |
| `PD-0020-02-04` | Whether existing `docs/ASPICE/*` survey files become the live contract | **Closed** by `DEC-0020-002`: stay informative; not live gates | Architect `uras` |
| `PD-0020-02-05` | How shared/external interface evidence is identified so it is not mistaken for opportunistic aggregation | `REQ-0020-05` assumes later `0020-03`/`0020-04`/`0020-09` will name the two sides | Those Tasks; do not pre-empt them |

---

## 6. Affected interfaces (identified, not designed)

Consumers of this boundary, once enforcement is activated:

- Task `0020-07` (assessment input / official-outcome worksheets)
- Task `0020-08` (process/work-product/evidence catalogue)
- Task `0020-09` (selected-profile execution register)
- Feature `0025` (pilot assessment and evidence freeze)
- Feature `0019` (classified `documentation-execution` by this Task)
- Features `0022`–`0032` and `0011`–`0018` under the Feature `0020` ASPICE envelope
- Survey files `docs/ASPICE/01-assessment-basis-and-scope.md`, `02-level-1-requirements.md`, `04-gap-roadmap.md`, `05-evidence-register.md` (current vocabulary sources; not yet live gates)

This list is an interface identification. It is not a new prerequisite graph and does not change those items' markers.

---

## 7. Gate classification (preparation, not mutation)

Canonical predicate (`decision-record@v1` §2, `cross-item-blast-radius`): a qualifying gate can block the start, validation, acceptance, integration, publication, or closure of **another** work unit, or change that unit's contract.

| Candidate behavior | Qualifies? | Why |
|---|---|---|
| This dossier stating SHALLs for `0020-02`'s own contract | No | Local definition. Other units are not blocked by this file existing. |
| Adding TODO prerequisites from `0020-07`/`0020-08`/`0025-*`/etc. onto this contract | Yes, if those items cannot start or close without it | Would change another unit's start/closure contract |
| A repository check that fails other Tasks' validation when metadata/origin rules are unmet | Yes | Blocks validation of other units |
| A freeze/assessment rule that rejects mixed-origin or cross-product sets | Yes | Blocks `0025` freeze / assessment closure |
| A local fixture that only tests this contract's examples | No, while it cannot fail another unit | Task-local |

**Current session action:** `DEC-0020-002` and the Architect review are reachable on `0020-02`. Optional CON-01 helper/fixtures classify examples locally and are **not** registered as a shared gate. Consumer-side refusal remains with `0020-07` / `0020-08` / `0020-09` / `0025-02` / `0025-03`.

---

## 8. Assumptions and exclusions (summary)

**Assumptions**

- `0020-01` `[x]` / `DEC-0020-001` is the start-gate product bound.
- Origin strings and meanings already in `docs/ASPICE/05-evidence-register.md` are the vocabulary to preserve.
- `I`/`M`/`O`/`S` stays a separate classification.
- Define and enforce are separable; define does not silently activate enforce.

**Exclusions**

- Architecture of the enforcer, schema, or storage.
- Task `0020-03` responsibility matrix.
- Process applicability (`0020-04`/`0020-05`/`0020-06`).
- Writing `Acceptance: ✓`, integrating Feature `0020`, advancing `main`, touching Feature `0033`, starting `0020-03`.
- Inventing a customer, kernel inclusion, or 20-process system profile.

---

## 9. What would complete “enforce” later (intent only)

When (and only when) `PD-0020-02-01` is closed with `uras` + `decision-record@v1` as required:

- substitution and opportunistic aggregation described in `REQ-0020-04` and `REQ-0020-05` are refused at the chosen observable point;
- missing origin or missing required metadata is refused at that same point;
- the refusal is visible in retained evidence (not only in prose).

This section is acceptance *intent* for a later enforcement increment. It is not authorization to implement it in this claim before the gate review.
