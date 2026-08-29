# Requirements — selected-profile execution register (`0020-09`)

**Item:** Task `0020-09` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-09-20260826T131500Z.md`
**owner_token:** `agent:hguh:0020-09:20260826T131500Z`
**Recorded at:** `2026-08-26T13:18:00Z`

Mailbox `1787750086810-a8f94975` is coordination, not authority.

This register maps the selected 14-process profile to execution Features, completion gates, and interface/freeze edges. It does **not** rate capability, freeze evidence, or implement `0025-02` / `0025-03`.

---

## 1. Provenance (preserved)

Task text: Create and validate the selected-profile execution register: for every included base, cybersecurity, safety, or other lifecycle process, identify the exact execution Feature/task and completion gate; for every shared process, record whether it is rated, the assessed unit's exact outcomes/activities and execution gate, and the external input/output/acceptance/feedback gate; for every fully external process, identify the approved interface-evidence gate and prohibit an internal rating. Materialize every conditional predecessor, release, and assessment relationship as a concrete TODO prerequisite or machine-enforced selected-profile edge; reject a profile, release, evidence freeze, or assessment when an included process or selected edge has no executable, satisfied path to valid evidence, or when interface evidence is substituted for the assessed unit's own performance.

Bound inputs: `DEC-0020-001`; `0020-02` / `DEC-0020-002` (refuse-at-use for this register); `0020-04` 14-process nucleus; `0020-05` no conditional-process inclusion; `0020-06` CS/FS Features = 0; `0020-07` worksheets; `0020-08` catalogue (no ratings; no `ecu-execution` yet).

---

## 2. Selected profile this increment

| Field | Value |
|---|---|
| Profile | 14-process ECU software-delivery nucleus |
| Increment | `software-without-kernel` |
| `product_id` | `virtualized-automotive-ecu` |
| `project_id` | `autodocs-ecu-software` |
| Included/rated, execution `internal` | `SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6` |
| Shared rows | **0** |
| CS/FS owned lifecycles | **0** (no Automotive SPICE for Cybersecurity model; no ISO/SAE 21434; no ISO 26262) |
| Conditional PAM inclusions (`ACQ.4`, `HWE.*`, `MLE.*`, `SUP.11`, `PIM.3`, `REU.2`) | **0** |
| `SYS.1`–`SYS.5`, `VAL.1` | `out of scope/not rated`; not this increment's selected-profile execution |

This register is `process-definition`. It is not `ecu-execution` of any included process.

---

## 3. Atomic requirements

### `REQ-0020-09-01` — Every included process has an execution Feature, completion gate, and path

For each of the 14 included processes, the register SHALL name (a) the execution Feature, (b) the completion Task whose `ecu-execution` is the PA 1.1 outcome evidence, and (c) the ordered executable path of predecessor Tasks already in `TODO.md`. A path that exists but is still `[ ]` is a **gap**, not a missing path.

### `REQ-0020-09-02` — Shared processes

Every `shared` process SHALL record whether it is rated, the assessed unit's exact outcomes/activities and execution gate, and the external input/output/acceptance/feedback gate. This increment has **zero** shared processes (`0020-04`/`0020-05`). The shared section SHALL be the empty set, not omitted.

### `REQ-0020-09-03` — Fully external processes: interface-evidence gate, no internal rating

For each fully external process decided in `0020-05`, the register SHALL point at the approved interface-evidence record and SHALL prohibit an internal rating. Absence of an execution Feature SHALL NOT be treated as the process being forgotten.

### `REQ-0020-09-04` — CS/FS are not selected-profile execution

No cybersecurity or functional-safety Feature, completion gate, or profile edge SHALL be registered as included. PAM 4.0 evidence SHALL NOT be offered as ISO/SAE 21434 or ISO 26262 proof (`0020-06`).

### `REQ-0020-09-05` — Out-of-scope SYS and VAL: no internal rating; no unconditional SYS/VAL blockers

`SYS.1`–`SYS.5` and `VAL.1` SHALL receive no internal rating. Features `0022`, `0026`, and `0028`–`0032` remain conditional envelopes. This Task SHALL NOT add `0023-11:0029-02`, `0023-11:0030-02`, `0024-02:0026`, or any other new start-prerequisite that would make an excluded process an unconditional blocker (`DEC-0020-002` ALT-03 rejected; `docs/ASPICE/04-gap-roadmap.md` §5).

### `REQ-0020-09-06` — Materialize relationships as existing TODO edges or named freeze/use gates

Conditional predecessor, release, and assessment relationships SHALL be materialized as:

1. **already-present** `TODO.md` prerequisites that name `0020-09` (`0022-01`, `0023-11`, `0024-02`, `0025-01`, `0026-01`, `0029-01`, `0030-01`, `0031-01`, `0032-01`); and/or
2. **machine-enforced selected-profile edges** owned by `0025-02` (readiness) and `0025-03` (freeze), **not implemented here**.

This Task SHALL NOT register those checks in `_src/validate.py`.

### `REQ-0020-09-07` — Refuse-at-use for this register (`DEC-0020-002`)

When this register is used to justify a profile, release, evidence freeze, or assessment, the use SHALL be **refused** if:

- an included process has no executable path to valid `ecu-execution`;
- a selected edge is absent, stale, or unsatisfied at freeze/assessment time;
- interface evidence is substituted for the assessed unit's own performance of an included `internal` process;
- offered outcome evidence is `documentation-execution`, `controlled-scenario`, `process-definition`, or `implemented-mechanism` in place of `ecu-execution` (`0020-02`).

Satisfaction of included-process paths is judged at `0025-02` / `0025-03`, not by this definition Task inventing ratings.

### `REQ-0020-09-08` — SWE.1 inputs when SYS is not internal

`0023-11` SHALL treat `SYS.2`/`SYS.3` as external this increment: validate allocated software requirements and architecture/interface constraints (including kernel-interface exclusions from `DEC-0020-001`) without claiming internal SYS performance. The named external input gate is that validation, not Feature `0029`/`0030` execution.

### `REQ-0020-09-09` — SPL.2 / VAL.1 when VAL is not included

`0024-02` SHALL NOT require Feature `0026` this increment. The selected-profile release edge SHALL require the approved **external/shared validation and acceptance interface** (party unnamed; `0020-03` `VAL.1` `not-decided`) and SHALL fail if intended-use validation is claimed as internally performed.

---

## 4. Included processes — execution Feature, completion gate, path

Common evidence obligation: origin `ecu-execution` with `0020-02` metadata. Common current gap: no `ecu-execution` yet (`0020-08`). Define/spec Tasks are not the PA 1.1 completion gate when a later execute/operate Task exists.

| Process | Execution Feature | Completion gate (PA 1.1 `ecu-execution`) | Executable path already in `TODO.md` | Current path status |
|---|---|---|---|---|
| `SWE.1` | `0023` | `0023-01` | `0023-11` → `0023-01` | path exists; all `[ ]` |
| `SWE.2` | `0023` | `0023-02` | `0023-01` → `0023-02` | path exists; all `[ ]` |
| `SWE.3` | `0023` | `0023-04` (construction; `0023-03` is design) | `0023-02` → `0023-03` → `0023-04` | path exists; all `[ ]` |
| `SWE.4` | `0023` | `0023-06` (execute; `0023-05` is spec) | `0023-04` + `0023-05` → `0023-06` | path exists; all `[ ]` |
| `SWE.5` | `0023` | `0023-08` (execute; `0023-07` is spec) | `0023-02`/`0023-03`/`0023-06` → `0023-07` → `0023-08` | path exists; all `[ ]` |
| `SWE.6` | `0023` | `0023-10` (execute; `0023-09` is spec) | `0023-01`/`0023-02`/`0023-08` → `0023-09` → `0023-10` | path exists; all `[ ]` |
| `SPL.2` | `0024` | `0024-02` (assemble/deliver; `0024-01` is define) | `0024-01` + supporting `0027-*` named on `0024-02` → `0024-02` | path exists; all `[ ]` |
| `SUP.1` | `0027` | `0027-06` | `0027-01` + `0027-05` → `0027-06` | path exists; all `[ ]` |
| `SUP.8` | `0027` | `0027-05` | `0027-05` (prereq `0020-08`) | path exists; `[ ]` |
| `SUP.9` | `0027` | `0027-09` (operate; `0027-07` is mechanism) | `0027-07` → `0027-09` | path exists; all `[ ]` |
| `SUP.10` | `0027` | `0027-10` (operate; `0027-08` is mechanism) | `0027-08` → `0027-10` | path exists; all `[ ]` |
| `MAN.3` | `0027` | `0027-02` (operate; `0027-01` is plan) | `0027-01` → `0027-02` | path exists; all `[ ]` |
| `MAN.5` | `0027` | `0027-03` | `0027-01` + `0020-08` → `0027-03` | path exists; all `[ ]` |
| `MAN.6` | `0027` | `0027-04` | `0027-01` + `0020-08` → `0027-04` | path exists; all `[ ]` |

**Included CS/FS / other lifecycle processes:** none. Count of included execution Features created by `0020-05`/`0020-06`: **0**.

---

## 5. Shared processes

**Empty set.** No process is rated as shared. No assessed-unit shared-outcome gate and no dual external I/O/acceptance/feedback gate is registered, because no named shared party exists (`0020-03`/`0020-04`/`0020-05`).

A later Management `DEC-0020-*` that names a shared party SHALL revise this section; this Task does not invent one.

---

## 6. Fully external processes — interface-evidence gate, internal rating prohibited

Interface records live in `docs/dossiers/req-0020-05-conditional-process-applicability.md` §4. This register **points**; it does not duplicate or rate.

| Process | Rated internally? | Interface-evidence gate | Execution Feature |
|---|---|---|---|
| `ACQ.4` | **no** | `0020-05` §4.2; no named supplier | none |
| `HWE.1`–`HWE.4` | **no** | `0020-05` §4.1; hardware/virtualization constraints as `external` input, not this unit's HWE `ecu-execution` | none |
| `MLE.1`–`MLE.4`, `SUP.11` | **no** | `0020-05` §4.3; assistant AI is not MLE | none |
| `PIM.3` | **no** | `0020-05` §4.4; backlog hygiene is not PIM.3 | none |
| `REU.2` | **no** | `0020-05` §4.5; this increment is not a reuse product | none |

---

## 7. Out-of-scope SYS / VAL — not selected-profile execution

| Process | Disposition | Internal rating | What this register does | What it does **not** do |
|---|---|---|---|---|
| `SYS.1`–`SYS.5` | `out of scope/not rated` (`0020-04`) | prohibited | Names the SWE.1 external input gate (`REQ-0020-09-08`); `0022-01` later writes the per-SYS interface plan from this register | Does not start `0028`–`0032`; does not add SYS Tasks as unconditional `0023` predecessors |
| `VAL.1` | `out of scope/not rated` (`0020-04`) | prohibited | Names the SPL.2 external validation/acceptance interface (`REQ-0020-09-09`); party unnamed | Does not start `0026`; does not add `0024-02:0026` |

CS/FS interface (not absence): `docs/dossiers/req-0020-06-cybersecurity-safety-applicability.md` §4.

---

## 8. Materialized edges (inspectable)

### 8.1 Concrete TODO prerequisites that already name `0020-09`

These edges already exist in `TODO.md`. This Task records them; it does not widen them.

| Consumer | Existing PREREQ | Relationship this register supplies |
|---|---|---|
| `0023-11` | `0023-11:0020-09` | SWE.1 allocated-input gate: SYS external this increment (`REQ-0020-09-08`) |
| `0024-02` | `0024-02:0020-09` | Release: VAL not included; use external validation/acceptance interface (`REQ-0020-09-09`); fail if a selected-profile edge is absent/unsatisfied |
| `0025-01` | `0025-01:0020-09` | Pilot instance selection reads this register |
| `0025-02` | `0025-02:0025-01` (then this register by transitivity) | Machine-enforced selected-profile readiness / freeze-block (implemented in `0025-02`, not here) |
| `0022-01` | `0022-01:0020-09` | SYS interface plan consumes disposition vs execution from this register |
| `0026-01` | `0026-01:0020-09` | VAL envelope must read that VAL is **not** selected; must not internally rate |
| `0029-01` | `0029-01:0020-09` | SYS.2 envelope: SYS.2 is not selected |
| `0030-01` | `0030-01:0020-09` | SYS.3 envelope: SYS.3 is not selected |
| `0031-01` | `0031-01:0020-09` | SYS.4 envelope: SYS.4 is not selected |
| `0032-01` | `0032-01:0020-09` | SYS.5 envelope: SYS.5 is not selected |

Feature-level predecessors already present: `0023:0020`, `0024:0020`, `0025:0020`, `0027:0020`.

### 8.2 Machine-enforced selected-profile edges (not implemented here)

| Gate | Owner Task | What it must reject (contract for later implementation) |
|---|---|---|
| Selected-profile readiness | `0025-02` | Included process with no complete valid `ecu-execution`; shared (none today) missing either side; fully external missing interface evidence **or** given an internal rating; out-of-scope process internally rated; activated conditional lifecycle missing; wrong-origin / substituted interface evidence |
| Evidence freeze | `0025-03` | Documentation-pipeline or synthetic evidence as ECU outcome; missing `0020-02` metadata |

`DEC-0020-002` CON-02: this register applies refuse-at-use when **it** is used (`REQ-0020-09-07`); it does not implement the freeze Tasks.

### 8.3 Relationships deliberately **not** added as TODO start-gates

| Hypothetical edge | Why it is not a `TODO` prerequisite this increment |
|---|---|
| `0023-11:0029-02` / `0030-02` | SYS.2/SYS.3 not included; would make excluded SYS an unconditional SWE blocker |
| `0024-02:0026` | VAL.1 not included; Feature `0024` goal requires `0026` only when intended-use validation **is** included |
| `0025-*:0026` / `0028`–`0032` / CS/FS Features | Those lifecycles are not selected |
| New `0020-09:0020-02` start-gate | `DEC-0020-002` ALT-03 rejected; refuse-at-use is enough |
| `_src/validate.py` registration | Forbidden by dispatch and `DEC-0020-002` ALT-02 |

---

## 9. Validation of this register (definition, not freeze)

| Check | Result |
|---|---|
| 14 included processes each have Feature + completion gate + TODO path | pass (`§4`) |
| Shared set recorded | pass (empty) |
| Fully external processes have interface-evidence gates and no internal rating | pass (`§6`) |
| CS/FS Features = 0; no CS/FS profile gate | pass (`0020-06`) |
| SYS/VAL no internal rating; envelopes not selected-profile execution | pass (`§7`) |
| Conditional/release/assessment relationships materialized as existing TODO **or** named `0025-02`/`0025-03` edges | pass (`§8`) |
| Executable paths currently satisfied with `ecu-execution` | **fail as freeze** — honest gap: all completion Tasks `[ ]`; no `ecu-execution` (`0020-08`). This does **not** fail this definition Task. `0025-02` SHALL reject freeze/assessment until those paths are satisfied. |
| Capability rating assigned | none — this register SHALL NOT assign `N/P/L/F` or CL |

---

## 10. Open decisions

| ID | Decision |
|---|---|
| `PD-0020-09-01` | Named party for the VAL.1 / intended-use validation interface |
| `PD-0020-09-02` | Named party for allocated SYS.2/SYS.3 inputs to `0023-11` (beyond unnamed kernel/system constraints) |
| `PD-0020-09-03` | Later inclusion of any SYS, VAL, HWE, ACQ, MLE, CS, or FS lifecycle (requires new Management `DEC-0020-*` and a revised register) |

---

## 11. Exclusions

Capability ratings; `Acceptance: ✓`; implementation of `0025-02` / `0025-03` freeze; `_src/validate.py` registration; adding new TODO start-gates onto `0025-*` or envelope Features; Feature `0020` integration; `main`; Feature `0033`; overwriting prior `0020-02`..`0020-08` owner_tokens; treating this register as `ecu-execution`.
