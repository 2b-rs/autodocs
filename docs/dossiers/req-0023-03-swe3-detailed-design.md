# `REQ-0023-03` — ECU Software Detailed Design & Unit Interface Specifications (0023-03)

- **Feature / Task:** `0023-03` (PREREQ: `0023-02`)
- **Process ID:** `SWE.3` (Software Detailed Design and Unit Construction)
- **Status:** `SWE3-DETAILED-DESIGN-BASELINE`

---

## 1. Software Units Detailed Design

### 1.1 Diagnostic Service Unit (`unit_uds_service.c`)
- **Static Interface**: `int handle_uds_request(const uint8_t *req, size_t req_len, uint8_t *resp, size_t *resp_len);`
- **Control Flow**: Inspects byte 0 (Service ID); dispatches to session control (`0x10`), routine control (`0x31`), or security access (`0x27`). Returns NRC `0x11` (ServiceNotSupported) for unrecognized requests.
- **Resource Constraints**: Stack buffer bounded to 256 bytes; non-blocking execution completed within < 5ms.

### 1.2 Telemetry Cyclic Unit (`unit_telemetry_stream.c`)
- **Static Interface**: `void publish_telemetry_frame(const TelemetrySnapshot *data);`
- **Algorithm**: Packs 64-bit timestamp, vehicle velocity, and battery status into CAN-FD payload with crc8 SAE-J1850 checksum.
- **Timing Constraint**: Invoked cyclically by OS timer task every 10.00ms ± 0.05ms.

### 1.3 Safety Monitor Unit (`unit_safety_guard.c`)
- **Static Interface**: `bool evaluate_safety_limits(int32_t sensor_reading, uint32_t delta_time_ms);`
- **Control Flow**: Plausibility check against upper/lower threshold; if violated for >= 2 consecutive cycles, sets `g_safe_state_latch = true` and signals actuator shutdown.

### 1.4 Cryptographic Interface Unit (`unit_crypto_verifier.c`)
- **Static Interface**: `CryptoResult verify_image_signature(const uint8_t *digest, const uint8_t *sig, const PublicKey *key);`
- **Algorithm**: Hardware HSM driver call for PKCS#1 v1.5 RSA-3072 signature verification.

---

## 2. Coding Principles & Guidelines
- Adherence to MISRA C:2012 / AUTOSAR C++14 coding rules.
- Mandatory deterministic execution: zero dynamic memory allocation (`malloc`/`free` prohibited).
- Bounded loop iteration counts and fail-safe fallback returns.
