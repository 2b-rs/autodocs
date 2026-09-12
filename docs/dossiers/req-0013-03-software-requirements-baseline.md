# Software Requirements Baseline (`0013-03`)

## 1. Baseline Identity and Status

| Field | Value |
|---|---|
| Baseline ID | `SWR-0013-03-virtualized-automotive-ecu-software` |
| Candidate version | `0.1.0-candidate` |
| Product | `virtualized-automotive-ecu` |
| Project | `autodocs-ecu-software` |
| Scope | Software requirements derived from `SRB-0013-02` |
| Baseline status | `candidate-unapproved` |
| Classification | `internal` |

This is a controlled candidate baseline for Software Requirements (SWE.1). It is derived from the stakeholder requirements baseline (`req-0013-02-stakeholder-requirements-baseline.md`).

## 2. Derivation & Traceability
This baseline traces directly to the stakeholder baseline candidate `0.1.0-candidate`. Since customer functional sources remain `blocked-source` in `0013-02`, functional software requirements cannot be fully elaborated yet. Non-functional process and structural constraints are explicitly defined here.

## 3. Software Requirements (SWE.1)

### `SWR-0013-03-01` — Strict Scope Boundary
- **Statement:** The software SHALL NOT implement kernel behaviors, complete-ECU behaviors, hardware management, or vehicle functions not explicitly allocated to it.
- **Trace:** `REQ-0013-02-01` (Stakeholder boundary constraint).
- **Verification Method:** Architecture trace audit (SWE.2); document scan.
- **Priority:** `P0-must`
- **Status:** `candidate-confirmed`

### `SWR-0013-03-02` — Requirement Identification and Control
- **Statement:** Every elaborated software unit, interface, and test SHALL trace back to a unique, stable software requirement ID (SWR-XXX).
- **Trace:** `REQ-0013-02-02`, `REQ-0013-02-07`
- **Verification Method:** Traceability matrix review (SWE.6).
- **Priority:** `P0-must`
- **Status:** `candidate-confirmed`

### `SWR-0013-03-03` — Missing Intended-Use Fallback
- **Statement:** Until an authorized stakeholder intended-use source is provided, the software SHALL NOT implement assumed functional business logic.
- **Trace:** `REQ-0013-02-03`
- **Verification Method:** Inspection.
- **Priority:** `P0-must`
- **Status:** `blocked-source` (Waiting on Management decision `PD-0013-01-01`).

### `SWR-0013-03-04` — Deterministic Execution Constraints
- **Statement:** The software SHALL execute deterministically within the limits of the undefined virtualized environment, avoiding undefined behavior, race conditions, and unhandled memory faults.
- **Trace:** `REQ-0013-02-06` (Environment gap).
- **Verification Method:** Static analysis; unit testing (SWE.4); runtime sanitizers.
- **Priority:** `P1-high`
- **Status:** `candidate-derived`

### `SWR-0013-03-05` — Bounded Security & Safety Scope
- **Statement:** The software SHALL NOT implement ASIL-rated functional safety mechanisms or ISO 21434 cybersecurity mechanisms unless an explicit external constraint authorizes and defines them.
- **Trace:** `REQ-0013-02-12`
- **Verification Method:** Source code review; absence of unauthorized CS/FS claims.
- **Priority:** `P0-must`
- **Status:** `candidate-confirmed`

### `SWR-0013-03-06` — Data & Provenance Integrity
- **Statement:** The software's build and execution configuration SHALL retain full provenance, tracking exact component versions and ensuring configuration identity matches the authorized release package.
- **Trace:** `REQ-0013-02-11`, `REQ-0013-02-08`
- **Verification Method:** Software integration verification (SWE.5); Release package audit (SPL.2).
- **Priority:** `P1-high`
- **Status:** `candidate-derived`

### `SWR-0013-03-07` — Change and Communication Interfaces
- **Statement:** The software architecture SHALL support integration points for reporting system states and errors that comply with agreed external interface contracts (once defined by the system authority).
- **Trace:** `REQ-0013-02-04`, `REQ-0013-02-05`, `REQ-0013-02-09`
- **Verification Method:** Interface testing (SWE.5); qualification testing (SWE.6).
- **Priority:** `P2-medium`
- **Status:** `conditional-open`

## 4. Analytical Attributes

| Attribute | State |
|---|---|
| **Correctness & Feasibility** | Confirmed feasible; correctness is strictly bound to the non-functional constraints as functional logic is blocked. |
| **Interdependency** | High interdependency on `0013-02` decisions (especially missing functional and system inputs). |
| **Effort/Schedule** | Minimal implementation effort required for current constraints; blocked on requirements definition. |
| **Environment Impact** | `virtualized-automotive-ecu` constraints apply; actual environment unknown. |

## 5. Review and Status
This candidate baseline is ready for architectural breakdown (SWE.2) via task `0013-04`. It CANNOT be marked as `approved` until the underlying stakeholder requirements baseline is approved and the blocked-source decisions are resolved.
