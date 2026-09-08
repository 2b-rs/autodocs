---
schema_version: "1.0"
id: "0028-03"
level: "task"
parent: "0028"
state: "closed"
visibility: "internal"
prerequisites:
  - "0028-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2733"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0028-03:0028-02 Perform and retain controlled stakeholder elicitation and analysis: methods, dates, participants, normal/abnormal/out-of-use intended-use scenarios, environments/variants, needs/constraints, priorities/rationale, assumptions, duplicates, conflicts and authority-backed resolution or explicit open disposition, changes, impacts, risks, status and communication. Preserve source and stakeholder trace; never invent a conflict resolution or agreement. Write only `docs/dossiers/req-0028-03-elicitation-analysis.md`, own claim and bookkeeping. DoD: coverage matrix, scenario/environment inventory, unresolved-conflict register, findings disposition, digests and REF; no baseline approval or SYS.1 credit.

## Scope

- **Capability/cognitive profile:** `unprivileged`, direct Git/stdlib, cognitive `high` (breadth/depth/context/ambiguity/verification high), distinct roles; 60–120 minutes, CPU <2 minutes, no network, uncertainty ±35%, risk high.
  - **Test derivation:** stakeholder/scenario/environment coverage, orphan, duplicate, conflict and prohibited-claim risks; deterministic scans plus bounded manual analysis review.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** reversible analysis only; it cannot create the agreed consumer baseline and is reviewed through `0028-04` and `0028-05`.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
