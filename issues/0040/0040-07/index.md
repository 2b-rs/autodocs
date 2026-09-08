---
schema_version: "1.0"
id: "0040-07"
level: "task"
parent: "0040"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:560"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Demonstrate that the agent instructions actually realize the defined processes, and make the demonstration repeatable. REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`.

## Scope

- **Reason (2026-08-18, explicit customer decision):** Deferred by the customer, not by an agent: the question of effectiveness "wird erst deutlich später beantwortet — wenn das Projekt Früchte trägt". Replaced for now by the cheaper measurement rule agreed in round 5 and recorded in section 10 of `docs/pipeline/process-roles.md`: after 20 completed Tasks, count how many `TK-2` decision records were actually written and how many escalations occurred — **at zero the rule is withdrawn, not extended**. `RQ-EFF-01` stays open and unsatisfied; this is a deferral with a named condition, not a claim of fulfilment.
  - **Requirements covered:** `RQ-EFF-01`.
  - **Context:** This is the customer's sharpest requirement — "Stelle sicher, dass die Agenteninstruktionen die Prozesse auch tatsächlich verwirklichen." A process that exists only in `docs/pipeline/` and is contradicted or simply not reachable from `AGENTS.md` is not in effect. `T8` is the proof that this gap is real: the documented intent and the binding instruction disagreed, and the instruction won.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the Task's own output *is* a verification result, and it is re-examined by the integrator at `0040-09` as the Feature's effectiveness evidence; a second checkpoint here would review the same evidence twice.

## Acceptance criteria

- **AC-001** A checkable consistency statement covers, for each process obligation introduced by `0040-01`, `0040-03`, `0040-05` and `0040-06`: which binding instruction text realizes it, and where. Obligations with no realizing instruction are reported as findings. Contradictions between authority documents are reported as findings. The check is repeatable — a tool, or a documented procedure precise enough that two reviewers reach the same result — and is run against the current state with retained evidence

## Definition of Done

Committed with real `REF`; zero unrealized obligations and zero contradictions remain, or each residual has an explicit recorded disposition; the check is registered wherever repeatable checks are catalogued.
