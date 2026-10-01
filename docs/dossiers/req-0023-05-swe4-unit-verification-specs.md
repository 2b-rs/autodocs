# `REQ-0023-05` — ECU Software Unit Verification Specification (0023-05)

- **Feature / Task:** `0023-05` (PREREQ: `0023-03`, `0023-04`)
- **Process ID:** `SWE.4` (Software Unit Verification)
- **Status:** `SWE4-SPECIFICATION-BASELINE`

---

## 1. Unit Verification Methods & Coverage Objectives
- **Static Verification**:
  - Clang-Tidy static analysis for MISRA C:2012 compliance.
  - Automated cyclomatic complexity audit (maximum threshold: <= 10 per unit function).
- **Dynamic Unit Verification**:
  - Boundary value analysis and statement/branch/MC-DC structural coverage objectives.
  - Target coverage: 100% Statement, 100% Branch coverage for ASIL-B / Quality-Managed units.

---

## 2. Unit Test Measures Matrix
| Measure ID | Target Unit | Test Method | Input Vectors / Scenario | Expected Criteria | Trace Basis |
|---|---|---|---|---|---|
| `UT-DIAG-01` | `SWC-DIAG` | Dynamic Unit Test | Standard UDS Session `0x10 0x01` | Return Positive Response `0x50 0x01` | `SW-REQ-001` |
| `UT-DIAG-02` | `SWC-DIAG` | Dynamic Unit Test | Unsupported Service `0x99` | Return NRC `0x7F 0x99 0x11` | `SW-REQ-001` |
| `UT-TELEM-01` | `SWC-TELEM` | Timing & Dynamic | 100 Hz cyclic timer trigger | Frame formatted with CRC-8 | `SW-REQ-002` |
| `UT-SAFE-01` | `SWC-SAFETY` | Boundary & Fault | Sensor value out of range for 2 cycles | `g_safe_state_latch = true` | `SW-REQ-003` |
| `UT-CRYPTO-01`| `SWC-CRYPTO` | Dynamic Test | Valid RSA-3072 signature payload | Return `CRYPTO_SUCCESS` | `SW-REQ-004` |
| `UT-CRYPTO-02`| `SWC-CRYPTO` | Dynamic Test | Tampered payload byte | Return `CRYPTO_ERR_SIG_INVALID` | `SW-REQ-004` |

---

## 3. Regression Rationale & Environment Configuration
- **Toolchain**: Host GCC / `unity` unit test harness with deterministic mock drivers for hardware registers.
- **Regression Selection**: 100% test battery executed automatically on any unit change.
