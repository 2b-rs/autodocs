# `REQ-0028-02` — Controlled Stakeholder and Source Register (0028-02)

- **Record format:** `register@v1`
- **Feature / Task:** `0028-02` (PREREQ: `0028-01`)
- **Governing Architecture:** `DEC-0028-001`, `DEC-0022-001`
- **Status:** `BASELINE-STAKEHOLDER-REGISTER`

---

## 1. Stakeholder & Source Directory
| Source ID | Stakeholder Category | Role / Remit | Originator / Authority | Confidentiality | Status |
|---|---|---|---|---|---|
| `SRC-OEM-01` | Customer / OEM | Complete Vehicle Integration & Power Net Requirements | OEM Vehicle Engineering (`auth:oem-lead`) | Restricted | Controlled |
| `SRC-REG-01` | Regulatory Body | UNECE R155/R156, ECE Braking & Chassis Regulations | International Standards Board | Public | Approved |
| `SRC-SAF-01` | Functional Safety | ISO 26262 Item Definition & Safety Goals | Vehicle Safety Assessor (`auth:safety-lead`) | Confidential | Baselined |
| `SRC-USR-01` | Driver / Operator | HMI & Telemetry Intended Operational Scenarios | User Experience Research (`auth:ux-lead`) | Internal | Reviewed |
| `SRC-SUP-01` | Tier-1 / Silicon | Hardware Microcontroller Specification & Errata | Semiconductor Vendor (`auth:silicon-rep`) | Proprietary | Baselined |

---

## 2. Integrity Controls
- Duplicate source IDs strictly rejected.
- Anonymous authorities prohibited (`originator` field mandatory).
- Scope changes require append-only supersession records.
