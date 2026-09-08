# `REQ-0023-02` — ECU Software Architectural Design Specification (0023-02)

- **Feature / Task:** `0023-02` (PREREQ: `0023-01`)
- **Process ID:** `SWE.2` (Software Architectural Design)
- **Status:** `SWE2-ARCHITECTURE-BASELINE`

---

## 1. Software Component Decomposition
1. **`SWC-DIAG` (Diagnostic Handler)**:
   - Manages UDS service requests (`0x10`, `0x22`, `0x2E`, `0x31`, `0x34`, `0x36`, `0x37`).
2. **`SWC-TELEM` (Telemetry Engine)**:
   - Streams vehicle status frames at 100 Hz cadence with jitter compensation.
3. **`SWC-SAFETY` (Safety Monitor & Watchdog)**:
   - Evaluates sensor bounds, computes plausibility checksums, and commands safe-state actuator transitions.
4. **`SWC-CRYPTO` (Cryptographic & Secure Boot Interface)**:
   - Interfaces with hardware HSM for RSA-3072 signature verification and keystore access.

---

## 2. Requirement Allocation & Concurrency
- `SW-REQ-001` (UDS Diagnostic Interface) -> `SWC-DIAG`
- `SW-REQ-002` (Cyclic Telemetry Delivery) -> `SWC-TELEM`
- `SW-REQ-003` (Plausibility & Safety Shutdown) -> `SWC-SAFETY`
- `SW-REQ-004` (Cryptographic Verification) -> `SWC-CRYPTO`
