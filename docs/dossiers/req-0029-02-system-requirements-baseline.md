# `REQ-0029-02` — ECU System Requirements Specification & Baseline (0029-02)

- **Record format:** `specification@v1`
- **Feature / Task:** `0029-02` (PREREQ: `0029-01`)
- **Governing Standard:** Automotive SPICE `SYS.2` (System Requirements Analysis)
- **Status:** `BASELINE-SYS2-SPECIFICATION`

---

## 1. System Requirements Breakdown
1. **`SYS-REQ-001` (Boot & Diagnostic Session)**:
   - ECU shall complete diagnostic cold boot within 200ms of battery power application and transition to UDS session `0x01`.
2. **`SYS-REQ-002` (Cyclic Telemetry Communication)**:
   - ECU shall broadcast vehicle health telemetry cyclically at 10ms ± 50µs over CAN-FD / SOME/IP.
3. **`SYS-REQ-003` (Fault Detection & FTTI)**:
   - ECU shall detect invalid sensor data within 20ms and transition actuators to safe state within FTTI <= 100ms.
4. **`SYS-REQ-004` (Secure Firmware Update)**:
   - ECU shall verify RSA-3072 signature and SHA-256 digest of update payload prior to non-volatile flash commit.

---

## 2. Traceability Matrix
- `SYS-REQ-001` <-> `SRC-OEM-01`
- `SYS-REQ-002` <-> `SRC-USR-01`
- `SYS-REQ-003` <-> `SRC-SAF-01`
- `SYS-REQ-004` <-> `SRC-REG-01`
