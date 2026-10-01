# SUP.10 Change Impact Analysis, Authorization, and Traceability Procedure (0016-04)

## 1. Scope & Purpose
- **Feature / Task**: `0016-04` (PREREQ: `0013-08`, `0016-02`)
- **Governing Standard**: Automotive SPICE `SUP.10`
- **Objective**: Enforce multi-dimensional impact analysis, prioritization, authorization gates, and end-to-end traceability before change implementation.

---

## 2. Multi-Dimensional Impact Analysis Framework
Prior to authorization, every `SUP.10` Change Request must evaluate impact across six dimensions:
1. **Requirements Impact**: Stakeholder requirements (`0013-02`), system/software requirements (`0013-03`).
2. **Architecture & Design Impact**: Software architecture (`SWE.2`), detailed unit design contracts (`SWE.3`).
3. **Verification & Test Impact**: Unit tests (`SWE.4`), integration tests (`SWE.5`), qualification batteries (`SWE.6`), validation scenarios (`VAL.1`).
4. **Risk & Safety Impact**: Exposure recalculation in `MAN.5` Risk Register (`REG-RSK-*`), FTTI/ASIL integrity impact.
5. **Schedule & Resource Impact**: Planned duration, agent capacity, milestone deadlines in `MAN.3`.
6. **Configuration & Baseline Impact**: Affected configuration items, baseline hashes, and intended target release (`SPL.2`).

---

## 3. Prioritization & Change Control Board (CCB) Authorization
- **Priority Classes**:
  - *Emergency (P1)*: Critical safety or blocking integration blocker. Expedited CCB review within 2 hours.
  - *High (P2)*: Significant defect resolution or major milestone scope modification.
  - *Medium / Low (P3/P4)*: Non-blocking optimization or deferred cosmetic enhancement.
- **Change Authorization Gate**:
  - Requires signed concurrence from:
    1. Project Lead (`jadzia`) — Schedule & resource approval.
    2. Software Architect (`kira`) — Architecture & technical integrity.
    3. QA / Safety Authority (`jake` / `odo`) — Verification & safety impact.
- **Traceability Enforcement**:
  - The Change Request record must capture explicit links: `CR -> REQ -> ARCH -> CODE -> TEST -> BASELINE`.
