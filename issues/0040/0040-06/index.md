---
schema_version: "1.0"
id: "0040-06"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:552"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Add Automotive SPICE references to the process documentation, distinguishing process support from assessed capability. REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`.

## Scope

- **Reason (2026-08-18, trilateral agreement round 5):** Rescoped to near-zero. "References in every process document at the points where they carry weight" is an unbounded instruction against 71 files in `docs/pipeline/`, with no operational return for a single-operator project that makes no assessment claim. The one durable insight — finding A, that "Evidence Baseline" is this repository's own term and splits into a SUP.8 baseline and the SWE/SYS traceability practices — is five lines and is carried in `docs/pipeline/process-roles.md` and in the requirements baseline. Standard references are added where a document is touched anyway, never as a campaign of their own. `RQ-STD-01/02` remain binding as a *manner of writing*, not as a Task.
  - **Requirements covered:** `RQ-STD-01`, `RQ-STD-02`.
  - **Context:** Section 5 of the requirements baseline holds a provisional mapping — SUP.8 for baselines, the SWE/SYS bidirectional-traceability and consistency practices, SUP.10 and PA 2.1 for decision circumstances, SUP.1 for the QA Manager's independence, SUP.9 for escalation. It is analysis input and must be verified against the applicable PAM edition before it becomes normative. The customer's own premise was imprecise in one respect worth preserving in the documentation: "Evidence Baseline" is this repository's term, not ASPICE terminology, and it splits into a SUP.8 baseline and the SWE/SYS traceability practices — see finding A.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** references are additive documentation and make no capability claim; the risk of overclaiming is bounded by the mandatory qualification and re-checked in aggregate at `0040-09`.

## Acceptance criteria

- **AC-001** Each process document gains references at the points where they carry weight, not decoratively. Every reference states the nature of the relationship (direct or supporting) and carries the standing qualification that this is process support and not assessed capability. The terminological separation from finding A is documented. The boundary against the ECU assessment of Features `0011`–`0032` is explicit. Any reference that cannot be verified against the applicable PAM edition is marked as unverified rather than asserted

## Definition of Done

Committed with real `REF`; no reference claims conformance; the ECU boundary appears in every document that carries references; unverified references are visibly marked as such.
