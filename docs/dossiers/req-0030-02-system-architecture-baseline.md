# `REQ-0030-02` — ECU System Architecture Design & Baseline (0030-02)

- **Record format:** `specification@v1`
- **Feature / Task:** `0030-02` (PREREQ: `0030-01`)
- **Governing Standard:** Automotive SPICE `SYS.3` (System Architectural Design)
- **Status:** `BASELINE-SYS3-ARCHITECTURE`

---

## 1. System Architectural Elements & Allocation
1. **`ELEM-HW-MCU` (Hardware Core)**:
   - Quad-core ARM Cortex-R52 with hardware lockstep execution and MPU isolation.
2. **`ELEM-SW-RUNTIME` (Software Runtime Layer)**:
   - Posix/AUTOSAR adaptive runtime executing application partitions with memory protection.
3. **`ELEM-COMM-IF` (Communication Subsystem)**:
   - Isolated CAN-FD / Ethernet driver handling frame filtration and hardware timestamping.
4. **`ELEM-SEC-HSM` (Hardware Security Module)**:
   - Dedicated cryptographic enclave managing RSA keys, signature verification, and secure boot sequencing.

---

## 2. System Requirement Allocation Matrix
- `SYS-REQ-001` -> `ELEM-SW-RUNTIME`, `ELEM-COMM-IF`
- `SYS-REQ-002` -> `ELEM-COMM-IF`, `ELEM-HW-MCU`
- `SYS-REQ-003` -> `ELEM-HW-MCU`, `ELEM-SW-RUNTIME`
- `SYS-REQ-004` -> `ELEM-SEC-HSM`, `ELEM-SW-RUNTIME`
