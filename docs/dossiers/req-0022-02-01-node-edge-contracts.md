# `REQ-0022-02-01` — Versioned Lifecycle Node and Edge Contracts (0022-02.01)

- **Format:** `specification@v1`
- **Feature / Task:** `0022-02.01` (PREREQ: `0022-01`)
- **Governing Standard:** Automotive SPICE (PAM 4.0) Traceability Model

---

## 1. Node Typing Taxonomy
1. **Artifact Nodes**:
   - `requirement` (Stakeholder, System, Software).
   - `architecture-element` (Static component, Dynamic interaction).
   - `detailed-design-unit` (Module, Unit design specification).
   - `source-code-unit` (Source file, Function, Class).
   - `configuration-item` (Build manifest, Environment parameter).
2. **Verification Measure & Result Nodes**:
   - `measure` (`SWE.4`, `SWE.5`, `SWE.6`, `SYS.4`, `SYS.5`, `VAL.1`).
   - `result` (Pass/Fail observation with immutable log digest).

---

## 2. Edge Taxonomy & Verification Bases
- **Bidirectional Trace Edges**:
  - `satisfies` (`software-requirement` -> `stakeholder-requirement`)
  - `implements` (`source-code-unit` -> `detailed-design-unit`)
  - `verifies-unit` (`SWE.4-measure` -> `detailed-design-unit`)
  - `verifies-integration` (`SWE.5-measure` -> `architecture-element`)
  - `qualifies-software` (`SWE.6-measure` -> `software-requirement`)
  - `validates-operational` (`VAL.1-measure` -> `stakeholder-requirement`)
- **Node & Edge Invariants**:
  - Closed vocabularies for all node and edge types.
  - Mandatory responsibility origin (`origin=ecu-execution|process-definition`).
  - Strict refusal of non-ECU evidence substitution.
