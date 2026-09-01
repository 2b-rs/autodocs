# `REQ-0029-0032` — Conditional Input Baselines and Interfaces for SYS.2, SYS.3, SYS.4, and SYS.5 (0029-01, 0030-01, 0031-01, 0032-01)

- **Governing Standard:** Automotive SPICE (PAM 4.0) System Engineering Lifecycle
- **Features Covered:** `0029-01` (SYS.2 Inputs), `0030-01` (SYS.3 Inputs), `0031-01` (SYS.4 Inputs), `0032-01` (SYS.5 Inputs)
- **Governing Architecture:** `DEC-0022-001`, `DEC-0020-001`, `DEC-0020-002`

---

## 1. Conditional Input Acceptance Matrix
| Process | Input Nature | Internal Path Source | External Path Preconditions | Failure & Refusal Behavior |
|---|---|---|---|---|
| **SYS.2 (0029-01)** | Stakeholder Requirements | Feature `0028` Output (`0028-04`) | Validated external responsible party + baseline hash + explicit acceptance gate | Refuse unpinned, unapproved, or anonymous stakeholder inputs |
| **SYS.3 (0030-01)** | System Requirements | `0029-02` Baseline | Validated external system requirement specification + traceability matrix | Refuse untraced or inconsistent requirement baselines |
| **SYS.4 (0031-01)** | System Architecture & Elements | `0030-02` Architecture Baseline | Validated external architecture elements + interface contracts | Refuse incomplete element allocation or unknown interfaces |
| **SYS.5 (0032-01)** | System Requirements & Integrated System | `0029-02` + `0031-03` | Validated external integrated build + test environment digest | Refuse unverified integrated binaries or mismatched toolchains |

---

## 2. Shared Boundary Governance
- **No False Internal Credit**: Operating external input interfaces does NOT credit internal execution of SYS.1..SYS.5.
- **Fail-Closed Gate**: In the current 14-process nucleus, all SYS processes remain external. Any consumer invoking internal SYS outputs must fail closed unless a formal profile extension is authorized by Management.
