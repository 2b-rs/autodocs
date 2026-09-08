# `REQ-0023-07` — ECU Software Component Integration & Verification Specification (0023-07)

- **Feature / Task:** `0023-07` (PREREQ: `0023-02`, `0023-03`, `0023-06`)
- **Process ID:** `SWE.5` (Software Integration and Integration Testing)
- **Status:** `SWE5-SPECIFICATION-BASELINE`

---

## 1. Software Integration Sequence & Preconditions
- **Preconditions**:
  1. All 4 software units (`SWC-DIAG`, `SWC-TELEM`, `SWC-SAFETY`, `SWC-CRYPTO`) verified under `SWE.4` with 100% statement/branch coverage and 0 open defects.
  2. Software unit interfaces baselined in `_src/ecu/` and pinned in `SUP.8`.
- **Integration Sequence**:
  - **Step 1 (Security Subsystem)**: `SWC-CRYPTO` interface to hardware HSM driver.
  - **Step 2 (Diagnostic & Safety Subsystem)**: Integrate `SWC-SAFETY` and `SWC-DIAG` to verify fault monitoring and session transitions.
  - **Step 3 (Telemetry Subsystem)**: Integrate `SWC-TELEM` with `SWC-SAFETY` to broadcast telemetry and assert safe-state indicators.
  - **Step 4 (Complete ECU Software Build)**: Link all units into executable image `ecu_app_image.elf`.

---

## 2. Component Integration Verification Measures
| Measure ID | Target Interface | Verification Method | Pass / Fail Criteria | Trace Basis |
|---|---|---|---|---|
| `INT-SEC-01` | `SWC-CRYPTO` <-> HSM | Crypto API Test | Cryptographic handshake completed < 15ms | `SWE.2` Arch |
| `INT-DIAG-SAFE-01` | `SWC-DIAG` <-> `SWC-SAFETY` | Dynamic Interface Test | Diagnostic safe-state read matches latch | `SWE.2` Arch |
| `INT-TELEM-SAFE-01` | `SWC-TELEM` <-> `SWC-SAFETY`| Bus Interaction Test | Telemetry frame sets fault bit on safe state | `SWE.2` Arch |
| `INT-FULL-BUILD-01` | Complete Image | Binary Integration Test | Zero undefined symbols, memory fits partition | `SWE.2` Arch |

---

## 3. Regression Rationale & Environment
- **Environment**: Target hardware emulator running under QEMU / ARM Cortex-R52 virtual container.
- **Regression Selection**: Re-run all 4 integration measures on any component modification or interface adjustment.
